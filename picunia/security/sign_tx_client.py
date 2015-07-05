import subprocess
import threading
import zlib, base64
import time
import select
import logging
from picunia.config.settings import Settings
from crypt.reedsolo import RSCodec, ReedSolomonError
from Queue import Queue
from protocol import assemble_package, disassemble_package, assemble_package_tx_only
from transmitter import transmit_package
from pycoin.tx.Tx import Tx


send_queue = Queue()
resend_package = False

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Consumer(threading.Thread):
    def __init__(self, e):
        threading.Thread.__init__(self)
        self.event = e

    def confirm_package(self, package):
        global resend_package
        while True:
            transmit_package(package)
            logger.debug("Wait for answer..")
            self.event.wait()
            logger.debug("Wait released..")
            if not resend_package:
                logger.debug("not Resend package")
                break
            time.sleep(1)

    def run(self):
        global send_queue
        global resend_package

        package = send_queue.get()
        logger.debug("Consumed")

        self.confirm_package(package)

        send_queue.task_done()

        logger.info("End Consumer")


class Receiver:
    class ReceiverReader(threading.Thread):
        def __init__(self, stdout, stderr, event, compress=True):
            threading.Thread.__init__(self)
            self.stdout = stdout
            self.stderr = stderr
            self.compress = compress
            self.func_cb = []
            self.event = event
            self.signal = True

        def check_signature(self, tx_hex):
            if tx_hex.find('tpub') == 0 or tx_hex.find('xpub') == 0:
                return True

            tx = Tx.tx_from_hex(tx_hex)
            for idx, tx_in in enumerate(tx.txs_in):
                if not tx.is_signature_ok(tx_in_idx=idx):
                    return False
            return True

        def run(self):
            in_packet = False
            packet = ''
            global resend_package
            while self.signal:
                self.event.clear()
                readers, _, _ = select.select([self.stdout, self.stderr], [], [])
                if in_packet:
                    if self.stdout in readers:
                        data = self.stdout.read(1)
                        if not data:
                            break
                        packet += data
                        continue
                if self.stderr in readers:
                    line = self.stderr.readline()
                    if not line:
                        break
                    if line.startswith('### CARRIER '):
                        start = time.time()
                        in_packet = True
                        packet = ''
                    elif line.startswith('### NOCARRIER '):
                        in_packet = False
                        if len(packet) < 100:
                            continue
                        b = bytearray()
                        b.extend(packet)

                        rs = RSCodec(Settings.RSCODEC_NSYM)
                        try:
                            packet = rs.decode(b)
                            if self.compress:
                                packet = zlib.decompress(base64.b64decode(packet))
                        except:
                            logger.debug("Package broken, wait for resend..")
                            resend_package = True
                            self.event.set()
                            continue

                        logger.debug("Got packet: %s", packet)
                        end = time.time()
                        logger.debug("It took %s", (end - start))

                        p = disassemble_package(packet)

                        if not p.rtype == 'SGN':
                            logger.debug("This package is not from signserver, ignore")
                            continue

                        if p.tx.find('RESEND') > 0:
                            logger.debug("RESEND sent by the server..")
                            resend_package = True
                            self.event.set()
                            continue

                        if not self.check_signature(p.tx):
                            logger.debug("SIGNATURE ERROR wait for resend..")
                            resend_package = True
                            self.event.set()
                            continue

                        # Callback function with the signed transaction
                        cb = self.func_cb.pop(0)
                        if cb is not None:
                            cb(p.tx)

                        resend_package = False
                        self.event.set()
                        logger.info("End Receiver")
                        self.signal = False

    def __init__(self, event, compress=True, **kwargs):
        self.p = subprocess.Popen(['minimodem', '-r', '-8', '-A',
            kwargs.get('baudmode', 'rtty')] + kwargs.get('extra_args', []),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.compress = compress
        self.reader = Receiver.ReceiverReader(self.p.stdout, self.p.stderr, event, compress)
        self.reader.setDaemon(True)
        self.reader.start()

receiver = None

def start_service():
    event = threading.Event()
    logger.info("Start Receiver")

    global receiver
    receiver = Receiver(event,
                        compress=Settings.USE_COMPRESSION,
                        baudmode=Settings.BAUD_MINIMODEM)
    logger.info("Start Consumer")

    consumer = Consumer(event)
    consumer.setDaemon(True)
    consumer.start()

    #receiver.p.wait()

def stop_service():
    global receiver
    receiver.reader.signal = False
    receiver.p.terminate()

def sign_tx(wallet_index, key_index, tx, cb):
    global receiver

    if not isinstance(wallet_index, int):
        raise TypeError("Expected int, got %s" % (type(wallet_index),))
    if not isinstance(key_index, list):
        raise TypeError("Expected list, got %s" % (type(key_index),))
    if not isinstance(tx, unicode):
        raise TypeError("Expected int, got %s" % (type(tx),))

    receiver.reader.func_cb.append(cb)

    package = assemble_package(wallet_index, key_index, tx, rtype="TXN")

    send_queue.put(package)

def request_public_key(wallet_index, cb):
    global receiver

    receiver.reader.func_cb.append(cb)

    # Since we are requesting a public key we can leave tx empty.
    # And key_index is zero since this is the first key.
    package = assemble_package(wallet_index, [0], '', rtype="KEY")

    send_queue.put(package)


# TESTING ----------------------------
'''
import time
start_service()
time.sleep(5)

def callback(tx_hex):
    print "callback called"
    print tx_hex

for i in range(0,5):
    request_public_key(i, callback)

time.sleep(500000)



t = u'01000000013ee4638534d6a48979e79fad3a98158f0c1265f247560af07ec20fb1488d0b910000000000ffffffff02ecff0000000000001976a914fd906708ad09ee08bc03cda5db4983e3a817b73b88ac593b0800000000001976a9145e518af5696b29693c266086d46fd73943d87d1f88ac0000000055620900000000001976a9143575a1070562bc3d348b557a9e51722e2878697288ac' 
sign_tx(4657,4, t, callback)
time.sleep(500000)


sign_tx(4967,8,'XTN', '0100000002d636cae1cb2db9f586ae4e7cccd56e613f87cc6bfa687f659de2b26e65b5fb1b0100000000ffffffff1a054bb7b551b296d7bfdddda81c591430da90f5b9ac28fe07391b5646c8da710000000000ffffffff02a0050000000000001976a9146be7733f895908c7a8e412e29580c88bdb105c7488ac930b0000000000001976a914a6a2371e74f88918dd705d9a23a7d1ac991046f588ac000000001d2b0000000000001976a914a6a2371e74f88918dd705d9a23a7d1ac991046f588ac260d0000000000001976a914a41d436944bec4107f7124463071c9adbcf5b6ca88ac')
sign_tx(925,10,'XTN', '0100000001f87239ac1658887a50e5f0a9b85b5932625cf5327429acaf5a7d922b8cd81f240100000000ffffffff0225220000000000001976a914841de1c8c900a6902528f8924254f8da56c559e388ac27c00000000000001976a9149476f505c1b7d7b31e1ad1fae8acf967a38210ba88ac000000005c090100000000001976a9149476f505c1b7d7b31e1ad1fae8acf967a38210ba88ac')
sign_tx(6865,2,'XTN', '010000000152ee011e4d01b7db9a7940f9440cd28688722e3905457f64da5f4fc5e8c7c16e0100000000ffffffff0292250000000000001976a91459d55e2898fc2016c1d4a11d61dadff348b3ecd888ac142b0100000000001976a914328047f57b5bb98b668a6e0fa5180babf7e027b988ac00000000b6770100000000001976a914328047f57b5bb98b668a6e0fa5180babf7e027b988ac')
sign_tx(692,4,'XTN' , '0100000001efb7a4c1cecf9fbed9e3c368b3ef00116788285b036596a9fc4162124e559bb10100000000ffffffff0271110000000000001976a9144bb36dce89a414b18dd3e7adf2ff996f46ead9a488acac6a0000000000001976a914e29d09e7e5c5c04bb28e3eaa002d26af3c3ba99e88ac000000002da30000000000001976a914e29d09e7e5c5c04bb28e3eaa002d26af3c3ba99e88ac')
'''

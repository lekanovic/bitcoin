import subprocess
import threading
import zlib, base64
import time
import select
import logging
import os
import signal
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
            self.func_cb = None
            self.event = event
            self.signal = True

        def is_package_valid(self, s):
            '''
            "### NOCARRIER ndata=628 confidence=3.0 ampl=1.999 bps=3000.00 (rate perfect) ###"
            '''
            a = s.split('=')
            ndata = float(a[1].split(' ')[0])
            confidence = float(a[2].split(' ')[0])
            ampl = float(a[3].split(' ')[0])
            if confidence < 2.2 or ndata < 100 or ampl < 1.2:
                return False
            return True

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

                        if not self.is_package_valid(line):
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
                        self.func_cb(p.tx)

                        resend_package = False
                        self.event.set()
                        logger.info("End Receiver")
                        self.signal = False

    def __init__(self, event, compress=True, **kwargs):
        self.p = subprocess.Popen(['minimodem', '-r', '-8', '-A', '-c', Settings.CONFIDENCE_MINIMODEM,
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

    time.sleep(1)

def stop_service():
    global receiver
    receiver.reader.signal = False
    pid = receiver.p.pid

    os.kill(pid, signal.SIGKILL)

def sign_tx(wallet_index, key_index, tx, cb):
    global receiver

    if not isinstance(wallet_index, int):
        raise TypeError("Expected int, got %s" % (type(wallet_index),))
    if not isinstance(key_index, list):
        raise TypeError("Expected list, got %s" % (type(key_index),))
    if not isinstance(tx, unicode):
        raise TypeError("Expected unicode, got %s" % (type(tx),))

    receiver.reader.func_cb = cb

    package = assemble_package(wallet_index, key_index, tx, rtype="TXN")

    send_queue.put(package)

def request_public_key(wallet_index, cb):
    global receiver

    receiver.reader.func_cb = cb

    # Since we are requesting a public key we can leave tx empty.
    # And key_index is zero since this is the first key.
    package = assemble_package(wallet_index, [0], '', rtype="KEY")

    send_queue.put(package)


# TESTING ----------------------------
def callback(tx_hex):
    print "+++++++++callback called+++++++++"
    print tx_hex

def test_key():
    start_service()
    time.sleep(2)

    request_public_key(30, callback)

    time.sleep(30)

def test_sign():
    start_service()
    time.sleep(2)

    t = u"0100000001a3a2702d3c1ffe732ec5104ee215e06e2162815069c39a36943dc2c2e1dabd540000000000ffffffff0300000000000000002a6a28436875636b204e6f727269732066696e697368656420576f726c64206f662057617263726166742e10270000000000001976a9149f35ecd88caf647acec5445728bd667a8adb7f3488acf6726600000000001976a914d50a29953fe8fa5c8d18ed60c6400fc7c508b79a88ac0000000016c16600000000001976a914d17fd859759cce0aec42857a06e9adc70354cc5d88ac"
 
    sign_tx(3,[117], t, callback)
    time.sleep(30)

#test_sign()
#test_key()


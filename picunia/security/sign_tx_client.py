import subprocess
import threading
import zlib, base64
import time
import select
import logging
from signer import Signer
from crypt.reedsolo import RSCodec, ReedSolomonError
from Queue import Queue
from protocol import assemble_package, disassemble_package, assemble_package_tx_only
from transmitter import transmit_package


send_queue = Queue()
resend_package = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Consumer(threading.Thread):
    def __init__(self, e):
        threading.Thread.__init__(self)
        self.event = e

    def run(self):
        global send_queue
        global resend_package
        while True:
            package = send_queue.get()
            logger.debug("Consumed")

            while True:
                transmit_package(package)
                logger.debug("Wait for answer..")
                self.event.wait()
                if not resend_package:
                    break
                time.sleep(1)

            send_queue.task_done()


class Receiver:
    class ReceiverReader(threading.Thread):
        def __init__(self, stdout, stderr, event, compress=True, cb=None):
            threading.Thread.__init__(self)
            self.stdout = stdout
            self.stderr = stderr
            self.compress = compress
            self.func_cb = cb
            self.event = event

        def run(self):
            in_packet = False
            packet = ''
            global resend_package
            while True:
                readers, _, _ = select.select([self.stdout, self.stderr], [], [])
                self.event.clear()
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
                        if len(packet) < 30:
                            continue
                        b = bytearray()
                        b.extend(packet)

                        rs = RSCodec(10)
                        try:
                            packet = rs.decode(b)
                        except ReedSolomonError:
                            logger.debug("Package broken, wait for resend..%s", b)
                            resend_package = True
                            self.event.set()
                            continue

                        if self.compress:
                            try:
                                packet = zlib.decompress(base64.b64decode(packet))
                            except:
                                pass

                        logger.debug("Got packet: %s", packet)
                        end = time.time()
                        logger.debug("It took %s", (end - start))

                        p = disassemble_package(packet)

                        resend_package = False
                        self.event.set()
                        # Callback function with the signed transaction
                        if self.func_cb is not None:
                            self.func_cb(p.tx)

    def __init__(self, event, cb=None, compress=True, **kwargs):
        self.p = subprocess.Popen(['minimodem', '-r', '-8', '-A',
            kwargs.get('baudmode', 'rtty')] + kwargs.get('extra_args', []),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.compress = compress
        self.reader = Receiver.ReceiverReader(self.p.stdout, self.p.stderr, event, compress, cb)
        self.reader.setDaemon(True)
        self.reader.start()

def start_service(callback):
    use_compression = True
    baud = '3000'
    event = threading.Event()
    logger.info("Start Receiver")

    receiver = Receiver(event, cb=callback, compress=use_compression, baudmode=baud)
    logger.info("Start Consumer")

    consumer = Consumer(event)
    consumer.start()

    #receiver.p.wait()

def sign_tx(account_nr, key_index, netcode, tx, cb):
    if not isinstance(account_nr, int):
        raise TypeError("Expected int, got %s" % (type(account_nr),))
    if not isinstance(key_index, int):
        raise TypeError("Expected int, got %s" % (type(key_index),))
    if not isinstance(netcode, str):
        raise TypeError("Expected int, got %s" % (type(netcode),))
    if not isinstance(tx, unicode):
        raise TypeError("Expected int, got %s" % (type(tx),))

    logger.info("Starting service...")
    start_service(cb)

    package = assemble_package(account_nr, key_index, netcode, tx)
    send_queue.put(package)

'''
sign_tx(12,0,'XTN', '01000000015a06d623ff099d77dbba3cd6fd2eec42f250768c61d443584b53a827acaaad580100000000ffffffff0600000000000000002a6a284163636f7264696e6720746f2074686520456e6379636c6f7065646961204272697474616e69636100000000000000002a6a282c20746865204e617469766520416d65726963616e202671756f743b547261696c206f662054656100000000000000002a6a2872732671756f743b20686173206265656e207265646566696e656420617320616e7977686572652000000000000000001a6a187468617420436875636b204e6f727269732077616c6b732e10270000000000001976a914bd52402e41483cc632ced18ad798b1b8c59de7a688acd3dc0700000000001976a914aeb7b78c4e59a0613260b949b863e2a4dcdf3dc688ac00000000f32a0800000000001976a914aeb7b78c4e59a0613260b949b863e2a4dcdf3dc688ac')


package = assemble_package(12, 0, "XTN", '01000000015a06d623ff099d77dbba3cd6fd2eec42f250768c61d443584b53a827acaaad580100000000ffffffff0600000000000000002a6a284163636f7264696e6720746f2074686520456e6379636c6f7065646961204272697474616e69636100000000000000002a6a282c20746865204e617469766520416d65726963616e202671756f743b547261696c206f662054656100000000000000002a6a2872732671756f743b20686173206265656e207265646566696e656420617320616e7977686572652000000000000000001a6a187468617420436875636b204e6f727269732077616c6b732e10270000000000001976a914bd52402e41483cc632ced18ad798b1b8c59de7a688acd3dc0700000000001976a914aeb7b78c4e59a0613260b949b863e2a4dcdf3dc688ac00000000f32a0800000000001976a914aeb7b78c4e59a0613260b949b863e2a4dcdf3dc688ac')

sender = Transmitter(compress=use_compression, baudmode=baud)
sender.write(package)

sender.close()
time.sleep(10)
'''
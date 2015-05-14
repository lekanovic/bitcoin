import subprocess
import threading
import select
import zlib, base64
import logging
from threading import Thread
from crypt.reedsolo import RSCodec, ReedSolomonError
from Queue import Queue
from signer import get_public_key, sign_tx
from protocol import assemble_package, disassemble_package, assemble_package_tx_only
from transmitter import transmit_package
from picunia.config.settings import Settings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

msg_queue = Queue()
prev_tx = {}

class Consumer(threading.Thread):

    def sign(self, p):
        tx_signed_hex = ''
        if p.rtype == "KEY":
            print "KEY request"
            tx_signed = get_public_key(p.wallet_index)
            tx_signed_hex = tx_signed
            print tx_signed_hex
        elif p.rtype == "TXN":
            print "TXN request"
            tx_signed = sign_tx(p.wallet_index, p.key_index, p.tx, netcode=p.netcode)
            tx_signed_hex = tx_signed.as_hex(include_unspents=True)
            print tx_signed_hex
        else:
            raise ValueError("Package header incorrect")
        return tx_signed_hex

    def run(self):
        global msg_queue
        global prev_tx
        while True:
            msg = msg_queue.get()
            logger.debug("Consumed")
            tx_signed_hex = ''
            p = disassemble_package(msg)

            if p.tx in prev_tx:
                tx_signed_hex = prev_tx[p.tx]
            else:
                tx_signed_hex = self.sign(p)

            prev_tx.clear()

            prev_tx[p.tx] = tx_signed_hex

            package = assemble_package_tx_only(tx_signed_hex)

            transmit_package(package)

            msg_queue.task_done()


class Receiver:
    class ReceiverReader(threading.Thread):
        def __init__(self, stdout, stderr, compress=True):
            threading.Thread.__init__(self)
            self.stdout = stdout
            self.stderr = stderr
            self.compress = compress

        def run(self):
            in_packet = False
            packet = ''
            global msg_queue
            while True:
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
                        in_packet = True
                        packet = ''
                    elif line.startswith('### NOCARRIER '):
                        in_packet = False
                        if len(packet) < 30:
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
                            package = assemble_package_tx_only(' RESEND '*5)
                            transmit_package(package)
                            continue

                        logger.debug("Got packet: %s", packet)
                        msg_queue.put(packet)

    def __init__(self, compress=True, **kwargs):
        self.p = subprocess.Popen(['minimodem', '-r', '-8', '-A',
            kwargs.get('baudmode', 'rtty')] + kwargs.get('extra_args', []),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.compress = compress
        self.reader = Receiver.ReceiverReader(self.p.stdout, self.p.stderr, compress)
        self.reader.setDaemon(True)
        self.reader.start()


if __name__ == "__main__":
    logger.info("Start Receiver")
    receiver = Receiver(compress=Settings.USE_COMPRESSION,
                        baudmode=Settings.BAUD_MINIMODEM)
    logger.info("Start Consumer")
    consumer = Consumer()
    consumer.start()
    receiver.p.wait()






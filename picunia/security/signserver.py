import subprocess
import threading
import time
import select
import zlib, base64
from threading import Thread
from crypt.reedsolo import RSCodec
from Queue import Queue
from signer import Signer
from protocol import assemble_package, disassemble_package
from transmitter import transmit_package

msg_queue = Queue()


class Consumer(threading.Thread):

    def run(self):
        global msg_queue
        while True:
            msg = msg_queue.get()
            print "Consumed"
            p = disassemble_package(msg)

            tx_signed = Signer.sign_tx(p.account_nr, p.key_index, p.tx, netcode=p.netcode)

            print tx_signed

            transmit_package(tx_signed)

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
                        packet = rs.decode(b)

                        if self.compress:
                            try:
                                packet = zlib.decompress(base64.b64decode(packet))
                            except:
                                pass

                        print 'Got packet: %s' % packet
                        msg_queue.put(packet)
                        end = time.time()
                        print "It took %s" % (end - start)

    def __init__(self, compress=True, **kwargs):
        self.p = subprocess.Popen(['minimodem', '-r', '-8', '-A',
            kwargs.get('baudmode', 'rtty')] + kwargs.get('extra_args', []),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.compress = compress
        self.reader = Receiver.ReceiverReader(self.p.stdout, self.p.stderr, compress)
        self.reader.setDaemon(True)
        self.reader.start()


if __name__ == "__main__":
    use_compression = True
    baud = '3000'
    print "Start Receiver"
    receiver = Receiver(compress=use_compression, baudmode=baud)
    print "Start Consumer"
    consumer = Consumer()
    consumer.start()
    receiver.p.wait()






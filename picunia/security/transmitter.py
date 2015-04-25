import subprocess
import zlib, base64
from crypt.reedsolo import RSCodec
from Queue import Queue


class Transmitter:
    def __init__(self, compress=True, **kwargs):
        self.p = subprocess.Popen(['minimodem', '-t', '-8',
            kwargs.get('baudmode', 'rtty')] + kwargs.get('extra_args', []),
            stdin=subprocess.PIPE)
        self.compress = compress

    def write(self, text):
        s = len(text)

        if self.compress:
            text = base64.b64encode(zlib.compress(text))
            print "Size before %d size after %d" % (s, len(text))

        rs = RSCodec(10)
        text = rs.encode(text)

        self.p.stdin.write(text)

    def close(self):
        self.p.stdin.close()
        self.p.wait()

def transmit_package(package):
    use_compression = True
    baud = '3000'
    sender = Transmitter(compress=use_compression, baudmode=baud)
    sender.write(package)
    sender.close()

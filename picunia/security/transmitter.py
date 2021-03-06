import subprocess
import zlib, base64
import logging
from crypt.reedsolo import RSCodec
from Queue import Queue
from picunia.config.settings import Settings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Transmitter:
    def __init__(self, compress=True, **kwargs):
        self.p = subprocess.Popen(['minimodem', '-t', '-8', '-A',
            kwargs.get('baudmode', 'rtty')] + kwargs.get('extra_args', []),
            stdin=subprocess.PIPE)
        self.compress = compress

    def write(self, text):
        s = len(text)

        if self.compress:
            text = base64.b64encode(zlib.compress(text))
            percent = "{0:.0f}%".format(float(len(text))/s * 100)
            logger.debug("Packge compressed %s", percent)

        rs = RSCodec(Settings.RSCODEC_NSYM)
        text = rs.encode(text)

        self.p.communicate(text)

    def close(self):
        self.p.stdin.close()
        self.p.wait()

def transmit_package(package):
    sender = Transmitter(compress=Settings.USE_COMPRESSION,
                        baudmode=Settings.BAUD_MINIMODEM)
    sender.write(package)
    sender.close()

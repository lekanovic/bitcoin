import subprocess
import threading
import zlib, base64
import time
import select
import logging
import shelve
import time
from picunia.config.settings import Settings
from crypt.reedsolo import RSCodec, ReedSolomonError
from Queue import Queue
from protocol import assemble_package, disassemble_package, assemble_package_tx_only
from transmitter import transmit_package
from pycoin.tx.Tx import Tx
from mnemonic import Mnemonic
from pycoin.key.BIP32Node import BIP32Node
from pycoin.encoding import wif_to_secret_exponent
from pycoin.tx.pay_to import build_hash160_lookup
from random import randint

send_queue = Queue()
signed_queue = Queue()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def BIP39_mnemonics():
    words = "category fiscal fuel great review rather useful shop middle defense cube vacuum resource fiber special nurse chief category mask display bag echo concert click february fame tenant innocent affair usual hole soon bean adjust shoe voyage immune chest gaze chaos tip way glimpse sword tray craft blur seminar"
    seed = Mnemonic.to_seed(words)
    return seed, words

class LazySecretExponentDB(object):
    """
    The pycoin pure python implementation that converts secret exponents
    into public pairs is very slow, so this class does the conversion lazily
    and caches the results to optimize for the case of a large number
    of secret exponents.
    """
    def __init__(self, wif_iterable, secret_exponent_db_cache):
        self.wif_iterable = iter(wif_iterable)
        self.secret_exponent_db_cache = secret_exponent_db_cache

    def get(self, v):
        if v in self.secret_exponent_db_cache:
            return self.secret_exponent_db_cache[v]
        for wif in self.wif_iterable:
            secret_exponent = wif_to_secret_exponent(wif)
            d = build_hash160_lookup([secret_exponent])
            self.secret_exponent_db_cache.update(d)
            if v in self.secret_exponent_db_cache:
                return self.secret_exponent_db_cache[v]
        self.wif_iterable = []
        return None

def get_public_key(wallet_index):
    seed, words = BIP39_mnemonics()
    master = BIP32Node.from_master_secret(seed, Settings.NETCODE)

    key_path = Settings.KEY_PATHS

    path = key_path + "%dH.pub" % wallet_index

    account_keys = master.subkey_for_path( path ).as_text()

    logger.debug("%d %s %s", wallet_index, Settings.NETCODE, account_keys)

    return account_keys

def signer_sign_tx(wallet_index, key_index, tx_unsigned, netcode="BTC"):

    private_key_db = shelve.open(Settings.KEYS_DB, writeback=True)
    wifs_db = shelve.open(Settings.WIFS_DB, writeback=True)

    tx_unsigned = Tx.tx_from_hex(tx_unsigned)

    seed, words = BIP39_mnemonics()

    master = BIP32Node.from_master_secret(seed, Settings.NETCODE)

    logger.debug("%d %s %s %s", wallet_index, str(key_index), Settings.NETCODE, tx_unsigned)

    key_path = Settings.KEY_PATHS


    wifs = []
    start = time.time()

    for k in key_index:

        p1 = key_path + "%sH/0/%s" % (wallet_index, k)

        try:
            existing = wifs_db[p1]
            logger.debug("From cache: %s", existing)
        except:
            wifs_db[p1] = master.subkey_for_path(p1).wif(use_uncompressed=False)

        wifs.append( wifs_db[p1] )
        k += 1

    p1 = key_path + "%sH/1" % (wallet_index)

    try:
        existing = wifs_db[p1]
        logger.debug("From cache: %s", existing)
    except:
        wifs_db[p1] = master.subkey_for_path(p1).wif(use_uncompressed=False)

    wifs.append( wifs_db[p1] )

    end = time.time()
    logger.debug("Key generation took: %.7f", (end - start))

    start = time.time()
    tx_signed = tx_unsigned.sign(LazySecretExponentDB(wifs, private_key_db))
    end = time.time()
    logger.debug("Signing took: %.7f", (end - start))

    private_key_db.close()
    wifs_db.close()

    return tx_signed

class Consumer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def sign(self, p):
        tx_signed_hex = ''
        if p.rtype == "KEY":
            logger.debug("KEY request")
            tx_signed = get_public_key(p.wallet_index)
            tx_signed_hex = tx_signed
            logger.debug(tx_signed_hex)
        elif p.rtype == "TXN":
            logger.debug("TXN request")
            tx_signed = signer_sign_tx(p.wallet_index, p.key_index, p.tx, p.netcode)
            tx_signed_hex = tx_signed.as_hex(include_unspents=True)
            logger.debug(tx_signed_hex)
        else:
            raise ValueError("Package header incorrect")
        return tx_signed_hex

    def run(self):
        global send_queue

        package = send_queue.get()
        logger.debug("Consumed")

        p = disassemble_package(package)

        tx_signed = self.sign(p)

        # Simulate lag time
        sleep_time = randint(3, 30)
        time.sleep(sleep_time)

        signed_queue.put(tx_signed)

        send_queue.task_done()

        logger.info("End Consumer")


class Receiver:
    class ReceiverReader(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)

            self.func_cb = None
            self.signal = True

        def run(self):
            in_packet = False
            packet = ''

            while self.signal:

                tx = signed_queue.get()

                # Callback function with the signed transaction
                self.func_cb(tx)

                logger.info("End Receiver")
                self.signal = False

    def __init__(self, **kwargs):
        self.reader = Receiver.ReceiverReader()
        self.reader.setDaemon(True)
        self.reader.start()

receiver = None

def start_service():
    logger.info("Start Receiver")

    global receiver
    receiver = Receiver()
    logger.info("Start Consumer")

    consumer = Consumer()
    consumer.setDaemon(True)
    consumer.start()

    #receiver.p.wait()

def stop_service():
    global receiver
    logger_info("Terminate Receiver")
    try:
        receiver.reader.signal = False
        receiver.p.terminate()
    except:
        pass

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


from pycoin.key.BIP32Node import BIP32Node
from pycoin.serialize import h2b
from pycoin.tx.Tx import Tx
from pycoin.encoding import wif_to_secret_exponent
from pycoin.tx.pay_to import build_hash160_lookup
from picunia.config.settings import Settings
from mnemonic import Mnemonic
import shelve
import time
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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

def BIP39_mnemonics():
	words = open(Settings.SEED_FILE).read()
	seed = Mnemonic.to_seed(words)
	return seed, words


def get_public_key(wallet_index):
	seed, words = BIP39_mnemonics()
	master = BIP32Node.from_master_secret(seed, Settings.NETCODE)

	key_path = Settings.KEY_PATHS

	path = key_path + "%dH.pub" % wallet_index

	account_keys = master.subkey_for_path( path ).as_text()

	logger.debug("%d %s %s", wallet_index, Settings.NETCODE, account_keys)

	return account_keys

def sign_tx(wallet_index, key_index, tx_unsigned, netcode="BTC"):

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

'''
print get_public_key(2)
tx = '01000000050468194b68edb348adcf23444c89cd591abf4a5f85d8e36655539fec42971c110000000000ffffffff90cc080d0f3c1df41d67e62cc9896b54b2395bc05eaf05fe19a626d966d3398e0000000000ffffffffbe4cb589cc20861d4881a7d5daf3de1780909d261bbf1182adc72be4bc97e9450000000000ffffffff831f9861f5e40e4a5371d4b069ff71818fa9e2d532687edadb1d72a8ab8418160100000000ffffffff4590040629ffbdef75bf610452dbca4edeb7e4fead6c97a009dc28c57cea76930100000000ffffffff0288130000000000001976a914ca03162cb9bdeada6087bd7fb605496817299c4288acf5010000000000001976a91448a9c88c79252ecb8efb187b9175a9abaf03cc4f88ac0000000022270000000000001976a914be46bcf8e6ee88c99d17e037893bd48b00fa79fe88ac1e0a0000000000001976a9149e7af516dee4b9b97c59e7ca84acf9129eeb9d1f88ac32050000000000001976a914ebde8fb3410b3b8992ba445a33caed5d5a34e00a88ac10030000000000001976a91448a9c88c79252ecb8efb187b9175a9abaf03cc4f88ac0b030000000000001976a91448a9c88c79252ecb8efb187b9175a9abaf03cc4f88ac'
print sign_tx(2, [29, 26, 24, 23], tx, netcode="XTN")
'''
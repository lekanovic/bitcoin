from pycoin.key.BIP32Node import BIP32Node
from pycoin.serialize import h2b
from pycoin.tx.Tx import Tx
from pycoin.encoding import wif_to_secret_exponent
from pycoin.tx.pay_to import build_hash160_lookup
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


class Signer:

	@classmethod
	def sign_tx(cls, account_nr, key_index, tx_unsigned, netcode="BTC"):
		def BIP39_static_seed():
			words = 'category fiscal fuel great review rather useful shop middle defense cube vacuum resource fiber special nurse chief category mask display bag echo concert click february fame tenant innocent affair usual hole soon bean adjust shoe voyage immune chest gaze chaos tip way glimpse sword tray craft blur seminar'
			seed = h2b('6ad72bdbc8b5c423cdc52be4b27352086b230879a0fd642bbbb19f5605941e3001eb70c6a53ea090f28d4b0e3033846b23ae2553c60a9618d7eb001c3aba2a30')
			return seed, words

		private_key_db = shelve.open('key.db', writeback=True)
		wifs_db = shelve.open('wifs.db', writeback=True)

		tx_unsigned = Tx.tx_from_hex(tx_unsigned)
		key_index = int(key_index)
		seed, words = BIP39_static_seed()
		
		master = BIP32Node.from_master_secret(seed, netcode)

		logger.debug("%d %d %s %s", account_nr, key_index, netcode, tx_unsigned)

		if netcode == "XTN":
			key_path = "44H/1H/"
		elif netcode == "BTC":
			key_path = "44H/1H/"

		k = 0
		wifs = []
		start = time.time()

		while k < key_index:
			p1 = key_path + "%sH/0/%s" % (account_nr, k)
			try:
				existing = wifs_db[p1]
				logger.debug("From cache: %s", existing)
			except:
				wifs_db[p1] = master.subkey_for_path(p1).wif(use_uncompressed=False)

			wifs.append( wifs_db[p1] )
			k += 1

		p1 = key_path + "%sH/1" % (account_nr)

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
tx = '01000000018e0518c9fa9d6c54e5692c7b6c8b913bd55d790fac57f5265af07deec94410a90100000000ffffffff0265480000000000001976a9145e27c1c859310d5f5b75edbd2c93067e3b80b82788aca5170200000000001976a914be0a1a260aa3784747055567f0ac9d304c33d61888ac000000001a870200000000001976a914be0a1a260aa3784747055567f0ac9d304c33d61888ac'
print Signer.sign_tx(2392, 8, tx, netcode="XTN")
'''
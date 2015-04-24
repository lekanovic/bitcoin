from pycoin.key.BIP32Node import BIP32Node
from pycoin.serialize import h2b
from pycoin.tx.Tx import Tx


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

		tx_unsigned = Tx.tx_from_hex(tx_unsigned)
		key_index = int(key_index)
		seed, words = BIP39_static_seed()
		
		master = BIP32Node.from_master_secret(seed, netcode)

		if netcode == "XTN":
			key_path = "44H/1H/"
		elif netcode == "BTC":
			key_path = "44H/1H/"

		wifs = []
		for k in range(0, key_index):
			p1 = key_path + "%sH/0/%s" % (account_nr, k)
			wifs.append( master.subkey_for_path(p1).wif(use_uncompressed=False) )

		p1 = key_path + "%sH/1" % (account_nr)

		wifs.append( master.subkey_for_path(p1).wif(use_uncompressed=False) )

		tx_signed = tx_unsigned.sign(LazySecretExponentDB(wifs, {}))

		return tx_signed

#tx = Tx.tx_from_hex('0100000001e592a74c5501acacce333e0592b7af21d7f6502a0236b0d990bc65cac09c1b790100000000ffffffff0251110000000000001976a91422f5a7614e1276c3cce52c7dfbf8c0a567d8d97088ac036e0000000000001976a914254702c244d402120bd9aa12e99939f7848b050288ac0000000064a60000000000001976a914254702c244d402120bd9aa12e99939f7848b050288ac')
#print Signer.sign_tx(0, 0, tx, netcode="XTN")
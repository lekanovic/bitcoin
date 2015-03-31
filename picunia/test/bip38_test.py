import unittest
import pyBIP0038

class Bip38TestCase(unittest.TestCase):

	def test_password(self):
		privKey = '5KN7MzqK5wt2TP1fQCYyHBtDrXdJuXbUzm4A9rKAteGu3Qi5CVR'
		passPhrase = 'TestingOneTwoThree'

		bip38key =  pyBIP0038.encrypt_privkey_from_password(passPhrase,privKey)

		base58privkey = pyBIP0038.decrypt_priv_key(passPhrase, bip38key)

		self.assertEqual(base58privkey, privKey)

if __name__ == '__main__':
	unittest.main()
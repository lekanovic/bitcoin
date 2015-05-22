import unittest
import sys
sys.path.append('..')
sys.path.append('../..')
from users.wallet import Wallet
import time

class WalletTestCase(unittest.TestCase):

	def test_from_json(self):
		doc = {}
		doc['status'] = "active"
		doc['public_key'] = "tpubDCVcrTzunZwuc67hSQHmjHN8efpCVw4aZDUqvztyryj8QDpsvjxipein85QKt3ZuWXGapnuYVBEUGyvAQMJBNpruqxqStQ5RdrLhRCzNtuc".encode('utf-8')
		doc['date'] = "2015-03-17 14:04:17.578191"
		doc['wallet_index'] = "1"
		doc['wallet-balance'] = 0

		wallet = Wallet.from_json(doc)

		self.assertEqual(wallet.wallet_index, "1")
		self.assertEqual(wallet.status, "active")
		self.assertEqual(wallet.public_key, "tpubDCVcrTzunZwuc67hSQHmjHN8efpCVw4aZDUqvztyryj8QDpsvjxipein85QKt3ZuWXGapnuYVBEUGyvAQMJBNpruqxqStQ5RdrLhRCzNtuc")

	def test_performance(self):
		doc = {}
		doc['status'] = "active"
		doc['public_key'] = "tpubDCVcrTzunZwuc67hSQHmjHN8efpCVw4aZDUqvztyryj8QDpsvjxipein85QKt3ZuWXGapnuYVBEUGyvAQMJBNpruqxqStQ5RdrLhRCzNtuc"
		doc['date'] = "2015-03-17 14:04:17.578191"
		doc['wallet_index'] = "2"
		doc['wallet-balance'] = 0

		start_time = time.time()
		wallet = Wallet.from_json(doc)
		delta = (time.time() - start_time)

		self.assertLess(7, delta)
		self.assertEqual(wallet.wallet_index, "1")
		self.assertEqual(wallet.status, "active")
		self.assertEqual(wallet.public_key, "tpubDCVcrTzunZwuc67hSQHmjHN8efpCVw4aZDUqvztyryj8QDpsvjxipein85QKt3ZuWXGapnuYVBEUGyvAQMJBNpruqxqStQ5RdrLhRCzNtuc")

	def test_sign(self):
		tx_original = "01000000020468194b68edb348adcf23444c89cd591abf4a5f85d8e36655539fec42971c110000000000ffffffff341399ed836cf04195002a6a093499fa40865284a23cfc9b5f70fc8acb81db1d0000000000ffffffff0288130000000000001976a914ca03162cb9bdeada6087bd7fb605496817299c4288acac130000000000001976a91448a9c88c79252ecb8efb187b9175a9abaf03cc4f88ac0000000022270000000000001976a914be46bcf8e6ee88c99d17e037893bd48b00fa79fe88ac22270000000000001976a914948c56ce2874444e00f5473690df2a576381a0be88ac"
		pub = 'tpubDCVcrTzunZwudiYHyQ21fvpUpUTPh1vUm9Z633hGwAzacBYoNpjv4NJpwV3A8avhWpnyTpWhKypLwaEEfta5SvnhEraGtobeUyEaWsbBKSy'

		w = Wallet(pub,"My precious")

		tx, key_indexes = w.pay_to_address('myw6VGNg5uB52p1RWYc6BTbZzwrGo5tEgC',5000)
		print w.wallet_info()
		self.assertEqual(tx.as_hex(include_unspents=True), tx_original)

if __name__ == '__main__':
	unittest.main()
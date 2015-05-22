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

if __name__ == '__main__':
	unittest.main()
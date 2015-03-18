import unittest
import sys
sys.path.append('..')
from account import Account

class AccountTestCase(unittest.TestCase):

	def test_from_json(self):
		doc = {}
		doc['status'] = "active"
		doc['public_key'] = "tpubDCVcrTzunZwuc67hSQHmjHN8efpCVw4aZDUqvztyryj8QDpsvjxipein85QKt3ZuWXGapnuYVBEUGyvAQMJBNpruqxqStQ5RdrLhRCzNtuc"
		doc['date'] = "2015-03-17 14:04:17.578191"
		doc['name'] = "Maja"
		doc['account_index'] = "1"
		doc['passwd'] = "password2"
		doc['lastname'] = "Lekanovic"
		doc['wallet-balance'] = 0
		doc['email'] = "majasusa@hotmail.com"

		account = Account.from_json(doc, network="testnet")

		self.assertEqual(account.name, "Maja")
		self.assertEqual(account.lastname, "Lekanovic")
		self.assertEqual(account.passwd, "password2")
		self.assertEqual(account.email, "majasusa@hotmail.com")
		self.assertEqual(account.account_index, "1")
		self.assertEqual(account.status, "active")
		self.assertEqual(account.public_key, "tpubDCVcrTzunZwuc67hSQHmjHN8efpCVw4aZDUqvztyryj8QDpsvjxipein85QKt3ZuWXGapnuYVBEUGyvAQMJBNpruqxqStQ5RdrLhRCzNtuc")

if __name__ == '__main__':
	unittest.main()
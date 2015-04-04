import unittest
import sys
import json
sys.path.append('..')
from picunia.database.storage import Storage
from users.account import Account

class BalanceTestCase(unittest.TestCase):

	def test_check_balance(self):
		db = Storage()

		accounts = [json.loads(a) for a in db.get_all_accounts()]

		for a in accounts:
			account = Account.from_json(a, network="testnet")
			self.assertEqual(account.wallet_balance(), a['wallet-balance'])

if __name__ == '__main__':
	unittest.main()
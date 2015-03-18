from pymongo import MongoClient
from bson.json_util import dumps
import datetime
import os


class AccountsDB(object):
	"""docstring for AccountsDB"""
	def __init__(self):
		if not 'MONGODB_ADDRESS' in os.environ:
			URL = "localhost"
		else:
			URL = os.environ['MONGODB_ADDRESS']

		if not 'MONGODB_PORT' in os.environ:
			PORT = "27017"
		else:
			PORT =  os.environ['MONGODB_PORT']
		URL = URL + ":" + PORT

		self.client = MongoClient(URL)
		self.db = self.client.accountsDB

	def add_account(self, account):
		''' Add an account to the database

			Args:
				account (json dict):
				User account information

			Returns:
				Bool: True if account was added, False if account alread exists
		'''
		res = self.find_account(account)
		if res != None:
			return False
		self.db.account.insert(account)
		return True

	def update_balance(self, account, new_balance):
		res = self.find_account(account)
		# Update balance for a specific account
		self.db.account.update({'_id': res['_id']},
			{'$set': {'wallet-balance': new_balance}},upsert=False, multi=False)

	def update_passwd(self, account, new_passwd):
		res = self.find_account(account)
		# Update balance for a specific account
		self.db.account.update({'_id': res['_id']},
			{'$set': {'passwd': new_passwd}},upsert=False, multi=False)

	def update_status(self, account, new_status):
		res = self.find_account(account)
		# Update balance for a specific account
		self.db.account.update({'_id': res['_id']},
			{'$set': {'status': new_status}},upsert=False, multi=False)

	def find_account(self, account):
		res = self.db.account.find_one({"email" : account['email']})
		return dumps(res, indent=4)

	def get_all_accounts(self):
		return [dumps(account, indent=4) for account in self.db.account.find()]

	def get_number_of_accounts(self):
		return self.db.account.count()

	def drop_database(self):
		self.db.account.drop()


doc1 = {
		"name": "Radovan",
		"passwd": "password1",
		"lastname": "Lekanovic",
		"account_index": "0",
		"wallet-balance": 47288000,
		"email": "lekanovic@gmail.com",
		"status": "active",
		"public_key": "tpubDCVcrTzunZwuae4YJ9mZAvcxp5TSyKdWXnmc3XbYdGKHAkpvuUQ9Ks38LnGeBQj99pPNG2EPtLwe3GzaYfRrT67fhs54VQtuk2RzboTdnCS",
		"date":  str( datetime.datetime.now() )
		}

doc2 = {
		"name": "Maja",
		"passwd": "password2",
		"lastname": "Lekanovic",
		"account_index": "1",
		"wallet-balance": 372000,
		"email": "majasusa@hotmail.com",
		"status": "active",
		"public_key": "tpubDCVcrTzunZwuc67hSQHmjHN8efpCVw4aZDUqvztyryj8QDpsvjxipein85QKt3ZuWXGapnuYVBEUGyvAQMJBNpruqxqStQ5RdrLhRCzNtuc",
		"date":  str( datetime.datetime.now() )
		}

'''
a = AccountsDB()

print a.add_account(doc1)
print a.add_account(doc2)


a.update_balance(doc1, 8989898)
a.update_balance(doc2, 6767676)
a.update_passwd(doc2, "majana82")
a.update_status(doc2, "inactive")
for i in a.get_all_accounts():
	print i['account_index']

print a.get_number_of_accounts()

a.drop_database()
'''
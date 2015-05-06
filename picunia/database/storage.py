from pymongo import MongoClient
from bson.json_util import dumps
from picunia.config.settings import Settings
import datetime
import os


class Storage(object):
	"""docstring for Storage"""
	def __init__(self):

		URL = Settings.MONGODB_ADDRESS + ":" + Settings.MONGODB_PORT

		self.client = MongoClient(URL)
		self.dba = self.client.accountsDB
		self.dbt = self.client.TransactionDB
		self.db_blk = self.client.blockDB

	def add_account(self, account):
		''' Add an account to the database

			Args:
				account (json dict):
				User account information

			Returns:
				Bool: True if account was added, False if account alread exists
		'''
		res = self.find_account(account)
		if res != "null":
			return False
		self.dba.account.insert(account)
		return True

	def __find_account(self, account):
		res = self.dba.account.find_one({"email" : account['email']})
		return res

	def update_account(self, account):
		res = self.__find_account(account)
		self.dba.account.update({'_id': res['_id']}, account,upsert=False, multi=False)

	def update_balance(self, account, new_balance):
		res = self.__find_account(account)
		# Update balance for a specific account
		self.dba.account.update({'_id': res['_id']},
			{'$set': {'wallet-balance': new_balance}},upsert=False, multi=False)

	def update_passwd(self, account, new_passwd):
		res = self.__find_account(account)
		# Update balance for a specific account
		self.dba.account.update({'_id': res['_id']},
			{'$set': {'passwd': new_passwd}},upsert=False, multi=False)

	def update_status(self, account, new_status):
		res = self.__find_account(account)
		# Update balance for a specific account
		self.dba.account.update({'_id': res['_id']},
			{'$set': {'status': new_status}},upsert=False, multi=False)

	def find_account(self, account):
		if type(account) == str:
			res = self.dba.account.find_one({"email" : account})
		elif type(account) == dict:
			res = self.dba.account.find_one({"email" : account['email']})
		elif type(account) == unicode:
			res = self.dba.account.find_one({"email" : account})
		else:
			raise ValueError("Wrong type")

		return dumps(res, indent=4)

	def find_account_index(self, account):
		if type(account) == str:
			res = self.dba.account.find_one({"account_index" : account})
		elif type(account) == dict:
			res = self.dba.account.find_one({"account_index" : account['account_index']})
		return dumps(res, indent=4)

	def find_bitcoin_address(self, bitcoin_address):
		res = self.dba.account.find_one({"spendable.public_address" : bitcoin_address })

		return dumps(res, indent=4)

	def get_all_accounts(self):
		return [dumps(account, indent=4) for account in self.dba.account.find()]

	def get_number_of_accounts(self):
		return self.dba.account.count()

	def drop_database(self, which="all"):
		if which == "all":
			self.dba.account.drop()
			self.dbt.transaction.drop()
		elif which == "account":
			self.dba.account.drop()
		elif which == "transaction":
			self.dbt.transaction.drop()

	def add_transaction(self, transaction):
		'''
			arg - dict
		'''
		self.dbt.transaction.insert(transaction)

	def find_last_block(self):
		res = self.db_blk.blockDB.find().sort("block-height", -1).limit(1)
		return dumps(res, indent=4)

	def add_block(self, block):
		self.db_blk.blockDB.insert(block)

	def find_transaction(self, transaction):
		res = self.dbt.transaction.find_one({"tx_id" : transaction['tx_id']})
		return dumps(res, indent=4)

	def update_transaction(self, transaction):
		res = self.dbt.transaction.find_one({"tx_id" : transaction['tx_id']})

		self.dbt.transaction.update({'_id': res['_id']},
			{'$set': {'confirmations': transaction['confirmations']}},upsert=False, multi=False)

		self.dbt.transaction.update({'_id': res['_id']},
			{'$set': {'block': transaction['block']}},upsert=False, multi=False)

	def get_unconfirmed_transactions(self, confirms=0):
		return [dumps(transaction, indent=4) for transaction in
				self.dbt.transaction.find({"confirmations" : {"$lt" : confirms}})]

	def get_all_transactions(self):
		return [dumps(transaction, indent=4) for transaction in
				self.dbt.transaction.find()]

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
d = {}
d['from'] = "ethel.herrera14@example.com"
d['to_addr'] = "mojERYaVYcXPkUhXGEFMcJ3srXGGfN31gR"
d['to_email'] =  "riley.sims25@example.com"
d['tx_id'] = "d42f6f4d47ea9053b84fa2acdb01b247575c7f103bb5ca4e968d8d1d5ef993e9"
d['amount'] = 22830
d['fee'] = 10000
d['confirmations'] = 10
d['date'] = "2015-04-04 14:49:34.006587"
d['block'] = 370000


'''
import json
a = Storage()
a.update_transaction(d)

for j in a.get_unconfirmed_transactions():
	print j




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
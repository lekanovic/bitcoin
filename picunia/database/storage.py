from pymongo import MongoClient
from bson.json_util import dumps, loads
from picunia.config.settings import Settings
import datetime
import os


class Storage(object):
	"""docstring for Storage"""
	def __init__(self):

		URL = Settings.MONGODB_ADDRESS + ":" + Settings.MONGODB_PORT

		self.client = MongoClient(URL)
		self.dba = self.client.accountsDB
		self.dbw = self.client.walletDB
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
		if res != None:
			return False
		self.dba.account.insert(account)
		return True

	def add_wallet(self, wallet):
		res = self.dbw.wallet.find_one({"wallet_index" : wallet['wallet_index']})
		if res != None:
			return False
		self.dbw.wallet.insert(wallet)
		return True

	def find_wallet(self, wallet):
		if type(wallet) == int:
			wallet = str(wallet)
		res = self.dbw.wallet.find_one({"wallet_index" : wallet})
		return loads(dumps(res))

	def __find_account(self, account):
		res = self.dba.account.find_one({"email" : account['email']})
		return res

	def update_wallet(self, wallet):
		res = self.dbw.wallet.find_one({"wallet_index" : wallet['wallet_index']})
		self.dbw.wallet.update({'_id': res['_id']}, wallet, upsert=False, multi=False)

	def update_account(self, account):
		res = self.__find_account(account)
		self.dba.account.update({'_id': res['_id']}, account, upsert=False, multi=False)
	'''
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
	'''
	def find_account(self, account):
		if type(account) == str:
			res = self.dba.account.find_one({"email" : account})
		elif type(account) == dict:
			res = self.dba.account.find_one({"email" : account['email']})
		elif type(account) == unicode:
			res = self.dba.account.find_one({"email" : account})
		else:
			raise ValueError("Wrong type")

		return loads(dumps(res))


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

	def get_number_of_wallets(self):
		return self.dbw.wallet.count()

	def get_number_of_accounts(self):
		return self.dba.account.count()

	def drop_database(self, which="all"):
		if which == "all":
			self.dba.account.drop()
			self.dbt.transaction.drop()
			self.dbw.wallet.drop()
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

'''
db = Storage()

account = {}
account["status"] = "active"
account["name"] = "Radovan"
account["lastname"] = "Lekanovic"
account["email"] = "lekanovic@gmail.com"
account["password"] = "hemils"
account["account_index"] = db.get_number_of_accounts()
account["created"] = str( datetime.datetime.now() )

db.add_account(account)

res = db.find_account(account["email"])

res["name"] = "Nils"
res["password"] = "smyga"

db.update_account(res)
'''
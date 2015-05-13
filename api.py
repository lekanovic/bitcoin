from picunia.database.storage import Storage
from picunia.users.wallet import Wallet
from picunia.security.sign_tx_client import request_public_key, start_service
from bson.json_util import dumps
import json
import datetime

class AccountExistException():
	pass

class KeyCreateHandler():
	def __init__(self):
		self.db = Storage()

	def callback(self, key_hex):
		print key_hex

		wallet = json.loads(Wallet(key_hex).to_json())

		self.db.add_wallet(wallet)


def create_account(name,lastname,email,password):
	db = Storage()
	res = db.find_account(email)

	if not res is None  :
		raise AccountExistException()

	account = {}
	account["status"] = "active"
	account["name"] = name
	account["lastname"] = lastname
	account["email"] = email
	account["password"] = password
	account["account_index"] = db.get_number_of_accounts()
	account["created"] = str( datetime.datetime.now() )

	number = db.get_number_of_wallets()
	account["wallets"] = [number]

	kh = KeyCreateHandler()

	db.add_account(account)

	request_public_key(number, kh.callback)

def add_wallet(email):
	db = Storage()
	number = db.get_number_of_wallets()

	kh = KeyCreateHandler()
	request_public_key(number, kh.callback)

	account = db.find_account(email)

	account['wallets'].append(number)

	db.update_account(account)

def del_wallet(email, wallet_index):
	db = Storage()
	account = db.find_account(email)

	if wallet_index in account["wallets"]:
		account["wallets"].remove(wallet_index)
		db.update_account(account)
	else:
		raise ValueError("wallet index %d does not exist in %s" % (wallet_index, email))

def fetch_account(email):
	db = Storage()
	return db.find_account(from_email)

def activate_account(email):
	db = Storage()
	account = db.find_account(email)

	if account['status'] == 'inactive':
		account['status'] = 'active'
		db.update_account(account)

def deactivate_account(email):
	db = Storage()
	account = db.find_account(email)

	if account['status'] == 'active':
		account['status'] = 'inactive'
		db.update_account(account)

def pay_to(from_email, wallet, to_email, amount):
	pass


'''
import time

start_service()
time.sleep(5)
add_wallet('lekanovic@gmail.com')
time.sleep(6000000)

create_account('radovan','lekanovic','lekanovic@gmail.com', 'hemlis')
time.sleep(15)

add_wallet('lekanovic@gmail.com')
time.sleep(15)
add_wallet('lekanovic@gmail.com')
time.sleep(15)
add_wallet('lekanovic@gmail.com')
time.sleep(15)
add_wallet('lekanovic@gmail.com')

del_wallet('lekanovic@gmail.com', 0)

time.sleep(6000000)

'''





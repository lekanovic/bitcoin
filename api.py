from picunia.database.storage import Storage
from picunia.users.wallet import Wallet
from picunia.security.sign_tx_client import request_public_key, start_service
from bson.json_util import dumps
import json
import datetime

class AccountExistException():
	pass

wallet_counter = 0

class KeyCreateHandler():
	def __init__(self):
		self.db = Storage()

	def callback(self, key_hex):

		wallet = json.loads(Wallet(key_hex).to_json())

		print "callback", wallet['wallet_index']
		if not self.db.add_wallet(wallet):
			print "Wallet %s already exist" % wallet['wallet_index']

def create_account(name,lastname,email,password):
	global wallet_counter
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
	account["wallets"] = [wallet_counter]

	kh = KeyCreateHandler()
	request_public_key(wallet_counter, kh.callback)

	db.add_account(account)

	wallet_counter += 1

def add_wallet(email):
	global wallet_counter
	db = Storage()

	print "add_wallet", wallet_counter
	kh = KeyCreateHandler()
	request_public_key(wallet_counter, kh.callback)

	account = db.find_account(email)

	account['wallets'].append(wallet_counter)

	db.update_account(account)

	wallet_counter += 1

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

def pay_to(from_email, to_email, amount):
	from_email = db.find_account(from_email)
	to_email = db.find_account(to_email)

	wallet_index = from_email["wallets"][0]

	wallet = db.find_wallet(wallet_index)

	print wallet

'''
db = Storage()

import time

start_service()
time.sleep(5)

create_account('radovan','lekanovic','lekanovic@gmail.com', 'hemlis')

add_wallet('lekanovic@gmail.com')
add_wallet('lekanovic@gmail.com')
add_wallet('lekanovic@gmail.com')
add_wallet('lekanovic@gmail.com')

create_account('jimmy','larsson','jlarrsson@gmail.com', 'tutti')
add_wallet('lekanovic@gmail.com')
add_wallet('jlarrsson@gmail.com')


add_wallet('lekanovic@gmail.com')
time.sleep(15)
add_wallet('lekanovic@gmail.com')
time.sleep(15)
add_wallet('lekanovic@gmail.com')

del_wallet('lekanovic@gmail.com', 0)
'''
time.sleep(6000000)







from picunia.database.storage import Storage
from picunia.users.wallet import Wallet
from picunia.security.sign_tx_client import request_public_key, start_service, sign_tx
from picunia.handlers.interface import TransactionHandler, KeyCreateHandler
import json
import datetime
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AccountExistException():
	pass


def create_dummy_wallet(wallet_index):
	dummy_wallet = {}
	dummy_wallet['wallet_index'] = str(wallet_index)
	dummy_wallet['wallet_balance'] = 0
	dummy_wallet['status'] = 'active'
	dummy_wallet['public_key'] = ''
	dummy_wallet['date'] = ''
	dummy_wallet['spendable'] = []
	return dummy_wallet

def create_account(name,lastname,email,password):
	db = Storage()
	res = db.find_account(email)
	wallet_counter = db.get_number_of_wallets()

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

	dummy_wallet = create_dummy_wallet(wallet_counter)

	kh = KeyCreateHandler()
	request_public_key(wallet_counter, kh.callback)

	db.add_wallet(dummy_wallet)
	db.add_account(account)

def add_wallet(email):
	db = Storage()
	wallet_counter = db.get_number_of_wallets()

	print "add_wallet", wallet_counter
	kh = KeyCreateHandler()
	request_public_key(wallet_counter, kh.callback)

	account = db.find_account(email)

	account['wallets'].append(wallet_counter)

	dummy_wallet = create_dummy_wallet(wallet_counter)

	db.add_wallet(dummy_wallet)
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

def pay_to(send_from, send_to, amount):
	db = Storage()

	from_email = db.find_account(send_from)
	to_email = db.find_account(send_to)

	wallet_index = to_email["wallets"][0]

	wallet = db.find_wallet(wallet_index)

	key = wallet['public_key']

	to_email_wallet = Wallet(key)
	bitcoin_address = to_email_wallet.get_bitcoin_address()

	wallet_index = from_email["wallets"][0]
	print wallet_index
	wallet = db.find_wallet(wallet_index)
	print "Wallet balance %d" % wallet['wallet_balance']

	key = wallet['public_key']

	from_email_wallet = Wallet(key)

	print from_email_wallet.wallet_index
	print from_email_wallet.index

	tx_unsigned = from_email_wallet.pay_to_address(bitcoin_address, amount)

	tx_info={}
	tx_info['from'] = send_from
	tx_info['to_addr'] = bitcoin_address
	tx_info['to_email'] =  send_to
	tx_info['amount'] = amount
	tx_info['confirmations'] = -1
	tx_info['date'] = str( datetime.datetime.now() )
	tx_info['block'] = -1
	tx_info['type'] = "STANDARD"

	th = TransactionHandler(tx_info)

	sign_tx(int(from_email_wallet.wallet_index),
			from_email_wallet.index,
			tx_unsigned.as_hex(include_unspents=True),
			cb=th.callback)

'''
db = Storage()

import time

start_service()
time.sleep(5)
pay_to('lekanovic@gmail.com', 'jlarrsson@gmail.com', 10000)


create_account('radovan','lekanovic','lekanovic@gmail.com', 'hemlis')

add_wallet('lekanovic@gmail.com')



add_wallet('lekanovic@gmail.com')
add_wallet('lekanovic@gmail.com')
add_wallet('lekanovic@gmail.com')

create_account('jimmy','larsson','jlarrsson@gmail.com', 'tutti')
add_wallet('lekanovic@gmail.com')
add_wallet('jlarrsson@gmail.com')


#del_wallet('lekanovic@gmail.com', 0)
'''
time.sleep(6000000)







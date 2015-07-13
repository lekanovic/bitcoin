from picunia.database.storage import Storage
from picunia.users.wallet import Wallet, InsufficientFunds, UnconfirmedAddress
from picunia.config.settings import Settings
from picunia.handlers.interface import TransactionHandler, KeyCreateHandler
from picunia.security.crypt.utils import encrypt_password, validate_password
from random import randint
import random
import json
import datetime
import logging
import time
import importlib

request_public_key = getattr(importlib.import_module(Settings.SIGN_TX_PATH), "request_public_key")
start_service = getattr(importlib.import_module(Settings.SIGN_TX_PATH), "start_service")
sign_tx = getattr(importlib.import_module(Settings.SIGN_TX_PATH), "sign_tx")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AccountExistException(Exception):
	def __init__(self, email):
		self.message = email


def log_in(email, password):
	db = Storage()
	account = db.find_account(email)

	hashed = account['password'].encode('utf-8')
	password = password.encode('utf-8')

	return validate_password(password, hashed)


def create_account(name,lastname,email,password):
	def create_dummy_wallet(wallet_index):
		dummy_wallet = {}
		dummy_wallet['wallet_index'] = str(wallet_index)
		dummy_wallet['wallet_balance'] = 0
		dummy_wallet['status'] = 'active'
		dummy_wallet['public_key'] = ''
		dummy_wallet['date'] = ''
		dummy_wallet['wallet_name'] = 'undefined'
		dummy_wallet['spendable'] = []
		return dummy_wallet

	db = Storage()
	res = db.find_account(email)
	wallet_counter = db.get_number_of_wallets()

	if not res is None  :
		raise AccountExistException(email)

	account = {}
	account["status"] = "active"
	account["name"] = name
	account["lastname"] = lastname
	account["email"] = email
	account["password"] = encrypt_password(password.encode('utf-8'))
	account["account_index"] = db.get_number_of_accounts()
	account["created"] = str( datetime.datetime.now() )
	account["wallets"] = [wallet_counter]

	dummy_wallet = create_dummy_wallet(wallet_counter)

	start_service()

	kh = KeyCreateHandler()
	request_public_key(wallet_counter, kh.callback)

	db.add_wallet(dummy_wallet)
	db.add_account(account)

	return kh

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

def find_account_with_balance():
	def find_random_account(db):
		number_of_accounts = db.get_number_of_accounts()
		rnd = str(random.randrange(0, number_of_accounts))
		return db.find_account_index(int(rnd))

	db = Storage()
	timeout_start = time.time()
	timeout = 60*1

	while time.time() < timeout_start + timeout:
		account = find_random_account(db)
		wallet_index = account['wallets'][0]
		wallet = db.find_wallet(wallet_index)

		if wallet['wallet_balance'] > 10000:
			return account, wallet['wallet_balance']
	return {}, -1

def fetch_account(email):
	db = Storage()
	return db.find_account(email)

def fetch_transactions_by_email(email):
	db = Storage()
	txs = db.find_all_transactions(email)

	return txs

def fetch_wallet(email, index=0):
	db = Storage()
	account = db.find_account(email)

	wallet_id = account['wallets'][index]
	wallet = db.find_wallet(wallet_id)

	return wallet

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

def pay_to_address(send_from, send_to, amount, msg="undefined"):
	db = Storage()

	from_email = db.find_account(send_from)
	to_email = db.find_account(send_to)

	wallet_index = to_email["wallets"][0]

	wallet = db.find_wallet(wallet_index)

	key = wallet['public_key']

	to_email_wallet = Wallet(key)
	bitcoin_address = to_email_wallet.get_bitcoin_address()

	wallet_index = from_email["wallets"][0]

	wallet = db.find_wallet(wallet_index)
	print "Wallet balance %d" % wallet['wallet_balance']

	key = wallet['public_key']

	from_email_wallet = Wallet(key)

	try:
		tx_unsigned, keylist = from_email_wallet.pay_to_address(bitcoin_address, amount)
	except InsufficientFunds as e:
		raise
	except UnconfirmedAddress as e:
		raise

	tx_info={}
	tx_info['from'] = send_from
	tx_info['to_addr'] = bitcoin_address
	tx_info['to_email'] =  send_to
	tx_info['amount'] = amount
	tx_info['confirmations'] = -1
	tx_info['date'] = str( datetime.datetime.now() )
	tx_info['block'] = -1
	tx_info['type'] = "STANDARD"
	tx_info['message'] = msg

	start_service()

	th = TransactionHandler(tx_info)

	sign_tx(int(from_email_wallet.wallet_index),
			keylist,
			tx_unsigned.as_hex(include_unspents=True),
			cb=th.callback)

	return th

def multisig_transacion(from_email, to_email, escrow_email, amount, msg="undefined"):
	def create_user_info(email, wallet_index, key_index):
		user = {}
		user['email'] = email
		user['wallet_index'] = wallet_index
		user['key_index'] = key_index
		user['signed'] = 'no'
		return user

	db = Storage()
	tx_unsigned = 0

	sender = db.find_account(from_email)
	receiver = db.find_account(to_email)
	escrow = db.find_account(escrow_email)

	sender_wallet = db.find_wallet(sender["wallets"][0])
	receiver_wallet = db.find_wallet(receiver["wallets"][0])
	escrow_wallet = db.find_wallet(escrow["wallets"][0])

	sender_wallet = Wallet(sender_wallet['public_key'])
	receiver_wallet = Wallet(receiver_wallet['public_key'])
	escrow_wallet = Wallet(escrow_wallet['public_key'])

	keys = []
	keys.append(sender_wallet.get_key())
	keys.append(receiver_wallet.get_key())
	keys.append(escrow_wallet.get_key())

	tx_multi_unsigned, multi_address = sender_wallet.multisig_2_of_3(keys)

	tx_info={}

	tx_info['from'] = create_user_info(from_email,
										sender_wallet.wallet_index,
										sender_wallet.index)

	tx_info['to_email'] = create_user_info(to_email,
											receiver_wallet.wallet_index,
											receiver_wallet.index)

	tx_info['escrow'] = create_user_info(escrow_email,
										escrow_wallet.wallet_index,
										escrow_wallet.index)

	tx_info['amount'] = amount
	tx_info['confirmations'] = -1
	tx_info['date'] = str( datetime.datetime.now() )
	tx_info['block'] = -1
	tx_info['multisig_address'] = multi_address
	tx_info['message'] = msg
	tx_info['type'] = "MULTISIG"

	try:
		tx_unsigned, keylist = sender_wallet.pay_to_address(multi_address,amount)
	except InsufficientFunds as e:
		raise
	except UnconfirmedAddress as e:
		raise

	start_service()

	th = TransactionHandler(tx_info)

	sign_tx(int(sender_wallet.wallet_index),
			keylist,
			tx_unsigned.as_hex(include_unspents=True),
			cb=th.callback)

	return th

def write_blockchain_message(email, message):
	db = Storage()
	tx_unsigned = 0

	# Find the user in database
	sender = db.find_account(email)
	wallet_index = sender["wallets"][0]

	wallet = db.find_wallet(wallet_index)

	sender = Wallet(wallet['public_key'])

	try:
		tx_unsigned, keylist, address = sender.proof_of_existens(message)
	except InsufficientFunds as e:
		raise
	except UnconfirmedAddress as e:
		raise

	tx_info={}
	tx_info['from'] = email
	tx_info['to_addr'] = address
	tx_info['to_email'] =  ''
	tx_info['amount'] = ''
	tx_info['confirmations'] = -1
	tx_info['date'] = str( datetime.datetime.now() )
	tx_info['block'] = -1
	tx_info['type'] = "OPRETURN"
	tx_info['message'] = message

	start_service()

	th = TransactionHandler(tx_info)

	sign_tx(int(sender.wallet_index),
			keylist,
			tx_unsigned.as_hex(include_unspents=True),
			cb=th.callback)

	return th

'''
db = Storage()

import time

start_service()
time.sleep(5)

print log_in('lekanovic@gmail.com', 'hemliss')
print log_in('lekanovic@gmail.com', 'hemlis')

multisig_transacion('lekanovic@gmail.com',
					'sveningvarsson@gmail.com',
					'jlarrsson@gmail.com', 10000)

pay_to_address('lekanovic@gmail.com', 
				'jlarrsson@gmail.com', 10000)


create_account('radovan','lekanovic','lekanovic@gmail.com', 'hemlis')

add_wallet('lekanovic@gmail.com')
add_wallet('lekanovic@gmail.com')
add_wallet('lekanovic@gmail.com')
create_account('Sven','Ingvarss','sveningvarsson@gmail.com', 'minmamma')

add_wallet('lekanovic@gmail.com')
create_account('jimmy','larsson','jlarrsson@gmail.com', 'tutti')

add_wallet('lekanovic@gmail.com')
add_wallet('jlarrsson@gmail.com')


#del_wallet('lekanovic@gmail.com', 0)

time.sleep(6000000)
'''

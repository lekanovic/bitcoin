from picunia.database.storage import Storage
from picunia.users.wallet import Wallet, InsufficientFunds, UnconfirmedAddress
from picunia.config.settings import Settings
from picunia.handlers.interface import TransactionHandler, KeyCreateHandler
from picunia.security.crypt.utils import encrypt_password, validate_password
from picunia.network.gcm_sender import send_to_device
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

	if account == None:
		return False

	hashed = account['password'].encode('utf-8')
	password = password.encode('utf-8')

	return validate_password(password, hashed)

def create_account(name,lastname,email,password,reg_id):
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
	account["reg_id"] = reg_id

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

def find_random_account():
	def find_random_account(db):
		number_of_accounts = db.get_number_of_accounts()
		rnd = str(random.randrange(0, number_of_accounts))
		return db.find_account_index(int(rnd))
	db = Storage()
	account = find_random_account(db)
	wallet = db.find_wallet(account['wallets'][0])

	return account, wallet['wallet_balance']

def fetch_account(email):
	def fetch_wallets(email):
		db = Storage()
		account = db.find_account(email)

		wallets = []
		for wallet_id in account['wallets']:
			w = db.find_wallet(wallet_id)
			del w['_id']
			wallets.append(w)

		return wallets

	db = Storage()
	account = db.find_account(email)
	if not account:
		return {}
	account[u'transactions'] = fetch_transactions_by_email(email)
	account[u'wallets'] = fetch_wallets(email)

	return account

def fetch_account_regid(email):
	resp = {}
	db = Storage()
	account = db.find_account(email)
	if not account:
		return {}
	resp[u'reg_id'] = account['reg_id']
	return resp

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
	def get_wallet(email):
		db = Storage()

		account = db.find_account(email)

		wallet = db.find_wallet(account["wallets"][0])

		return Wallet.from_json(wallet)

	from_email_wallet = get_wallet(send_from)
	to_email_wallet = get_wallet(send_to)

	bitcoin_address = to_email_wallet.get_bitcoin_address()

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
	def create_user_info(email, wallet_index):
		user = {}
		user['email'] = email
		user['wallet_index'] = wallet_index
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

	sender_wallet = Wallet.from_json(sender_wallet)
	receiver_wallet = Wallet.from_json(receiver_wallet)
	escrow_wallet = Wallet.from_json(escrow_wallet)

	keys = []
	keys.append(sender_wallet.get_key())
	keys.append(receiver_wallet.get_key())
	keys.append(escrow_wallet.get_key())

	tx_multi_unsigned, multi_address = sender_wallet.multisig_2_of_3(keys)

	tx_info={}

	tx_info['from'] = create_user_info(from_email,
										sender_wallet.wallet_index)

	tx_info['to_email'] = create_user_info(to_email,
											receiver_wallet.wallet_index)

	tx_info['escrow'] = create_user_info(escrow_email,
										escrow_wallet.wallet_index)

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

	sender = Wallet.from_json(wallet)

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

def request_payment(gcm_api_key, requester, request_from, amount, message):
	db = Storage()

	account = db.find_account(requester)

	requester_info = {}
	requester_info['name'] = account['name']
	requester_info['lastname'] = account['lastname']
	requester_info['email'] = account['email']

	msg = {}
	msg['type'] = 'REQUEST'
	msg['amount'] = amount
	msg['from'] = [requester_info]
	msg['message'] = message

	string_message = json.dumps(msg)

	account = db.find_account(request_from)

	if not send_to_device(gcm_api_key, string_message, account['reg_id']):
		response = {}
		response['status'] = 'FAILED to send to %s NotRegistered or InvalidRegistration' % account['reg_id']
		return response

	response = {}
	response['status'] = 'Pending'
	response['message'] = 'Sending request to %s for amount %d' % (args['request_from'], args['amount']) 

	return response

def issueasset(email, amount, metadata='', fees=10000):
	def get_wallet(email):
		db = Storage()

		account = db.find_account(email)

		wallet = db.find_wallet(account["wallets"][0])

		return Wallet.from_json(wallet)

	token_issuer = get_wallet(email)

	try:
		tx_unsigned, keylist = token_issuer.openasset_issueasset(amount, metadata=metadata, fees=fees)
	except InsufficientFunds as e:
		raise
	except UnconfirmedAddress as e:
		raise

	tx_info={}
	tx_info['owner'] = email
	tx_info['amount'] = 600 #Dust for assets
	tx_info['confirmations'] = -1
	tx_info['date'] = str( datetime.datetime.now() )
	tx_info['block'] = -1
	tx_info['type'] = "ISSUEASSET"
	tx_info['message'] = ''

	asset = {}
	asset['oa_address'] = token_issuer.get_oa_address()
	asset['quantity'] = amount
	asset['metadata'] = metadata

	tx_info['openasset'] = asset

	start_service()

	th = TransactionHandler(tx_info)

	sign_tx(int(token_issuer.wallet_index),
			keylist,
			tx_unsigned.as_hex(include_unspents=True),
			cb=th.callback)

	return th

def sendasset(from_email, to_email, amount, asset_id):
	def get_wallet(email):
		db = Storage()

		account = db.find_account(email)

		wallet = db.find_wallet(account["wallets"][0])

		return Wallet.from_json(wallet)

	token_sender = get_wallet(from_email)
	token_receiver = get_wallet(to_email)

	bitcoin_address = token_sender.key_change.address()
	to_oa_address = token_receiver.get_oa_address()

	tx_info={}
	tx_info['from'] = from_email
	tx_info['to'] = to_email
	tx_info['amount'] = 600 #Dust for assets
	tx_info['confirmations'] = -1
	tx_info['date'] = str( datetime.datetime.now() )
	tx_info['block'] = -1
	tx_info['type'] = "SENDASSET"
	tx_info['message'] = ''

	asset = {}
	asset['oa_address'] = to_oa_address
	asset['quantitys'] = amount
	asset['metadata'] = ''
	asset['asset_id'] = asset_id

	tx_info['openasset'] = asset

	try:
		tx_unsigned, keylist = token_sender.openasset_sendasset(bitcoin_address,
																asset_id,
																amount,
																to_oa_address,
																fees=1000)
	except InsufficientFunds as e:
		raise
	except UnconfirmedAddress as e:
		raise

	start_service()

	th = TransactionHandler(tx_info)

	sign_tx(int(token_sender.wallet_index),
			keylist,
			tx_unsigned.as_hex(include_unspents=True),
			cb=th.callback)

	return th, to_oa_address

'''
transaction_handler = pay_to_address('lekanovic@gmail.com', 'popjull@teleworm.us', 10000)

transaction_handler = issueasset_wallet('popjull@teleworm.us', 10, metadata='http://goo.gl/s34sd')

while not transaction_handler.has_been_called:
	time.sleep(0.5)
print transaction_handler.tx_info

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

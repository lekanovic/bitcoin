from lockfile import LockFile
from celery import Celery
from api import *
import time, json

app = Celery('tasks', backend='amqp', broker='amqp://localhost')
app.conf.update(
    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],  # Ignore other content
    CELERY_RESULT_SERIALIZER='json',
    CELERY_TIMEZONE='US/Pacific',
    CELERY_ENABLE_UTC=True,
)

signservice = "signservice"


@app.task
def validate_passwd_rpc(email, password):
	return log_in(email, password)

@app.task
def create_account_rpc(name,lastname,email,password,reg_id):
	print name,lastname,email,password
	resp = {}
	resp['type'] = 'CREATE_ACCOUNT'
	resp['email'] = email
	resp['name'] = name
	resp['lastname'] = lastname

	lock = LockFile(signservice)
	lock.acquire()

	try:
		key_handler = create_account(name,lastname,email,password.encode('utf-8'),reg_id)
	except AccountExistException as e:
		lock.release()
		resp['status'] = 'FAILED %s' % e.message
		return resp

	while not key_handler.has_been_called:
		time.sleep(0.5)

	lock.release()

	return resp

@app.task
def fetch_account_rpc(email):
	a = fetch_account(email)
	return a

@app.task
def fetch_account_regid_rpc(email):
	a = fetch_account_regid(email)
	return a

@app.task
def find_account_with_balance_rpc():
	account, balance = find_account_with_balance()

	d = {}
	d['email'] = account['email']
	d['balance'] = balance
	d['wallet_index'] = 0
	return json.dumps(d)

@app.task
def find_random_account_rpc():
	account, balance = find_random_account()

	d = {}
	d['email'] = account['email']
	d['balance'] = balance
	d['wallet_index'] = 0 #We only support one wallet
	return json.dumps(d)

@app.task
def pay_to_address_rpc(send_from, send_to, amount, msg):
	print send_from, send_to, amount, msg
	resp = {}
	resp['type'] = 'STANDARD'
	resp['from'] = send_from
	resp['to'] = send_to
	resp['amount'] = amount
	resp['message'] = msg

	lock = LockFile(signservice)
	lock.acquire()

	try:
		transaction_handler = pay_to_address(send_from, send_to, amount, msg=msg)
	except InsufficientFunds as e:
		lock.release()
		resp['status'] = 'FAILED %s' % e.message
		return resp
	except UnconfirmedAddress as e:
		lock.release()
		resp['status'] = 'FAILED %s' % e.message
		return resp

	while not transaction_handler.has_been_called:
		time.sleep(0.5)

	lock.release()

	if transaction_handler.has_error:
		resp['status'] = 'FAILED %s' % transaction_handler.error_message
		return resp

	resp['tx_id'] = transaction_handler.tx_info['tx_id']

	return resp

@app.task
def multisig_transacion_rpc(from_email, to_email, escrow_email, amount, msg):
	print from_email, to_email, escrow_email, amount, msg
	resp = {}
	resp['type'] = 'MULTISIG'
	resp['from'] = from_email
	resp['to'] = to_email
	respo['escrow'] = escrow_email
	resp['amount'] = amount
	resp['message'] = msg

	lock = LockFile(signservice)
	lock.acquire()

	try:
		transaction_handler = multisig_transacion(from_email, to_email, escrow_email, amount, msg=msg)
	except InsufficientFunds as e:
		lock.release()
		resp['status'] = 'FAILED %s' % e.message
		return resp
	except UnconfirmedAddress as e:
		lock.release()
		resp['status'] = 'FAILED %s' % e.message
		return resp

	while not transaction_handler.has_been_called:
		time.sleep(0.5)

	lock.release()

	if transaction_handler.has_error:
		resp['status'] = 'FAILED %s' % transaction_handler.error_message
		return resp

	resp['tx_id'] = transaction_handler.tx_info['tx_id']

	return resp

@app.task
def write_blockchain_message_rpc(email, message):
	print email, message
	resp = {}
	resp['status'] = 'SUCCESS'
	resp['type'] = 'BLKCHN_MESSAGE'
	resp['from'] = email
	resp['message'] = message

	lock = LockFile(signservice)
	lock.acquire()

	try:
		transaction_handler = write_blockchain_message(email, message)
	except InsufficientFunds as e:
		lock.release()
		resp['status'] = 'FAILED %s' % e.message
		return resp
	except UnconfirmedAddress as e:
		lock.release()
		resp['status'] = 'FAILED %s' % e.message
		return resp

	while not transaction_handler.has_been_called:
		time.sleep(0.5)

	lock.release()

	if transaction_handler.has_error:
		resp['status'] = 'FAILED %s' % transaction_handler.error_message
		return resp

	resp['tx_id'] = transaction_handler.tx_info['tx_id']

	return resp

@app.task
def issueasset_rpc(email, amount, metadata):
	'''
		Issue an asset and attach some metadata. Metadata
		should be a URL to the asset information

		email - Email address for the asset issuer
		amount - How many assets to issue
		metadata - Any data, but prefered is to have an URL
				pointing to asset information
	'''
	resp = {}
	resp['status'] = 'SUCCESS'
	resp['type'] = 'ISSUEASSET'
	resp['from'] = email
	resp['metadata'] = metadata

	lock = LockFile(signservice)
	lock.acquire()

	try:
		transaction_handler = issueasset(email, amount, metadata=metadata, fees=10000)
	except InsufficientFunds as e:
		lock.release()
		resp['status'] = 'FAILED %s' % e.message
		return resp
	except UnconfirmedAddress as e:
		lock.release()
		resp['status'] = 'FAILED %s' % e.message
		return resp

	while not transaction_handler.has_been_called:
		time.sleep(0.5)

	lock.release()

	if transaction_handler.has_error:
		resp['status'] = 'FAILED %s' % transaction_handler.error_message
		return resp

	resp['tx_id'] = transaction_handler.tx_info['tx_id']

	return resp

@app.task
def sendasset_rpc(from_email, to_email, amount, asset_id):
	'''
		Send an asset to another user.
		from_email - Self explained
		to_email - Self explained
		amount - How many assets to send
		asset_id - The ID of the asset to send
		to_oa_address - Opanasset address to send asset to
	'''
	resp = {}
	resp['status'] = 'SUCCESS'
	resp['type'] = 'SENDASSET'
	resp['from'] = from_email
	resp['to'] = to_email
	resp['amount'] = amount
	resp['asset_id'] = asset_id


	lock = LockFile(signservice)
	lock.acquire()

	try:
		transaction_handler, to_oa_address = sendasset(from_email,
										to_email,
										amount,
										asset_id)
		resp['oa_address'] = to_oa_address

	except InsufficientFunds as e:
		lock.release()
		resp['status'] = 'FAILED %s' % e.message
		return resp
	except UnconfirmedAddress as e:
		lock.release()
		resp['status'] = 'FAILED %s' % e.message
		return resp

	while not transaction_handler.has_been_called:
		time.sleep(0.5)

	lock.release()

	if transaction_handler.has_error:
		resp['status'] = 'FAILED %s' % transaction_handler.error_message
		return resp

	resp['tx_id'] = transaction_handler.tx_info['tx_id']

	return resp

@app.task
def request_payment_rpc(gcm_api_key, requester, request_from, amount, msg):
	resp = request_payment(gcm_api_key, requester, request_from, amount, msg)

	return resp

@app.task
def fetch_transaction_by_email_rpc(email):
	d = fetch_transactions_by_email(email)

	return json.dumps(d)

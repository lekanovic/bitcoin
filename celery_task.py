from picunia.security.sign_tx_client import start_service
from celery import Celery
from api import *
import time

app = Celery('tasks', backend='amqp', broker='amqp://localhost')
app.conf.update(
    CELERY_TASK_SERIALIZER='json',
    CELERY_ACCEPT_CONTENT=['json'],  # Ignore other content
    CELERY_RESULT_SERIALIZER='json',
    CELERY_TIMEZONE='US/Pacific',
    CELERY_ENABLE_UTC=True,
)

@app.task
def validate_passwd_rpc(email, password):
	return log_in(email, password)

@app.task
def create_account_rpc(name,lastname,email,password):
	print name,lastname,email,password
	start_service()
	time.sleep(2)

	key_handler = create_account(name,lastname,email,password.encode('utf-8'))

	while not key_handler.has_been_called:
		time.sleep(0.5)

	return "Account %s created" % (email)

@app.task
def fetch_account_rpc(email):
	a = fetch_account(email)
	return a

@app.task
def pay_to_address_rpc(send_from, send_to, amount, msg):
	print send_from, send_to, amount, msg
	start_service()
	time.sleep(2)

	transaction_handler = pay_to_address(send_from, send_to, amount, msg=msg)

	while not transaction_handler.has_been_called:
		time.sleep(0.5)

	return "STANDARD transaction %s created" % (transaction_handler.tx_info['tx_id'])

@app.task
def multisig_transacion_rpc(from_email, to_email, escrow_email, amount, msg):
	print from_email, to_email, escrow_email, amount, msg
	start_service()
	time.sleep(2)

	transaction_handler = multisig_transacion(from_email, to_email, escrow_email, amount, msg=msg)

	while not transaction_handler.has_been_called:
		time.sleep(0.5)

	return "MULTISIG transaction %s created" % (transaction_handler.tx_info['tx_id'])

@app.task
def write_blockchain_message_rpc(email, message):
	print email, message
	start_service()
	time.sleep(2)

	transaction_handler = write_blockchain_message(email, message)

	while not transaction_handler.has_been_called:
		time.sleep(0.5)

	return "BLKCHN_MESSAGE transaction %s created" % (transaction_handler.tx_info['tx_id'])
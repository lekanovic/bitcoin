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
def create_account_rpc(name,lastname,email,password):
	print name,lastname,email,password
	start_service()
	time.sleep(2)

	create_account(name,lastname,email,password.encode('utf-8'))

	while True:
		wallet = fetch_wallet(email)
		if wallet['public_key']:
			break
		time.sleep(2)

	return "Account %s created" % (email)

@app.task
def fetch_account_rpc(email):
	a = fetch_account(email)
	return a


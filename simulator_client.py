from celery_task import create_account_rpc
from celery_task import fetch_account_rpc
from celery_task import pay_to_address_rpc
from celery_task import validate_passwd_rpc
from celery_task import find_account_with_balance_rpc
import time, sys, argparse
import urllib, json
from random import randint

'''
e = fetch_account_rpc.delay('qwert@gmail.com')

print e.get()

account = create_account_rpc.delay("Radovan","Lekanovic","qwert@gmail.com","hemlist")

while not account.ready():
	time.sleep(2)
# name,lastname,email,password)
print account.get()

account = create_account_rpc.delay("Pelle","Olsson","olsson@gmail.com","hemlist")

while not account.ready():
	time.sleep(2)
# name,lastname,email,password)
print account.get()


tx = pay_to_address_rpc.delay('qwert@gmail.com', 'olsson@gmail.com' , 10000, 'For the pizza')

while not tx.ready():
	time.sleep(1)

print tx.get()


valid = validate_passwd_rpc.delay('qwert@gmail.com', 'hemlist')

while not valid.ready():
	time.sleep(2)

print valid.get()
'''
joke_database = []

def fetch_jokes():
    url = "http://api.icndb.com/jokes/random/1000"
    response = urllib.urlopen(url);
    data = json.loads(response.read())
    for i in data['value']:
		joke_database.append(i['joke'])

def get_chucknorris_joke():
	if not joke_database:
		fetch_jokes()
	return joke_database.pop()

def send_chucknorris_joke_as_proofofexistens(from_email):
	db = Storage()
	tx_unsigned = 0
	proofofexistens_msg = get_chucknorris_joke()

	write_blockchain_message(from_email, proofofexistens_msg)

def call_api(items=0):
	url = "http://api.randomuser.me/?results=%d" % items
	response = urllib.urlopen(url);
	data = json.loads(response.read())

	for d in data['results']:
		name = d["user"]["name"]["first"]
		lastname = d["user"]["name"]["last"]
		passwd = d["user"]["password"]
		email = d["user"]["email"]
		create_account_rpc.delay(name, lastname, email, passwd.encode('utf-8'))

def fill_database(items=1):
	if items <= 100:
		call_api(items)
	else:
		n = items / 100
		for p in range(n):
			call_api(100)
		r = items % 100
		if r > 0:
			call_api(r)

def find_account_with_balance():
	account = find_account_with_balance_rpc.delay()
	while not account.ready():
		time.sleep(0.3)

	value =  account.get()
	value = json.loads(value)
	print value, value['balance']
	return value, value['balance']

def one_round():
	sender, balance = find_account_with_balance()
	receiver, tmp = find_account_with_balance()
	amount = balance / 10

	if randint(0,20) == 10:
		send_chucknorris_joke_as_proofofexistens(sender['email'])

	#if randint(0,20) == 10:
	#    escrow, tmp = find_account_with_balance()
	#    multisig_2of3(sender['email'], receiver['email'], escrow['email'], amount)

	print "%s sending %d to %s" % (sender['email'], amount, receiver['email'])
	send_from_to(sender['email'], receiver['email'], amount)

def send_from_to(from_email, to_email, amount):
	tx = pay_to_address_rpc.delay(from_email, to_email, amount, msg="This is a test message")

def generate_accounts(n):
	fill_database(n)

def main(argv):
	msg = "Test that simulates new accounts created. Simulates user sending Satoshis between them."
	parser = argparse.ArgumentParser(description=msg)
	parser.add_argument("-g","--generate",
		help="Generate random user accounts. Input: int - number of accounts to create")
	parser.add_argument("-s","--simulate",
		help="Simulate random user sending Satoshi to another random user. Input: int - rounds to run simulator")

	args = parser.parse_args()

	if args.generate:
		number = int(args.generate)
		generate_accounts(number)

	if args.simulate:
		number = int(args.simulate)
		for i in range(0, number):
			one_round()
			time.sleep(5)

	time.sleep(1000000)

if __name__ == "__main__":
  main(sys.argv[1:])
# -*- coding: utf-8 -*-
import argparse, sys
import random
import os
import subprocess
import urllib, json
import time
import datetime
from pycoin.tx.Tx import Tx
from pycoin.serialize import h2b
from picunia.users.account import Account, InsufficientFunds
from picunia.database.storage import Storage
from picunia.security.sign_tx_client import sign_tx, start_service
from bson.json_util import dumps
from pycoin.encoding import wif_to_secret_exponent
from pycoin.tx.pay_to import build_hash160_lookup
from random import randint
import logging
from api import create_account, pay_to_address, multisig_transacion


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

    # Find the user in database
    sender = json.loads(db.find_account(from_email))
    # Add the user to Account object
    sender = Account.from_json(sender)

    try:
        tx_unsigned = sender.proof_of_existens(proofofexistens_msg)
    except InsufficientFunds:
        balance = sender.wallet_balance()
        a = json.loads(db.find_account(from_email))
        if a['wallet-balance'] != balance:
            print "Updating balance from %d to %d" % (a['wallet-balance'], balance)
            db.update_account(a)
        else:
            print "Transaction failed amount too small.."
        return

    if not tx_unsigned is None:
        d={}
        d['from'] = from_email
        d['to_addr'] = "N/A"
        d['to_email'] =  "N/A"
        d['amount'] = 10000
        d['confirmations'] = -1
        d['date'] = str( datetime.datetime.now() )
        d['block'] = -1
        d['type'] = "OPRETURN"
        d['message'] = proofofexistens_msg
        print d
        sender.tx_info = d
        sign_transaction(sender, tx_unsigned, sender.transaction_cb)

    else:
        print "Transaction failed"

def multisig_2of3(from_email, to_email, escrow_email, amount):
    message = "This is a multisig test"
    multisig_transacion(from_email, to_email, escrow_email, amount, msg=message)

def call_api(items=0):
    url = "http://api.randomuser.me/?results=%d" % items
    response = urllib.urlopen(url);
    data = json.loads(response.read())

    for d in data['results']:
        name = d["user"]["name"]["first"]
        lastname = d["user"]["name"]["last"]
        passwd = d["user"]["password"]
        email = d["user"]["email"]
        create_account(name, lastname, email, passwd.encode('utf-8'))

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

def find_account_index(index):
    db = Storage()
    return db.find_account_index(int(index))

def get_number_of_accounts():
    db = Storage()
    ret = db.get_number_of_accounts()
    return int(ret)

def find_account_with_balance():
    db = Storage()
    while True:
        account = find_random_account()
        wallet_index = account['wallets'][0]
        wallet = db.find_wallet(wallet_index)

        if wallet['wallet_balance'] > 10000:
            return account, wallet['wallet_balance']

def find_random_account():
    rnd = str(random.randrange(0, get_number_of_accounts()))
    return find_account_index(rnd)

def generate_accounts(n):
    fill_database(n)

def one_round():
    sender, balance = find_account_with_balance()
    receiver = find_random_account()
    amount = balance / 10

    #if randint(0,20) == 10:
    #    send_chucknorris_joke_as_proofofexistens(sender['email'])

    #if randint(0,20) == 10:
    escrow = find_random_account()
    multisig_2of3(sender['email'], receiver['email'], escrow['email'], amount)

    #print "%s sending %d to %s" % (sender['email'], amount, receiver['email'])
    #send_from_to(sender['email'], receiver['email'], amount)


def send_from_to(from_email, to_email, amount):
    pay_to_address(from_email, to_email, amount, msg="This is a test message")

def main(argv):
    msg = "Test that simulates new accounts created. Simulates user sending Satoshis between them."
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument("-g","--generate",
        help="Generate random user accounts. Input: int - number of accounts to create")
    parser.add_argument("-s","--simulate",
        help="Simulate random user sending Satoshi to another random user. Input: int - rounds to run simulator")

    start_service()
    time.sleep(2)

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
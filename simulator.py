# -*- coding: utf-8 -*-
import argparse, sys
import random
import os
import subprocess
import urllib, json
import time
import datetime
from pycoin.tx.Tx import Tx
from pycoin.key.BIP32Node import BIP32Node
from pycoin.serialize import h2b
from picunia.users.account import Account, InsufficientFunds
from picunia.database.storage import Storage
from picunia.security.sign_tx_client import sign_tx, start_service
from bson.json_util import dumps
from pycoin.encoding import wif_to_secret_exponent
from pycoin.tx.pay_to import build_hash160_lookup
from pycoin.services.insight import InsightService
from random import randint
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

joke_database = []
insight = InsightService("http://localhost:3001")

netcode="XTN"
network="testnet"
key_path = "44H/1H/"

#netcode = 'BTC'
#networkd = "mainnet"
#key_path = "44H/0H/"

def transaction_cb(tx_hex):
    logger.debug("Transaction size %d signed", len(tx_hex))
    ret = 0
    tx = Tx.tx_from_hex(tx_hex)
    try:
        ret = insight.send_tx(tx)
    except urllib2.HTTPError as ex:
        logger.info("Transaction could not be sent")
        return -1
    print json.loads(ret)['txid']

def sign_transaction(account, tx_unsigned, netcode, callback):
    account_nr = int(account.account_index)
    key_index = int(account.index)
    tx_hex = tx_unsigned.as_hex(include_unspents=True)
    sign_tx(account_nr, key_index, netcode, tx_hex, cb=callback)

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

def send_chucknorris_joke_as_proofofexistens(sender):
    joke = get_chucknorris_joke()
    cmd = "python cc.py -p %s:\"%s\"" % (sender['email'], joke)

    proc = subprocess.Popen([cmd],
                    stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()

    print out

def multisig_transacion(sender, receiver, escrow, amount):
    cmd = "python cc.py -m %s:%s:%s:%d" % (sender, receiver, escrow,  amount)

    print sender
    proc = subprocess.Popen([cmd],
                    stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()

    print out

def call_api(items=0):
    url = "http://api.randomuser.me/?results=%d" % items
    response = urllib.urlopen(url);
    data = json.loads(response.read())

    for d in data['results']:
        name = d["user"]["name"]["first"]
        lastname = d["user"]["name"]["last"]
        passwd = d["user"]["password"]
        email = d["user"]["email"]
        add_account(name, lastname, email, passwd)

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
    cmd = "python cc.py -i %s" % index
    proc = subprocess.Popen([cmd],
                    stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()

    return json.loads(out)

def get_number_of_accounts():
    cmd = "python cc.py -n"
    proc = subprocess.Popen([cmd],
                    stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    return int(out)

def add_account(name, lastname, email, passwd):
    cmd = "python cc.py -a %s:%s:%s:%s" % (name, lastname, email, passwd)
    proc = subprocess.Popen([cmd],
                    stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    print out

def get_all_accounts():
    proc = subprocess.Popen(["python cc.py -l"],
                    stdout=subprocess.PIPE, shell=True)

    (out, err) = proc.communicate()
    return json.loads(out)['accounts']

def find_account_with_balance():
    while True:
        account = find_random_account()
        if account['wallet-balance'] > 10000:
            return account, account['wallet-balance']

def find_random_account():
    rnd = str(random.randrange(0, get_number_of_accounts()))
    return find_account_index(rnd)

def generate_accounts(n):
    fill_database(n)

def one_round():
    sender, balance = find_account_with_balance()
    receiver = find_random_account()
    amount = balance / 10
    '''
    if randint(0,20) == 10:
        send_chucknorris_joke_as_proofofexistens(sender)

    if randint(0,20) == 10:
        escrow = find_random_account()
        multisig_transacion(sender['email'], receiver['email'], escrow['email'], amount)
    '''
    print "%s sending %d to %s" % (sender['email'], amount, receiver['email'])
    send_from_to(sender['email'], receiver['email'], amount)

def send_from_to(from_email, to_email, amount):
    tx_unsigned = 0
    db = Storage()
    print from_email, to_email, amount

    sender = json.loads(db.find_account(from_email))

    receiver = json.loads(db.find_account(to_email))

    sender = Account.from_json(sender, network)
    receiver = Account.from_json(receiver, network)

    addr = receiver.get_bitcoin_address()
    db.update_account(json.loads(receiver.to_json()))

    if sender.has_unconfirmed_balance() or receiver.has_unconfirmed_balance():
        print "has_unconfirmed_balance, cannot send right now"
        exit(1)

    try:
        tx_unsigned = sender.pay_to_address(addr,amount)
    except InsufficientFunds:
        balance = sender.wallet_balance()
        a = json.loads(db.find_account(from_email))
        if a['wallet-balance'] != balance:
            print "Updating balance from %d to %d" % (a['wallet-balance'], balance)
            #db.update_balance(a, balance)
            db.update_account(json.loads(sender.to_json()))
        else:
            print "Transaction failed amount too small.."
        return

    if not tx_unsigned is None:
        tx_signed = sign_transaction(sender, tx_unsigned, netcode, sender.transaction_cb)
        d={}
        d['from'] = from_email
        d['to_addr'] = addr
        d['to_email'] =  to_email
        d['tx_id'] = -1 # tx_signed.id()
        d['amount'] = amount
        d['fee'] = -1 # tx_signed.fee()
        d['confirmations'] = -1
        d['date'] = str( datetime.datetime.now() )
        d['block'] = -1
        d['type'] = "STANDARD"

        db.add_transaction(d)
    else:
        print "Transaction failed"

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

    time.sleep(1000000)

if __name__ == "__main__":
  main(sys.argv[1:])
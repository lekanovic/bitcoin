import argparse, sys
import json
import time
import datetime
from pycoin.key.BIP32Node import BIP32Node
from pycoin.serialize import h2b
from picunia.users.account import Account, InsufficientFunds
from picunia.database.storage import Storage
from bson.json_util import dumps
from pycoin.encoding import wif_to_secret_exponent
from pycoin.tx.pay_to import build_hash160_lookup


class LazySecretExponentDB(object):
    """
    The pycoin pure python implementation that converts secret exponents
    into public pairs is very slow, so this class does the conversion lazily
    and caches the results to optimize for the case of a large number
    of secret exponents.
    """
    def __init__(self, wif_iterable, secret_exponent_db_cache):
        self.wif_iterable = iter(wif_iterable)
        self.secret_exponent_db_cache = secret_exponent_db_cache

    def get(self, v):
        if v in self.secret_exponent_db_cache:
            return self.secret_exponent_db_cache[v]
        for wif in self.wif_iterable:
            secret_exponent = wif_to_secret_exponent(wif)
            d = build_hash160_lookup([secret_exponent])
            self.secret_exponent_db_cache.update(d)
            if v in self.secret_exponent_db_cache:
                return self.secret_exponent_db_cache[v]
        self.wif_iterable = []
        return None

def BIP39_static_seed():
    words = 'category fiscal fuel great review rather useful shop middle defense cube vacuum resource fiber special nurse chief category mask display bag echo concert click february fame tenant innocent affair usual hole soon bean adjust shoe voyage immune chest gaze chaos tip way glimpse sword tray craft blur seminar'
    seed = h2b('6ad72bdbc8b5c423cdc52be4b27352086b230879a0fd642bbbb19f5605941e3001eb70c6a53ea090f28d4b0e3033846b23ae2553c60a9618d7eb001c3aba2a30')    
    return seed, words

def sign_tx(account, tx_unsigned, netcode):
	seed, words = BIP39_static_seed()
	master = BIP32Node.from_master_secret(seed, netcode)

	account_nr = account.account_index

	if netcode == "XTN":
		key_path = "44H/1H/"
	elif netcode == "BTC":
		key_path = "44H/1H/"

	wifs = []
	for k in range(0, account.index):
		p1 = key_path + "%sH/0/%s" % (account_nr, k)
		wifs.append( master.subkey_for_path(p1).wif(use_uncompressed=False) )

	p1 = key_path + "%sH/1" % (account_nr)

	wifs.append( master.subkey_for_path(p1).wif(use_uncompressed=False) )

	tx_signed = tx_unsigned.sign(LazySecretExponentDB(wifs, {}))

	return tx_signed

def main(argv):
	netcode="XTN"
	network="testnet"
	key_path = "44H/1H/"

	#netcode = 'BTC'
	#networkd = "mainnet"
	#key_path = "44H/0H/"

	parser = argparse.ArgumentParser(description="Command and Control for accounts")
	parser.add_argument("-a","--add", help="Create new account: name:lastname:email:password")
	parser.add_argument("-l","--list", action='store_true', help="List all accounts")
	parser.add_argument("-d","--delete", help="Delete all accounts. Ex cc -d transaction|account|all")
	parser.add_argument("-f","--find", help="Find account by email")
	parser.add_argument("-i","--index", help="Find account by index")
	parser.add_argument("-c","--findtransaction", help="Find transaction by transaction id")
	parser.add_argument("-p","--proofofexsitens",
		help="Create an proof of existens. EX: bob@hotmail.com:'This string will end up in the blockchain'")
	parser.add_argument("-t","--transactions", action='store_true', help="List all transactions")
	parser.add_argument("-n","--number", action='store_true', help="Number of accounts")
	parser.add_argument("-m","--multisig",
		help="Create a multisigtransaction: from:to:escrow:amount. Ex bob@hotmail.com:alice@gmail.com:escrow@lawyer.com:34000")
	parser.add_argument("-s","--send",
		help="Send Satoshi from one email to another: from:to:amount. Ex bob sends alice 34000 Satoshi bob@hotmail.com:alice@gmail.com:34000")
	args = parser.parse_args()

	db = Storage()

	if args.multisig:
		s = args.multisig.split(":")
		from_email = s[0]
		to_email = s[1]
		escrow = s[2]
		amount = int(s[3])
		tx_unsigned = 0

		sender = json.loads(db.find_account(from_email))
		receiver = json.loads(db.find_account(to_email))
		escrow = json.loads(db.find_account(escrow))

		sender = Account.from_json(sender,network)
		receiver = Account.from_json(receiver,network)
		escrow = Account.from_json(escrow,network)

		keys = []
		keys.append(sender.get_key(0))
		keys.append(receiver.get_key(0))
		keys.append(escrow.get_key(0))

		tx_multi_unsigned, multi_address = sender.multisig_2_of_3(keys)

		# Now that we have created the multisig address let's send some money to it
		if sender.has_unconfirmed_balance():
			print "has_unconfirmed_balance, cannot send right now"
			exit(1)

		try:
			tx_unsigned = sender.pay_to_address(multi_address,amount)
		except InsufficientFunds:
			balance = sender.wallet_balance()
			a = json.loads(db.find_account(from_email))
			if a['wallet-balance'] != balance:
				print "Updating balance from %d to %d" % (a['wallet-balance'], balance)
				db.update_account(a)
			else:
				print "Transaction failed amount too small.."
			exit(1)

		if not tx_unsigned is None:
			tx_signed = sign_tx(sender, tx_unsigned, netcode)
			d={}
			d['from'] = from_email
			d['to_addr'] = multi_address
			d['to_email'] =  to_email
			d['escrow'] = escrow
			d['tx_id'] = tx_signed.id()
			d['amount'] = amount
			d['fee'] = tx_signed.fee()
			d['confirmations'] = -1
			d['date'] = str( datetime.datetime.now() )
			d['block'] = -1
			d['type'] = "MULTISIG"

			db.add_transaction(d)

			sender.send_tx(tx_signed)
		else:
			print "Transaction failed"

	if args.findtransaction:
		tx_id = {}
		tx_id['tx_id'] = args.findtransaction
		print db.find_transaction(tx_id)

	if args.proofofexsitens:
		s = args.proofofexsitens.split(":")
		from_email = s[0]
		proofofexistens_msg = s[1]

		# Find the user in database
		sender = json.loads(db.find_account(from_email))
		# Add the user to Account object
		sender = Account.from_json(sender,network)

		tx_unsigned = sender.proof_of_existens(proofofexistens_msg)

		tx_signed = sign_tx(sender, tx_unsigned, netcode)

		if not tx_unsigned is None:
			tx_signed = sign_tx(sender, tx_unsigned, netcode)
			d={}
			d['from'] = from_email
			d['to_addr'] = "N/A"
			d['to_email'] =  "N/A"
			d['tx_id'] = tx_signed.id()
			d['amount'] = 10000
			d['fee'] = tx_signed.fee()
			d['confirmations'] = -1
			d['date'] = str( datetime.datetime.now() )
			d['block'] = -1
			d['type'] = "OPRETURN"

			db.add_transaction(d)

			sender.send_tx(tx_signed)
		else:
			print "Transaction failed"

	if args.transactions:
		for t in db.get_all_transactions():
			print t

	if args.index:
		print db.find_account_index(args.index)

	if args.number:
		print db.get_number_of_accounts()

	if args.send:
		s = args.send.split(":")
		from_email = s[0]
		to_email = s[1]
		amount = int(s[2])
		tx_unsigned = 0

		sender = json.loads(db.find_account(from_email))

		receiver = json.loads(db.find_account(to_email))

		sender = Account.from_json(sender,network)
		receiver = Account.from_json(receiver,network)

		addr = receiver.get_bitcoin_address()

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
				db.update_account(sender.to_json())
			else:
				print "Transaction failed amount too small.."
			exit(1)

		if not tx_unsigned is None:
			tx_signed = sign_tx(sender, tx_unsigned, netcode)
			d={}
			d['from'] = from_email
			d['to_addr'] = addr
			d['to_email'] =  to_email
			d['tx_id'] = tx_signed.id()
			d['amount'] = amount
			d['fee'] = tx_signed.fee()
			d['confirmations'] = -1
			d['date'] = str( datetime.datetime.now() )
			d['block'] = -1
			d['type'] = "STANDARD"

			db.add_transaction(d)

			sender.send_tx(tx_signed)
		else:
			print "Transaction failed"

	if args.find:
		res = db.find_account(args.find)
		if res == "null":
			print "email [%s] not found" % args.find
		else:
			print res

	if args.delete:
		if args.delete == "account":
			db.drop_database(which="account")
		elif args.delete == "transaction":
			db.drop_database(which="transaction")
		elif args.delete == "all":
			db.drop_database()

	if args.list:
		print "{\"accounts\" : ["

		n = db.get_number_of_accounts()-1
		for index in range(0, n):
			print "%s," % db.find_account_index(str(index))
		print db.find_account_index(str(n))

		print "]}"

	if args.add:
		# split the name:lastname:email:password string
		s = args.add.split(":")

		seed, words = BIP39_static_seed()
		master = BIP32Node.from_master_secret(seed, netcode)

		nr = db.get_number_of_accounts()
		path = key_path + "%dH.pub" % nr

		account_keys = master.subkey_for_path( path )

		account = Account(s[0],s[1],s[2],s[3], account_keys, network)

		json_account = account.to_json()
		json_dict = json.loads(json_account)
		if not db.add_account(json_dict):
			print "Account already exist"
		print json_account

if __name__ == "__main__":
	main(sys.argv[1:])
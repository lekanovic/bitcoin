import argparse, sys
import json
import time
from pycoin.key.BIP32Node import BIP32Node
from pycoin.serialize import h2b
from picunia.users.account import Account
from picunia.database.accountDB import AccountsDB
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
	parser.add_argument("-d","--delete", action='store_true', help="Delete all accounts")
	parser.add_argument("-f","--find", help="Find account by email")
	parser.add_argument("-i","--index", help="Find account by index")
	parser.add_argument("-n","--number", action='store_true', help="Number of accounts")
	parser.add_argument("-s","--send",
		help="Send Satoshi from one email to another: from:to:amount. Ex bob sends alice 34000 Satoshi bob@hotmail.com:alice@gmail.com:34000")
	args = parser.parse_args()

	db = AccountsDB()

	if args.index:
		print db.find_account_index(args.index)

	if args.number:
		print db.get_number_of_accounts()

	if args.send:
		s = args.send.split(":")
		from_email = s[0]
		to_email = s[1]
		amount = int(s[2])

		sender = json.loads(db.find_account(from_email))

		receiver = json.loads(db.find_account(to_email))

		sender = Account.from_json(sender,network)
		receiver = Account.from_json(receiver,network)

		addr = receiver.get_bitcoin_address()

		if sender.has_unconfirmed_balance():
			print "has_unconfirmed_balance, waiting for confirmation.."
			while sender.has_unconfirmed_balance():
				time.sleep(5)

		tx_unsigned = sender.pay_to_address(addr,amount)

		if not tx_unsigned is None:
			tx_signed = sign_tx(sender, tx_unsigned, netcode)
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

		json_account = account.to_json(include_spendables=True)
		json_dict = json.loads(json_account)
		if not db.add_account(json_dict):
			print "Account already exist"
		print json_account

if __name__ == "__main__":
	main(sys.argv[1:])
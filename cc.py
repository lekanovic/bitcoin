import argparse, sys
import json
from pycoin.key.BIP32Node import BIP32Node
from pycoin.serialize import h2b
from account import Account
from database.accountDB import AccountsDB
from bson.json_util import dumps

def BIP39_static_seed():
    words = 'category fiscal fuel great review rather useful shop middle defense cube vacuum resource fiber special nurse chief category mask display bag echo concert click february fame tenant innocent affair usual hole soon bean adjust shoe voyage immune chest gaze chaos tip way glimpse sword tray craft blur seminar'
    seed = h2b('6ad72bdbc8b5c423cdc52be4b27352086b230879a0fd642bbbb19f5605941e3001eb70c6a53ea090f28d4b0e3033846b23ae2553c60a9618d7eb001c3aba2a30')    
    return seed, words

def main(argv):
	parser = argparse.ArgumentParser()
	parser.add_argument("-a","--add", help="Create new account: name:lastname:email:password")
	parser.add_argument("-l","--list", action='store_true', help="List all accounts")
	parser.add_argument("-d","--delete", action='store_true', help="Delete all accounts")
	parser.add_argument("-f","--find", help="Find account by email")
	args = parser.parse_args()

	db = AccountsDB()

	if args.find:
		doc = {}
		doc['email'] = args.find
		res = db.find_account(doc)

		if res == "null":
			print "email [%s] not found" % args.find
		else:
			print res


	if args.delete:
		db.drop_database()

	if args.list:
		for a in db.get_all_accounts():
			print a

	if args.add:
		# split the name:lastname:email:password string
		s = args.add.split(":")

		seed, words = BIP39_static_seed()
		master = BIP32Node.from_master_secret(seed, netcode="XTN")

		nr = db.get_number_of_accounts()
		path = "44H/1H/" + "%dH.pub" % nr

		account_keys = master.subkey_for_path( path )

		account = Account(s[0],s[1],s[2],s[3], account_keys, network="testnet")

		print "Creating account:"
		json_dict = json.loads(account.to_json())
		if not db.add_account(json_dict):
			print "Account already exist"
		print account.to_json()

if __name__ == "__main__":
	main(sys.argv[1:])
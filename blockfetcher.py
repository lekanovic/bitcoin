from picunia.database.storage import Storage
from picunia.users.account import Account
from pycoin.services.insight import InsightService
from pycoin.serialize import b2h_rev
from pycoin.tx import Tx, TxIn, TxOut, tx_utils
#from daemon import runner
import os
import time
import json
import thread
import datetime

# http://nanvel.name/weblog/python-unix-daemon/
class BlockchainFetcher():

	def __init__(self):
		self.stdin_path = '/dev/null'
		self.stdout_path = '/dev/tty'
		self.stderr_path = '/dev/tty'
		self.pidfile_path = '%s/mydaemon.pid' % os.getcwd()
		self.pidfile_timeout = 5

		self.insight = InsightService("http://localhost:3001")
		self.db = Storage()
		self.netcode="XTN"

	def check_inputs_outputs(self, tx):
		for t1 in tx.txs_in:
			account_json = json.loads(self.db.find_bitcoin_address(t1.bitcoin_address(self.netcode)))
			if account_json:
				print "Sending bitcoins %s" % account_json['email']
				a = Account.from_json(account_json, network="testnet")
				if a.wallet_balance() != account_json['wallet-balance']:
					print "Old balance %d New balance %d" % (account_json['wallet-balance'], a.wallet_balance())
					self.db.update_account( json.loads(a.to_json()) )

		for t2 in tx.txs_out:
			account_json = json.loads(self.db.find_bitcoin_address(t2.bitcoin_address(self.netcode)))
			if account_json:
				print "Receiving bitcoins %s" % account_json['email']
				a = Account.from_json(account_json, network="testnet")
				if a.wallet_balance() != account_json['wallet-balance']:
					print "Old balance %d New balance %d" % (account_json['wallet-balance'], a.wallet_balance())
					self.db.update_account( json.loads(a.to_json()) )

	def update_transactions(self, block_height):
		for unconf_tx in self.db.get_all_transactions():
			unconf_tx = json.loads(unconf_tx)['tx_id']
			tx_dict = {}
			try:
				tx_dict = self.insight.get_tx_dict(unconf_tx)
			except:
				print "WARNING Transaction %s has not made it onto blockchain" % unconf_tx
				continue
			tx_dict['tx_id'] = unconf_tx
			tx_dict['block'] = block_height
			self.db.update_transaction(tx_dict)

	def catch_up(self):
		'''
		TODO
			Work your way back by using the previous block until we reach
			last_height. Then we have all the blocks that we have missed.
		'''
		last_height = json.loads(self.db.find_last_block())
		if not last_height:
			return
		tip_hash = self.insight.get_blockchain_tip()
		blockheader, tx_hashes = self.insight.get_blockheader_with_transaction_hashes(tip_hash)

		print type(last_height)
		print len(last_height)
		print "block height %s" % last_height[0]['block-height']

	def run(self):
		previous_block=0
		print "Starting blockchain fetcher..."
		while True:
			tip_hash = self.insight.get_blockchain_tip()
			current_block = b2h_rev(tip_hash)
			if current_block != previous_block: # A new block has been accepted in the blockchain
				blockheader, tx_hashes = self.insight.get_blockheader_with_transaction_hashes(tip_hash)
				print blockheader

				for t1 in tx_hashes:
					hex_tx = b2h_rev(t1)
					tx = self.insight.get_tx(t1)
					self.check_inputs_outputs(tx)
				self.update_transactions(blockheader.height)
			previous_block = current_block
			blk = {}
			blk['block-height'] = blockheader.height
			self.db.add_block(blk)
			time.sleep(5)

def sync_all_accounts(threadName, delay):
	db = Storage()
	n = db.get_number_of_accounts()-1

	start_time = time.time()
	print "Syncing all accounts.."
	for index in range(0, n):
		account_json = json.loads(db.find_account_index(str(index)))
		a = Account.from_json(account_json, network="testnet")
		if a.wallet_balance() != account_json['wallet-balance']:
			print "Old balance %d New balance %d" % (account_json['wallet-balance'], a.wallet_balance())
			db.update_account( json.loads(a.to_json()) )
	delta = (time.time() - start_time)
	print "DONE! syncing all accounts it took %s " %  str(datetime.timedelta(seconds=delta))

try:
	thread.start_new_thread(sync_all_accounts, ("Sync-account-thread", 2))
except:
   print "Error: unable to start thread"

app = BlockchainFetcher()
app.catch_up()
app.run()
#daemon_runner = runner.DaemonRunner(app)
#daemon_runner.do_action()

'''
account_json = json.loads(db.find_bitcoin_address("mxnEPXCb6NbPGtg3iFdjUHnuQag9RhUDPv"))

a = Account.from_json(account_json, network="testnet")
print a.wallet_balance()
print account_json['wallet-balance']
print account_json['email']
db.update_balance(account_json, a.wallet_balance())

db_tx = TransactionDB()
print db_tx.get_all_transactions()
'''
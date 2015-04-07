from picunia.database.storage import Storage
from picunia.users.account import Account
from pycoin.services.insight import InsightService
from pycoin.serialize import b2h_rev
from pycoin.tx import Tx, TxIn, TxOut, tx_utils
#from daemon import runner
import os
import time
import json


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
				print "Old balance %d New balance %d" % (account_json['wallet-balance'], a.wallet_balance())
				self.db.update_balance(account_json, a.wallet_balance())
		for t2 in tx.txs_out:
			account_json = json.loads(self.db.find_bitcoin_address(t2.bitcoin_address(self.netcode)))
			if account_json:
				print "Receiving bitcoins %s" % t2.bitcoin_address(self.netcode)
				a = Account.from_json(account_json, network="testnet")
				print "Old balance %d New balance %d" % (account_json['wallet-balance'], a.wallet_balance())
				self.db.update_balance(account_json, a.wallet_balance())

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

	def run(self):
		previous_block=0
		while True:
			tip_hash = self.insight.get_blockchain_tip()
			current_block = b2h_rev(tip_hash)
			if current_block != previous_block: # A new block has been accepted in the blockchain
				blockheader, tx_hashes = self.insight.get_blockheader_with_transaction_hashes(tip_hash)
				print blockheader
				'''
				Get all tx ids from the new block. Check if we have unconfirmed tx and compare
				those with to the one's in the new block. If we find a match update our database.
				'''
				tx_ids = [ json.loads(p)['tx_id'] for p in self.db.get_unconfirmed_transactions()]

				for t1 in tx_hashes:
					hex_tx = b2h_rev(t1)
					if hex_tx in tx_ids:
						print "Transaction made from our wallets"
						tx = self.insight.get_tx(t1)
						self.check_inputs_outputs(tx)
				self.update_transactions(blockheader.height)
			previous_block = current_block
			time.sleep(5)

app = BlockchainFetcher()
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
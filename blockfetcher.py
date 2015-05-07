from picunia.database.storage import Storage
from picunia.users.account import Account
from pycoin.services.insight import InsightService
from pycoin.serialize import b2h_rev
from pycoin.tx import Tx, TxIn, TxOut, tx_utils
from picunia.config.settings import Settings
#from daemon import runner
import os
import time
import json
import thread
import datetime
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# http://nanvel.name/weblog/python-unix-daemon/
class BlockchainFetcher():

	def __init__(self):
		self.stdin_path = '/dev/null'
		self.stdout_path = '/dev/tty'
		self.stderr_path = '/dev/tty'
		self.pidfile_path = '%s/mydaemon.pid' % os.getcwd()
		self.pidfile_timeout = 5

		self.insight = InsightService(Settings.INSIGHT_ADDRESS)
		self.db = Storage()

	def check_inputs_outputs(self, tx):
		for t1 in tx.txs_in:
			account_json = json.loads(self.db.find_bitcoin_address(t1.bitcoin_address(Settings.NETCODE)))
			if account_json:
				logger.debug("Sending bitcoins %s", account_json['email'])
				a = Account.from_json(account_json)
				if a.wallet_balance() != account_json['wallet-balance']:
					logger.debug("Old balance %d New balance %d", account_json['wallet-balance'], a.wallet_balance())
					self.db.update_account( json.loads(a.to_json()) )

		for t2 in tx.txs_out:
			account_json = json.loads(self.db.find_bitcoin_address(t2.bitcoin_address(Settings.NETCODE)))
			if account_json:
				logger.debug("Receiving bitcoins %s", account_json['email'])
				a = Account.from_json(account_json)
				if a.wallet_balance() != account_json['wallet-balance']:
					logger.debug("Old balance %d New balance %d", account_json['wallet-balance'], a.wallet_balance())
					self.db.update_account( json.loads(a.to_json()) )

	def update_transactions(self, block_height):
		for unconf_tx in self.db.get_all_transactions():
			unconf_tx = json.loads(unconf_tx)['tx_id']
			tx_dict = {}
			try:
				tx_dict = self.insight.get_tx_dict(unconf_tx)
			except:
				logger.debug("WARNING Transaction %s has not made it onto blockchain", unconf_tx)
				continue
			tx_dict['tx_id'] = unconf_tx
			tx_dict['block'] = block_height
			self.db.update_transaction(tx_dict)

	def catch_up(self):
		'''
		This function will restart at the last block that was processes. This function
		is necessary if the process stops running or needs to be restarted. We want to
		be sure not to miss any blocks.

		'''
		block_hashes = []
		current_height = 0
		last_height = json.loads(self.db.find_last_block())[0]['block-height']

		if not last_height:
			return

		tip_hash = self.insight.get_blockchain_tip()
		while last_height != current_height:
			blockheader, tx_hashes = self.insight.get_blockheader_with_transaction_hashes(tip_hash)
			current_height = blockheader.height
			tip_hash = blockheader.previous_block_hash
			block_hashes.insert(0,tip_hash)
			blk = {}
			blk['block-height'] = blockheader.height
			self.db.add_block(blk)

		# Reverse the list
		for b in block_hashes:
			blockheader, tx_hashes = self.insight.get_blockheader_with_transaction_hashes(b)
			logger.info(blockheader.height)

			for t1 in tx_hashes:
				hex_tx = b2h_rev(t1)
				tx = self.insight.get_tx(t1)
				self.check_inputs_outputs(tx)
			self.update_transactions(blockheader.height)

	def run(self):
		previous_block=0
		logger.info("Starting blockchain fetcher...")
		while True:
			tip_hash = self.insight.get_blockchain_tip()
			current_block = b2h_rev(tip_hash)
			if current_block != previous_block: # A new block has been accepted in the blockchain
				blockheader, tx_hashes = self.insight.get_blockheader_with_transaction_hashes(tip_hash)
				logger.debug(blockheader)

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
	logger.info("Syncing all accounts..")
	for index in range(0, n):
		account_json = json.loads(db.find_account_index(str(index)))
		a = Account.from_json(account_json)
		if a.wallet_balance() != account_json['wallet-balance']:
			logger.info("Old balance %d New balance %d", account_json['wallet-balance'], a.wallet_balance())
			db.update_account( json.loads(a.to_json()) )
	delta = (time.time() - start_time)
	logger.info("DONE! syncing all accounts it took %s ", str(datetime.timedelta(seconds=delta)))

try:
	thread.start_new_thread(sync_all_accounts, ("Sync-account-thread", 2))
except:
	logger.info("Error: unable to start thread")

app = BlockchainFetcher()
app.catch_up()
app.run()



#daemon_runner = runner.DaemonRunner(app)
#daemon_runner.do_action()

'''
account_json = json.loads(db.find_bitcoin_address("mxnEPXCb6NbPGtg3iFdjUHnuQag9RhUDPv"))

a = Account.from_json(account_json)
print a.wallet_balance()
print account_json['wallet-balance']
print account_json['email']
db.update_balance(account_json, a.wallet_balance())

db_tx = TransactionDB()
print db_tx.get_all_transactions()
'''
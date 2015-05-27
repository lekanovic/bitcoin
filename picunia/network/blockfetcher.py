from picunia.database.storage import Storage
from picunia.users.wallet import Wallet
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

	def __update_balance(self, w, account):
		if w.wallet_balance() != account['wallet_balance']:
			logger.debug("Old balance %d New balance %d", account['wallet_balance'], w.wallet_balance())
			self.db.update_wallet(w.to_dict())

	def check_inputs_outputs(self, tx):
		for t1 in tx.txs_in:
			account, wallet = self.db.find_bitcoin_address(t1.bitcoin_address(Settings.NETCODE))
			if account and wallet['public_key']:
				logger.debug("Sending bitcoins %s", account['email'])
				key = wallet['public_key']
				w = Wallet(key)
				self.__update_balance(w, wallet)

		for t2 in tx.txs_out:
			account, wallet = self.db.find_bitcoin_address(t2.bitcoin_address(Settings.NETCODE))
			if account and wallet['public_key']:
				logger.debug("Receiving bitcoins %s", account['email'])
				key = wallet['public_key']
				w = Wallet(key)
				self.__update_balance(w, wallet)

	def update_transactions(self, block_height):
		for unconf_tx in self.db.get_all_transactions():
			unconf_tx = unconf_tx['tx_id']
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

		last_height = self.db.find_last_block()

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
				logger.info(blockheader.height)

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
	n = db.get_number_of_wallets()

	start_time = time.time()
	logger.info("Syncing all wallets..")
	for index in range(0, n):
		w = db.find_wallet(index)

		key = w['public_key']
		if not key: # Make sure this is not a dummy wallet
			continue

		wallet = Wallet(key)

		if wallet.wallet_balance() != w['wallet_balance']:
			logger.info("Old balance %d New balance %d", w['wallet_balance'], wallet.wallet_balance())
			db.update_wallet(wallet.to_dict())
	delta = (time.time() - start_time)
	logger.info("DONE! syncing all wallets it took %s ", str(datetime.timedelta(seconds=delta)))

try:
	thread.start_new_thread(sync_all_accounts, ("Sync-wallet-thread", 2))
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
print account_json['wallet_balance']
print account_json['email']
db.update_balance(account_json, a.wallet_balance())

db_tx = TransactionDB()
print db_tx.get_all_transactions()
'''
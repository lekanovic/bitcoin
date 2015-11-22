from picunia.database.storage import Storage
from picunia.users.wallet import Wallet
from picunia.network.insightserviceproxy import InsightServiceProxy
from pycoin.serialize import b2h_rev
from pycoin.tx import Tx, TxIn, TxOut, tx_utils
from pycoin.tx.script.tools import opcode_list
from pycoin.serialize.bitcoin_streamer import parse_bc_int
from picunia.config.settings import Settings
from picunia.openasset.utils import oa_parse_script, OPEN_ASSETS_TAG
from picunia.openasset.utils import hash_script, oa_issueasset, oa_listunspent, oa_getbalance
#from daemon import runner
import os
import time
import json
import threading
import datetime
import logging
import io
import binascii


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

		self.insight = InsightServiceProxy()
		self.db = Storage()

	def get_balance(self, btc_address):
		total = 0
		if self.insight.has_unconfirmed_balance([btc_address]):
			total = self.insight.address_unconfirmed_balance(btc_address)
		else:
			total = self.insight.address_balance(btc_address)
		return total

	def is_markeroutput(self, tx_out):
		op_codes = opcode_list(tx_out.script)

		if op_codes[0] != 'OP_RETURN':
			return False

		payload = binascii.unhexlify(op_codes[1])

		oap_marker = payload[0:4]
		if oap_marker != OPEN_ASSETS_TAG:
			return False
		return True

	def update_openasset(self, tx):

		addresses  = set()
		is_issue_asset = True
		issuance_asset = []
		transact_asset = []
		markeroutput = None
		metadata = None

		for i, t2 in enumerate(tx.txs_out):
			btc_address = t2.bitcoin_address(Settings.NETCODE)
			if self.is_markeroutput(t2):
				is_issue_asset = False
				prev_tx = self.insight.get_tx(tx.txs_in[0].previous_hash)
				script = prev_tx.txs_out[tx.txs_in[0].previous_index].script

				markeroutput = t2.script
				continue

			if is_issue_asset:
				issuance_asset.append(t2)
			else:
				transact_asset.append(t2)

			addresses.add(btc_address)

		if markeroutput:
			metadata, amount = oa_parse_script(markeroutput)
			print "METADATA:", metadata, amount

		for a in issuance_asset:
			print "ISSUEASSET asset", a

		for a in transact_asset:
			print "TRANSACTION asset", a

		for addr in list(addresses):
			_, wallet = self.db.find_bitcoin_address(addr)

			asset_balance = oa_getbalance(addr)
			print asset_balance
			print "oa_address:",asset_balance[0]['oa_address']
			for a in  asset_balance[0]['assets']:
				#a['metadata'] = metadata
				print a
				self.db.update_wallet_asset(wallet,
											a['asset_id'], 
											a['quantity'],
											metadata=metadata)


	def check_inputs_outputs(self, tx):

		for t1 in tx.txs_in:
			btc_address = t1.bitcoin_address(Settings.NETCODE)
			account, wallet = self.db.find_bitcoin_address(btc_address)
			logger.info("btc_address %s" % btc_address)
			logger.info(opcode_list(t1.script))
			if account and wallet['public_key']:
				w = Wallet.from_json(wallet)

				total = self.get_balance(btc_address)

				logger.info("Sending %d SAT from %s address %s" % (total, account['email'], btc_address))

				w.update_balance(btc_address, total)
				self.db.update_wallet(w.to_dict())

		isopenasset = any((True for t2 in tx.txs_out if self.is_markeroutput(t2)))

		if isopenasset:
			self.update_openasset(tx)

		for t2 in tx.txs_out:
			btc_address = t2.bitcoin_address(Settings.NETCODE)
			account, wallet = self.db.find_bitcoin_address(btc_address)
			logger.info("btc_address %s" % btc_address)

			if account and wallet['public_key']:
				w = Wallet.from_json(wallet)

				total = self.get_balance(btc_address)
				logger.info("Receiving %d SAT %s to address %s" % (total, account['email'], btc_address))

				w.update_balance(btc_address, total)
				self.db.update_wallet(w.to_dict())


	def update_transactions(self, block_height):
		for unconf_tx in self.db.get_all_transactions():
			unconf_tx = unconf_tx['tx_id']
			tx_dict = {}
			try:
				tx_dict = self.insight.get_tx_dict(unconf_tx)
			except:
				logger.info("WARNING Transaction %s has not made it onto blockchain", unconf_tx)
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
			logger.info("Catch up no previous block found..")
			return

		tip_hash = self.insight.get_blockchain_tip()

		logger.info("Catch up unprocessed blocks last block: %d" % last_height)
		while last_height != current_height:
			blockheader, tx_hashes = self.insight.get_blockheader_with_transaction_hashes(tip_hash)
			current_height = blockheader.height
			if current_height < last_height:
				msg = "last block %s worked on cannot be larger than tip %s" % (last_height, current_height)
				raise ValueError(msg)
			print current_height
			tip_hash = blockheader.previous_block_hash
			block_hashes.insert(0,tip_hash)

			self.db.add_block(blockheader.height)

		logger.info("Catch up from %d with to tip: %d" % (last_height, current_height))
		# Reverse the list
		for b in block_hashes:
			blockheader, tx_hashes = self.insight.get_blockheader_with_transaction_hashes(b)
			logger.info(blockheader.height)

			t = threading.Thread(target=self.worker_thread, args=(tx_hashes,))
			t.setDaemon(True)
			t.start()

			self.update_transactions(blockheader.height)
		logger.info("Catch up DONE!")

	def worker_thread(self, tx_hashes):
		name = threading.currentThread().getName()
		logger.info("start - worker_thread %s" % name)
		start_time = time.time()
		for t1 in tx_hashes:
			hex_tx = b2h_rev(t1)
			tx = 0
			try:
				tx = self.insight.get_tx(t1)
			except TypeError:
				logger.info("Could not read tx: %s" % hex_tx)
				continue
			self.check_inputs_outputs(tx)
		delta = (time.time() - start_time)
		delta = str(datetime.timedelta(seconds=delta))
		logger.info("end - worker_thread %s runtime: %s" % (name, delta))

	def run(self):
		previous_block=0
		logger.info("Starting blockchain fetcher...")
		while True:
			tip_hash = self.insight.get_blockchain_tip()
			current_block = b2h_rev(tip_hash)
			if current_block != previous_block: # A new block has been accepted in the blockchain
				blockheader, tx_hashes = self.insight.get_blockheader_with_transaction_hashes(tip_hash)
				logger.info("Block: [%d] %s" %(blockheader.height, str(datetime.datetime.now())))

				t = threading.Thread(target=self.worker_thread, args=(tx_hashes,))
				t.setDaemon(True)
				t.start()

				self.update_transactions(blockheader.height)
			previous_block = current_block
			self.db.add_block(blockheader.height)
			time.sleep(5)



def sync_all_wallets(threadName, delay):
	db = Storage()
	n = db.get_number_of_wallets()

	start_time = time.time()
	logger.info("Syncing all wallets..")
	for index in range(0, n):
		w = db.find_wallet(index)

		key = w['public_key']
		if not key: # Make sure this is not a dummy wallet
			continue

		wallet = Wallet.from_json(w)
		wallet.sync_wallet()

	delta = (time.time() - start_time)
	logger.info("DONE! syncing all wallets it took %s ", str(datetime.timedelta(seconds=delta)))

#t = threading.Thread(target=sync_all_wallets, args=("Sync-wallet-thread", 2))
#t.setDaemon(True)
#t.start()


app = BlockchainFetcher()
#app.catch_up()
app.run()


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

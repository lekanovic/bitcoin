from pycoin.tx.Tx import Tx
from pycoin.services.insight import InsightService
from picunia.config.settings import Settings
from picunia.database.storage import Storage
from picunia.users.wallet import Wallet
import urllib2
import logging
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TransactionHandler():
	def __init__(self, tx_info):
		self.tx_info = tx_info
		self.insight = InsightService(Settings.INSIGHT_ADDRESS)
		self.has_been_called = False

	def callback(self, tx_hex):
		logger.debug("Transaction size %d signed %s", len(tx_hex), tx_hex)
		db = Storage()

		ret = 0
		tx = Tx.tx_from_hex(tx_hex)

		if not self.tx_info:
			raise ValueError("Must set transaction information: self.tx_info = dict")

		self.tx_info['tx_id'] = tx.id()
		self.tx_info['fee'] = tx.fee()

		db.add_transaction(self.tx_info)

		try:
			ret = self.insight.send_tx(tx)
		except urllib2.HTTPError as ex:
			logger.info("Transaction could not be sent")
			return

		self.has_been_called = True
		logger.debug("%s", json.loads(ret)['txid'])


class KeyCreateHandler():
	def __init__(self, wallet_name='undefined'):
		self.db = Storage()
		self.name = wallet_name
		self.has_been_called = False

	def callback(self, key_hex):
		wallet = Wallet(key_hex).to_dict()

		wallet['wallet_name'] = self.name

		logger.debug("callback %s", wallet['wallet_index'])

		if not self.db.add_wallet(wallet):
			logger.debug("Wallet %s already exist, updating", wallet['wallet_index'])
			self.db.update_wallet(wallet)

		self.has_been_called = True
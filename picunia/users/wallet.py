
from pycoin.convention import btc_to_satoshi, satoshi_to_btc
from pycoin.key.BIP32Node import BIP32Node
from picunia.network.insightserviceproxy import InsightServiceProxy
from pycoin.tx.Tx import Tx
from pycoin.tx.TxOut import TxOut, standard_tx_out_script
from pycoin.tx.pay_to import address_for_pay_to_script, ScriptMultisig
from pycoin.tx.TxIn import TxIn
from pycoin.tx.Spendable import Spendable
from pycoin.tx.tx_utils import distribute_from_split_pool
from pycoin.convention import tx_fee
from picunia.collection.proof import ProofOfExistence
from picunia.config.settings import Settings
from picunia.database.storage import Storage
from picunia.openasset.utils import oa_issueasset, oa_listunspent, oa_getbalance, oa_sendasset
import datetime
import md5
import json
import urllib2
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class UnconfirmedAddress(Exception):
	def __init__(self, m):
		self.message = m

class InsufficientFunds(Exception):
    def __init__(self, m):
		self.message = m

# Test BIP32 wallet
# https://dcpos.github.io/bip39/

class Wallet():

	def __init__(self, bip32node, name="undefined", create_new_object=True):

		bip32node = BIP32Node.from_text(bip32node)
		self.subkeys = []
		self.insight = InsightServiceProxy()
		self.wallet_index, self.key_external,  self.key_change = self.get_key_info(bip32node)
		self.public_key = bip32node.wallet_key(as_private=False)

		# Dont update this if called from: from_json
		if create_new_object:
			self.spendable = []
			self.status = u'active'
			self.date_updated = self.wallet_created = str( datetime.datetime.now() )
			self.wallet_name = name
			self.spendable = self.__generate_initial_keys()

		public_addresses =  [ a[u'public_address'] for a in self.spendable]
		public_addresses.pop() # remove change address
		self.subkeys.extend(public_addresses)

		self.discovery()

	@classmethod
	def from_json(cls, json):
		cls.status = json[u'status']
		cls.wallet_created = json[u'date']
		cls.wallet_name = json[u'wallet_name']
		cls.spendable = json[u'spendable']
		cls.balance = json[u'wallet_balance']
		cls.date_updated = str( datetime.datetime.now() )

		return cls(json[u'public_key'], create_new_object=False)

	def __generate_initial_keys(self):
		d = {}
		key_amount = []

		d[u'public_address'] = self.get_key(0).address()
		d[u'amount'] = 0
		key_amount.append(d)

		d = {}
		d[u'public_address'] = self.key_change.address()
		d[u'amount'] = 0
		key_amount.append(d)
		return key_amount

	def get_key_info(self, bip32node):
		child_number = bip32node.child_index()
		if child_number >= 0x80000000:
			wc = child_number - 0x80000000
			child_index = "%d" % wc
		else:
			child_index = "%d" % child_number

		external = bip32node.subkey_for_path("0")
		change = bip32node.subkey_for_path("1")

		return child_index, external, change

	def get_all_pub_keys(self):
		return self.subkeys

	def get_wallet_index(self):
		return self.wallet_index

	def get_bitcoin_address(self):
		self.discovery()
		return self.subkeys[-1]

	def get_key(self, index=-1):
		if index == -1:
			index_of_last_address = len(self.subkeys)
			return self.key_external.subkey_for_path(str(index_of_last_address))
		else:
			return self.key_external.subkey_for_path(str(index))

	def update_balance(self, address, balance):
		if type(address) != unicode or type(balance) != int:
			raise ValueError("Wrong type address %s balance %s" % (type(address),type(balance) ))

		for a in self.spendable:
			if a[u'public_address'] == address:
				logger.debug("Updating %s with %d SAT prev balance %d SAT" % (address, balance, a[u'amount']))
				a[u'amount'] = balance
				self.date_updated = str( datetime.datetime.now() )

	def __next_address(self, i):
		index = 0
		if type(i) == int:
			index = str(i)
		else:
			index = i
		k = self.key_external.subkey_for_path(index)
		return k.address()

	def __check_gap(self, index):
		"""
		Search for key that has previously NOT been used in transactions.
		The search is only limited by the constant GAP_LIMIT. If there is
		keys beyond that that has been used in transaction they will not be
		found.

		ref: http://bitcoin.stackexchange.com/questions/35555/
			 what-does-it-mean-when-addresses-are-labelled-beyond-the-gap-limit-highlighted

		Args:
			index (int): index of key account

		Returns:
			bool: True if there was an address that has been previously used
				  int the gap. False otherwise
		"""
		tmp = []

		for i in range(index,index + Settings.GAP_LIMIT):
			key = self.__next_address(i)
			tmp.append(key)

			if self.insight.is_address_used(key):
				self.subkeys.extend(tmp)
				return True

		return False

	def discovery(self):

		index_of_last_address = len(self.subkeys) - 1
		key = self.__next_address(index_of_last_address)

		while self.insight.is_address_used(key):
			index_of_last_address += 1
			key = self.__next_address(index_of_last_address)
			self.subkeys.append(key)

		key_amount=[]
		amount=0

		public_addresses = [a['public_address'] for a in self.spendable]

		for s in self.__get_all_keys():
			d={}
			if s in public_addresses:
				continue
			spendable = self.insight.spendables_for_address(s)
			amount=0

			for a in spendable:
				amount += a.coin_value

			d[u'public_address'] = s
			d[u'amount'] = amount
			key_amount.append(d)

		for x in key_amount:
			self.spendable.insert(-1,x)#Add change address last

	def print_keys(self, howmany=7):
		for i in range(0, howmany):
			addr = self.__next_address(i)
			print "%d %s %d" % (i, addr, self.insight.address_balance(addr))
		print "change key:", self.key_change.address()

	def wallet_balance(self):
		return sum([a['amount'] for a in self.spendable])

	def wallet_info(self):
		balance = self.wallet_balance()
		logger.debug("Wallet name: [%s] balance: Satoshi/BTC %d/%f",
					self.wallet_name,
					balance,
					satoshi_to_btc(balance))
		for k in self.subkeys:
			print "%s" % (k)

	def to_json(self, nice=False):
		if nice:
			return json.dumps(self.to_dict(),indent=4, separators=(',', ': '))
		else:
			return json.dumps(self.to_dict())

	def to_dict(self):
		wallet = {}
		wallet[u"wallet_index"] = self.wallet_index
		wallet[u"wallet_balance"] = self.wallet_balance()
		wallet[u"wallet_name"] = self.wallet_name
		wallet[u"status"] = self.status
		wallet[u"public_key"] = self.public_key
		wallet[u"date"] = self.wallet_created
		wallet[u"spendable"] = self.spendable
		wallet[u"date_updated"] = self.date_updated

		return wallet

	def sync_wallet(self):
		i = 0
		for addr in self.__get_all_keys():
			balance = self.insight.address_balance(addr)
			if balance != self.spendable[i]['amount']:
				msg = "WARN! %s object balance %d real balance %d" % (addr, self.spendable[i]['amount'], balance)
				logger.info(msg)
				self.update_balance(addr, balance)
			i = i + 1

	def __get_all_keys(self):
		# Get all of the key's in wallet. But don't forget the change key
		all_keys = self.subkeys + [self.key_change.address()]
		return all_keys

	def __greedy(self, spendable, amount):
		lesser = [utxo for utxo in spendable if utxo.coin_value < amount]
		greater =  [utxo for utxo in spendable if utxo.coin_value >= amount]
		key_func = lambda utxo: utxo.coin_value
		if greater:
			min_greater = min(greater)
			change = min_greater.coin_value - amount
			return [min_greater], change
		lesser.sort(key=key_func, reverse=True)
		result = []
		accum = 0
		for utxo in lesser:
			result.append(utxo)
			accum += utxo.coin_value
			if accum >= amount:
				change = accum - amount
				return result, change
		return None, 0

	def has_unconfirmed_balance(self):
		return self.insight.has_unconfirmed_balance(self.__get_all_keys())

	def has_unconfirmed_address(self, bitcoin_address):
		return self.insight.has_unconfirmed_balance([bitcoin_address])

	def __get_address_index(self, bitcoin_address):
		i = 0
		length = len(self.subkeys)
		while i <= length:
			addr = self.__next_address(i)
			if addr == bitcoin_address:
				return i
			i += 1
		return None

	def __get_key_indexes(self, to_spend):
		key_indexes = []
		for spendable in to_spend:
			btc_addr = spendable.bitcoin_address(netcode=Settings.NETCODE)

			if self.has_unconfirmed_address(btc_addr):
				raise UnconfirmedAddress("Unconfirmed address %s" % btc_addr)

			idx = self.__get_address_index(btc_addr)
			if idx == None:# If we don't find address then this means its a change address
				continue
			key_indexes.append(idx)
			logger.debug( "%s %d", btc_addr, idx)

		return key_indexes

	def __pay_with_fee(self, to_addr, amount, fee=10000):
		logger.debug("Pay %d to %s", amount, to_addr)
		spendables = self.insight.spendables_for_addresses(self.__get_all_keys())

		available_funds = sum(s.coin_value for s in spendables)

		if available_funds < (amount + fee):
			msg = "Available %d trying to spend %d " % (available_funds, amount + fee)
			raise InsufficientFunds(msg)

		# Get spendables including fee
		to_spend, change = self.__greedy(spendables, amount + fee)

		available_funds = sum(s.coin_value for s in to_spend)

		if available_funds < (amount + fee):
			msg = "Available %d trying to spend %d " % (available_funds, amount + fee)
			raise InsufficientFunds(msg)

		logger.debug("The change is %d", change)

		txs_in = [spendable.tx_in() for spendable in to_spend]

		key_indexes = self.__get_key_indexes(to_spend)

		txs_out = []
		# Send bitcoin to the addess 'to_addr'
		script = standard_tx_out_script(to_addr)
		txs_out.append(TxOut(amount, script))

		# Return the change back to our wallet if there is any change.
		if change > 0:
			script = standard_tx_out_script(self.key_change.address())
			txs_out.append(TxOut(change, script))

		tx = Tx(version=1, txs_in=txs_in, txs_out=txs_out, lock_time=0)
		tx.set_unspents(to_spend)

		logger.debug("Transaction fee %d", tx.fee())
		t = tx.as_hex(include_unspents=True)
		logger.debug(t)
		logger.debug("Transaction size %d unsigned", len(t))

		return tx, key_indexes

	# http://bitcoin.stackexchange.com/questions/1077/what-is-the-coin-selection-algorithm
	def pay_to_address(self, to_addr, amount, fee=10000):
		tx, key_indexes = self.__pay_with_fee(to_addr, amount, fee)

		recommended_fee = tx_fee.recommended_fee_for_tx(tx)

		if recommended_fee != fee:
			logger.debug("Recommended fee %d but using %d", recommended_fee, fee)
			tx, key_indexes = self.__pay_with_fee(to_addr, amount, recommended_fee)

		return tx, key_indexes

	def proof_of_existens(self, message, fee=10000):
		amount = 10000
		spendables = self.insight.spendables_for_addresses(self.__get_all_keys())

		available_funds = sum(s.coin_value for s in spendables)

		if available_funds < (amount + fee):
			msg = "Available %d trying to spend %d " % (available_funds, amount + fee)
			raise InsufficientFunds(msg)

		to_spend, change = self.__greedy(spendables, amount + fee)

		logger.debug("The change is %d", change)
		logger.debug("Wallet balance %s", self.wallet_balance())
		txs_in = [spendable.tx_in() for spendable in to_spend]

		key_indexes = self.__get_key_indexes(to_spend)

		# Create 40 bytes packages from the message that we want to
		# embed in the transaction.
		txs_out = []
		txs_out.extend(ProofOfExistence(message).generate_txout())

		address = self.get_bitcoin_address()
		script = standard_tx_out_script(address)
		txs_out.append(TxOut(amount, script))

		# Return the change back to our wallet if there is any change.
		if change > 0:
			script = standard_tx_out_script(self.key_change.address())
			txs_out.append(TxOut(change, script))

		tx = Tx(version=1, txs_in=txs_in, txs_out=txs_out, lock_time=0)
		tx.set_unspents(to_spend)

		if tx.fee() == 0:
			raise InsufficientFunds("No fee added, must have fee")

		logger.debug("Transaction fee %d", tx.fee())
		t = tx.as_hex(include_unspents=True)
		logger.debug(t)
		logger.debug("Transaction size %d unsigned", len(t))

		return tx, key_indexes, address

	# http://bitcore.io/playground/#/transaction
	def multisig_2_of_3(self, keys):
		N = 2 # Keys needed to unlock
		M = 3 # Keys used to sign

		tx_in = TxIn.coinbase_tx_in(script=b'')

		script = ScriptMultisig(n=N, sec_keys=[key.sec() for key in keys[:M]])

		logger.debug("Script %s", repr(script))
		logger.debug("TxIn %s", tx_in.bitcoin_address())
		script = script.script()

		address = address_for_pay_to_script(script, Settings.NETCODE)
		logger.debug("Multisig address: %s", address)

		tx_out = TxOut(10000, script)
		tx1 = Tx(version=1, txs_in=[tx_in], txs_out=[tx_out])

		logger.debug(tx1.as_hex(include_unspents=True))

		return tx1, address

	def openasset_issueasset(self, amount, metadata='', fees=0):
		bitcoin_address=None
		key_index=0

		for idx, addr in enumerate(self.spendable):
			if addr['amount'] >= (600 + fees):
				bitcoin_address = addr['public_address']
				key_index = idx
				break

		spendables = self.insight.spendables_for_address(bitcoin_address)

		tx_unsigned = oa_issueasset(bitcoin_address,
									amount,
									to=None,
									metadata=metadata,
									fees=fees,
									txformat='raw')

		tx = Tx.tx_from_hex(tx_unsigned[1:-1])

		unspents = []
		for txin in tx.txs_in:
			for s in spendables:
				if txin.previous_hash == s.tx_hash and txin.previous_index == s.tx_out_index:

					sp = Spendable(s.coin_value,
									s.script,
									txin.previous_hash,
									txin.previous_index)
					unspents.append(sp)

		tx.set_unspents(unspents)

		assets = self.openasset_listunspent(bitcoin_address)

		asset_list = []
		for a in assets:
			if a['asset_id'] != None:
				item = {}
				item['asset_id'] = a['asset_id']
				item['asset_quantity'] = a['asset_quantity']
				item['oa_address'] = a['oa_address']
				item['address'] = a['address']
				asset_list.append(item)

		logger.debug("Transaction fee %d", tx.fee())
		t = tx.as_hex(include_unspents=True)
		logger.debug(t)
		logger.debug("Transaction size %d unsigned", len(t))

		return tx, [key_index], asset_list

	def openasset_sendasset(self, bitcoin_address, asset_id, amount, to_oa_address, fees=0):
		'''
			bitcoin_address - The bitcoin address containing the asset
			asset_id - The asset ID identifying the asset to send
			amount - Amount of assets to send
			to_oa_address - The oa_address to send it to
		'''
		key_index = self.__get_address_index(bitcoin_address)
		spendables = self.insight.spendables_for_address(bitcoin_address)

		tx_unsigned = oa_sendasset(bitcoin_address,
									asset_id,
									amount,
									to_oa_address,
									fees=fees,
									txformat='raw')

		tx = Tx.tx_from_hex(tx_unsigned[1:-1])

		unspents = []
		for txin in tx.txs_in:
			for s in spendables:
				if txin.previous_hash == s.tx_hash and txin.previous_index == s.tx_out_index:

					sp = Spendable(s.coin_value,
									s.script,
									txin.previous_hash,
									txin.previous_index)
					unspents.append(sp)
		tx.set_unspents(unspents)

		logger.debug("Transaction fee %d", tx.fee())
		t = tx.as_hex(include_unspents=True)
		logger.debug(t)
		logger.debug("Transaction size %d unsigned", len(t))

		return tx, [key_index]


	def openasset_listunspent(self, bitcoin_address, minconf='1', maxconf='9999999'):

		assets = oa_listunspent(bitcoin_address, minconf=minconf, maxconf=maxconf)

		return assets

	def openasset_getbalance(self, bitcoin_address, minconf='1', maxconf='9999999'):

		assets = oa_getbalance(bitcoin_address, minconf=minconf, maxconf=maxconf)

		return assets

	def openasset_distribute(address, forward_address, price, metadata='', fees=None, mode='unsigned', txformat='raw'):
		raise NotImplementedError(self.__class__.__name__ + '.openasset_distribute')


'''
pub = 'tpubDCwC9yxc8BmzJzPh8TzAd7hSPDid58ENdbYKcnwEXPsCAydfofutTTW6S3tNCkr6d4dd9mbHzjTLm9fAD69uD3Uido865Z8g8ur8TwpXFcw'
w = Wallet(pub)

#print w.openasset_listunspent('mosh1uA8LcVqnRgj8XK1JFxrewj6hQ7YVG')
print w.openasset_getbalance('mosh1uA8LcVqnRgj8XK1JFxrewj6hQ7YVG')

tx = w.openasset_sendasset('mosh1uA8LcVqnRgj8XK1JFxrewj6hQ7YVG',
							'2fErxWooof8vfheQxHfHfQ4Gtqaf4oK2X3H',
							'5',
							'bWyqaG4yTp6PXefr6B9RBx7sRzYuGczJUQ8')

print w.openasset_getbalance('mosh1uA8LcVqnRgj8XK1JFxrewj6hQ7YVG')


print "wallet index %s" % w.wallet_index
print "key index %d" % w.index
print "wallet ballance %d" % w.wallet_balance()
print w.wallet_info()

tx, key_indexes = w.pay_to_address('moRFkYXeu8vjVoH4HpxvmSZf7MbYbUuuNR',5000)

for k in key_indexes:
	print k

print w.get_key(27).address()
print w.get_key(23).address()
print w.get_key(24).address()
print w.get_key(3).address()
print w.get_key(4).address()
print w.get_key(26).address()

print ""

for i in range(0,120):
	addr = w.get_key(i).address()
	#print addr
	if addr in 'mxs3RUaGL6wf7G7Lecm9rZarxBRJnpypd2':
		print "Hittade %d" % i
		print addr

	if addr in 'n327hy1EjZ1cbgt6Zp3kJM1RYbEc5JfEoD':
		print "Hittade %d" % i
		print addr

	if addr in 'n1P8PbhkhWkXTj1QvTjxaAMNtaHQV6Qg53':
		print "Hittade %d" % i
		print addr

	if addr in 'miU7fUgT97h63WaPX9LNpQs23QB1Dhd6mg':
		print "Hittade %d" % i
		print addr
'''
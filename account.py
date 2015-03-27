
from pycoin.convention import btc_to_satoshi, satoshi_to_btc
from pycoin.key.BIP32Node import BIP32Node
from pycoin.services.insight import InsightService
from pycoin.tx.Tx import Tx
from pycoin.tx.TxOut import TxOut, standard_tx_out_script
from pycoin.tx.pay_to import address_for_pay_to_script, ScriptMultisig
from pycoin.tx.TxIn import TxIn

import datetime
import md5
import json


# Test BIP32 wallet
# https://dcpos.github.io/bip39/

class Account():

	def __init__(self, name, lastname, email, passwd, bip32node, network='mainnet'):
		self.name = name
		self.lastname = lastname
		self.passwd = passwd
		self.email = email
		self.subkeys = []
		self.index = 0
		self.network = network
		if network == 'mainnet':
			self.netcode = 'BTC'
		elif network == 'testnet':
			self.netcode = 'XTN'
		self.insight = InsightService("http://localhost:3001")
		self.account_index, self.key_external,  self.key_change = self.get_key_info(bip32node)
		self.public_key = bip32node.wallet_key(as_private=False)
		self.GAP_LIMIT = 5
		self.account_created = str( datetime.datetime.now() )

		self.discovery()

	@classmethod
	def from_json(cls, json, network="mainnet"):
		cls.status = json['status']
		cls.account_created = json['date']

		return cls(json['name'], json['lastname'],
				   json['email'], json['passwd'],
				   BIP32Node.from_text(json['public_key']),
				   network)

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

	def get_account_number(self):
		return self.account_index

	def get_bitcoin_address(self):
		self.discovery()
		return self.subkeys[-1]

	def get_name(self):
		return self.name

	def get_lastname(self):
		return self.lastname

	def get_email(self):
		return self.email

	def get_key(self, index=-1):
		if index == -1:
			return self.key_external.subkey_for_path(str(self.index))
		else:
			return self.key_external.subkey_for_path(str(index))

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
		Search for key that has previously been used in transactions. But
		the search is only limited by the constant GAP_LIMIT. If there is
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
		for i in range(index,index + self.GAP_LIMIT):
			key = self.__next_address(i)
			tmp.append(key)

			if self.insight.is_address_used(key):
				self.index += self.GAP_LIMIT
				self.subkeys.extend(tmp)
				return True

		return False

	def discovery(self):
		while True:
			key = self.__next_address(self.index)
			self.subkeys.append(key)
			if not self.insight.is_address_used(key):
				if not self.__check_gap(self.index):
					break
			self.index += 1

	def wallet_balance(self):
		total = 0
		# Check the wallet for spendables
		for s in self.insight.spendables_for_addresses(self.__get_all_keys()):
			total += s.coin_value
		return total

	def wallet_info(self):
		balance = self.wallet_balance()
		print "Account owner %s balance %d Satoshi = %f BTC" % (self.name, balance, satoshi_to_btc(balance))
		for k in self.subkeys:
			print "%s" % (k)

	def to_json(self, include_spendables=False):
		balance = self.wallet_balance()
		if include_spendables:
			key_amount=[]
			amount=0
			for s in self.subkeys:
				spendable = self.insight.spendables_for_address(s)
				amount=0
				for a in spendable:
					amount += a.coin_value
				key_amount.append( (s + ":" + str(amount)))

			amount=0
			for a in self.insight.spendables_for_address(self.key_change.address()):
				amount += a.coin_value
			key_amount.append( ("change:" + self.key_change.address() + ":" + str(amount)))

			return json.dumps({"name" : self.name, "lastname" : self.lastname,
							   "email" : self.email, "passwd" : self.passwd,
							   "account_index" : self.account_index,
							   "wallet-balance" : balance,
							   "status": "active",
							   "public_key": self.public_key,
							   "date": self.account_created,
							   "spendable" : key_amount}, indent=4)
		else:
			return json.dumps({"name" : self.name, "lastname" : self.lastname,
							   "email" : self.email, "passwd" : self.passwd,
							   "account_index" : self.account_index,
							   "wallet-balance" : balance,
							   "status": "active",
							   "public_key": self.public_key,
							   "date": self.account_created}, indent=4)

	def __get_all_keys(self):
		# Get all of the key's in wallet. But don't forget the change key
		all_keys = [self.key_change.address()] + self.subkeys
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

	# http://bitcoin.stackexchange.com/questions/1077/what-is-the-coin-selection-algorithm
	def pay_to_address(self, to_addr, amount, fee=10000):
		print "Pay %d to %s" % (amount, to_addr)
		spendables = self.insight.spendables_for_addresses(self.__get_all_keys())

		if amount <= fee:
			print " Amount smaller then the fee"
			return None

		# Get spendables including fee
		to_spend, change = self.__greedy(spendables, amount + fee)

		print "The change is %d" % change

		if to_spend is None:
			return None

		txs_in = [spendable.tx_in() for spendable in to_spend]

		txs_out = []
		# Send bitcoin to the addess 'to_addr'
		script = standard_tx_out_script(to_addr)
		txs_out.append(TxOut(amount, script))

		# Return the change back to our wallet
		script = standard_tx_out_script(self.key_change.address())
		txs_out.append(TxOut(change, script))

		tx = Tx(version=1, txs_in=txs_in, txs_out=txs_out, lock_time=0)
		tx.set_unspents(to_spend)

		print "Transaction fee %d" % tx.fee()
		t = tx.as_hex(include_unspents=True)
		print t
		print "Transaction size %d unsigned" % len(t)

		return tx

	# http://bitcore.io/playground/#/transaction
	def multisig_2_of_3(self, keys):
		N = 2 # Keys needed to unlock
		M = 3 # Keys used to sign

		tx_in = TxIn.coinbase_tx_in(script=b'')

		script = ScriptMultisig(n=N, sec_keys=[key.sec() for key in keys[:M]])

		print "Script %s" % repr(script)
		print "TxIn %s" % tx_in.bitcoin_address()
		script = script.script()

		address = address_for_pay_to_script(script, self.netcode)
		print "Multisig address: %s" % address

		tx_out = TxOut(1000000, script)
		tx1 = Tx(version=1, txs_in=[tx_in], txs_out=[tx_out])

		print tx1.as_hex(include_unspents=True)

		return tx1, address
		'''
		hash160_lookup = build_hash160_lookup(key.secret_exponent() for key in keys)
		tx_signed = tx2.sign(hash160_lookup=hash160_lookup)

		for idx, tx_out in enumerate(tx2.txs_in):
			if not tx2.is_signature_ok(idx):
				print "Signature Error"

		print_tx(tx_signed)
		'''

	def send_tx(self, tx_signed):
		t = tx_signed.as_hex(include_unspents=True)
		print t
		print "Transaction size %d signed" % len(t)

		for idx, tx_out in enumerate(tx_signed.txs_in):
			if not tx_signed.is_signature_ok(idx):
				print "Signature Error"
		# Send the transaction to network.
		self.insight.send_tx(tx_signed)
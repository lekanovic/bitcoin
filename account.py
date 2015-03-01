
from pycoin.key.BIP32Node import BIP32Node
from blockchain_info import BlockChainInfo
import md5
import json

class Account():

	def __init__(self, name, lastname, email, passwd, bip32node):
		'extended_pub_key => BIP32Node object'
		self.name = name
		self.lastname = lastname
		self.passwd = passwd
		self.email = email
		self.subkeys = []
		self.index = 0
		self.key_external = bip32node.subkey_for_path("0")
		self.key_change = bip32node.subkey_for_path("1")
		self.GAP_LIMIT = 5

		self.account_number = self.create_account_number()
		self.discovery()

	def create_account_number(self):
		"Hash name lastname and email, the hash will be the account number"
		m = md5.new()
		msg = self.name + self.lastname + self.email
		m.update(msg)
		return m.hexdigest()

	def get_account_number(self):
		return self.account_number

	def get_bitcoin_address(self):
		self.discovery()
		return self.subkeys[-1]

	def get_name(self):
		return self.name

	def get_lastname(self):
		return self.lastname

	def get_email(self):
		return self.email

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

			if BlockChainInfo.is_address_used(key):
				self.index += self.GAP_LIMIT
				self.subkeys.extend(tmp)
				return True

		return False

	def discovery(self):
		while True:
			key = self.__next_address(self.index)
			self.subkeys.append(key)
			if not BlockChainInfo.is_address_used(key):
				if not self.__check_gap(self.index):
					break
			self.index += 1

	def wallet_balance(self):
		total = 0
		for k in self.subkeys:
			total += BlockChainInfo.get_balance(k)
		return total

	def wallet_info(self):
		balance = self.wallet_balance()
		print "Account owner %s balance %d" % (self.name, balance)
		for k in self.subkeys:
			print "%s" % (k)

	def to_json(self):
		balance = self.wallet_balance()
		return json.dumps({"name" : self.name, "lastname" : self.lastname,
						   "email" : self.email, "passwd" : self.passwd,
						   "account_number" : self.account_number,
						   "wallet-balance" : balance}, indent=4)



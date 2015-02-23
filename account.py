
from pycoin.key.BIP32Node import BIP32Node
from blockchain_info import BlockChainInfo

class Account():

	def __init__(self, name, lastname, email, bip32node):
		'extended_pub_key => BIP32Node object'
		self.name = name
		self.lastname = lastname
		self.email = email
		self.subkeys = []
		self.index = 0
		self.account_root_key = bip32node

		self.generate_key()

	def get_bitcoin_address(self):
		return self.subkeys[-1]

	def get_name(self):
		return self.name

	def get_lastname(self):
		return self.lastname

	def get_email(self):
		return self.email

	def generate_key(self):
		key = self.account_root_key.subkey_for_path(str(self.index)).address()
		self.subkeys.append(key)
		self.index = self.index + 1

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

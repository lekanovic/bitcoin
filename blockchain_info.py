
from urllib2 import urlopen
import json

class BlockChainInfo():

	@staticmethod
	def get_balance(bitcoin_address):
	    "return balance"
	    URL = "https://blockchain.info/q/addressbalance/%s?confirmations=6" % bitcoin_address
	    return int(urlopen(URL).read())

	@staticmethod
	def get_sentby_address(bitcoin_address):
		"return amount sent"
		URL = "https://blockchain.info/q/getsentbyaddress/%s" % bitcoin_address
		return int(urlopen(URL).read())

	@staticmethod
	def get_receivedby_address(bitcoin_address):
		"return amount sent"
		URL = "https://blockchain.info/q/getreceivedbyaddress/%s" % bitcoin_address
		return int(urlopen(URL).read())

	@staticmethod
	def is_address_used(bitcoin_address):
		"return has address been used in a transaction before"
		URL = "https://blockchain.info/q/addressfirstseen/%s" % bitcoin_address
		return int(urlopen(URL).read()) != 0
import urllib2 
import json

# More info in the API
# https://support.biteasy.com/kb/rest-api

class Biteasy():

	@staticmethod
	def get_balance(bitcoin_address, network="mainnet"):
	    "return balance"

	    if network == "mainnet":
	    	URL = "https://api.biteasy.com/blockchain/v1/addresses/%s" % bitcoin_address
	    elif network == "testnet":
	    	URL = "https://api.biteasy.com/testnet/v1/addresses/%s" % bitcoin_address
	    try:
	    	request = urllib2.Request(URL, headers={'User-Agent' : "Biteasy"})
	    	blocks = json.load(urllib2.urlopen(request))
	    except urllib2.HTTPError, error:
	    	return -1
	    return blocks['data']['balance']

	@staticmethod
	def is_address_used(bitcoin_address, network="mainnet"):
		"return has address been used in a transaction before"
		if network == "mainnet":			
			URL = "https://api.biteasy.com/blockchain/v1/search?q=%s" % bitcoin_address
		elif network == 'testnet':
			URL = "https://api.biteasy.com/testnet/v1/search?q=%s" % bitcoin_address
		request = urllib2.Request(URL, headers={'User-Agent' : "Biteasy"})
		blocks = json.load(urllib2.urlopen(request))

		return len(blocks['data']['results']) != 0
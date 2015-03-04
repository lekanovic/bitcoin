import urllib2 
import json
from pycoin.tx.Spendable import Spendable
from pycoin.tx.script import tools
from pycoin.serialize import h2b_rev

try:
    from urllib2 import urlopen, Request
except ImportError:
    from urllib.request import urlopen, Request

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
	    	return 0
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

	@staticmethod
	def spendables_for_address(bitcoin_address, network="mainnet"):
	    """
	    Return a list of Spendable objects for the
	    given bitcoin address.
	    """
	    if network == "mainnet":
			URL = "https://api.biteasy.com/blockchain/v1/addresses/%s/unspent-outputs" % bitcoin_address
	    elif network == "testnet":
			URL = "https://api.biteasy.com/testnet/v1/addresses/%s/unspent-outputs" % bitcoin_address

	    r = Request(URL,
	                headers={"content-type": "application/json", "accept": "*/*", "User-Agent": "curl/7.29.0"})
	    d = urlopen(r).read()
	    json_response = json.loads(d.decode("utf8"))
	    spendables = []
	    for tx_out_info in json_response.get("data", {}).get("outputs"):
	        if tx_out_info.get("to_address") == bitcoin_address:
	            coin_value = tx_out_info["value"]
	            script = tools.compile(tx_out_info.get("script_pub_key_string"))
	            previous_hash = h2b_rev(tx_out_info.get("transaction_hash"))
	            previous_index = tx_out_info.get("transaction_index")
	            spendables.append(Spendable(coin_value, script, previous_hash, previous_index))
	    return spendables
from picunia.config.settings import Settings
import requests
import logging
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('openassets')


def send_request(operation, payload):
	base_url = Settings.OPENASSET_SERVER

	try:
		res = requests.post(base_url + operation, data=payload)
	except requests.exceptions.Timeout as e:
		logger.exception(e)
	except requests.exceptions.HTTPError as e:
		logger.exception(e)
	except requests.exceptions.TooManyRedirects as e:
		logger.exception(e)
	except requests.exceptions.ConnectTimeout as e:
		logger.exception(e)
	except requests.exceptions.RequestException as e:
		logger.exception(e)
	return res.text

def oa_issueasset(address, amount, to=None, metadata='', fees=None, txformat='raw'):
	'''
	Creates a transaction for issuing an asset.
	'''
	payload = { 'address': address,
				'amount': amount,
				'to': to,
				'metadata': metadata,
				'fees': fees,
				'txformat': txformat,
				'mode': 'unsigned'}
	res = send_request("issueasset", payload)

	#Return the unsigned transaction, raw
	return res

def oa_listunspent(address, minconf='1', maxconf='9999999'):
	'''
	Returns an array of unspent transaction outputs, augmented
	with the asset ID and quantity of each output.
	'''
	payload = { 'address': address,
				'minconf': minconf,
				'maxconf': maxconf}
	res = send_request("listunspent", payload)

	#Return a list with unspents in json
	return json.loads(res)

def oa_getbalance(address, minconf='1', maxconf='9999999'):
	'''
	Returns the balance in both bitcoin and colored coin
	assets for all of the addresses available in your
	Bitcoin Core wallet.
	'''
	payload = { 'address': address,
				'minconf': minconf,
				'maxconf': maxconf}
	res = send_request("getbalance", payload)

	#Return a list with balance info json
	return json.loads(res)

def oa_sendasset(address, asset, amount, to, fees=None, txformat='raw'):
	'''
	Creates a transaction for sending an asset from an
	address to another.
	'''
	payload = { 'address': address,
				'asset': asset,
				'amount': amount,
				'to': to,
				'fees': fees,
				'txformat': txformat,
				'mode': 'unsigned'}
	res = send_request("sendasset", payload)

	#Return the unsigned transaction, raw
	return res

def oa_distribute(address, forward_address, price, metadata='', fees=None, mode='unsigned', txformat='raw'):
	'''
	 Creates a batch of transactions used for creating
	 a token and distributing it to participants of a crowd sale.
	'''
	payload = { 'address': address,
				'forward_address': forward_address,
				'price': price,
				'metadata': metadata,
				'fees': fees,
				'txformat': txformat,
				'mode': mode}
	res = send_request("distribute", payload)

	#Return the unsigned transaction, raw
	return res

'''
print oa_issueasset('mjNYhMoHDbfdVuLy3mHwSfvVDock2gSqZJ', 10, to=None, metadata='USD')
print oa_listunspent('mjNYhMoHDbfdVuLy3mHwSfvVDock2gSqZJ')
print oa_getbalance('mjNYhMoHDbfdVuLy3mHwSfvVDock2gSqZJ')
print oa_sendasset('mjNYhMoHDbfdVuLy3mHwSfvVDock2gSqZJ',
					'AQKbkUkQjKLe7ru44MhgkU8UnnrDUSEqjn',
					4,
					'mrqANLJ5j48Zt4Vc3GZbMbyNsao5Sbmxvc',
					fees=10000)

print oa_distribute('mjNYhMoHDbfdVuLy3mHwSfvVDock2gSqZJ',
					'mrqANLJ5j48Zt4Vc3GZbMbyNsao5Sbmxvc',
					100,
					metadata='testing',
					fees=10000)
'''

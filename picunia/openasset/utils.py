from pycoin.encoding import a2b_base58, b2a_base58, double_sha256
from picunia.config.settings import Settings
import requests
import logging
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('openassets')

class EncodingError(Exception):
    pass

def as_openasset_address(address):
	'''
		Convert bitcoin address to openassets address

		address - base58 acsii encoded bitcoin address
		return - The openasset address
	'''
	def check_hash(data):
		data, the_hash = data[:-4], data[-4:]
		if double_sha256(data)[:4] == the_hash:
			return True
		else:
			return False

	data = None
	version = None
	namespace = None

	decoded_bytes = a2b_base58(address)
	data = decoded_bytes

	if not check_hash(decoded_bytes):
		raise EncodingError("hashed base58 has bad checksum %s" % address)

	if len(decoded_bytes) == 26:
		# The address has a namespace defined
		namespace, version, data = decoded_bytes[0:1], decoded_bytes[1:2], decoded_bytes[2:-4]
	elif len(decoded_bytes) == 25:
		# The namespace is undefined
		version, data = decoded_bytes[0:1], decoded_bytes[1:-4]
		namespace = "".join(map(chr, [19]))
	else:
		raise ValueError('Invalid length')

	full_payload = namespace + version + data

	checksum = double_sha256(full_payload)[0:4]

	return b2a_base58(full_payload + checksum)

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

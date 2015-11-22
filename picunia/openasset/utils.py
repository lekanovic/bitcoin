from pycoin.encoding import a2b_base58, b2a_base58, double_sha256, a2b_hashed_base58
from pycoin.encoding import hash160_sec_to_bitcoin_address, EncodingError, hash160
from pycoin.serialize.bitcoin_streamer import parse_bc_int
from pycoin.tx.script.tools import opcode_list
from picunia.config.settings import Settings
import requests
import logging
import json
import binascii
import io


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('openassets')


OPEN_ASSETS_TAG = 'OA\x01\x00'

def oa_parse_script(script):
	op_codes = opcode_list(script)

	if op_codes[0] != 'OP_RETURN':
		return '', []

	payload = binascii.unhexlify(op_codes[1])

	with io.BytesIO(payload) as stream:
		oap_marker = stream.read(4)

		if oap_marker != OPEN_ASSETS_TAG:
			return '', []

		output_count = parse_bc_int(stream)

		asset_quantities = []
		for i in range(0, output_count):
			asset_quantity = leb128_decode(stream)
			asset_quantities.append(asset_quantity)

		metadata_length = parse_bc_int(stream)
		metadata = stream.read(metadata_length)

	return metadata, asset_quantities

def leb128_decode(data):
	"""
	Decodes a LEB128-encoded unsigned integer.
	:param BufferedIOBase data: The buffer containing the LEB128-encoded integer to decode.
	:return: The decoded integer.
	:rtype: int
	"""
	result = 0
	shift = 0

	while True:
		character = data.read(1)
		if len(character) == 0:
			raise bitcoin.core.SerializationTruncationError('Invalid LEB128 integer')

		b = ord(character)
		result |= (b & 0x7f) << shift
		if b & 0x80 == 0:
			break
		shift += 7
	return result

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

def asset_id_to_base58(asset_id):
	'''
		Convert an asset id to an base58 string
		asset_id - binary format of RIPEMD160(SHA256(script))
		return - string base58
	'''
	return hash160_sec_to_bitcoin_address(asset_id, address_prefix=Settings.OA_VERSION_BYTE)

def base58_to_asset_id(base58_asset_id):
	'''
		Converts an base58 string to asset id
		base58_asset_id - string as base58
		return - asset_id as binary
	'''
	blob = a2b_hashed_base58(base58_asset_id)
	if len(blob) != 21:
		raise EncodingError("incorrect binary length (%d) for Bitcoin address %s" % (len(blob), bitcoin_address))

	if blob[:1] not in [Settings.OA_VERSION_BYTE]:
		raise EncodingError("incorrect first byte (%s) for Bitcoin address %s" % (blob[0], bitcoin_address))

	return blob[1:]

def hash_script(data):
	'''
		script_hash = RIPEMD160(SHA256(script))
	'''
	return hash160(data)

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

data_lookup = []
a = ('M`\x9e\xcb\x90\x7fL\x84\xc6\xa7`e7}\xe0\xaa\x99c\x00j','oPvW1Z9JJhYJXAEkGRVqCtkV31tM2vp7us')
data_lookup.append(a)
a = ('~\xba\x92\x87\xf9\x92\x95\xcc~\xb1\xd74\xce\xb5PKS\x16\x87e','oURSswE4u6ZTiZMDifmUX359EqkSE7rryk')
data_lookup.append(a)
a = ('\x7f\x13Y\x8d\xde\xf8\x1dq\x06\\\xc0\xff\xbbJ\xf1\x8e\xc0\xb9\x94\x88','oUTHEJMMCLi9nytxhcB8qz3aNtwk9XbMsq')
data_lookup.append(a)
a = ('\xd5\x02g;\xeb\xe09\x91\xc6]\xabY$Xa?\x14\xab\xce ','ocHf3L4raLX7zcnfP4V5HtFMRp65mjiYv3')
data_lookup.append(a)

for data in data_lookup:
	p = asset_id_to_base58(data[0])
	if p != data[1]:
		print 'Test FAILED!!!'
	p = base58_to_asset_id(p)
	if p != data[0]:
		print 'Test FAILED!!!'
'''

# Global settings file

class Settings():
	MONGODB_ADDRESS = 'localhost'
	MONGODB_PORT = '27017'
	INSIGHT_ADDRESS = 'http://localhost:3001'
	GAP_LIMIT = 5
	NETWORK = 'testnet'
	if NETWORK == 'testnet':
		NETCODE = 'XTN'
		KEY_PATHS = "44H/1H/"
	else:
		NETCODE = 'BTC'
		KEY_PATHS = "44H/0H/"
	RSCODEC_NSYM = 64
	USE_COMPRESSION = True
	BAUD_MINIMODEM = '3000'
	WIFS_DB = '/raid10/wifs.db'
	KEYS_DB = '/raid10/key.db'
	SEED_FILE = '/raid10/masterseed'
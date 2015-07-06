# Global settings file

class Settings():
	MONGODB_ADDRESS = 'localhost'
	MONGODB_PORT = '27017'
	INSIGHT_ADDRESS = 'http://localhost:3001'
	GAP_LIMIT = 5
	NETWORK = 'testnet'
	USE_RPI_EMULATOR = True
	RSCODEC_NSYM = 64
	USE_COMPRESSION = True
	BAUD_MINIMODEM = '3000'
	if NETWORK == 'testnet':
		NETCODE = 'XTN'
		KEY_PATHS = "44H/1H/"
	else:
		NETCODE = 'BTC'
		KEY_PATHS = "44H/0H/"
	if USE_RPI_EMULATOR:
		SIGN_TX_PATH = "picunia.security.sign_tx_client_simulator"
		WIFS_DB = 'wifs.db'
		KEYS_DB = 'key.db'
		SEED_FILE = 'masterseed'
	else:
		SIGN_TX_PATH = "picunia.security.sign_tx_client"
		WIFS_DB = '/raid10/wifs.db'
		KEYS_DB = '/raid10/key.db'
		SEED_FILE = '/raid10/masterseed'

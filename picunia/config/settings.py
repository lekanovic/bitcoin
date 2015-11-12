# Global settings file

class Settings():
	MONGODB_ADDRESS = 'localhost'
	MONGODB_PORT = '27017'
	INSIGHT_ADDRESS = 'http://localhost:3001'
	GAP_LIMIT = 5
	NETWORK = 'testnet'
	USE_RPI_EMULATOR = False
	RSCODEC_NSYM = 64
	USE_COMPRESSION = True
	BAUD_MINIMODEM = '3000'
	CONFIDENCE_MINIMODEM = '2.3'
	WIFS_DB = 'wifs.db'
	KEYS_DB = 'key.db'
	SEED_FILE = 'masterseed'
	OPENASSET_SERVER = 'http://localhost:8080/'

	if NETWORK == 'testnet':
		NETCODE = 'XTN'
		KEY_PATHS = "44H/1H/"
		OA_VERSION_BYTE = b'\x73'
	else:
		NETCODE = 'BTC'
		KEY_PATHS = "44H/0H/"
		OA_VERSION_BYTE = b'\x17'
	if USE_RPI_EMULATOR:
		SIGN_TX_PATH = "picunia.security.sign_tx_client_emulator"
	else:
		SIGN_TX_PATH = "picunia.security.sign_tx_client"
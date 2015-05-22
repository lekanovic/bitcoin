from pycoin.convention import btc_to_satoshi, satoshi_to_btc
from pycoin.key.BIP32Node import BIP32Node
from pycoin.services.insight import InsightService
from pycoin.tx.Tx import Tx
from pycoin.tx.TxOut import TxOut, standard_tx_out_script
from pycoin.tx.pay_to import address_for_pay_to_script, ScriptMultisig
from pycoin.tx.TxIn import TxIn
from pycoin.tx.tx_utils import distribute_from_split_pool
from pycoin.convention import tx_fee
from picunia.collection.proof import ProofOfExistence
from picunia.config.settings import Settings
from picunia.database.storage import Storage
from picunia.security.signer import get_public_key
from picunia.users.wallet import Wallet
from pycoin.serialize import h2b
from pycoin.tx.Tx import Tx
from pycoin.encoding import wif_to_secret_exponent
from pycoin.tx.pay_to import build_hash160_lookup
from picunia.security.signer import sign_tx
from mnemonic import Mnemonic
import shelve
import time
import logging
import datetime
import md5
import json
import urllib2


#pub = 'tpubDCVcrTzunZwudiYHyQ21fvpUpUTPh1vUm9Z633hGwAzacBYoNpjv4NJpwV3A8avhWpnyTpWhKypLwaEEfta5SvnhEraGtobeUyEaWsbBKSy'
pub = get_public_key(5)
w = Wallet(pub)

print "wallet index %s" % w.wallet_index
print "key index %d" % w.index
print "wallet ballance %d" % w.wallet_balance()
#print w.wallet_info()

tx, key_indexes = w.pay_to_address('myw6VGNg5uB52p1RWYc6BTbZzwrGo5tEgC',5000)

print key_indexes

sign_tx(5, key_indexes, tx.as_hex(include_unspents=True), netcode="XTN")

# -*- coding: utf-8 -*-


from pycoin.tx.tx_utils import create_tx, create_signed_tx
from biteasy import Biteasy
from pycoin.key.BIP32Node import BIP32Node
from pycoin.networks import full_network_name_for_netcode, network_name_for_netcode
from pycoin.serialize import b2h, h2b, h2b_rev
from pycoin.tx.Spendable import Spendable
from insight import send_tx
from mnemonic import Mnemonic
from account import Account
import binascii

import urllib
import urllib2

# Testnet - Where to get free bitcoins
# http://tpfaucet.appspot.com/

def print_key_info(key, subkey_path=None):
    output_dict = {}
    output_order = []

    def add_output(json_key, value=None, human_readable_key=None):
        if human_readable_key is None:
            human_readable_key = json_key.replace("_", " ")
        if value:
            output_dict[json_key.strip().lower()] = value
        output_order.append((json_key.lower(), human_readable_key))

    network_name = network_name_for_netcode(key._netcode)
    full_network_name = full_network_name_for_netcode(key._netcode)
    add_output("network", full_network_name)
    add_output("netcode", key._netcode)

    if hasattr(key, "wallet_key"):
        if subkey_path:
            add_output("subkey_path", subkey_path)

        add_output("wallet_key", key.wallet_key(as_private=key.is_private()))
        if key.is_private():
            add_output("public_version", key.wallet_key(as_private=False))

        child_number = key.child_index()
        if child_number >= 0x80000000:
            wc = child_number - 0x80000000
            child_index = "%dH (%d)" % (wc, child_number)
        else:
            child_index = "%d" % child_number
        add_output("tree_depth", "%d" % key.tree_depth())
        add_output("fingerprint", b2h(key.fingerprint()))
        add_output("parent_fingerprint", b2h(key.parent_fingerprint()), "parent f'print")
        add_output("child_index", child_index)
        add_output("chain_code", b2h(key.chain_code()))

        add_output("private_key", "yes" if key.is_private() else "no")

    secret_exponent = key.secret_exponent()
    if secret_exponent:
        add_output("secret_exponent", '%d' % secret_exponent)
        add_output("secret_exponent_hex", '%x' % secret_exponent, " hex")
        add_output("wif", key.wif(use_uncompressed=False))
        add_output("wif_uncompressed", key.wif(use_uncompressed=True), " uncompressed")

    public_pair = key.public_pair()

    if public_pair:
        add_output("public_pair_x", '%d' % public_pair[0])
        add_output("public_pair_y", '%d' % public_pair[1])
        add_output("public_pair_x_hex", '%x' % public_pair[0], " x as hex")
        add_output("public_pair_y_hex", '%x' % public_pair[1], " y as hex")
        add_output("y_parity", "odd" if (public_pair[1] & 1) else "even")

        add_output("key_pair_as_sec", b2h(key.sec(use_uncompressed=False)))
        add_output("key_pair_as_sec_uncompressed", b2h(key.sec(use_uncompressed=True)), " uncompressed")

    hash160_c = key.hash160(use_uncompressed=False)
    if hash160_c:
        add_output("hash160", b2h(hash160_c))
    hash160_u = key.hash160(use_uncompressed=True)
    if hash160_u:
        add_output("hash160_uncompressed", b2h(hash160_u), " uncompressed")

    if hash160_c:
        add_output("%s_address" % key._netcode,
                key.address(use_uncompressed=False), "%s address" % network_name)

    if hash160_u:
        add_output("%s_address_uncompressed" % key._netcode,
                key.address(use_uncompressed=True), " uncompressed")

    print('')
    max_length = max(len(v[1]) for v in output_order)
    for key, hr_key in output_order:
        space_padding = ' ' * (1 + max_length - len(hr_key))
        val = output_dict.get(key)
        if val is None:
            print(hr_key)
        else:
            if len(val) > 80:
                val = "%s\\\n%s%s" % (val[:66], ' ' * (5 + max_length), val[66:])
            print("%s%s: %s" % (hr_key, space_padding, val))


# Generate seed using BIP39
def BIP39_seed():
    mnemo = Mnemonic('english')
    words = mnemo.generate(512)

    if not mnemo.check(words):
        print "Something went wrong"
        exit(1)

    seed = Mnemonic.to_seed(words)

    return seed, words

def BIP39_static_seed():
    words = 'category fiscal fuel great review rather useful shop middle defense cube vacuum resource fiber special nurse chief category mask display bag echo concert click february fame tenant innocent affair usual hole soon bean adjust shoe voyage immune chest gaze chaos tip way glimpse sword tray craft blur seminar'
    seed = h2b('6ad72bdbc8b5c423cdc52be4b27352086b230879a0fd642bbbb19f5605941e3001eb70c6a53ea090f28d4b0e3033846b23ae2553c60a9618d7eb001c3aba2a30')    
    return seed, words

def create_new_account(name, lastname, email, passwd, key):
    user = Account(name, lastname, email, passwd, key)
    print user.to_json()

# This will generate private keys for the two accounts
def get_priv_key(account, index):
    p1 = "44H/0H/%dH/0/%d" % (account, index)
    return master.subkey_for_path(p1).wif(use_uncompressed=False)

seed, words = BIP39_static_seed()

print "Mnemonic:"
print words
print "Seed:"
print b2h(seed)

network = 'testnet'

if network == "testnet":
    netcode = 'XTN'
elif network == "mainnet":
    netcode == 'BTC'

master = BIP32Node.from_master_secret(seed, netcode)
#master = BIP32Node.from_master_secret(seed, netcode='BTC')
#print_key_info(master)

# Get account key path
account_keys = master.subkey_for_path("44H/0H/0H.pub")
#print_key_info(account_keys)

radde_account = Account('Radovan','Lekanovic','lekanovic@gmail.com', 'password1', account_keys, network)
#print_key_info(account_keys)

# Get account key path
account_keys = master.subkey_for_path("44H/0H/1H.pub")
print_key_info(account_keys)

maja_account = Account('Maja','Lekanovic','majasusa@hotmail.com', 'password2', account_keys, network)

print maja_account.to_json()
print radde_account.to_json()
#print master.subkey_for_path("44H/0H/0H/0/0").address()
radde_account.wallet_info()
maja_account.wallet_info()

# Recreate account_keys. Using the xpub address we can create
# all the account public keys.
#t = BIP32Node.from_text('xpub661MyMwAqRbcFoBYLHdXxaBao1pAZhopxEa2v8yJno9KLVz5aBWRhYr5FTMUibk2Zm16XbEpiodB6Lygsiuq9uFvJA3YUBpZ72fACHhNinv')
#print_key_info(t)

tx_unsigned = radde_account.pay_to_address(maja_account.get_bitcoin_address(),amount=12000000)

if tx_unsigned is None:
    print "Insufficient funds cannot perform transaction"
    exit(1)

wifs=[]
for i in range(0, int(radde_account.index)):
    priv_key = get_priv_key(int(radde_account.account_index), i)
    wifs.append(priv_key)
    print priv_key

print priv_key

radde_account.sign(tx_unsigned, wifs)

#maja_account.pay_to_address(radde_account.get_bitcoin_address(),amount=12000000)
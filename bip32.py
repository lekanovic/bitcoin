# -*- coding: utf-8 -*-


from pycoin.key.BIP32Node import BIP32Node
from pycoin.networks import full_network_name_for_netcode, network_name_for_netcode
from pycoin.serialize import b2h, h2b, h2b_rev
from mnemonic import Mnemonic
from account import Account
import binascii

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

seed, words = BIP39_static_seed()

print "Mnemonic:"
print words
print "Seed:"
print b2h(seed)

grand_master = BIP32Node.from_master_secret(seed, netcode='BTC')
'''
print_key_info(seed, master)

m0p = master.subkey(i=0, is_hardened=True)
pub_m0p = master.subkey(i=0, is_hardened=True, as_private=False)
print_key_info(seed, m0p)

#m0p1 = m0p.subkey(i=0)
pub_m0p1 = m0p.subkey(i=0, as_private=False)
print_key_info(seed, pub_m0p1)

account1 = Account('Radovan','Lekanovic','lekanovic@gmail.com',pub_m0p1.wallet_key(as_private=False))

#m0p2 = m0p.subkey(i=1)
pub_m0p2 = m0p.subkey(i=1, as_private=False)

account2 = Account('Maja','Lekanovic','majasusa@hotmail.com',pub_m0p2.wallet_key(as_private=False))

account2.generate_key()
account2.generate_key()
account2.generate_key()
account2.generate_key()

account1.wallet_info()
account2.wallet_info()
'''

# Get master key path
master = grand_master.subkey_for_path("")
# Get sub master key path
master_sub = master.subkey_for_path("0H")

# Account 1 path - Create sub tree. Use only public
a = master_sub.subkey_for_path("0H/0.pub")
account1 = Account('Radovan','Lekanovic','lekanovic@gmail.com', a)
account1.wallet_info()

# Account 2 path - Create sub tree. Use only public
a = master_sub.subkey_for_path("0H/1.pub")
print_key_info(a)

account2 = Account('Maja','Lekanovic','majasusa@hotmail.com', a)
account2.generate_key()
account2.generate_key()
account2.generate_key()
account2.generate_key()
account2.wallet_info()
print ""
for i in range(0,5):
    path = "0H/1/%d" % i
    print master_sub.subkey_for_path(path).address()

print ""
for i in range(0,5):
    path = "%d" % i
    print a.subkey_for_path(path).address()


t = BIP32Node.from_text('xpub6DGWioViQ3yCcDoCWJtAnNQou1mfCUkdysa3ez4kRUjwdKya7ugogEz18VNu24tpXNTzBZnAwwofwt9Er2631SFtM7FHXeLg8TAMK3N5n3j')
print_key_info(t)

'''
m0p1_1_2p = m0p1.subkey(i=2, is_hardened=True)
pub_m0p1_1_2p = m0p1.subkey(i=2, as_private=False, is_hardened=True)


output_dict, output_order = create_output(seed, master)
dump_output(output_dict, output_order)

output_dict, output_order = create_output(seed, subkey)
dump_output(output_dict, output_order)

output_dict, output_order = create_output(seed, ssubkey)
dump_output(output_dict, output_order)

for key in master.subkeys("1H"):
    print key
'''
# -*- coding: utf-8 -*-


from pycoin.key.BIP32Node import BIP32Node
from pycoin.networks import full_network_name_for_netcode, network_name_for_netcode
from pycoin.serialize import b2h
from randomseed import RandomSeed

def create_output(item, key, subkey_path=None):
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
    add_output("input", item)
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

    return output_dict, output_order


def dump_output(output_dict, output_order):
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


secretPass = RandomSeed.generate(512)
print "Seed: %x" % secretPass
secretPass = str(secretPass)

key = BIP32Node.from_master_secret(secretPass.encode("utf8"), netcode='BTC')

subkey = key.subkey_for_path("1H")

output_dict, output_order = create_output(secretPass, key)
dump_output(output_dict, output_order)

output_dict, output_order = create_output(secretPass, subkey)
dump_output(output_dict, output_order)

ssubkey = subkey.subkey_for_path("2H")

output_dict, output_order = create_output(secretPass, ssubkey)
dump_output(output_dict, output_order)

for key in key.subkeys("1H"):
    print key
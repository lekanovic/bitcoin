# -*- coding: utf-8 -*-

import pyBIP0038

# Documentation for BIP38
# https://github.com/bitcoin/bips/blob/master/bip-0038.mediawiki

# Library used
# https://github.com/7trXMk6Z/pyBIP0038

# Install module
# pip install pyBIP0038

privKey = '5KN7MzqK5wt2TP1fQCYyHBtDrXdJuXbUzm4A9rKAteGu3Qi5CVR'
pubAddress = '1Jq6MksXQVWzrznvZzxkV6oY57oWXD9TXB'
passPhrase = 'TestingOneTwoThree'


bip38key =  pyBIP0038.encrypt_privkey_from_password(passPhrase,privKey)

print bip38key

base58privkey = pyBIP0038.decrypt_priv_key(passPhrase, bip38key)

print base58privkey
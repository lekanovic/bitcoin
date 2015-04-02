from pycoin.key import Key
from pycoin.tx.pay_to import ScriptMultisig
from pycoin.tx import Tx, TxIn, TxOut, tx_utils
from pycoin.serialize import b2h, h2b, b2h_rev
from pycoin.key.BIP32Node import BIP32Node
from pycoin.tx.pay_to import address_for_pay_to_script, build_hash160_lookup, build_p2sh_lookup
from pycoin.services.insight import InsightService
from pycoin.tx.TxOut import TxOut, standard_tx_out_script
import time

netcode="XTN"
network="testnet"
key_path = "44H/1H/"

def BIP39_static_seed():
	words = 'category fiscal fuel great review rather useful shop middle defense cube vacuum resource fiber special nurse chief category mask display bag echo concert click february fame tenant innocent affair usual hole soon bean adjust shoe voyage immune chest gaze chaos tip way glimpse sword tray craft blur seminar'
	seed = h2b('6ad72bdbc8b5c423cdc52be4b27352086b230879a0fd642bbbb19f5605941e3001eb70c6a53ea090f28d4b0e3033846b23ae2553c60a9618d7eb001c3aba2a30')    
	return seed, words


def print_tx(tx):
	import io
	from pycoin.serialize import b2h
	s = io.BytesIO()
	tx.stream(s)
	tx_as_hex = b2h(s.getvalue())

	print tx_as_hex

def multisig_2_of_3(keys):
	N = 2
	M = 3

	tx_in = TxIn.coinbase_tx_in(script=b'')
	script = ScriptMultisig(n=N, sec_keys=[key.sec() for key in keys[:M]])

	print "Script %s" % repr(script)
	print "TxIn %s" % tx_in.bitcoin_address()
	script = script.script()

	address = address_for_pay_to_script(script, netcode)
	print "Multisig address: %s" % address

	tx_out = TxOut(1000000, script)
	tx1 = Tx(version=1, txs_in=[tx_in], txs_out=[tx_out])
	tx2 = tx_utils.create_tx(tx1.tx_outs_as_spendable(), [keys[-1].address()])

	hash160_lookup = build_hash160_lookup(key.secret_exponent() for key in keys)
	tx_signed = tx2.sign(hash160_lookup=hash160_lookup)

	for idx, tx_out in enumerate(tx2.txs_in):
		if not tx2.is_signature_ok(idx):
			print "Signature Error"

	print_tx(tx_signed)


addr = [
"mxnEPXCb6NbPGtg3iFdjUHnuQag9RhUDPv",
"mrvb5GzdQhtef7JTY8hy5Ut8Sis3ytLKWo",
"mmupy39RhRJuPJPGUFS5sCuSGoxfTb1RrU",
"n1P8PbhkhWkXTj1QvTjxaAMNtaHQV6Qg53",
"miU7fUgT97h63WaPX9LNpQs23QB1Dhd6mg",
"mr8pZigeiqZQgJDpWcMgfmKLT8xdZ3n9Kw",
"mmtzP315J3iF6F6qtTUhF9SDid9HvuL14Q",
"n2bjPFh5Y1HyGund9NKuqhnER3MrTkN6hq",
"myELxCfPvW77N6yjgbgp2XTCSCy15Fj4G1",
"mn9ALd5MGqLbWnswpwJy6MtkpiAKvQEC3n"
]


addr = ["mn9ALd5MGqLbWnswpwJy6MtkpiAKvQEC3n",
		"myELxCfPvW77N6yjgbgp2XTCSCy15Fj4G1",
		"mmtzP315J3iF6F6qtTUhF9SDid9HvuL14Q",
		"miU7fUgT97h63WaPX9LNpQs23QB1Dhd6mg",
		"mxnEPXCb6NbPGtg3iFdjUHnuQag9RhUDPv"]

insight = InsightService("http://localhost:3001")
tmp=0
while True:
	tip_hash = insight.get_blockchain_tip()
	cur = b2h_rev(tip_hash)
	if cur != tmp:
		blockheader, tx_hashes = insight.get_blockheader_with_transaction_hashes(tip_hash)
		print blockheader
		for t in tx_hashes:
			#print b2h_rev(t)
			tx = insight.get_tx(t)
			print "tx_in:"
			for t in tx.txs_in:
				print t.bitcoin_address(netcode)
			print "tx_out:"
			for t in tx.txs_out:
				print t.bitcoin_address(netcode)
			print repr(tx)
	tmp = cur
	time.sleep(5)

if insight.has_unconfirmed_balance(addr):
	print "Has unconfirmed"

spendables = insight.spendables_for_addresses(addr)

txs_in = [s.tx_in() for s in spendables]

amount=0
for s in spendables:
	print s.coin_value
	amount += s.coin_value

'''
txs_out = []
# Send bitcoin to the addess 'to_addr'
script = standard_tx_out_script("mqESpoK2bDzreSNEu2SmH9cQLc4EuYAZL8")
txs_out.append(TxOut(amount, script))

tx = Tx(version=1, txs_in=txs_in, txs_out=txs_out, lock_time=0)
tx.set_unspents(spendables)

hash160_lookup = build_hash160_lookup(key.secret_exponent() for key in keys)
tx_signed = tx.sign(hash160_lookup=hash160_lookup)

for idx, tx_out in enumerate(tx2.txs_in):
	if not tx.is_signature_ok(idx):
		print "Signature Error"

print_tx(tx_signed)





N = 2
M = 3

seed, words = BIP39_static_seed()
master = BIP32Node.from_master_secret(seed, netcode)
keys = []

#for k in range(0, M):
#	p1 = key_path + "%sH/0/%s" % (0, k)
#	keys.append( master.subkey_for_path(p1) )
#	print b2h(master.subkey_for_path(p1).sec(use_uncompressed=True))

keys = [Key(secret_exponent=i) for i in range(1, M+1)]

for k in keys:
	print b2h(k.sec(use_uncompressed=True))

multisig_2_of_3(keys)



http://suffix.be/blog/send-coins-multisig-address

./bitcoin-cli createmultisig 2 '["04d0a66a1e782a6cd9945e564f65df243cfb93766b7946639713031a5bd9e1747c5db18bec9934538037b0dbb384ff53d55e88c42d037ff3be773e5984a937e39c","048b309a6a4f76a101f221433510b5865c855cd7cca47d83bfdd05009a07a80d1fc6392bb7b8c20c394c3310b412665f2fd9aa021fd264e3ec4b71f6295f86c4f4","042ca6ee90df872966dc4f6ca69afaa6528954b4b450c89216df5fcae3b18bd53905f18ab8461e2d25d4df4c3e79bf54d75d6153449fd097972d3172214113c8a4"]'

{
    "address" : "2MujS7gd4pf4CDPQrBUrXLRvNrgvxTghLTU",
    "redeemScript" : "524104d0a66a1e782a6cd9945e564f65df243cfb93766b7946639713031a5bd9e1747c5db18bec9934538037b0dbb384ff53d55e88c42d037ff3be773e5984a937e39c41048b309a6a4f76a101f221433510b5865c855cd7cca47d83bfdd05009a07a80d1fc6392bb7b8c20c394c3310b412665f2fd9aa021fd264e3ec4b71f6295f86c4f441042ca6ee90df872966dc4f6ca69afaa6528954b4b450c89216df5fcae3b18bd53905f18ab8461e2d25d4df4c3e79bf54d75d6153449fd097972d3172214113c8a453ae"
}

'''
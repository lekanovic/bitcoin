from construct import Struct, UBInt32, String, CString, Container, GreedyRange
from picunia.config.settings import Settings

#http://construct.readthedocs.org/en/latest/basics.html

'''
  rtype
      TXN - Request signing a transactions
      KEY - Requesting a new public key
'''
package = Struct("package",
            String("rtype", 3),
            UBInt32("wallet_index"),
            String("netcode", 3),
            CString("tx"),
            GreedyRange(UBInt32("key_index")),
            )

def assemble_package(wallet_index, key_index, tx_unsigned, rtype="TXN"):
	c = Container(
          rtype=rtype,
          wallet_index=wallet_index,
				  key_index=key_index,
				  netcode=Settings.NETCODE,
				  tx=tx_unsigned)
	return package.build(c)

def assemble_package_tx_only(tx_signed):
  '''
    Use this when only the transaction is to be sent. Rest of the
    values is blanked out.

      tx_signed - signed transaction as HEX.
  '''
  return assemble_package(0, [0], tx_signed)

def disassemble_package(p):
	return package.parse(p)


'''
tx = "010000000190459cb906a38cbba81475eee39faae5d9553f672c25bafe154876fb4d6cbacf0000000000ffffffff02160b0000000000001976a9142276b5ca904e79efe9fc45dfd5fa562160182e9d88acf6210000000000001976a914ed82a5e1944f61b916f6f20ab3a27ff9cd4729e088ac000000001c540000000000001976a914b57f9dace2b6d5edc2b3109eb837cc85e4abd76788ac"
p = assemble_package(123, [1,2,3,4,5], tx, rtype="TXN")

p = disassemble_package(p)

print p.wallet_index
print p.key_index
print p.netcode
print p.tx


c = Container(account_nr=100,
              key_index=15,
              netcode="BTC",
              tx="010000000190459cb906a38cbba81475eee39faae5d9553f672c25bafe154876fb4d6cbacf0000000000ffffffff02160b0000000000001976a9142276b5ca904e79efe9fc45dfd5fa562160182e9d88acf6210000000000001976a914ed82a5e1944f61b916f6f20ab3a27ff9cd4729e088ac000000001c540000000000001976a914b57f9dace2b6d5edc2b3109eb837cc85e4abd76788ac")

print c
p = package.build(c)

print p

p = package.parse(p)

print p.account_nr
print p.key_index
print p.netcode
'''
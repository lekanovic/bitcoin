from construct import Struct, UBInt32, String, CString, Container


#http://construct.readthedocs.org/en/latest/basics.html

package = Struct("package",
            UBInt32("account_nr"),
            UBInt32("key_index"),
            String("netcode", 3),
            CString("tx")
            )

def assemble_package(account_nr, key_index, netcode, tx_unsigned):
	c = Container(account_nr=account_nr,
				  key_index=key_index,
				  netcode=netcode,
				  tx=tx_unsigned)
	return package.build(c)

def assemble_package_tx_only(tx_signed):
  '''
    Use this when only the transaction is to be sent. Rest of the
    values is blanked out.

      tx_signed - signed transaction as HEX.
  '''
  return assemble_package(0, 0, "XXX", tx_signed)

def disassemble_package(p):
	return package.parse(p)

'''
p = assemble_package(123, 1111, "BTC", "010000000190459cb906a38cbba81475eee39faae5d9553f672c25bafe154876fb4d6cbacf0000000000ffffffff02160b0000000000001976a9142276b5ca904e79efe9fc45dfd5fa562160182e9d88acf6210000000000001976a914ed82a5e1944f61b916f6f20ab3a27ff9cd4729e088ac000000001c540000000000001976a914b57f9dace2b6d5edc2b3109eb837cc85e4abd76788ac")

print p

p = disassemble_package(p)

print p.account_nr
print p.key_index
print p.netcode

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
# -*- coding: utf-8 -*-
# installed from here: https://github.com/jgarzik/python-bitcoinrpc
from bitcoinrpc.authproxy import AuthServiceProxy
import os

#print rpc_connection.getblockchaininfo()
#print rpc_connection.getblockcount()
#print rpc_connection.listlockunspent()
#print rpc_connection.getwalletinfo()
#print rpc_connection.getpeerinfo()
#print rpc_connection.getinfo()
#print(rpc_connection.getblock(best_block_hash))

def getLatestTransactions(rpc_connection):
    print "hi"
    transactions = rpc_connection.getrawmempool()
    for t in transactions:
        print t
        print rpc_connection.getrawtransaction(t)
        exit(1)


def main():
    conf_file = os.path.expanduser("~/.bitcoin/bitcoin.conf")

    with open(conf_file) as f:
        content = f.readlines()

    rpc_user=content[0].split("=")[1].rstrip("\n")
    rpc_password=content[1].split("=")[1].rstrip("\n")
    login_data="http://%s:%s@127.0.0.1:8332"%(rpc_user, rpc_password)
    rpc_connection = AuthServiceProxy(login_data)

    getLatestTransactions(rpc_connection)

if __name__ == "__main__":
    main()
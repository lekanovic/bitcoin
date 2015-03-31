# -*- coding: utf-8 -*-
# installed from here: https://github.com/jgarzik/python-bitcoinrpc
#from bitcoinrpc.authproxy import AuthServiceProxy
import bitcoin.rpc
from bitcoin.core import COIN
from bitcoin.wallet import CBitcoinAddress
import os
import getpass

# To see all functions run:
# bitcoin-cli help
myCoinbaseAddress = '19hVoLAQ7cUcKiZTAkfzESSjPo8APAgWz'
minfee = 0.0001

# Before we can send we need to unlock the wallet
# We must make sure to set min transaction of 0.0001
def sendto(rpc, addr,amount):
    print "Sending %.6f BTC to %s" % (amount, addr)

    addr = CBitcoinAddress(addr)

    # Set min fee
    rpc.settxfee(minfee)

    try:
        txid = rpc.sendtoaddress(addr, amount)
    except bitcoin.rpc.JSONRPCException as exp:
        if exp.error['code'] == -13:  # Wallet locked, need to unlock it
            pwd = getpass.getpass('Enter wallet passphrase')
            rpc.walletpassphrase(pwd, 5)
            # send again
            txid = rpc.sendtoaddress(addr, (amount-minfee))

    print "Successful transaction txid %s" % (txid)

def main():
    bitcoin.SelectParams('mainnet')
    conf_file = os.path.expanduser("~/.bitcoin/bitcoin.conf")

    with open(conf_file) as f:
        content = f.readlines()

    rpc_user=content[0].split("=")[1].rstrip("\n")
    rpc_password=content[1].split("=")[1].rstrip("\n")
    login_data="http://%s:%s@127.0.0.1:8332"%(rpc_user, rpc_password)

    rpc = bitcoin.rpc.Proxy(login_data)

    print rpc.getaccountaddress('')
    print "Balance: %.6f BTC %d Satoshi" % (float(rpc.getbalance())/COIN, float(rpc.getbalance()))
    balance = (float(rpc.getbalance())/COIN)
    if balance > 0:
        sendto(rpc,myCoinbaseAddress, balance)
    else:
        print "You have no money left to send"

    print rpc.gettransaction('7c0acfdecfbd850d8a6f30622b814d86bb63bc9ab7a5abeb4f4abbcb66b963e4')

    print rpc.getinfo()


    print rpc.validateaddress("1KtYokBB4dVvB25LFafPrjDvjyDKBmWySf")
    print rpc.getrawmempool()

if __name__ == "__main__":
    main()
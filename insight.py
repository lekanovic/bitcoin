import io
import json
import urllib2, urllib

try:
    from urllib2 import urlopen, HTTPError
except ImportError:
    from urllib.request import urlopen

from pycoin.convention import btc_to_satoshi
from pycoin.tx import Tx, Spendable
from pycoin.serialize import b2h_rev, h2b, h2b_rev


def spendables_for_address(bitcoin_address):
    """
    Return a list of Spendable objects for the
    given bitcoin address.
    """
    URL = "http://localhost:3001/api/addr/%s/utxo" % bitcoin_address
    print URL
    r = json.loads(urlopen(URL).read().decode("utf8"))
    spendables = []
    for u in r:
        coin_value = btc_to_satoshi(u['amount'])
        print coin_value
        script = h2b(u['scriptPubKey'])
        previous_hash = h2b(u['txid'])
        previous_index = u['vout']
        spendables.append(Spendable(coin_value, script, previous_hash, previous_index))
    return spendables

def send_tx(tx):
    args = urllib.urlencode({'rawtx': tx})
    URL = "http://localhost:3001/api/tx/send"
    print args

    req = urllib2.Request(URL, data=args)

    try:
        d = urllib2.urlopen(req)
    except HTTPError as ex:
        d = ex.read()
        print(ex)
    print d

'''
"http://localhost:3001/api/addr/n3Mx326UYHWNK4qrJj7DYoAWAsNp1fn7sg/utxo"

[
    {
        "address":"n3Mx326UYHWNK4qrJj7DYoAWAsNp1fn7sg",
        "txid":"42af2c5433cdca532cb89b28f27280ca069e94b133d6ea1a57807fab8cc4d4e2",
        "vout":0,
        "ts":1425618322,
        "scriptPubKey":"76a914ef9ecea520ca406b66c05081d52860a360a8ea2688ac",
        "amount":0.25,
        "confirmations":6,
        "confirmationsFromCache":true
    }
]
'''
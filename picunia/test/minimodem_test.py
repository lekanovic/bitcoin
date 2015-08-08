from picunia.security.sign_tx_client import sign_tx, start_service
import time
import sys

'''
This test will send a unsigned transactions to a signserver. The async result will
be in callback function.

* Prerequisite
Must have a RPI connected using AUX cables to this computer. And the RPI
must have the signserver running.
'''
has_been_called = False

def test_sign():
    def callback(tx_hex):
        global has_been_called
        print "+++++++++callback called+++++++++"
        print tx_hex
        has_been_called = True

    global has_been_called
    start_service()
    time.sleep(2)

    t = u"0100000001a3a2702d3c1ffe732ec5104ee215e06e2162815069c39a36943dc2c2e1dabd540000000000ffffffff0300000000000000002a6a28436875636b204e6f727269732066696e697368656420576f726c64206f662057617263726166742e10270000000000001976a9149f35ecd88caf647acec5445728bd667a8adb7f3488acf6726600000000001976a914d50a29953fe8fa5c8d18ed60c6400fc7c508b79a88ac0000000016c16600000000001976a914d17fd859759cce0aec42857a06e9adc70354cc5d88ac"

    sign_tx(3,[117], t, callback)

    while not has_been_called:
        time.sleep(1)
    has_been_called = False

for i in range(10):
    start_time = time.time()
    test_sign()
    print("The signing took %s seconds ---" % (time.time() - start_time))
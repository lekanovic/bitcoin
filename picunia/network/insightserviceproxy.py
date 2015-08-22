from picunia.config.settings import Settings
from pycoin.services.insight import InsightService
from urllib2 import HTTPError, URLError
import time
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class InsightServiceProxy():
    def __init__(self, url=Settings.INSIGHT_ADDRESS):
        self.url = url
        self.insight = InsightService(self.url)
        self.timeout = 10

    def is_address_used(self, key):
        status = None
        for i in range(self.timeout):
            try:
                status = self.insight.is_address_used(key)
                break
            except HTTPError as err:
                logger.info("No connection, retrying %s attempts %d" % (err.readline(), i))
                time.sleep(1)
                continue
            except URLError, e:
                print e.reason, self.url
        return status

    def spendables_for_addresses(self, keys):
        status = None
        for i in range(self.timeout):
            try:
                status = self.insight.spendables_for_addresses(keys)
                break
            except HTTPError as err:
                logger.info("No connection, retrying %s attempts %d" % (err.readline(), i))
                time.sleep(1)
                continue
            except URLError, e:
                print e.reason, self.url
        return status

    def spendables_for_address(self, s):
        status = None
        for i in range(self.timeout):
            try:
                status = self.insight.spendables_for_address(s)
                break
            except HTTPError as err:
                logger.info("No connection, retrying %s attempts %d" % (err.readline(), i))
                time.sleep(1)
                continue
            except URLError, e:
                print e.reason, self.url
        return status

    def has_unconfirmed_balance(self, keys):
        status = None
        for i in range(self.timeout):
            try:
                status = self.insight.has_unconfirmed_balance(keys)
                break
            except HTTPError as err:
                logger.info("No connection, retrying %s attempts %d" % (err.readline(), i))
                time.sleep(1)
                continue
            except URLError, e:
                print e.reason, self.url
        return status

    def get_tx_dict(self, unconf_tx):
        tx_dict = None
        for i in range(self.timeout):
            try:
                tx_dict = self.insight.get_tx_dict(unconf_tx)
                break
            except HTTPError as err:
                if err.code == 404:
                    raise
                logger.info("No connection, retrying %s attempts %d" % (err.readline(), i))
                time.sleep(1)
                continue
            except URLError, e:
                print e.reason, self.url
        return tx_dict

    def get_blockchain_tip(self):
        tip_hash = None
        for i in range(self.timeout):
            try:
                tip_hash = self.insight.get_blockchain_tip()
                break
            except HTTPError as err:
                logger.info("No connection, retrying %s attempts %d" % (err.readline(), i))
                time.sleep(1)
                continue
            except URLError, e:
                print e.reason, self.url
        return tip_hash

    def get_blockheader_with_transaction_hashes(self, tip_hash):
        blockheader = None
        tx_hashes = None
        for i in range(self.timeout):
            try:
                blockheader, tx_hashes = self.insight.get_blockheader_with_transaction_hashes(tip_hash)
                break
            except HTTPError as err:
                logger.info("No connection, retrying %s attempts %d" % (err.readline(), i))
                time.sleep(1)
                continue
            except URLError, e:
                print e.reason, self.url
        return blockheader, tx_hashes

    def get_tx(self, t1):
        tx = None
        for i in range(self.timeout):
            try:
                tx = self.insight.get_tx(t1)
                break
            except HTTPError as err:
                logger.info("No connection, retrying %s attempts %d" % (err.readline(), i))
                time.sleep(1)
                continue
            except URLError, e:
                print e.reason, self.url
        return tx
'''
import time
start = time.time()

#insight = InsightServiceProxy(url='http://192.168.0.43:3001')
insight = InsightServiceProxy()

#Test valid address
print insight.is_address_used('n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi')
print insight.spendables_for_addresses(['n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi'])
print insight.has_unconfirmed_balance(['n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi'])
tip = insight.get_blockchain_tip()
print insight.get_blockheader_with_transaction_hashes(tip)

#Test invalid address
print insight.is_address_used('xxxxxxxxxxxxxxx')
print insight.spendables_for_addresses(['xxxxxxxxxxxxxxx'])
print insight.has_unconfirmed_balance(['xxxxxxxxxxxxxxx'])
end = time.time()
logger.debug("It took %s", (end - start))
'''
from picunia.config.settings import Settings
from pycoin.services.insight import InsightService
from urllib2 import HTTPError
import time
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class InsightServiceProxy():
    def __init__(self):
        self.insight = InsightService(Settings.INSIGHT_ADDRESS)
        self.timeout = 10

    def is_address_used(self, key):
        status = None
        for i in range(self.timeout):
            try:
                status = self.insight.is_address_used(key)
            except HTTPError as err:
                logger.info("No connection, retrying %s" % err.readline())
                time.sleep(1)
                continue
        return status

    def spendables_for_addresses(self, keys):
        status = None
        for i in range(self.timeout):
            try:
                status = self.insight.spendables_for_addresses(keys)
            except HTTPError as err:
                logger.info("No connection, retrying %s" % err.readline())
                time.sleep(1)
                continue
        return status

    def spendables_for_address(self, s):
        status = None
        for i in range(self.timeout):
            try:
                status = self.insight.spendables_for_address(s)
            except HTTPError as err:
                logger.info("No connection, retrying %s" % err.readline())
                time.sleep(1)
                continue
        return status

    def has_unconfirmed_balance(self, keys):
        status = None
        for i in range(self.timeout):
            try:
                status = self.insight.has_unconfirmed_balance(keys)
            except HTTPError as err:
                logger.info("No connection, retrying %s" % err.readline())
                time.sleep(1)
                continue
        return status

'''
insight = InsightServiceProxy()

#Test valid address
print insight.is_address_used('n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi')
print insight.spendables_for_addresses(['n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi'])
print insight.has_unconfirmed_balance(['n2eMqTT929pb1RDNuqEnxdaLau1rxy3efi'])

#Test invalid address
print insight.is_address_used('xxxxxxxxxxxxxxx')
print insight.spendables_for_addresses(['xxxxxxxxxxxxxxx'])
print insight.has_unconfirmed_balance(['xxxxxxxxxxxxxxx'])
'''
import json
import regex

from decimal import Decimal

SOFA_REGEX = regex.compile("^SOFA::(?P<type>[A-Za-z]+):(?P<json>.+)$")

class SofaBase:

    def __init__(self, type):

        self._type = type
        self._data = {}

    def __setitem__(self, key, value):
        self._data[key] = value

    def __getitem__(self, key):
        return self._data[key]

    def render(self):

        return "SOFA::{type}:{json}".format(type=self._type, json=json.dumps(self._data))

    def __str__(self):

        return self.render()

class SofaPayment(SofaBase):

    def __init__(self, status=None, txHash=None, value=None, fromAddress=None, toAddress=None, networkId=None):

        super().__init__("Payment")

        self['status'] = status
        self['txHash'] = txHash
        self['value'] = value
        self['fromAddress'] = fromAddress
        self['toAddress'] = toAddress
        self['networkId'] = networkId

    def __setitem__(self, key, value):

        if key not in ('status', 'txHash', 'value', 'tx_hash', 'hash', 'fromAddress', 'toAddress', 'networkId'):
            raise KeyError(key)
        if key == 'tx_hash' or key == 'hash':
            key = 'txHash'
        if key == 'value' and isinstance(value, (int, float, Decimal)):
            value = hex(value)

        return super().__setitem__(key, value)

    @classmethod
    def from_transaction(cls, tx, networkId=None):
        """converts a dictionary with transaction data as returned by a
        ethereum node into a sofa payment message"""

        if isinstance(tx, dict):
            if 'error' in tx:
                status = "error"
            elif tx['blockNumber'] is None:
                status = "unconfirmed"
            else:
                status = "confirmed"
            return SofaPayment(value=tx['value'], txHash=tx['hash'], status=status,
                               fromAddress=tx['from'], toAddress=tx['to'],
                               networkId=networkId)
        else:
            raise TypeError("Unable to create SOFA::Payment from type '{}'".format(type(tx)))


VALID_SOFA_TYPES = ('message', 'command', 'init', 'initrequest', 'payment', 'paymentrequest')
IMPLEMENTED_SOFA_TYPES = {
    'payment': SofaPayment
}

def parse_sofa_message(message):

    match = SOFA_REGEX.match(message)
    if not match:
        raise SyntaxError("Invalid SOFA message")
    body = match.group('json')
    try:
        body = json.loads(body)
    except json.JSONDecodeError:
        raise SyntaxError("Invalid SOFA message: body is not valid json")

    type = match.group('type').lower()
    if type not in VALID_SOFA_TYPES:
        raise SyntaxError("Invalid SOFA type")

    if type not in IMPLEMENTED_SOFA_TYPES:
        raise NotImplementedError("SOFA type '{}' has not been implemented yet".format(match.group('type')))

    try:
        return IMPLEMENTED_SOFA_TYPES[type](**body)
    except TypeError:
        raise SyntaxError("Invalid SOFA message: body contains unexpected fields")

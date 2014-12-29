''' This class  will be initiated as a cache item which should support auto-grabage collection, expriration, toString etc '''
# TODO need to check the efficieny of this method later during src implementation

import time

class Drop(object):
    def __init__(self, **kwargs):
        # TODO: except the value of the cache item using the kwargs
        self.value = None
        self.expiry = 0
        self.hits = 0
        self.dependants = []

    def __str__(self):
        return self.value

    def set(self,value, expiry=0):
        self.value = value
        self.set_expiry(expiry)
        self.update_last_accessed()

    def get(self):
        if self.expiry == 0 or int(time.time()) < self.expiry:
            self.update_last_accessed()
            self.hits_plus_plus()
            return self.value
        else:
            # expired data
            self.value = None

    def set_expiry(self, expiry=0):
        if expiry.isdigit() and int(expiry) > 0:
            expiry_time = int(time.time()) + int(expiry)
            self.expiry = expiry_time

    def add_dependant(self, key):
        self.dependants.append(key)

    def is_expired(self):
        if self.expiry > 0 and int(time.time()) > self.expiry:
            return True
        else:
            return False

    def update_last_accessed(self):
        self.last_accessed = int(time.time())

    def hits_plus_plus(self):
        self.hits += 1




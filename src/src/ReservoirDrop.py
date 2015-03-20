''' This class  will be initiated as a cache item which should support auto-grabage collection, expriration, toString etc '''
# TODO need to check the efficieny of this method later during src implementation

import time
import json

class Drop(object):
    def __init__(self, **kwargs):
        # TODO: except the value of the cache item using the kwargs
        self.value = None
        self.parent_key = None
        self.expiry = 0
        self.hits = 0
        self.key = kwargs.get('key', None)
        self.dependants = []
        self.created = time.time()
        self.type = None
        self.buckets = []

    def __str__(self):
        return self.value

    def set(self,value, expiry=0):
        if self.type in ['tpl']:
            return False
        self.value = value
        self.set_expiry(expiry)
        self.update_last_accessed()
        return True

    def get(self):
        if self.expiry == 0 or int(time.time()) < self.expiry:
            self.update_last_accessed()
            self.hits_plus_plus()
            return self.value
        else:
            # expired data
            self.value = None

    def set_expiry(self, expiry=0):
        if type(expiry) != int:
            expiry = int(expiry) if expiry.isdigit() else 0

        if expiry == 0:
            self.expiry = 0
            return

        # if the time is in epoc and greater than epoc then calculate else use number of seconds
        if expiry > time.time():
            expiry_time = expiry
        else:
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

    def increment(self):
        if type(self.value) != int:
            self.value = int(self.value) if self.value.isdigit() else 0
        self.value += 1
        return True
    
    def decrement(self):
        if type(self.value) != int:
            self.value = int(self.value) if self.value.isdigit() else 0
        self.value -= 1
        return True

    def get_active_time(self):
        return time.time() - self.created

    def set_type(self, t):
        self.type = t

    def get_type(self):
        return self.type

    def get_replay_log(self):
        # format <expiry>, <dependants>, <key>, <value>
        log_dict = {
            "key": self.key,
            "data": self.value,
            "expiry": self.expiry,
            "parent_key": self.parent_key,
            "type": self.type,
            "buckets": self.buckets,
            "dependants": self.dependants
        }
        log_string = json.dumps(log_dict)

        return log_string

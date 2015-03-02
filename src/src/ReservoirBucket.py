''' This class is will ONLY contain references to the Drops not the clone of it '''
class Bucket(object):
    def __init__(self, name, **kwargs):
        self.name = name
        self.bucket = []

    def __str__(self):
        return self.name

    def add(self, key):
        self.bucket.append(key)
        
    def delete(self, key):
        if key in self.bucket:
            self.bucket.remove(key)

    def check(self, key):
        return True if key in self.bucket else False

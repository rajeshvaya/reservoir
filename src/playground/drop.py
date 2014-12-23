''' This class  will be initiated as a cache item which should support auto-grabage collection, expriration, toString etc '''
# TODO need to check the efficieny of this method later during src implementation

class Drop(object):
	def __init__(self, **kwargs):
		# TODO: except the value of the cache item using the kwargs
		self.value = None
		self.expiry = 0
		pass

	def __str__(self):
		return self.value

	def set(self,value, expiry=0):
		self.value = value
		pass

	def get(self):
		return self.value





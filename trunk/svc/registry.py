class AbstractRegistry(object):
	def __init__(self):
		super(AbstractRegistry, self).__init__()
		self._children = set()
		self._setParent(None)
		self.setName(None)
	
	def getPath(self):
		ret = [self]
		while True:
			parent = ret[0].getParent()
			if parent is None:
				break
			else:
				ret.insert(0, parent)
		return ret
	
	def getParent(self):
		return self.__dict__['_parent']

	def _setParent(self, parent):
		self.__dict__['_parent'] = parent
	
	def getName(self):
		return self._name

	def setName(self, name):
		parent = self.getParent()
		if parent is not None:
			raise ValueError("setName() requires that parent == None")
		self._name = name
	
	def getFullName(self):
		def mapper(obj):
			name = obj.getName()
			if name is None: return '<anon>'
			else:            return name
		return '.'.join(mapper(obj) for obj in self.getPath())
	
	def addChild(self, child):
		my_path = self.getPath()
		if child in my_path:
			raise ValueError("You cannot create cycles, child %r is parent of %r" % (child, self))
		old_parent = child.getParent()
		if old_parent is not None:
			old_parent.delChild(child)
		child._setParent(self)
		self._children.add(child)
	
	def delChild(self, child):
		child._setParent(None)
		self._children.remove(child)
	
	def getChildren(self):
		return self._children
	
	def __setattr__(self, name, obj):
		if hasattr(obj, '_setParent'):
			if hasattr(obj, 'setName'):
				obj.setName(name)
			self.addChild(obj)
		self.__dict__[name] = obj
	
	def __delattr__(self, name):
		obj = getattr(self, name)
		if obj in self.getChildren():
			self.delChild(obj)
			if hasattr(obj, 'setName'):
				obj.setName(None)
		del self.__dict__[name]

	def _createMethod(self, name, pre_func=None, post_func=None):
		def method(*args, **kwargs):
			objects = iter(self)
			if pre_func is not None:
				objects = pre_func(objects)
			retvals = (obj(*args, **kwargs) for obj in objects)
			if post_func is not None:
				return post_func(retvals)
			else:
				return list(retvals)
		method.__name__ = name
		setattr(self, name, method)
	
	def createSequent(self, name, reduce=None, obs_name=None):
		if obs_name is None:
			obs_name = name
		def pre_func(objects):
			return (getattr(o, obs_name) for o in objects)
		self._createMethod(name, pre_func=pre_func, post_func=reduce)
	
	def createDirectSequent(self, name, reduce=None):
		self._createMethod(name, post_func=reduce)
	
	def createQuery(self, name, obs_name=None):
		if obs_name is None:
			obs_name = name
		def pre_func(objects):
			return (getattr(o, obs_name) for o in objects)
		def post_func(retvals):
			for o in retvals:
				if o is not None:
					return o
		self._createMethod(name, pre_func=pre_func, post_func=post_func)

	def createDirectQuery(self, name):
		def post_func(retvals):
			for o in retvals:
				if o is not None:
					return o
		self._createMethod(name, post_func=post_func)

	def createChain(self, name, obs_name=None):
		if obs_name is None:
			obs_name = name
		def method(args):
			for o in self:
				func = getattr(o, obs_name)
				args = func(args)
			return args
		method.__name__ = name
		setattr(self, name, method)
			
	def createDirectChain(self, name):
		def method(args):
			for o in self:
				args = o(args)
			return args
		method.__name__ = name
		setattr(self, name, method)

	
class Registry(AbstractRegistry, list):
	def __repr__(self):
		return "<registry %s: [%s]>" % (self.getFullName(), ', '.join(repr(obj) for obj in self))

	def __eq__(self, other):
		if isinstance(other, Registry):
			return self is other
		else:
			return super(Registry, self).__eq__(other)

	def __hash__(self):
		return id(self)


def register(registry):
	def decorator(func):
		registry.append(func)
		return func
	return decorator


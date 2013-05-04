class HTTPHandlerError(Exception):
	"""
	This exception is raised when there has occurred an error related to
	the HTTP handler. It is a subclass of Exception.
	"""
	def __init__(self, httpurl=None, httpcode=None, httpmsg=None, httpheaders=None, httpdata=None):
		Exception.__init__(self)
		self.url = ''
		self.code = 600
		self.message = ''
		self.headers = {}
		self.data = ''
		self.url = httpurl
		self.code = httpcode
		self.message = httpmsg
		self.headers = httpheaders
		self.data = httpdata

	def __repr__(self):
		return '<HTTPHandlerError %d, %s>' % (self.code, self.message)

	def __str__(self):
		return 'HTTPHandlerError %d: %s' % (self.code, self.message)

	def __unicode__(self):
		return 'HTTPHandlerError %d: %s' % (self.code, self.message)
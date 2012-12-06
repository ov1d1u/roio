import urllib, urllib2, json
from datetime import datetime

from settings import ROIO_SERVER

class NetworkResponse:	# metaclass
	status = 'ok'
	duration = 0.0
	data = {}

class ROIONetwork:
	def __init__(self):
		self.url = ROIO_SERVER

	def _do_request(self, values={}):
		nr = NetworkResponse()
		netdata = ''
		try:
			start = datetime.now()

			data = urllib.urlencode(values)
			req = urllib2.Request(self.url, data)
			response = urllib2.urlopen(req)
			
			stop = datetime.now()
			
			netdata = response.read()
			lag = stop - start
			nr.duration = (lag.seconds * 1000000 + lag.microseconds) / 1000
			nr.data = json.loads(netdata)
			nr.status = nr.data.get('status')
		except Exception, e:
			print Exception, e
			nr.status = 'fail'
			nr.data = {'exception', e}
		return nr
		
	def send_hello(self):
		return self._do_request({'action':'hello'})

	def new_user(self, data):
		return self._do_request(dict({'action':'register'}.items() + data.items()))

	def sign_in(self, data):
		return self._do_request(dict({'action':'signin'}.items() + data.items()))

	def recover(self, data):
		return self._do_request(dict({'action':'recover'}.items() + data.items()))

	def categories(self):
		return self._do_request({'action':'categories'})
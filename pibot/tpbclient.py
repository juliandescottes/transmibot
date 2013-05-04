import json, time, logging
from urllib import quote
from pibot.http.error import HTTPHandlerError
from pibot.http.httphandler import DefaultHTTPHandler

LOGGER = logging.getLogger('tpbclient')
LOGGER.setLevel(logging.INFO)

BASE_URL ='http://apify.ifc0nfig.com/tpb/search/'

class TPBClient(object):
	def __init__(self):
		self.http_handler = DefaultHTTPHandler()

	def request(self, keywords):
		LOGGER.info("TPBClient : " + keywords)
		start = time.time()
		url = BASE_URL + quote(keywords) + "?$top=5"

		LOGGER.info("TPBClient URL : " + url)
		http_data = self._http_request(url)
		elapsed = time.time() - start
		LOGGER.info('http request took %.3f s' % (elapsed))
		LOGGER.info(http_data)
		return json.loads(http_data)

	def _http_request(self, url, timeout=None):  
		result = '{}'

		while True:
			try:
				result = self.http_handler.get(url)
				break
			except HTTPHandlerError as error:
				raise
		return result

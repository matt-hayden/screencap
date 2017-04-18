
import requests

try:
	from . import debug, info, warning, error, fatal
except:
	debug = info = warning = error = fatal = print

def myindex(url):
	r = requests.get(url)
	if r.status_code == requests.codes.ok:
		c = url.content
		for line in c.split('\000'):
			yield line


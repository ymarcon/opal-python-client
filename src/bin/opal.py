#! /usr/bin/env python
#
# See http://www.angryobjects.com/2011/10/15/http-with-python-pycurl-by-example/
# Curl options http://curl.haxx.se/libcurl/c/curl_easy_setopt.html
#
# Usage: 
#

import sys
import pycurl
import base64
import getopt
import json

class Reader:
  def __init__(self):
    self.contents = ''

  def body_callback(self, buf):
    self.contents = self.contents + buf

opal = '';
user = 'administrator'
password = ''
ws = ''
verbose = False
jsonout = False

try:
  opts, args = getopt.getopt(sys.argv[1:], "oupw:vj", ["opal=","user=","password=","ws=", "json","verbose"])
except getopt.GetoptError, err:
  # print help information and exit:
  print str(err) # will print something like "option -a not recognized"
  sys.exit(2)
for o, a in opts:
  if o in ("-v", "--verbose"):
    verbose = True
  elif o in ("-j", "--json"):
    jsonout = True
  elif o in ("-o", "--opal"):
    opal = a
  elif o in ("-u", "--user"):
    user = a
  elif o in ("-p", "--password"):
    password = a
  elif o in ("-w", "--ws"):
    ws = a
  else:
    assert False, "unhandled option"

url = opal + '/ws' + ws
credentials = base64.b64encode(user + ':' + password)

reader = Reader()
c = pycurl.Curl()
c.setopt(c.URL, url)
c.setopt(c.HTTPHEADER, ['Accept: application/json', 'Authorization: X-Opal-Auth ' + credentials])
c.setopt(c.SSL_VERIFYPEER, 0)
c.setopt(c.CONNECTTIMEOUT, 5)
c.setopt(c.TIMEOUT, 8)
c.setopt(c.FAILONERROR, True)
c.setopt(c.VERBOSE, verbose)
c.setopt(c.WRITEFUNCTION, reader.body_callback)

try:
  c.perform()
except pycurl.error, error:
  errno, errstr = error
  print >> sys.stderr, 'An error occurred: ', errstr
  sys.exit(2)
else:
  if jsonout:
    res = json.loads(reader.contents)
    print json.dumps(res, sort_keys=True, indent=2)
  else:
    print reader.contents
finally:
  c.close()



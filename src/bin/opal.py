#! /usr/bin/env python
#
# Based on PyCurl http://pycurl.sourceforge.net/
# See also http://www.angryobjects.com/2011/10/15/http-with-python-pycurl-by-example/
# Curl options http://curl.haxx.se/libcurl/c/curl_easy_setopt.html
#
# Usage: 
#   opal.py --help
#
# Examples of Opal web services:
#
#  /datasources
#    All datasources
#
#  /datasource/xxx
#    A datasource
#
#  /datasource/xxx/tables
#    All tables of a datasource
#
#  /datasource/xxx/table/yyy
#    A table
#
#  /datasource/xxx/table/yyy/variables
#    All variables of a table
#
#  /datasource/xxx/table/yyy/variable/vvv
#    A variable
#
#  /datasource/xxx/table/yyy/entities
#    All entities of a table
#
#  /datasource/xxx/table/yyy/entities?script=sss
#    All entities of a table matching a script (see http://wiki.obiba.org/display/OPALDOC/Magma+Javascript+API)
#
#  /datasource/xxx/table/yyy/valueSet/zzz
#    All values of a entity in a table
#
#  /datasource/xxx/table/yyy/valueSet/zzz/variable/vvv
#    A variable value of a entity
#
#  /datasource/xxx/table/yyy/valueSet/zzz/variable/vvv/value
#    Raw variable value of a entity
#
#  /datasource/xxx/table/yyy/valueSet/zzz/variable/vvv/value?pos=1
#    Raw repeatable variable value of a entity at given position (start at 0)
#

import sys
import pycurl
import base64
import json
import argparse
import cStringIO

#
# Parse arguments
#
parser = argparse.ArgumentParser(description='REST call to Opal.')
parser.add_argument('--opal', '-o', required=True, help='Opal server base url')
parser.add_argument('--user', '-u', required=False, help='User name')
parser.add_argument('--password', '-p', required=False, help='User password')
parser.add_argument('--cert', '-c', required=False, help='Certificate (PEM)')
parser.add_argument('--key', '-k', required=False, help='Key (PEM)')
parser.add_argument('--method', '-m', required=False, help='HTTP method (default is GET, others are POST, PUT, DELETE, OPTIONS)')
parser.add_argument('--accept', '-a', required=False, help='Accept header (default is application/json)')
parser.add_argument('--content-type', '-ct', required=False, help='Content-Type header (default is application/json in case of POST or PUT requests)')
parser.add_argument('--ws', '-w', required=True, help='Web service path, for instance: /datasource/xxx/table/yyy/variable/vvv')
parser.add_argument('--out', '-f', required=False, help='Path to the file where response is to be written. Otherwise response is printed on the stdout.')
parser.add_argument('--json', '-j', action='store_true', help='Pretty JSON formatting of the response')
parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
args = parser.parse_args()

#
# Opal request
#
class OpalRequest:
  def __init__(self):
    self.headers = { 'Accept': 'application/json' }

  def init_connection(self):
    self.curl = pycurl.Curl()
    self.curl.setopt(self.curl.SSL_VERIFYPEER, 0)
    self.curl.setopt(self.curl.CONNECTTIMEOUT, 5)
    #self.curl.setopt(self.curl.TIMEOUT, 8)
    self.curl.setopt(self.curl.FAILONERROR, True)
    hlist = []
    for h in self.headers:
      hlist.append(h + ": " + self.headers[h])
    self.curl.setopt(self.curl.HTTPHEADER, hlist)
    self.curl.setopt(self.curl.VERBOSE, self.verbose)

  def authenticate(self, user, password):
    credentials = base64.b64encode(user + ':' + password)
    self.headers['Authorization'] = 'X-Opal-Auth ' + credentials

  def keys(self, private, certificate):
    self.private_key = private
    #c.setopt(c.SSLCERT, args.cert)
    self.certificate = certificate
    #c.setopt(c.SSLKEY, args.key)

  def accept(self, value):
    self.headers['Accept'] = value

  def content_type(self, value):
    self.headers['Content-Type'] = value

  def verbose(self, verbose):
    self.verbose = verbose

  def method(self, method):
    if not method:
      self.method = 'GET'
    elif m in ['GET','DELETE','PUT','POST','OPTIONS']:
      self.method = method
    else:
      raise Exception('Not a valid method: ' + method)
    if self.method in ['PUT','POST']:
      self.headers['Content-Type'] = 'application/json'

  def send(self, method, url):
    self.init_connection()

    self.method(method)
    self.url = url
    self.curl.setopt(self.curl.CUSTOMREQUEST, self.method)
    self.curl.setopt(self.curl.URL, self.url)

    self.buf = cStringIO.StringIO()
    self.curl.setopt(self.curl.WRITEFUNCTION, self.buf.write)
    self.curl.perform()
    self.response_body = self.buf.getvalue()
    self.buf.close()
    self.curl.close()

    return self.response_body


#
# Build and send request
#
url = args.opal + '/ws' + args.ws
opal = OpalRequest()
if args.user:
  opal.authenticate(args.user, args.password)
else:
  opal.keys(args.key, args.cert)
if args.accept:
  opal.accept(args.accept)
if args.content_type:
  opal.content_type(args.content)
opal.verbose(args.verbose)

try:
  # format response
  res = opal.send(args.method,url)
  if args.json:
    res = json.dumps(json.loads(res), sort_keys=True, indent=2)

  # output to file
  if args.out:
    f = open(args.out, 'w')
    f.write(res)
    f.close()
  else:
    print res
except Exception,e :
    print e
    sys.exit(2)
except pycurl.error, error:
  errno, errstr = error
  print >> sys.stderr, 'An error occurred: ', errstr
  sys.exit(2)

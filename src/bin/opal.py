#! /usr/bin/env python
#
# Based on PyCurl http://pycurl.sourceforge.net/
# See also http://www.angryobjects.com/2011/10/15/http-with-python-pycurl-by-example/
# Curl options http://curl.haxx.se/libcurl/c/curl_easy_setopt.html
#
# Usage: 
#   opal.py --help
#
# Examples of Opal web services on which GET can be performed:
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
import cStringIO
import os.path

#
# Opal client
#
class OpalClient:
  def __init__(self, base_url):
    self.base_url = base_url
    self.curl_options = {}
    self.headers = {}

  def credentials(self, user, password):
    return self.header('Authorization', 'X-Opal-Auth ' + base64.b64encode(user + ':' + password))

  def keys(self, cert_file, key_file, key_pwd=None, ca_certs=None):
    self.curl_option(pycurl.SSLCERT, cert_file)
    self.curl_option(pycurl.SSLKEY, key_file)
    if key_pwd:
      self.curl_option(pycurl.KEYPASSWD, key_pwd)
    if ca_certs:
      self.curl_option(pycurl.CAINFO, ca_certs)
    self.headers.pop('Authorization',None)
    return self

  def verify_peer(self, verify):
    return self.curl_option(pycurl.SSL_VERIFYPEER, verify)

  def verify_host(self, verify):
    return self.curl_option(pycurl.SSL_VERIFYHOST, verify)

  def ssl_version(self, version):
    return self.curl_option(pycurl.SSLVERSION, version)

  def curl_option(self, opt, value):
    self.curl_options[opt] = value
    return self

  def header(self, key, value):
    self.headers[key] = value
    return self

  def request(self):
    return OpalRequest(self)

#
# Opal request
#
class OpalRequest:
  def __init__(self, opal_client):
    self.client = opal_client
    self.curl_options = {}
    self.headers = { 'Accept': 'application/json' }
    self._verbose = False

  def curl_option(self, opt, value):
    self.curl_options[opt] = value
    return self

  def timeout(self, value):
    return self.curl_option(pycurl.TIMEOUT, value)

  def connection_timeout(self, value):
    return self.curl_option(pycurl.CONNECTTIMEOUT, value)

  def verbose(self):
    self._verbose = True
    return self.curl_option(pycurl.VERBOSE, True)

  def fail_on_error(self):
    return self.curl_option(pycurl.FAILONERROR, True)

  def header(self, key, value):
    self.headers[key] = value
    return self

  def accept(self, value):
    return self.header('Accept', value)

  def content_type(self, value):
    return self.header('Content-Type', value)

  def accept_json(self):
    return self.accept('application/json')

  def content_type_json(self):
    return self.content_type('application/json')

  def method(self, method):
    if not method:
      self.method = 'GET'
    elif method in ['GET','DELETE','PUT','POST','OPTIONS']:
      self.method = method
    else:
      raise Exception('Not a valid method: ' + method)
    return self

  def get(self):
    return self.method('GET')

  def put(self):
    return self.method('PUT')

  def post(self):
    return self.method('POST')

  def delete(self):
    return self.method('DELETE')

  def options(self):
    return self.method('OPTIONS')

  def __build_request(self):
    curl = pycurl.Curl()
    # curl options
    for o in self.client.curl_options:
      curl.setopt(o, self.client.curl_options[o])
    for o in self.curl_options:
      curl.setopt(o, self.curl_options[o])
    # headers
    hlist = []
    for h in self.client.headers:
      hlist.append(h + ": " + self.client.headers[h])
    for h in self.headers:
      hlist.append(h + ": " + self.headers[h])
    curl.setopt(pycurl.HTTPHEADER, hlist)
    if self.method:
      curl.setopt(pycurl.CUSTOMREQUEST, self.method)
    if self.resource:
      curl.setopt(pycurl.URL, self.client.base_url + '/ws' + self.resource)
    else:
      raise Exception('Resource is missing')
    return curl

  def resource(self, ws):
    self.resource = ws
    return self

  def content(self, content):
    if self._verbose:
      print '* Content:'
      print content
    self.curl_option(pycurl.POST,1)
    self.curl_option(pycurl.POSTFIELDSIZE,len(content))
    reader = cStringIO.StringIO(content)
    self.curl_option(pycurl.READFUNCTION, reader.read)
    return self

  def content_file(self, filename):
    if self._verbose:
      print '* File Content:'
      print filename
    self.curl_option(pycurl.POST,1)
    self.curl_option(pycurl.POSTFIELDSIZE,os.path.getsize(filename))
    reader = open(filename, 'rb')
    self.curl_option(pycurl.READFUNCTION, reader.read)
    return self

  def send(self):
    curl = self.__build_request()
    hbuf = HeaderStorage()
    cbuf = Storage()
    curl.setopt(curl.WRITEFUNCTION, cbuf.store)
    curl.setopt(curl.HEADERFUNCTION, hbuf.store)
    curl.perform()
    response = OpalResponse(curl.getinfo(pycurl.HTTP_CODE),hbuf.headers,cbuf.contents)
    curl.close()
    
    return response

#
# Content storage
#
class Storage:
  def __init__(self):
    self.contents = ''
    self.line = 0

  def store(self, buf):
    self.line = self.line + 1
    self.contents = self.contents + buf

  def __str__(self):
    return self.contents

#
# Header storage
#
class HeaderStorage(Storage):
  def __init__(self):
    Storage.__init__(self)
    self.headers = {}

  def store(self, buf):
    Storage.store(self, buf)
    header = buf.partition(':')
    if header[1]:
      value = header[2].rstrip().strip()
      if header[0] in self.headers:
        current_value = self.headers[header[0]]
        if isinstance(current_value, str):
          self.headers[header[0]] = [current_value]
        self.headers[header[0]].append(value)
      else:
        self.headers[header[0]] = value

#
# Opal Response
#
class OpalResponse:
  def __init__(self, code, headers, content):
    self.code = code
    self.headers = headers
    self.content = content

  def pretty_json(self):
    return json.dumps(json.loads(self.content), sort_keys=True, indent=2)

  def __str__(self):
    return self.content

#
# Main
#
if __name__ == "__main__":
  import argparse

  # Parse arguments
  parser = argparse.ArgumentParser(description='REST call to Opal. Output the result on the stdout.')
  parser.add_argument('--opal', '-o', required=True, help='Opal server base url')
  parser.add_argument('--user', '-u', required=True, help='User name')
  parser.add_argument('--password', '-p', required=True, help='User password')
  parser.add_argument('--ws','-w', required=True, help='Web service path, for instance: /datasource/xxx/table/yyy/variable/vvv')
  #parser.add_argument('--cert', '-c', required=False, help='Certificate (PEM)')
  #parser.add_argument('--key', '-k', required=False, help='Key (PEM)')
  parser.add_argument('--method', '-m', required=False, help='HTTP method (default is GET, others are POST, PUT, DELETE, OPTIONS)')
  parser.add_argument('--accept', '-a', required=False, help='Accept header (default is application/json)')
  parser.add_argument('--content-type', '-ct', required=False, help='Content-Type header (default is application/json in case of POST or PUT requests)')
  parser.add_argument('--stdin', '-i', action='store_true', help='Read the request content from the stdin.')
  parser.add_argument('--json', '-j', action='store_true', help='Pretty JSON formatting of the response')
  parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
  args = parser.parse_args()

  # Build and send request
  opal = OpalClient(args.opal)

  if args.opal.startswith('https:'):
    opal.verify_peer(0)
    #opal.verify_host(0)
    #opal.ssl_version(3)

  if args.user:
    opal.credentials(args.user, args.password)
  else:
    opal.keys(args.key, args.cert)

  request = opal.request()
  request.fail_on_error()
  if args.accept:
    request.accept(args.accept)
  else:
    request.accept_json()
  if args.content_type:
    request.content_type(args.content)
  else:
    request.content_type_json()
  if args.verbose:
    request.verbose()

  try:
    # send request
    request.method(args.method).resource(args.ws);
    if args.stdin:
      request.content(sys.stdin.read())
    response = request.send()

    # format response    
    res = response.content
    if args.json:
      res = response.pretty_json()
    elif args.method in ['OPTIONS']:
      res = response.headers['Allow']

    # output to stdout
    print res
  except Exception,e :
    print e
    sys.exit(2)
  except pycurl.error, error:
    errno, errstr = error
    print >> sys.stderr, 'An error occurred: ', errstr
    sys.exit(2)

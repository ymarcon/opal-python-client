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

#
# Parse arguments
#
parser = argparse.ArgumentParser(description='REST call to Opal.')
parser.add_argument('--opal', '-o', required=True, help='Opal server base url')
parser.add_argument('--user', '-u', required=True, help='User name')
parser.add_argument('--password', '-p', required=True, help='User password')
parser.add_argument('--ws', '-w', required=True, help='Web service path, for instance ')
parser.add_argument('--out', '-f', required=False, help='Path to the file where response is to be written. Otherwise response is printed on the stdout.')
parser.add_argument('--json', '-j', action='store_true', help='Pretty JSON formatting of the response')
parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
args = parser.parse_args()

#
# Response content reader
#
class Reader:
  def __init__(self):
    self.contents = ''

  def body_callback(self, buf):
    self.contents = self.contents + buf

#
# Build request
#
url = args.opal + '/ws' + args.ws
credentials = base64.b64encode(args.user + ':' + args.password)

reader = Reader()
c = pycurl.Curl()
c.setopt(c.URL, url)
c.setopt(c.HTTPHEADER, ['Accept: application/json', 'Authorization: X-Opal-Auth ' + credentials])
c.setopt(c.SSL_VERIFYPEER, 0)
c.setopt(c.CONNECTTIMEOUT, 5)
c.setopt(c.TIMEOUT, 8)
c.setopt(c.FAILONERROR, True)
c.setopt(c.VERBOSE, args.verbose)
c.setopt(c.WRITEFUNCTION, reader.body_callback)

#
# Output response
#
try:
  c.perform()
except pycurl.error, error:
  errno, errstr = error
  print >> sys.stderr, 'An error occurred: ', errstr
  sys.exit(2)
else:
  # format response
  res = '';
  if args.json:
    res = json.dumps(json.loads(reader.contents), sort_keys=True, indent=2)
  else:
    res = reader.contents
  # output to file
  if args.out:
    f = open(args.out, 'w')
    f.write(res)
    f.close()
  else:
    print res
finally:
  c.close()



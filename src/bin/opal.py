#! /usr/bin/env python
#
import opal.rest
import opal.dictionary
import opal.data
import argparse

#
# Add Opal access arguments
#
def add_opal_arguments(parser):
  parser.add_argument('--opal', '-o', required=False, help='Opal server base url')
  parser.add_argument('--user', '-u', required=False, help='User name')
  parser.add_argument('--password', '-p', required=False, help='User password')
  parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

# Parse arguments
parser = argparse.ArgumentParser(description='Opal command line.')
subparsers = parser.add_subparsers(title='sub-commands', help='Available sub-commands. Use --help option on the sub-command for more details.')

# REST command
subparser = subparsers.add_parser('rest', help='Request directly the Opal REST API.')
add_opal_arguments(subparser)
opal.rest.add_arguments(subparser)
subparser.set_defaults(func=opal.rest.do_command)

# Dictionary command
subparser = subparsers.add_parser('dict', help='Query Opal data dictionary.')
add_opal_arguments(subparser)
opal.dictionary.add_arguments(subparser)
subparser.set_defaults(func=opal.dictionary.do_command)

# Data command
subparser = subparsers.add_parser('data', help='Query Opal data.')
add_opal_arguments(subparser)
opal.data.add_arguments(subparser)
subparser.set_defaults(func=opal.data.do_command)

# Execute selected command
args = parser.parse_args()
args.func(args)

#! /usr/bin/env python
#
import opal.rest
import argparse

#
# Add Opal access arguments
#
def add_opal_arguments(parser):
  parser.add_argument('--opal', '-o', required=True, help='Opal server base url')
  parser.add_argument('--user', '-u', required=True, help='User name')
  parser.add_argument('--password', '-p', required=True, help='User password')

# Parse arguments
parser = argparse.ArgumentParser(description='Opal command line.')
subparsers = parser.add_subparsers(title='sub-commands', help='Available sub-commands. Use --help option on the sub-command for more details.')

# REST command
parser_rest = subparsers.add_parser('rest', help='This command allows to request directly the Opal REST API.')
add_opal_arguments(parser_rest)
opal.rest.add_arguments(parser_rest)
parser_rest.set_defaults(func=opal.rest.do_command)

# Execute selected command
args = parser.parse_args()
args.func(args)

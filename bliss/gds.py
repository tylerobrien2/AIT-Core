"""
BLISS Ground Data System

The BLISS.gds module provides utility functions specific to OCO-3 GDS
command-line tools.
"""

"""
Authors: Ben Bornstein

Copyright 2013 California Institute of Technology.  ALL RIGHTS RESERVED.
U.S. Government Sponsorship acknowledged.
"""


import os
import sys
import getopt
import zlib
import socket

import bliss


def compress (input_filename, output_filename=None, verbose=False):
  """compress(input_filename, output_filename=None, verbose=False) -> integer

  Uses zlib to compress input_filename and store the result in
  output_filename.  The size of output_filename is returned on
  success; zero is returned on failure.

  The input file is compressed in one fell swoop.  The output_filename
  defaults to input_filename + ".bliss-zlib".

  If verbose is True, compress() will use bliss.log.info() to report
  compression statistics.
  """
  input_size  = 0
  output_size = 0

  if output_filename is None:
    output_filename = input_fillename + '.bliss-zlib'

  try:
    stream     = open(input_filename , 'rb')
    output     = open(output_filename, 'wb')
    bytes      = stream.read()
    input_size = len(bytes)

    if verbose:
      bliss.log.info("Compressing %s (%d bytes).", input_filename, input_size)

    compressed  = zlib.compress(bytes, 3)
    output_size = len(compressed)
    output.write(compressed)

    stream.close()
    output.close()

    percent = (1.0 - (output_size / float(input_size) )) * 100

    if verbose:
      bliss.log.info("Wrote %s (%d bytes).", output_filename, output_size)
      bliss.log.info("Compressed %6.2f percent", percent)

  except (IOError, OSError), e:
    bliss.log.error(str(e) + ".")

  return output_size


def exit (status=None):
  """exit([status])

  Calls bliss.log.end()

  Exit the interpreter by raising SystemExit(status).  If the status
  is omitted or None, it defaults to zero (i.e., success).  If the
  status is numeric, it will be used as the system exit status.  If it
  is another kind of object, it will be printed and the system exit
  status will be one (i.e., failure).
  """
  bliss.log.end()
  sys.exit(status)


def hexdump (bytes, addr=None, preamble=None, printfunc=None, stepsize=16):
  """hexdump(bytes[, addr[, preamble[, printfunc[, stepsize=16]]]])

  Outputs bytes in hexdump format lines similar to the following (here
  preamble='Bank1', stepsize=8, and len(bytes) == 15):

    Bank1: 0xFD020000: 7f45  4c46  0102  0100  *.ELF....*
    Bank1: 0xFD020008: 0000  0000  0000  00    *....... *

  Where stepsize controls the number of bytes per line.  If addr is
  omitted, the address portion of the hexdump will not be output.
  Lines will be passed to printfunc for output, or Python's builtin
  print, if printfunc is omitted.

  If a byte is not in the range [32, 127), a period will rendered for
  the character portion of the output.
  """
  if preamble is None:
    preamble = ""

  bytes = bytearray(bytes)
  size  = len(bytes)

  for n in xrange(0, size, stepsize):
    if addr is not None:
      dump = preamble + "0x%04X: " % (addr + n)
    else:
      dump = preamble
    end   = min(size, n + stepsize)
    dump += hexdumpLine(bytes[n:end], stepsize)

    if printfunc is None:
      print dump
    else:
      printfunc(dump)


def hexdumpLine (bytes, length=None):
  """hexdumpLine(bytes[, length])

  Returns a single hexdump formatted line for bytes.  If length is
  greater than len(bytes), the line will be padded with ASCII space
  characters to indicate no byte data is present.

  Used by hexdump().
  """
  line = ""

  if length is None:
    length = len(bytes)

  for n in xrange(0, length, 2):
    if n < len(bytes) - 1:
      line += "%02x%02x  " % (bytes[n], bytes[n + 1])
    elif n < len(bytes):
      line += "%02x    "   % bytes[n]
    else:
      line += "      "

  line += "*"

  for n in xrange(length):
    if n < len(bytes):
      if bytes[n] in xrange(32, 127):
        line += "%c" % bytes[n]
      else:
        line += "."
    else:
      line += " "

  line += "*"
  return line



def parseArgs (argv, defaults):
  """parseArgs(argv, defaults) -> (dict, list)

  Parses command-line arguments according to the given defaults.  For
  every key in defaults, an argument of the form --key=value will be
  parsed.  Numeric arguments are converted from strings with errors
  reported via bliss.log.error() and default values used instead.

  Returns a copy of defaults with parsed option values and a list of
  any non-flag arguments.
  """
  options = dict(defaults)
  numeric = \
    [ k for k, v in options.items() if type(v) is float or type(v) is int ]

  try:
    longopts   = [ "%s=" % key for key in options.keys() ]
    opts, args = getopt.getopt(argv, "", longopts)

    for key, value in opts:
      if key.startswith("--"):
        key = key[2:]
      options[key] = value
  except getopt.GetoptError, err:
    bliss.log.error( str(err)  )
    bliss.gds.usage( exit=True )

  for key in numeric:
    value = options[key]
    if type(value) is str:
      options[key] = bliss.util.toNumber(value)

    if options[key] is None:
      msg = "Option '%s': '%s' is not a number, using default '%s' instead."
      bliss.log.error(msg, key, value, defaults[key])
      options[key] = defaults[key]

  return options, args


def usage (exit=False):
  """usage([exit])

  Prints the usage statement at the top of a Python program.  A usage
  statement is any comment at the start of a line that begins with a
  double hash marks (##).  The double hash marks are removed before
  the usage statement is printed.  If exit is True, the program is
  terminated with a return code of 2 (GNU standard status code for
  incorrect usage).
  """
  stream = open(sys.argv[0])
  for line in stream.readlines():
    if line.startswith("##"): print line.replace("##", ""),
  stream.close()

  if exit:
    sys.exit(2)


def getip():
  """
  getip()

  Returns the IP address of the computer. Helpful for those hosts that might
  sit behind gateways and report a hostname that is a little strange (I'm
  looking at you oco3-sim1).
  """
  return [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
#!/usr/bin/env python
'''

usage: bliss-seq-decode oco3_seq_SSS_NNN_desc.bin

Decodes the given relative time command sequence to text.

Examples:

  $ bliss-seq-decode seq/oco3_seq_gps_001_reset.bin
'''

import os
import sys

from bliss.core import gds, log, seq


def main():
    log.begin()

    defaults      = { }
    options, args = gds.parseArgs(sys.argv[1:], defaults)

    if len(args) == 0:
        gds.usage(exit=True)

    filename  = os.path.abspath(args[0])
    extension = os.path.splitext(filename)[1]

    if extension.lower() != '.bin':
        log.warn("Filename '%s' does not have a '.bin' extension", filename)

    sequence = seq.Seq(filename)

    if not sequence.validate():
        for msg in sequence.messages:
            log.error(msg)
    else:
        txtpath = sequence.txtpath
        seqid   = sequence.seqid
        version = sequence.version

        msg = "Writing %s (seqid=0x%04x, version=%u)."
        log.info(msg, txtpath, seqid, version)

        sequence.writeText()

    log.end()


if __name__ == '__main__':
    main()
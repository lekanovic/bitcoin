#!/usr/bin/env python
# vim: ts=4 et

"""
Notes:

A message starts with the character sequence 55 F0 repeating 3 times
"""

#from reedsolo import RSCodec
import argparse
import subprocess


MAX_ERRORS  = 5
PACKET_SIZE = 64


class Transmitter:
    def __init__(self, baudmode, other_args=[]):
        self.p = subprocess.Popen(['minimodem', '-t', '-8'] + other_args +
            [baudmode], stdin=subprocess.PIPE)

    def write(self, text):
        self.p.stdin.write(text)

    def close(self):
        self.p.stdin.close()
        self.p.wait()


class Receiver:
    def __init__(self, baudmode, other_args):
        print 'New Receiver'


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--tx','-t', dest='cls', action='store_const', const=Transmitter, help='transmitter')
    group.add_argument('--rx','-r', dest='cls', action='store_const', const=Receiver, help='receiver')
    parser.add_argument('args', nargs='*')
    parser.add_argument('baudmode')
    args = parser.parse_args()
    inst = args.cls(args.baudmode, args.args)
    inst.write('Hello world')

if __name__ == '__main__':
    main()


#!/usr/bin/env python3

import os
import sys
from time import sleep, time
from icmplib import ICMPv4Socket, ICMPRequest, ICMPError, ICMPLibError, PID, TimeoutExceeded
import argparse

def verbose_ping(address, interval=1, timeout=1):
    sock = ICMPv4Socket()
    seq = 0
    summary = PeriodSummary()
    while True:
        seq += 1
        rtt = 'Dropped'
        t = time()
        req = ICMPRequest(
            destination=address,
            id=PID,
            sequence=seq)
        try:
            sock.send(req)
            reply = sock.receive(req, timeout)

            reply.raise_for_status()

            rtt = (reply.time - req.time)

        except (TimeoutExceeded, ICMPError) as e:
            pass  # rtt has already been set to dropped
        except ICMPLibError as e:
            print(e, flush=True, file=sys.stderr)

        if Global.args.verbose:
            print(f'{t} {address} {seq} {rtt}', flush=True, file=sys.stderr)
        summary.add(t, address, seq, rtt)
        sleep(interval)

class Global:
    args = None

class PeriodSummary:
    def __init__(self, summary_period=60):
        self.period = summary_period
        self.periodStart = None

    def _initStats(self, start=None):
        self.periodStart = start
        if self.periodStart is not None:
            self.periodEnd = self.periodStart + self.period
        else:
            self.periodEnd = None
        self.dropped = 0
        self.minRTT = None
        self.maxRTT = None
        self.count = 0
        self.totRTT = 0

    def add(self, t, addr, seq, rtt):
        if not self.periodStart:
            self._initStats(t)
        self.count += 1
        if t > self.periodEnd:
            if self.totRTT == 0:
                avg = None
            else:
                avg = self.totRTT / self.count
            print(f'{self.periodStart},{self.minRTT},{avg},{self.maxRTT},{self.dropped}', flush=True)
            self._initStats(self.periodStart + self.period)
        else:
            if rtt == 'Dropped':
                self.dropped += 1
            else:
                if self.minRTT is None or rtt < self.minRTT:
                    self.minRTT = rtt
                if self.maxRTT is None or rtt > self.maxRTT:
                    self.maxRTT = rtt
                self.totRTT += rtt

def main():
    parser = argparse.ArgumentParser(description='''
        Pings a target and every minute prints a summary of min, average and max ping times
        along with the number of pings dropped.
        
        Output is in csv format.
    ''')
    parser.add_argument('target', nargs='?', default='google.co.nz', 
                        help='Target to ping')
    parser.add_argument('-v', '--verbose', action='store_true', 
                         help='Display individual ping returns to stdout')
    Global.args = parser.parse_args()
    #verbose_ping('8.8.8.8', timeout=5)
    verbose_ping(Global.args.target, timeout=5)



if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, BrokenPipeError):
        sys.exit()

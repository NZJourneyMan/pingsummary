#!/usr/bin/env python3

import os
import sys
from time import sleep, time
from icmplib import ICMPv4Socket, ICMPRequest, PID, ICMPError, ICMPLibError, TimeoutExceeded
import argparse
from threading import Thread, Event, Timer
from queue import Queue
from collections import OrderedDict
from socket import gethostbyname
import sqlite3
from datetime import datetime
import pytz

class PingSendFactory(Thread):
    def __init__(self, address, syncEvent, socketID, interval=1):
        super().__init__()
        self.address = address
        self.syncEvent = syncEvent
        self.interval = interval
        self.running = Event()
        self.sleep = Event()
        self.queue = Queue()
        self.socketID = socketID
        
    def stop(self):
        if Global.args.debug:
            print(f'Stopping {self.__class__.__name__}', file=sys.stderr)
        self.running.set()
        self.sleep.set()
        
    def run(self):
        sock = ICMPv4Socket()
        seq = 0
        while not self.running.is_set():
            seq += 1
            if seq > 0xFFFF:
                seq = 1
            req = ICMPRequest(
                destination=self.address,
                id=PID,
                sequence=seq)
            try:
                sock.send(req)
            except ICMPError:
                pass

            qItem = {
                'idx': (self.socketID, seq),
                'rtt': None,
                'req': req
            }
            self.queue.put(qItem)
            self.syncEvent.set()
            if Global.args.debug:
                print(f'{self.__class__.__name__}: '
                      f'EnQueued {qItem}. '
                      f'QLen: {self.queue.qsize()}. '
                      f'Sleeping {self.interval}', file=sys.stderr)
            self.sleep.wait(self.interval)

class PingRecvFactory(Thread):
    def __init__(self, syncEvent, socketID):
        super().__init__()
        self.syncEvent = syncEvent
        self.running = Event()
        self.queue = Queue()
        self.socketID = socketID
        
    def stop(self):
        if Global.args.debug:
            print(f'Stopping {self.__class__.__name__}', file=sys.stderr)
        self.running.set()
        
    def run(self):
        sock = ICMPv4Socket()
        while not self.running.is_set():
            try:
                # Timeout is only needed for a clean shutdown of the thread
                reply = sock.receive(timeout=0.1)
                reply.raise_for_status()
            except (ICMPError, TimeoutExceeded):
                pass
            else:
                if reply.id == self.socketID:
                    self.queue.put(reply)
                    self.syncEvent.set()
                    if Global.args.debug:
                        print(f'{self.__class__.__name__}: '
                            f'EnQueued {reply}. '
                            f'idx: {(reply.id, reply.sequence)}. '
                            f'QLen: {self.queue.qsize()}. '
                            , file=sys.stderr)
    
class PingSummary:
    def __init__(self, address, interval=1, timeout=1):
        self.address = address
        self.timeout = timeout
        self.summary = PeriodSummary()
        self.sync = Event()
        self.pingSend = PingSendFactory(self.address, self.sync, PID, interval)
        self.pingRecv = PingRecvFactory(self.sync, PID)
        self.pingSend.start()
        self.pingRecv.start()
        self.pingsWaiting = OrderedDict()
        self.alarm = Timer(0, lambda : True)

    def getFirst(self, od):
        if len(od) > 0:
            k = list(od.keys())[0]
            return od[k]
        else:
            return None

    def setDropped(self):
        req = self.getFirst(self.pingsWaiting)
        if Global.args.debug:
            print(f'Setting {req} to "Dropped"', file=sys.stderr)
        if req:
            req['rtt'] = 'Dropped'
            self.sync.set()

    def setAlarm(self, timeout):
        # Set the first pingsWaiting request to 'Dropped' if we timeout
        if not self.alarm.is_alive():
            req = self.getFirst(self.pingsWaiting)
            if req:
                alarmTimeout = req['req'].time - time() + timeout
                self.alarm.cancel()
                self.alarm = Timer(alarmTimeout, self.setDropped)
                self.alarm.start()
                if Global.args.debug:
                    print(f'Setting alarm to {alarmTimeout} '
                        f'for {req["idx"]} '
                        f'Alarm: {self.alarm} ', 
                        f'Status: {self.alarm.is_alive()}', 
                        file=sys.stderr)
    def run(self):
        while True:
            # Wait for something to happen: a packet sent, a packet received or an alarm
            # for a dropped packet
            self.sync.wait()

            # Add sent packets to the packet waiting queue
            while self.pingSend.queue.qsize() > 0:
                req = self.pingSend.queue.get()
                self.pingsWaiting[req['idx']] = req
                if Global.args.debug:
                    print(f'SendQueue got {req}. '
                        f'SendQLen: {self.pingSend.queue.qsize()} '
                        f'WaitQLen {len(self.pingsWaiting)}',
                        file=sys.stderr)
            self.setAlarm(self.timeout)  # Update the alarm if necessary

            # Update the waiting queue with the results of the received packets
            while self.pingRecv.queue.qsize() > 0:
                reply = self.pingRecv.queue.get()
                idx = reply.id, reply.sequence
                if idx in self.pingsWaiting:
                    req = self.pingsWaiting[idx]
                    rtt = (reply.time - req['req'].time)
                    self.pingsWaiting[req['idx']]['rtt'] = rtt
                    if Global.args.debug:
                        print(f'RecvQueue: Found id {idx} '
                            f'WaitQLen {len(self.pingsWaiting)}',
                            file=sys.stderr)
                    if req == self.getFirst(self.pingsWaiting):
                        if Global.args.debug:
                            print(f'PingsWaiting[0] has a rtt, so cancelling the alarm')
                        self.alarm.cancel()
                else:
                    # Reply must have timed out and been removed
                    if Global.args.debug:
                        print(f'RecvQueue: Could not find id {idx} '
                            f'WaitQLen {len(self.pingsWaiting)}',
                            file=sys.stderr)

            # Check to see if there are any items that can be summarised.
            # The first item in pingsWaiting has to have a rtt value to proceed
            while True:
                req = self.getFirst(self.pingsWaiting)
                if req:
                    if Global.args.debug:
                            print(f'PingsWaiting[0] rtt: {req["rtt"]} '
                                f'WaitQLen {len(self.pingsWaiting)}',
                                file=sys.stderr)
                    if req['rtt']:
                        self.alarm.cancel()
                        self.summary.add(req['req'].time,
                                         req['req'].destination,
                                         req['req'].sequence,
                                         req['rtt'])
                        if Global.args.verbose:
                            print(
                                  f"{mkISOTime(req['req'].time)} "
                                  f"{req['req'].time} "
                                  f"{req['req'].destination} "
                                  f"{req['req'].sequence} "
                                  f"{req['rtt']}",
                                  flush=True,
                                  file=sys.stdout)
                        del(self.pingsWaiting[req['idx']])
                    else:
                        break
                else:
                    if Global.args.debug:
                        print(f'PingsWaiting[0] None WaitQLen {len(self.pingsWaiting)}',
                            file=sys.stderr)
                    break

            self.setAlarm(self.timeout)  # Update the alarm if necessary
            
            self.sync.clear()

    def shutdown(self):
        self.pingSend.stop()
        self.pingRecv.stop()
        self.alarm.cancel()


class Global:
    args = None
    ip = None

class PeriodSummary:
    def __init__(self, summary_period=60):
        self.period = summary_period
        self.periodStart = None
        db = os.path.join(os.path.dirname(__file__), 'pingtest-summ.sqlite')
        self.con = sqlite3.connect(db)
        self.cur = self.con.cursor()
        self.createDB()

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

    def createDB(self):
        self.cur.execute('''
            create table if not exists pingsumm (
                    date text primary key,
                    unixdate real,
                    min real,
                    avg real,
                    max real,
                    dropped integer
            )
        ''')

    def add(self, t, addr, seq, rtt):
        if not self.periodStart:
            self._initStats(t)
        self.count += 1
        if t > self.periodEnd:
            if self.totRTT == 0:
                avg = None
            else:
                avg = self.totRTT / self.count
            isoTime = mkISOTime(self.periodStart)
            row = [isoTime, self.periodStart, self.minRTT, avg, self.maxRTT, self.dropped]
            if Global.args.verbose:
                print(' '.join([str(x) for x in row]), flush=True)
            sql = 'insert into pingsumm (date, unixdate, min, avg, max, dropped) values (?,?,?,?,?,?);'
            self.cur.execute(sql, row)
            self.con.commit()

            self._initStats(self.periodStart + self.period)
        if rtt == 'Dropped':
            self.dropped += 1
        else:
            if self.minRTT is None or rtt < self.minRTT:
                self.minRTT = rtt
            if self.maxRTT is None or rtt > self.maxRTT:
                self.maxRTT = rtt
            self.totRTT += rtt

def mkISOTime(t):
    timezone = pytz.timezone("NZ")
    return timezone.localize(datetime.fromtimestamp(t)).isoformat()

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
    parser.add_argument('-d', '--debug', action='store_true', 
                         help='Display debug information')
    Global.args = parser.parse_args()

    try:
        ping = None
        # Try 3 times to resolve hostname
        for _ in range(3):
            try:
                Global.ip = gethostbyname(Global.args.target)
                break
            except OSError:
                pass
            sleep(1)
        if not Global.ip:
            print(f'Could not resolve {Global.args.target}')
            sys.exit(1)

        ping = PingSummary(Global.ip, timeout=5)
        ping.run()
    except (KeyboardInterrupt, BrokenPipeError):
        if ping:
            ping.shutdown()



if __name__ == '__main__':
    main()

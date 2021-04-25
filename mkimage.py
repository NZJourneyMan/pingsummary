#!/usr/bin/env python3

import sys
import sqlite3
import pathlib 
from os.path import realpath, dirname, join as pjoin
from dateutil.parser import parse as dateparse
from datetime import datetime, timedelta
from argparse import ArgumentParser
from matplotlib import pyplot as plt, dates as mdates, patches as mpatches, rcParams

def removeNone(n):
    return 0 if n is None or n == 'None' else n

def main():
    parser = ArgumentParser(description='Generates a Graph for the requested date and '
       'outputs it to a file. Default file is "./data/images/$isodate"')
    parser.add_argument('date', help='Date to graph in the format YYYY-MM-DD')
    parser.add_argument('-f', '--file', metavar='name', help='Name of the output file')
    args = parser.parse_args()

    i = 0
    pDate = []
    min = []
    avg = []
    max = []
    dropped = []
    rootDir = dirname(realpath(__name__))
    dbName = pjoin(rootDir, 'data/db/pingsumm.sqlite')
    imagesDir = pjoin(rootDir, 'data/images')

    pathlib.Path(imagesDir).mkdir(exist_ok=True)

    con = sqlite3.connect(dbName)
    cur = con.cursor()
    
    startDateObj = dateparse(args.date).astimezone()
    endDateObj = startDateObj + timedelta(hours=23, minutes=59, seconds=59, milliseconds=999)

    for line in cur.execute("select date, unixdate, min, avg, max, (dropped*100/60), target "
                            "from pingsumm where date(date, 'localtime') = date(?, 'localtime') ", (args.date,)):

        i += 1
        pDate.append(datetime.fromtimestamp(line[1]).astimezone())
        min.append(float(removeNone(line[2])))
        avg.append(removeNone(line[3]))
        max.append(removeNone(line[4]))
        dropped.append(removeNone(line[5]))
        if i == 1:
            target = line[6]

    if i == 0:
        print(f'No ping summaries found for {args.date}')
        sys.exit()    
    print(f"{i} summarary lines found")

    rcParams['timezone'] = 'NZ'
    locator = mdates.AutoDateLocator()
    formatter = mdates.ConciseDateFormatter(locator)
    hl = mdates.HourLocator()

    fig, (plot1) = plt.subplots(figsize=(8,5), dpi=300)
    fig.set_facecolor('grey')

    plot1.set_title(f'Ping Summary: {target}', fontsize=12)

    plot1.xaxis.set_major_locator(locator)
    plot1.xaxis.set_major_formatter(formatter)
    plot1.xaxis.set_minor_locator(hl)
    plot1.set_xlim(startDateObj, endDateObj)

    plot1.fill_between(pDate, max, color='yellow')
    plot1.fill_between(pDate, avg, color='blue')
    plot1.fill_between(pDate, min, color='green')
    plot1.set_ylim(0, 0.5)
    # plot1.set_xlabel('Date', fontsize=14)
    plot1.set_ylabel('Latency seconds', fontsize=10)


    plot2 = plt.twinx()
    plot2.xaxis.set_major_locator(locator)
    plot2.xaxis.set_major_formatter(formatter)

    plot2.fill_between(pDate, dropped, color='red')
    plot2.set_ylim(100, 0)
    plot2.set_ylabel('Packet loss %', fontsize=10)
    plot2.set_facecolor('grey')

    import matplotlib.patches as mpatches

    red_legend = mpatches.Patch(color='red', label='Dropped Packets (%)')
    green_legend = mpatches.Patch(color='green', label='Minimum latency (s)')
    blue_legend = mpatches.Patch(color='blue', label='Average latency (s)')
    yellow_legend = mpatches.Patch(color='yellow', label='Maximum latency (s)')
    plt.legend(handles=[green_legend, blue_legend, yellow_legend, red_legend], 
            ncol=4, loc="center", bbox_to_anchor=(0, -0.034, 0.9, -0.11), fontsize='xx-small')

    fileName = args.file if args.file else pjoin(imagesDir, args.date)
    plt.savefig(fileName, bbox_inches='tight')
    # plt.show()

if __name__ == '__main__':
    main()

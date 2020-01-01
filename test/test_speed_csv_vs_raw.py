#!/usr/bin/python3

import time
import argparse
import os, sys

testdir = os.path.dirname(__file__)
srcdir = '../csv_analyzer'
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

import csv_analyzer
from csv_analyzer import CSVAnalyzer, BigCSVReader

def main():
    parser = argparse.ArgumentParser(description='Benchmark loading dictionary of variables from a csv file.')
    parser.add_argument('-f', '--file', metavar='FILE', type=str,
                        help='CSV file to load')
    parser.add_argument('columns', metavar='COL_NAME', type=str, nargs='+',
                    help='column name(s) to load')
    parser.add_argument('-x', '--xaxis', metavar='X_COL_NAME', type=str,
                    help='column name of x-axis')
    parser.add_argument('-r', '--rowstart', metavar='STARTROW', type=int,
                        help='row start number', default=0)
    parser.add_argument('-e', '--rowend', metavar='ENDROW', type=int,
                        help='row end number (0 to end of file)', default=0)       

    args = parser.parse_args()

    print("Loading " + args.file)     

    bigreader_raw = BigCSVReader()
    start = time.time()
    data, xaxis = bigreader_raw.get_csv_data(args.file, args.columns, args.xaxis, args.rowstart, args.rowend, True)
    end = time.time()
    print("Processed CSV using raw I/O in %f seconds", end - start)
    
    data = None
    xaxis = None

    bigreader_csv = BigCSVReader()
    start = time.time()
    data, xaxis = bigreader_csv.get_csv_data(args.file, args.columns, args.xaxis, args.rowstart, args.rowend, False)
    end = time.time()
    print("Processed CSV using csv module in %f seconds", end - start)

    data = None
    xaxis = None

if __name__ == "__main__":
    main()
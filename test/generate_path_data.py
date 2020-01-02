#!/usr/bin/python3

import pyautogui
import time
import argparse
import math

OFFSET_X = 10
OFFSET_Y = 10
DURATION = 5
start_time = time.time()

parser = argparse.ArgumentParser(description='Generate some CSV data from mouse movement')
parser.add_argument('-f', '--outputfile', metavar='OUTPUT', type=str,
                    default="path.csv", help='output file (path.csv)')
parser.add_argument('-x', '--offsetx', metavar='X_OFFSET', type=int,
                    default=OFFSET_X, help='x-offset')
parser.add_argument('-y', '--offsety', metavar='Y_OFFSET', type=int,
                    default=OFFSET_Y, help='y-offset')
parser.add_argument('-d', '--duration', metavar='DURATION_S', type=int,
                    default=DURATION, help='y-offset')

args = parser.parse_args()

print("Move your mouse around for the next %i seconds\nCSV will be captured to %s" % (args.duration, args.outputfile))

with open(args.outputfile, 'w') as f:
    f.write("t,x,y,offx,offy,v\n")
    t = time.time() - start_time

    last_x, last_y = pyautogui.position()
    last_t = 0
    v = 0
    v_measure = []
    while (t <= args.duration):
        x, y = pyautogui.position()
        t = time.time() - start_time
        
        if (x != last_x or y != last_y):
            d = math.sqrt( pow(x - last_x, 2) + pow(y - last_y, 2) )
            v = d / ( t - last_t )
            last_t = t
        else:
            v = 0
        v_measure.append(v)
        while len(v_measure) > 20:
            v_measure.pop(0)

        v_avg = sum(v_measure) / len(v_measure)
        
        x_offset = x + args.offsetx
        y_offset = y + args.offsety     
        f.write("{0:f},{1:d},{2:d},{3:d},{4:d},{5:f}\n".format(t, x, y, x_offset, y_offset, v_avg))
        last_x = x
        last_y = y
        

    f.close()

print("done")

exit(0)
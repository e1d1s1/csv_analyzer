#!/usr/bin/python

import matplotlib.pyplot as plotter
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D
import numpy as np

import sys
import argparse
import random
import pickle
import time
import os
#import csv

line_cnt = 0
legend_keys = []

parser = argparse.ArgumentParser(description='Plot collection of variables for a csv file.')
parser.add_argument('-f', '--file', metavar='FILE', type=str,
                    help='CSV file to plot')
parser.add_argument('-x', '--xaxis', metavar='X_COL_NAME', type=str,
                    help='column name of x-axis', default="logger_time")
parser.add_argument('columns_plot1', metavar='COL_NAME', type=str, nargs='+',
                    help='column name(s) of the plot items')
parser.add_argument('-r', '--rowstart', metavar='STARTROW', type=int,
                    help='row start number', default=0)
parser.add_argument('-e', '--rowend', metavar='ENDROW', type=int,
                    help='row end number (0 to end of file)', default=0)
parser.add_argument('-t', '--filter', metavar='expression', type=str,
                    help='filtering expression', default='')
parser.add_argument('-d', '--hideplot1', action='store_true',
                    help='hides the main plot')
parser.add_argument('-i', '--title', type=str,
                    help='title of plot 1', default='')
parser.add_argument('-l', '--filtertitle', type=str,
                    help='title of the filter plot', default='')
parser.add_argument('-s', '--sessionstart', action='store_true',
                    help='starts a new session so we only load data/assign colors once', default='')
parser.add_argument('-c', '--sessioncontinue', action='store_true',
                    help='Continues an existing session so we only load data/assign colors once', default='')
parser.add_argument('-m', '--terminate', action='store_true',
                    help='Closes immediately after data load and session save', default='')
parser.add_argument('--scatter', action='store_true',
                    help='Create scatter plots from pairs of values', default='')
parser.add_argument('--colorbyplot', action='store_true',
                    help='Keep plot color scheme consistent by plot order', default=False)

args = parser.parse_args()

if len(args.file) == 0 or len(args.xaxis) == 0 or len(args.columns_plot1) == 0:
    parser.print_help()
    exit(1)

def add_line(axis, key, lines_dict, color_dict):
    global line_cnt

    c = 'black'
    th = 0.4
    if args.colorbyplot:
        c = color_palette[line_cnt][0]
        th = color_palette[line_cnt][1]
    else:
        c = color_dict[key][0]
        th = color_dict[key][1]
    lines_dict[key] = Line2D([], [], color=c, linewidth=th)
    axis.add_line(lines_dict[key])
    line_cnt+=1

def create_lines(axis, lines_dict, color_dict):
    global line_cnt
    global legend_keys

    line_cnt = 0
    i = 0
    for key in args.columns_plot1:
        if not args.scatter or i % 2 != 0:
            add_line(axis, key, lines_dict, color_dict)
            legend_keys.append(key)
        i += 1


def assign_colors(color_dict):
    # automatically pick good looking colors
    colors = dict(mcolors.BASE_COLORS, **mcolors.CSS4_COLORS)
    by_hsv = sorted((tuple(mcolors.rgb_to_hsv(mcolors.to_rgba(color)[:3])), name)
                    for name, color in colors.items())
    sorted_names = [name for hsv, name in by_hsv]
    start_thickness = 0.5
    max_thickness = 1.1
    thickness = start_thickness
    thickness_increment = 0.1
    if len(color_dict) > 0:
        thickness_increment = (max_thickness - start_thickness) / len(color_dict.keys())
    cnt = 0
    for key in color_dict:
        if cnt <= 2 and args.colorbyplot:
            if cnt == 0:
                color_dict[key] = ("blue", start_thickness)
            elif cnt == 1:
                color_dict[key] = ("red", start_thickness)
            elif cnt == 2:
                color_dict[key] = ("green", start_thickness)
        else:
            luminosity = 1
            index = 0
            # we want dark lines
            while luminosity > 0.66:
                index = random.randint(0, len(sorted_names) - 1)
                color_name = sorted_names[index]
                rgb = mcolors.to_rgba(color_name)
                luminosity = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

            color_dict[key] = (color_name, thickness)
            if cnt % 2 == 0:
                thickness += thickness_increment
        
        color_palette.append(color_dict[key])
        cnt+=1

def fill_lines(lines_dict, ydata_dict):
    if args.scatter:
        i = 0
        for key in args.columns_plot1:
            if i % 2 == 0:
                xdata = ydata_dict[key]
                lines_dict.pop(key)
            else:
                d = ydata_dict[key]
                lines_dict[key].set_data(xdata, d)
            i+=1
    else:
        for key in lines_dict:
            d = ydata_dict[key]
            xdata = x_axis

            if not d is None:
                lines_dict[key].set_data(xdata, d)
            else:
                return False

    return True


def fit_plot(axis, lines, ydata_dict):
    min_y = float('inf')
    max_y = float('-inf')
    min_x = float('inf')
    max_x = float('-inf')

    if args.scatter:
        i = 0
        for key in args.columns_plot1:
            if i % 2 == 0:
                min_x = min(min_x, min(ydata_dict[key]))
                max_x = max(max_x, max(ydata_dict[key]))
            i+=1
    else:
        min_x = x_axis[0]
        max_x = x_axis[-1]

    for key in lines:
        if key in ydata_dict and len(ydata_dict[key]) > 0:
            min_y = min(min_y, min(ydata_dict[key]))
            max_y = max(max_y, max(ydata_dict[key]))

    if max_y != 0:
        max_y += 5

    if min_y != 0:
        min_y -= 5

    axis.set_ylim(min_y, max_y)
    axis.set_xlim(min_x, max_x)
    axis.set_xlabel(args.xaxis)
    axis.grid(True)


def get_csv_data(filename, columns, xaxis_name, rowstart, rowend):
    headers = {}
    data = {}
    xaxis = []

    for key in columns:
        data[key] = []

    row_count = 0
    row_num = 0
    idx_xaxis = 0

    with open(filename, 'r') as csvfile:
        row_count = sum(1 for row in csvfile)

    with open(filename, 'r') as csvfile:
        # fails on big files
        #reader = csv.reader(csvfile)
        lines = (line.rstrip() for line in csvfile)
        for rawrow in lines:
        # for row in reader:
            row = rawrow.split(',')
            if rowend > 0 and row_num > rowend:
                break

            if row_num == 0:
                i = 0
                for ele in row:
                    if ele in columns:
                        headers[i] = ele
                    if ele == xaxis_name:
                        idx_xaxis = i
                    i += 1
            elif row_num >= rowstart:
                i = 0
                for ele in row:
                    for idx, name in headers.items():
                        if idx == i:
                            data[name].append(float(ele))
                    if i == idx_xaxis:
                        xaxis.append(float(ele))
                    i += 1

            row_num += 1

            if row_num % 100000 == 0:
                print("processed %i rows of %i" % (row_num, row_count))

    return data, xaxis

dict_lines = {}
dict_data = {}
x_axis = []
color_palette = []
dict_colors = {}

dict_filter_lines = {}
dict_filter_data = {}

for header in args.columns_plot1:
    dict_lines[header] = None
    dict_colors[header] = ("black", 1)

figure_1 = None
axis_1 = None
figure_filter = None
axis_filter = None

if args.sessioncontinue:

    print ('restoring session data')
    try:
      while os.path.exists('csvsession.pickle.lock'):
        print("waiting for lock on pickle file")
        time.sleep(2)

      with open("csvsession.pickle", "rb") as f:
          dict_data = pickle.load(f)
          x_axis = pickle.load(f)
          dict_colors = pickle.load(f)
          color_palette = pickle.load(f)

    except:  # handle other exceptions
        print("Unexpected error:", sys.exc_info()[0])
        exit(1)
else:

    assign_colors(dict_colors)

    try:
        print ('reading CSV data')
        dict_data, x_axis = get_csv_data(args.file, args.columns_plot1, args.xaxis, args.rowstart, args.rowend)

    except IOError as e:
        print ("I/O error({0}): {1}".format(e.errno, e.strerror))
        exit(1)
    except:  # handle other exceptions
        print ("Unexpected error:", sys.exc_info()[0])
        exit(1)

doshow = False
# fill the plot lines with the data
if args.hideplot1 is False:
    figure_1 = plotter.figure(1)
    if len(args.title) > 0:
        figure_1.suptitle(args.title)
    axis_1 = figure_1.add_subplot(1, 1, 1)
    create_lines(axis_1, dict_lines, dict_colors)
    if fill_lines(dict_lines, dict_data):
        fit_plot(axis_1, dict_lines, dict_data)
        plotter.subplots_adjust(left=0.08, right=0.97, top=0.94, bottom=0.1)
        legend_values = []
        for key in legend_keys:
            legend_values.append(dict_lines[key])
        axis_1.legend(legend_values, legend_keys)
        doshow = True


# filtering expression and additional plots
if len(args.filter) > 0:
    # find the WHERE
    qry = str(args.filter)
    qrys = qry.split("WHERE")
    if len(qrys) == 2:
        plot_list = qrys[0]
        filter_expression = qrys[1]

        plot_list = plot_list.replace("SELECT", "")
        plot_list = plot_list.replace(" ", "")
        plots = plot_list.split(',')

        # build up the array query
        # replace column names with their dict entry
        key_order = plots
        for key_name in dict_data.keys():
            if filter_expression.find(key_name) >= 0:
                filter_expression = filter_expression.replace(key_name, "np.array(dict_data[\"" + key_name + "\"])")
                if key_name not in plots:
                    key_order.append(key_name)

        for key_name in key_order:
            dict_filter_lines[key_name] = None

        filter_expression = filter_expression.replace("AND", "&")
        filter_expression = filter_expression.replace("OR", "|")

        exe_str = "res = np.where(" + filter_expression + ")"
        res = []
        exec(exe_str)

        for key in key_order:
            dict_filter_data[key] = []

            for j in range(0, len(x_axis)):
                dict_filter_data[key].append(0)

            for arr in res:
                for idx in arr:
                    dict_filter_data[key][idx] = dict_data[key][idx]


        figure_filter = plotter.figure(2)
        if len(args.filtertitle) > 0:
            figure_filter.suptitle(args.filtertitle)
        axis_filter = figure_filter.add_subplot(1,1,1)

        create_lines(axis_filter, dict_filter_lines, dict_colors)
        if fill_lines(dict_filter_lines, dict_filter_data):
            fit_plot(axis_filter, dict_filter_lines, dict_filter_data)
            plotter.subplots_adjust(left=0.08, right=0.97, top=0.94, bottom=0.1)
            axis_filter.legend(dict_filter_lines.values(), dict_filter_lines.keys())
            doshow = True


if args.sessionstart:
    lockfile = open('csvsession.pickle.lock', 'w+')
    lockfile.close()
    with open("csvsession.pickle", "wb") as f:
        pickle.dump(dict_data, f)
        pickle.dump(x_axis, f)
        pickle.dump(dict_colors, f)
        pickle.dump(color_palette, f)

    
    if os.path.exists('csvsession.pickle.lock'):
        os.remove('csvsession.pickle.lock')

if args.terminate:
    exit(0)

dict_filter_data = None
dict_data = None
axis_1 = None
dict_colors = None

if doshow:
    plotter.show(True)

exit(0)



#!/usr/bin/python3

######################################################################
#  CSV Plotting Utility
#
#  ------------------------------------------------------------------
#  Author : Eric D. Schmidt
#  Language: Python 3
#  License: MIT
#  ------------------------------------------------------------------
#
#  Copyright (c) 2019 Eric D. Schmidt
######################################################################

import sys
import argparse
import random
import pickle
import time
import os
#import csv

import matplotlib.pyplot as plotter
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D
import numpy as np

class CSVAnalyzer:
    def __init__(self, columns, xaxis_label, colorbyplot, scatterplot):
        self.line_cnt = 0
        self.legend_keys = []
        self.color_palette = []
        self.dict_lines = {}
        self.dict_data = {}
        self.x_axis = []
        self.dict_colors = {}
        self.colorbyplot = colorbyplot
        self.columns_plot = columns
        self.scatter = scatterplot
        self.xaxis_label = xaxis_label

        self.figure_1 = None
        self.axis_1 = None

    def load_data(self, filename, rowstart, rowend, restore_pickle):
        if restore_pickle:
            self.restore_data()
        else:
            self.dict_data, self.x_axis = self.get_csv_data(
                filename, self.columns_plot, self.xaxis_label, rowstart, rowend)

    def get_data(self):
        return self.dict_data, self.x_axis
            
    def plot(self, title, filterstring):
        doplot = False

        for header in self.columns_plot:
            self.dict_lines[header] = None
            self.dict_colors[header] = ("black", 1)

        self.__assign_colors(self.dict_colors)

        # fill the plot lines with the data
        figure_1 = plotter.figure(1)
        if len(title) > 0:
            figure_1.suptitle(title)
        self.axis_1 = figure_1.add_subplot(1, 1, 1)
        self.__create_lines(self.axis_1, self.dict_lines, self.dict_colors)
        if self.__fill_lines(self.dict_lines, self.dict_data):
            self.__fit_plot(self.axis_1, self.dict_lines, self.dict_data)
            plotter.subplots_adjust(left=0.08, right=0.97, top=0.94, bottom=0.1)
            legend_values = []
            for key in self.legend_keys:
                legend_values.append(self.dict_lines[key])
            self.axis_1.legend(legend_values, self.legend_keys)
            doplot = True

        # filtering expression and highlighting plot
        if doplot and len(filterstring) > 0:
            self.dict_data[self.xaxis_label] = self.x_axis
            # find the WHERE
            qry = str(filterstring)
            qrys = qry.split("WHERE")
            if len(qrys) == 2:
                plot_list = qrys[0]

                plot_list = plot_list.replace("SELECT", "")
                plot_list = plot_list.replace(" ", "")
                tokens = qrys[1].split(' ')
                replacements = {}

                # build up the array query
                for key_name in self.dict_data.keys():
                    found_idx = 0
                    for token in tokens:
                        if token == key_name:
                            replacements[found_idx] = "np.array(dict_data[\"" + key_name + "\"])"
                        found_idx += 1

                filter_expression = ""
                for replacement in replacements:
                    tokens[replacement] = replacements[replacement]

                for token in tokens:
                    filter_expression += token + " "

                tokens = filter_expression.split("AND")
                if len(tokens) > 1:
                    filter_expression = ""
                    for token_idx in range(len(tokens)):
                        filter_expression += "(" + tokens[token_idx] + ") "
                        if token_idx < len(tokens) - 1:
                            filter_expression += " & "

                tokens = filter_expression.split("OR")
                if len(tokens) > 1:
                    filter_expression = ""
                    for token_idx in range(len(tokens)):
                        filter_expression += "(" + tokens[token_idx]+ ") "
                        if token_idx < len(tokens) - 1:
                            filter_expression += " | "

                exe_str = "res = np.where(" + filter_expression + ")"
            else:
                exe_str = "res = " + filterstring
            
            ldict = {}
            gdict = globals()
            gdict["dict_data"] = self.dict_data
            exec(exe_str, gdict, ldict)

            # hightlight the selected data range(s)
            if len(ldict["res"]) > 0:
                arr = ldict["res"][0]
                last_idx = -2
                min_x = np.amin(self.x_axis)
                max_x = min_x
                highlighted = False
                for idx in arr:
                    if last_idx != idx - 1:
                        if min_x != max_x:
                            plotter.axvspan(min_x, max_x, color='orange', alpha=0.5)
                            highlighted = True
                        min_x = self.x_axis[idx]
                    max_x = self.x_axis[idx]
                    last_idx = idx

                if not highlighted and min_x != max_x:
                    plotter.axvspan(min_x, max_x, color='orange', alpha=0.5)
    
        if doplot:
            plotter.show(block=True)


    def restore_data(self):
        print('restoring session data')
        # check if file is still being used
        while os.path.exists('csvsession.pickle.lock'):
            print("waiting for lock on pickle file")
            time.sleep(2)

        with open("csvsession.pickle", "rb") as f:
            self.dict_data = pickle.load(f)
            self.x_axis = pickle.load(f)
            self.dict_colors = pickle.load(f)
            self.color_palette = pickle.load(f)

    def serialize_pickle(self):
        # indicate that file is in use
        lockfile = open('csvsession.pickle.lock', 'w+')
        lockfile.close()
        with open("csvsession.pickle", "wb") as f:
            pickle.dump(self.dict_data, f)
            pickle.dump(self.x_axis, f)
            pickle.dump(self.dict_colors, f)
            pickle.dump(self.color_palette, f)

        if os.path.exists('csvsession.pickle.lock'):
            os.remove('csvsession.pickle.lock')

    def __add_line(self, axis, colname, lines_dict, color_dict):
        '''adds a line to the plot. Assigns color and style'''

        color_name = 'black'
        thickness = 0.4
        if self.colorbyplot:
            color_name = self.color_palette[self.line_cnt][0]
            thickness = self.color_palette[self.line_cnt][1]
        else:
            color_name = color_dict[colname][0]
            thickness = color_dict[colname][1]
        lines_dict[colname] = Line2D([], [], color=color_name, linewidth=thickness)
        axis.add_line(lines_dict[colname])
        self.line_cnt += 1

    def __create_lines(self, axis, lines_dict, color_dict):
        '''depending on plot type adds a line and legend entry to plot'''

        self.line_cnt = 0
        i = 0
        for col in self.columns_plot:
            if not self.scatter or i % 2 != 0:
                self.__add_line(axis, col, lines_dict, color_dict)
                self.legend_keys.append(col)
            i += 1


    def __assign_colors(self, color_dict):
        '''automatically pick good looking colors'''
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
        for color in color_dict:
            if cnt <= 2 and self.colorbyplot:
                if cnt == 0:
                    color_dict[color] = ("blue", start_thickness)
                elif cnt == 1:
                    color_dict[color] = ("red", start_thickness)
                elif cnt == 2:
                    color_dict[color] = ("green", start_thickness)
            else:
                luminosity = 1
                index = 0
                # we want dark lines
                while luminosity > 0.66:
                    index = random.randint(0, len(sorted_names) - 1)
                    color_name = sorted_names[index]
                    rgb = mcolors.to_rgba(color_name)
                    luminosity = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

                color_dict[color] = (color_name, thickness)
                if cnt % 2 == 0:
                    thickness += thickness_increment

            self.color_palette.append(color_dict[color])
            cnt += 1

    def __fill_lines(self, lines_dict, ydata_dict):
        '''fill lines with associated data'''
        if self.scatter:
            i = 0
            for col in self.columns_plot:
                if i % 2 == 0:
                    xdata = ydata_dict[col]
                    lines_dict.pop(col)
                else:
                    ydata = ydata_dict[col]
                    lines_dict[col].set_data(xdata, ydata)
                i += 1
        else:
            for line_name in lines_dict:
                ydata = ydata_dict[line_name]
                xdata = self.x_axis

                if not ydata is None:
                    lines_dict[line_name].set_data(xdata, ydata)
                else:
                    return False

        return True


    def __fit_plot(self, axis, lines, ydata_dict):
        '''figure out good bounding view for plot'''
        min_y = float('inf')
        max_y = float('-inf')
        min_x_axis = float('inf')
        max_x_axis = float('-inf')

        if self.scatter:
            i = 0
            for col in self.columns_plot:
                if i % 2 == 0:
                    min_x_axis = min(min_x_axis, min(ydata_dict[col]))
                    max_x_axis = max(max_x_axis, max(ydata_dict[col]))
                i += 1
        else:
            min_x_axis = self.x_axis[0]
            max_x_axis = self.x_axis[-1]

        for line_name in lines:
            if line_name in ydata_dict and len(ydata_dict[line_name]) > 0:
                min_y = min(min_y, min(ydata_dict[line_name]))
                max_y = max(max_y, max(ydata_dict[line_name]))

        if max_y != 0:
            max_y += 5

        if min_y != 0:
            min_y -= 5

        axis.set_ylim(min_y, max_y)
        axis.set_xlim(min_x_axis, max_x_axis)
        axis.set_xlabel(self.xaxis_label)
        axis.grid(True)


    def get_csv_data(self, filename, columns, xaxis_name, rowstart, rowend):
        '''parse the raw CSV data from the source file'''
        headers = {}
        data = {}
        xaxis = []

        for col in columns:
            data[col] = []

        row_count = 0
        row_num = 0
        idx_xaxis = -1

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
                        for col_idx, name in headers.items():
                            if col_idx == i:
                                data[name].append(float(ele))
                        if i == idx_xaxis:
                            xaxis.append(float(ele))
                        i += 1

                if idx_xaxis < 0 and row_num > 0:
                    xaxis.append(float(row_num - 1))

                row_num += 1

                if row_num % 100000 == 0:
                    print("processed %i rows of %i" % (row_num, row_count))

        return data, xaxis

def main():
    parser = argparse.ArgumentParser(description='Plot collection of variables for a csv file.')
    parser.add_argument('-f', '--file', metavar='FILE', type=str,
                        help='CSV file to plot')
    parser.add_argument('-x', '--xaxis', metavar='X_COL_NAME', type=str,
                        help='column name of x-axis')
    parser.add_argument('columns_plot', metavar='COL_NAME', type=str, nargs='+',
                        help='column name(s) of the plot items')
    parser.add_argument('-r', '--rowstart', metavar='STARTROW', type=int,
                        help='row start number', default=0)
    parser.add_argument('-e', '--rowend', metavar='ENDROW', type=int,
                        help='row end number (0 to end of file)', default=0)
    parser.add_argument('-t', '--filter', metavar='expression', type=str,
                        help='filtering expression', default='')
    parser.add_argument('-i', '--title', type=str,
                        help='title of plot', default='')
    parser.add_argument('-s', '--sessionstart', action='store_true',
                        help='starts a new session so we only load data & assign colors once',
                        default=False)
    parser.add_argument('-c', '--sessioncontinue', action='store_true',
                        help='Continues an existing session so we only load data & assign colors once',
                        default=False)
    parser.add_argument('-m', '--terminate', action='store_true',
                        help='Closes immediately after data load and session save',
                        default=False)
    parser.add_argument('--scatter', action='store_true',
                        help='Create scatter plots from pairs of values', default=False)
    parser.add_argument('--colorbyplot', action='store_true',
                        help='Keep plot color scheme consistent by plot order', default=False)

    args = parser.parse_args()
    xaxis_label = ""

    if len(args.file) == 0 or len(args.columns_plot) == 0:
        parser.print_help()
        exit(1)

    if not args.xaxis is None and len(args.xaxis) != 0:
        xaxis_label = args.xaxis
    else:
        col_cnt = 0
        for key in args.columns_plot:
            if col_cnt % 2 == 0:
                if len(xaxis_label) > 0:
                    xaxis_label += ","
                xaxis_label += key
            col_cnt += 1

    try:
        analyzer = CSVAnalyzer(args.columns_plot, xaxis_label, args.colorbyplot, args.scatter)
        analyzer.load_data(args.file, args.rowstart, args.rowend, args.sessioncontinue)
    except IOError as err:
        print("I/O error({0}): {1}".format(err.errno, err.strerror))
        exit(1)
    except:  # handle other exceptions
        print("Unexpected error:", sys.exc_info()[0])
        exit(1)


    # serialize data so we can reload CSV data from the pickle file later
    if args.sessionstart:
        analyzer.serialize_pickle()

    if args.terminate:
        exit(0)

    analyzer.plot(args.title, args.filter)

    exit(0)


if __name__ == "__main__":
    main()

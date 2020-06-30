import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plot
import sys
import argparse
import math

def smoothData(rawData, smooth):
    if smooth > 0:
        smoothed = [sum(rawData[0:smooth+1])/(smooth+1)]
        for i in range(smooth+1, len(rawData)):
            newSmoothed = smoothed[-1] - (rawData[i - smooth - 1] - rawData[i])/(smooth+1)
            smoothed.append(newSmoothed)

        return smoothed
    else:
        return rawData

parser = argparse.ArgumentParser(description='Display learning curves from the given file(s).')

parser.add_argument('files', metavar='file', nargs='+', help='file containing the score for each episode in a column.')
parser.add_argument('-i', '--ignoreheadings', action='store_true', default=False, help='ignore the first line of the input file.')
parser.add_argument('-c', '--column', type=int, default=[1], nargs='+', help='the column in the files that contains the learning data (default: %(default)s).')
parser.add_argument('-s', '--smooth', type=int, default=1, help='the size of the smoothing window (default: %(default)s, which is no smoothing).')
parser.add_argument('-a', '--avg', action='store_true', default=False, help='display the average curve of the given files (rather than each curve individually). Episodes not contained in all files will be displayed in red.')
parser.add_argument('-r', '--raw', action='store_true', default=False, help='display the raw data as well as the smoothed data.')
parser.add_argument('-t', '--timesteps', metavar='COLUMN', type=int, default=0, help='uses the number of steps from the supplied column to display learning versus number of steps rather than number of episodes (has no effect when combined with -a).')
parser.add_argument('-d', '--denominators', type=int, default=[], nargs='+', help='values in data column will be divided by values in this column.')
parser.add_argument('-l', '--title', metavar='TITLE', type=str, default=[], nargs='+', help='The title to display for this graph.')
parser.add_argument('-u', '--units', type=str, default=[], nargs='+', help='This string will label the y-axis (default: Score").')
parser.add_argument('-y', '--ylim', type=float, default = [], nargs='+', help='Fixes the limits of the y-axis', metavar=('MIN', 'MAX'))
parser.add_argument('-x', '--xlim', type=float, default = [], nargs='+', help='Fixes the limits of the x-axis', metavar=('MIN', 'MAX'))

args = parser.parse_args()

if len(args.ylim)%2 != 0 or len(args.xlim)%2 != 0:
    print("Number of arguments to -x and -y must be even")
    exit(1)

stepCol = args.timesteps - 1

numCols = len(args.column)
if numCols > 1:
    numPlotRows = int(math.sqrt(numCols));
    numPlotCols = math.ceil(numCols/numPlotRows)
else:
    numPlotRows = 1
    numPlotCols = 1

plot.ion();

print(numCols, numPlotRows, numPlotCols)
fig, axes = plot.subplots(nrows=numPlotRows, ncols=numPlotCols)

for c in range(numCols):
    axesR = c//numPlotCols
    axesC = c%numPlotCols
    print("Plot " + str(axesR) + ", " + str(axesC))
    
    column = args.column[c] - 1
    smooth = args.smooth - 1

    denomCol = 0
    if len(args.denominators) > c:
        denomCol = args.denominators[c] - 1

    title = ""
    if len(args.title) > c:
        title = args.title[c]

    units = "Score"
    if len(args.units) > c:
        units = args.units[c]

    xlim = None
    ylim = None
    if args.xlim != None and len(args.xlim) > 2*c:
        xlim = [args.xlim[2*c], args.xlim[2*c+1]]
    if args.ylim != None and len(args.ylim) > 2*c:
        ylim = [args.ylim[2*c], args.ylim[2*c+1]]        

    data = []
    steps = []
    maxLength = 0
    minLength = -1
    for filename in args.files:
        data.append([])
        if stepCol >= 0:
            steps.append([])
            curStep = 0

        try:
            fin = open(filename, 'r')
            heading = ""
            if args.ignoreheadings:
                headings = fin.readline().split();
                heading = headings[column]
                if denomCol > 0:
                    heading += "/" + headings[denomCol]
            print(str(len(data)) + ": " + filename + " -- " + heading)
            for line in fin:
                denom = 1
                if denomCol > 0:
                    denom = float(line.split()[denomCol])
                    if denom == 0:
                        denom = 1
                score = float(line.split()[column])/denom
                if stepCol >= 0:
                    step = int(line.split()[stepCol])
                    curStep += step
                    steps[-1].append(curStep)
                data[-1].append(score)
            fin.close()
        except Exception as inst:
            sys.stderr.write("Error reading " + filename + "\n")
            sys.stderr.write(str(inst) + "\n")

        if len(data[-1]) > maxLength:
            maxLength = len(data[-1])

        if minLength < 0 or len(data[-1]) < minLength:
            minLength = len(data[-1])

    if maxLength == 0:
        sys.stderr.write("No data to graph!\n")
        exit(1)

    if args.avg:
        avgData = []
        for i in range(maxLength):
            total = 0
            count = 0
            for j in range(len(data)):
                if i < len(data[j]):
                    total += data[j][i]
                    count += 1
            avgData.append(total/count)

        if args.raw:
            axes[axesR][axesC].plot(range(minLength), avgData[:minLength], color='0.75', label='Avg. data')
            axes[axesR][axesC].plot(range(minLength, len(avgData)), avgData[minLength:], color='lightcoral')

        if minLength > smooth:
            smoothed = smoothData(avgData, smooth)
            axes[axesR][axesC].plot(range(smooth, minLength), smoothed[:minLength-smooth], color='black')
            axes[axesR][axesC].plot(range(minLength, len(avgData)), smoothed[minLength-smooth:], color='red')
    else:
        if args.raw:
            for i in range(len(data)):
                rawData = data[i]
                xCoords = range(len(rawData))
                if stepCol >= 0:
                    xCoords = steps[i]
                axes[axesR][axesC].plot(xCoords, rawData, color='0.75', label='Raw')

        axes[axesR][axesC].set_prop_cycle('color', [plot.cm.jet(i) for i in np.linspace(0.1, 0.9, len(data))])

        for i in range(len(data)):
            rawData = data[i]
            if len(rawData) > smooth:
                smoothed = smoothData(rawData, smooth)
                xCoords = range(smooth, len(rawData))
                if stepCol >= 0:
                    xCoords = steps[i][smooth:]
                axes[axesR][axesC].plot(xCoords, smoothed, label=str(i+1))

    if stepCol >= 0:
        axes[axesR][axesC].set_xlabel("Timestep")
    else:
        axes[axesR][axesC].set_xlabel("Episode")
    axes[axesR][axesC].set_ylabel(units)
    axes[axesR][axesC].set_title(title)
    axes[axesR][axesC].legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.0)
    if ylim != None:
        axes[axesR][axesC].ylim(ymin=ylim[0], ymax=ylim[1])
    if xlim != None:
        axes[axesR][axesC].xlim(xmin=xlim[0], xmax=xlim[1])
plot.tight_layout()
plot.draw()
input("<press enter>")

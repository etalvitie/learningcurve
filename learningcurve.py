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
parser.add_argument('-c', '--column', type=int, default=[1], nargs='+', help='Sets the columns in the files that contain data to be plotted. Multiple provided columns will yield subplots, one for each column (default: 1).')
parser.add_argument('-s', '--smooth', type=int, default=1, help='the size of the smoothing window (default: %(default)s, which is no smoothing).')
parser.add_argument('-a', '--avg', default=None, type=int, nargs='*', metavar='NUM', help='display the average curve of the given files (rather than each curve individually). Episodes not contained in all files will be displayed in a lighter color. Arguments define groups of files to be averaged (so, -a 4 3 will separately average the first 4 files, the following 3 files, and the remainder of the files). When no arguments are provided all files will be averaged together.')
parser.add_argument('-r', '--raw', action='store_true', default=False, help='display the raw data as well as the smoothed data.')
parser.add_argument('-t', '--timesteps', metavar='COLUMN', type=int, default=0, help='uses the number of steps from the supplied column to display learning versus number of steps rather than number of episodes (has no effect when combined with -a).')
parser.add_argument('-d', '--denoms', type=int, default=[], nargs='+', help='Values in data column will be divided by values in this column. Multiple values will be matched with corresponding data columns (give 0 to indicate no denominator).')
parser.add_argument('-l', '--title', metavar='TITLE', type=str, default=[], nargs='+', help='The titles to display for the subplots (default title is blank).')
parser.add_argument('-u', '--units', type=str, default=[], nargs='+', help='These strings will label the y-axes of the subplots (default label is Score").')
parser.add_argument('-y', '--ylim', type=float, default = [], nargs='+', help='Sets the limits of the y-axes. Set MIN = MAX to use default axis limits.', metavar=('MIN MAX'))
parser.add_argument('-x', '--xlim', type=float, default = [], nargs='+', help='Sets the limits of the x-axes. Set MIN = MAX to use default axis limits.', metavar=('MIN MAX'))

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

print(numCols, numPlotRows, numPlotCols)
fig, axes = plot.subplots(nrows=numPlotRows, ncols=numPlotCols, squeeze=False)

for c in range(numCols):
    axesR = c//numPlotCols
    axesC = c%numPlotCols
    print("Plot " + str(axesR) + ", " + str(axesC))
    
    column = args.column[c] - 1
    smooth = args.smooth - 1

    denomCol = 0
    if len(args.denoms) > c:
        denomCol = args.denoms[c] - 1

    title = ""
    if len(args.title) > c:
        title = args.title[c]

    units = "Score"
    if len(args.units) > c:
        units = args.units[c]

    xlim = None
    ylim = None
    if args.xlim != []:
        if len(args.xlim) > 2*c and args.xlim[2*c] != args.xlim[2*c+1]:
            xlim = [args.xlim[2*c], args.xlim[2*c+1]]
        else:
            xlim = [args.xlim[-2], args.xlim[-1]]
    if args.ylim != []:
        if len(args.ylim) > 2*c and args.ylim[2*c] != args.ylim[2*c+1]:
            ylim = [args.ylim[2*c], args.ylim[2*c+1]]
        else:
            ylim = [args.ylim[-2], args.ylim[-1]]

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
                if len(args.units) <= c:
                    units = heading
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

    if args.avg != None:
        if args.avg == []:
            args.avg.append(len(data))
        numDiv = len(args.avg)
        if sum(args.avg) < len(data):
            numDiv += 1
        axes[axesR][axesC].set_prop_cycle('color', [plot.cm.jet(i) for i in np.linspace(0.1, 0.9, numDiv)])
        fileIdx = 0
        groupIdx = 0
        while fileIdx < len(data):
            if groupIdx < len(args.avg):
                g = args.avg[groupIdx]
            else:
                g = len(data) - fileIdx
            avgData = []
            someData = True
            i = 0
            maxLength = len(data[fileIdx])            
            minLength = len(data[fileIdx])
            for f in range(fileIdx+1, fileIdx+g):
                if len(data[f]) > maxLength:
                    maxLength = len(data[f])
                if len(data[f]) < minLength:
                    minLength = len(data[f])
            
            for i in range(maxLength):
                total = 0
                count = 0
                for j in range(fileIdx, fileIdx+g):
                    if i < len(data[j]):
                        total += data[j][i]
                        count += 1
                avgData.append(total/count)

            if args.raw:
                axes[axesR][axesC].plot(range(minLength), avgData[:minLength], color='0.75', label='Raw Avg.')
                axes[axesR][axesC].plot(range(minLength, len(avgData)), avgData[minLength:], color='0.85', label='Raw Inc.')

            if minLength > smooth:
                smoothed = smoothData(avgData, smooth)
                p = axes[axesR][axesC].plot(range(smooth, minLength), smoothed[:minLength-smooth], label='Avg. (' + str(fileIdx) + '-' + str(fileIdx+g) + ')')
                color = p[0].get_color()
                lighter = (color[0], color[1], color[2], 0.25)
                axes[axesR][axesC].plot(range(minLength, len(avgData)), smoothed[minLength-smooth:], color=lighter, label='Inc. (' + str(fileIdx) + '-' + str(fileIdx+g) + ')')

            fileIdx += g
            groupIdx += 1

    else: #args.avg == None
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

    if stepCol >= 0 and not args.avg:
        axes[axesR][axesC].set_xlabel("Timestep")
    else:
        axes[axesR][axesC].set_xlabel("Episode")
    axes[axesR][axesC].set_ylabel(units)
    axes[axesR][axesC].set_title(title)
    if ylim != None:
        axes[axesR][axesC].set_ylim(ymin=ylim[0], ymax=ylim[1])
    if xlim != None:
        axes[axesR][axesC].set_xlim(xmin=xlim[0], xmax=xlim[1])
axes[0][numPlotCols - 1].legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.0)
cfm = plot.get_current_fig_manager()
cfm.resize(*cfm.window.maxsize())
plot.tight_layout()
fig.set_tight_layout(True)
plot.show()

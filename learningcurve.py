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

parser.add_argument('files', metavar='FILE', nargs='*', help='file containing the score for each episode in a column.')
parser.add_argument('-i', '--ignoreheadings', action='store_true', default=False, help='ignore the first line of the input file.')
parser.add_argument('-c', '--column', type=int, default=[1], nargs='+', help='Sets the columns in the files that contain data to be plotted. Multiple provided columns will yield subplots, one for each column (default: 1).')
parser.add_argument('-s', '--smooth', type=int, default=1, help='the size of the smoothing window (default: %(default)s, which is no smoothing).')
#parser.add_argument('-a', '--avg', default=None, type=int, nargs='*', metavar='NUM', help='display the average curve of the given files (rather than each curve individually). Episodes not contained in all files will be displayed in a lighter color. Arguments define groups of files to be averaged (so, -a 4 3 will separately average the first 4 files, the following 3 files, and the remainder of the files). When no arguments are provided all files will be averaged together.')
parser.add_argument('-a', '--avg', action='append', type=str, nargs='+', metavar='FILE', help='The provided files will be averaged together. This option can be used multiple times to create multiple groups to be averaged together.')
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

fileGroups = []
for f in args.files:
    fileGroups.append([f])

for g in args.avg:
    fileGroups.append(g)

if len(fileGroups) == 0:
    print("No files given!")
    exit(1)

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

    fileIdx = 1

    axes[axesR][axesC].set_prop_cycle('color', [plot.cm.jet(i) for i in np.linspace(0.1, 0.9, len(fileGroups))])
    
    for group in fileGroups:
        data = []
        steps = []
        for filename in group:            
            data.append([])
            if stepCol >= 0:
                steps.append([])
                curStep = 0

            try:
                fin = open(filename, 'r')
                fileInfo = str(fileIdx) + ": " + filename
                if args.ignoreheadings:
                    headings = fin.readline().split();
                    heading = headings[column]
                    fileInfo += " -- " + heading
                    if denomCol > 0:
                        fileInfo += "/" + headings[denomCol]
                    if len(args.units) <= c:
                        units = heading
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
                fileInfo += " (" + str(len(data[-1])) + " eps"
                if stepCol >= 0:
                    fileInfo += ", " + str(steps[-1][-1]) + " frames"
                fileInfo += ")"
                print(fileInfo)
                fin.close()
            except Exception as inst:
                sys.stderr.write("Error reading " + filename + "\n")
                sys.stderr.write(str(inst) + "\n")

            smoothed = []
            xCoords = []
            for i in range(len(data)):
                if len(data[i]) > smooth:
                    smoothed.append(smoothData(data[i], smooth))
                    if stepCol > 0:
                        xCoords.append(steps[i][smooth:])
                    else:
                        xCoords.append(list(range(smooth, len(data[i]))))
                else:
                    smoothed.append([])
                    xCoords.append([])

            combinedXCoords = []
            avgData = []
            indices = [0]*len(smoothed)
            numComplete = 0
            remainingIndices = [i for i in range(len(indices)) if indices[i] < len(smoothed[i])]
            while len(remainingIndices) > 0:
                curX = [xCoords[i][indices[i]] for i in remainingIndices]                    
                curY = [smoothed[i][indices[i]] for i in remainingIndices]
                minX = min(curX)
                combinedXCoords.append(minX)                    
                avgData.append(sum(curY)/len(curY))
                if len(remainingIndices) == len(group):
                    numComplete += 1
                minXIndices = [i for i in range(len(curX)) if curX[i] == minX]
                for idx in minXIndices:
                    indices[remainingIndices[idx]] += 1
                remainingIndices = [i for i in range(len(indices)) if indices[i] < len(smoothed[i])]
            fileIdx += 1

        p = axes[axesR][axesC].plot(combinedXCoords[:numComplete], avgData[:numComplete], label='Avg. (' + str(fileIdx-len(group)) + '-' + str(fileIdx-1) + ')')
        color = p[0].get_color()
        lighter = (color[0], color[1], color[2], 0.25)
        axes[axesR][axesC].plot(combinedXCoords[numComplete:], avgData[numComplete:], color=lighter, label='Inc. (' + str(fileIdx-len(group)) + '-' + str(fileIdx-1) + ')')
        print('---')
        
    if stepCol >= 0:
        axes[axesR][axesC].set_xlabel("Timestep")
    else:
        axes[axesR][axesC].set_xlabel("Episode")
    axes[axesR][axesC].set_ylabel(units)
    axes[axesR][axesC].set_title(title)
    if ylim != None:
        axes[axesR][axesC].set_ylim(ymin=ylim[0], ymax=ylim[1])
    if xlim != None:
        axes[axesR][axesC].set_xlim(xmin=xlim[0], xmax=xlim[1])

handles, labels = axes[0][0].get_legend_handles_labels()
legend = fig.legend(handles, labels, loc='upper right')
bbox = legend.get_window_extent(fig.canvas.get_renderer()).transformed(fig.transFigure.inverted())
cfm = plot.get_current_fig_manager()
cfm.resize(*cfm.window.maxsize())
fig.set_tight_layout({"rect":(0, 0, (bbox.x0+bbox.x1)/2, 1), "h_pad":0.3, "w_pad":0.3})
plot.show()

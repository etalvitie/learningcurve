import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plot
import sys
import argparse
import math

# Takes a list of data and smooths it
# Each entry in the resulting list is the average smooth entries in the given list
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
parser.add_argument('-a', '--avg', action='append', type=str, nargs='+', metavar='FILE', help='The provided files will be averaged together. This option can be used multiple times to create multiple groups to be averaged together.')
parser.add_argument('-e', '--error', action='store_true', default=False, help='display standard error of averages')
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

fig, axes = plot.subplots(nrows=numPlotRows, ncols=numPlotCols, squeeze=False)

fileGroups = []
for f in args.files: # First the individual files
    fileGroups.append([f])

for g in args.avg: # Then the averaging groups
    fileGroups.append(g)

if len(fileGroups) == 0:
    print("No files given!")
    exit(1)

# Read the files
data = []
steps = []
allUnits = []
labels = []
fileIdx = 1
for g in range(len(fileGroups)):
    group = fileGroups[g]
    print("Group " + str(g) + ": " + str(len(group)) + " files")
    data.append([])
    steps.append([])
    if len(group) > 1:
        labels.append('Avg. (' + str(fileIdx) + '-' + str(fileIdx+len(group)-1) + ')')
    else:
        labels.append('File ' + str(fileIdx))

    for filename in group:        
        data[-1].append([[] for i in range(numCols)])
        if stepCol >= 0:
            steps[-1].append([])
            curStep = 0

        try:
            fin = open(filename, 'r')

            # Figure out the units for different columns
            # (Silly to do this for every file but...here we are)
            if args.ignoreheadings: # We'll use the column headings from the file
                allHeadings = fin.readline().split();
                selectedHeadings = []
                for c in range(numCols):
                    column = args.column[c] - 1
                    selectedHeadings.append(allHeadings[column])
                    if len(args.denoms) > c:
                        selectedHeadings[-1] += "/" + allHeadings[args.denoms[c]-1]
                allUnits = selectedHeadings
            else: # We'll just label things with the column number
                selectedUnits = []
                for c in range(numCols):
                    selectedUnits.append("Col " + str(args.column[c]))
                    if len(args.denoms) > c:
                        selectedUnits[-1] += " / Col " + str(args.denoms[c])
                allUnits = selectedUnits

            #Read from the file
            for line in fin:
                for c in range(numCols):
                    denom = 1
                    if len(args.denoms) > c:
                        denomCol = args.denoms[c] - 1
                        denom = float(line.split()[denomCol])
                    score = float(line.split()[args.column[c]-1])/denom
                    data[-1][-1][c].append(score)
                if stepCol >= 0:
                    step = int(line.split()[stepCol])
                    curStep += step
                    steps[-1][-1].append(curStep)

            fileInfo = str(fileIdx) + ": " + filename
            fileInfo += " (" + str(len(steps[-1][-1])) + " eps"
            if stepCol >= 0:
                fileInfo += ", " + str(steps[-1][-1][-1]) + " frames"
            fileInfo += ")"
            print(fileInfo)
            
            fin.close()

        except Exception as inst:
            sys.stderr.write("Error reading " + filename + "\n")
            sys.stderr.write(str(inst) + "\n")

        fileIdx += 1
    print('---')

#Plot the curves
for c in range(numCols):
    # Which plot are we talking about?
    axesR = c//numPlotCols
    axesC = c%numPlotCols

    # How much should we smooth?
    smooth = args.smooth - 1

    title = ""
    if len(args.title) > c:
        title = args.title[c]

    # Units will be on the y-axis label
    units = allUnits[c]
    if len(args.units) > c:
        units = args.units[c]

    plotInfo = "Plot " + str(axesR) + ", " + str(axesC) + ": " 
    if title == "":
        plotInfo += units
    else:
        plotInfo += title
    print(plotInfo)

    # What are the axis limits of the plot?
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

    # Automate color selection for curves
    axes[axesR][axesC].set_prop_cycle('color', [plot.cm.jet(i) for i in np.linspace(0.1, 0.9, len(fileGroups))])

    fileIdx = 0
    for g in range(len(data)):
        #First smooth the data
        smoothed = []
        xCoords = []
        for i in range(len(data[g])):
            if len(data[g][i][c]) > smooth:
                smoothed.append(smoothData(data[g][i][c], smooth))
                if stepCol > 0: # Use total steps as x-coordinates
                    xCoords.append(steps[g][i][smooth:])
                else: # Use num episodes as x-coordinates
                    xCoords.append(list(range(smooth, len(data[g][i][c])))) 
            else:
                smoothed.append([])
                xCoords.append([])

        #Compute the averages
        combinedXCoords = []
        avgData = []
        upperErr = []
        lowerErr = []
        indices = [0]*len(smoothed)
        numComplete = 0
        remainingIndices = [i for i in range(len(indices)) if indices[i] < len(smoothed[i])]
        while len(remainingIndices) > 0:
            # Find the x-coordinate for this data point
            # If using num episodes, this is just the next episode index
            # If using total steps, it's the number of steps all the trials have just crossed
            curX = [xCoords[i][indices[i]] for i in remainingIndices]                    
            minX = min(curX)
            combinedXCoords.append(minX)

            # Find the y-coordinate for this data point (average)
            curY = [smoothed[i][indices[i]] for i in remainingIndices]
            sampleAvg = sum(curY)/len(curY)
            avgData.append(sampleAvg)

            # Find the standard error for the average
            if args.error:
                if len(curY) > 1:
                    sqErrs = [(y - sampleAvg)*(y - sampleAvg) for y in curY]
                    stdDev = math.sqrt(sum(sqErrs)/(len(curY)-1))
                else:
                    stdDev = 0
                stdErr = stdDev/math.sqrt(len(curY))
                upperErr.append(sampleAvg+stdErr)
                lowerErr.append(sampleAvg-stdErr)
            
            if len(remainingIndices) == len(data[g]): # Else: we are averaging a subset
                numComplete += 1
            minXIndices = [i for i in range(len(curX)) if curX[i] == minX]
            for idx in minXIndices:
                indices[remainingIndices[idx]] += 1
            remainingIndices = [i for i in range(len(indices)) if indices[i] < len(smoothed[i])]

        # Plot the averages that use all trials
        p = axes[axesR][axesC].plot(combinedXCoords[:numComplete], avgData[:numComplete], label=labels[g], zorder=2)
        color = p[0].get_color()
        # Plot the averages that use a subset
        lighter = (color[0], color[1], color[2], 0.35)
        axes[axesR][axesC].plot(combinedXCoords[numComplete:], avgData[numComplete:], color=lighter, zorder=2)
        if len(data[g]) > 1 and args.error:
            # Plot the standard error for averages of all trials
            evenLighter = (color[0], color[1], color[2], 0.25)
            axes[axesR][axesC].fill_between(combinedXCoords[:numComplete], lowerErr[:numComplete], upperErr[:numComplete], color=evenLighter, zorder=1)
            # Plot the standard error for averages of a subset
            reallyLight = (color[0], color[1], color[2], 0.15)
            axes[axesR][axesC].fill_between(combinedXCoords[numComplete:], lowerErr[numComplete:], upperErr[numComplete:], color=reallyLight, zorder=1)

        fileIdx += len(data[g])

    #Labels and titles
    if stepCol >= 0:
        axes[axesR][axesC].set_xlabel("Timestep")
    else:
        axes[axesR][axesC].set_xlabel("Episode")
    axes[axesR][axesC].set_ylabel(units)
    axes[axesR][axesC].set_title(title)

    #Axis limits
    if ylim != None:
        axes[axesR][axesC].set_ylim(ymin=ylim[0], ymax=ylim[1])
    if xlim != None:
        axes[axesR][axesC].set_xlim(xmin=xlim[0], xmax=xlim[1])

#Place the legend. Try to keep it from overlapping...
handles, labels = axes[0][0].get_legend_handles_labels()
legend = fig.legend(handles, labels, loc='upper right')
bbox = legend.get_window_extent(fig.canvas.get_renderer()).transformed(fig.transFigure.inverted())

fig.set_size_inches((4*numPlotCols, 3*numPlotRows))

#Resize things to fit
fig.set_tight_layout({"rect":(0, 0, (bbox.x0+bbox.x1)/2, 1), "h_pad":0.3, "w_pad":0.3})
plot.show()

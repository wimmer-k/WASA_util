#!/usr/bin/python3
from PyQt5.QtWidgets import *
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import numpy as np
import sys
import time
import datetime
from signal import signal, SIGINT
import matplotlib.dates as mdates
filename = "csiHV.log"
ndev = 6
nch = 4
# names of channels
namedet = ["Ch 4", "Ch 5", "Ch 6", "Ch 7"]
# device 4 (counting from 1 is not in use)
donotdraw = [3]
threshold = 100

class HVDisplay(QMainWindow):
    def __init__(self, parent=None):
        super(HVDisplay, self).__init__()
        self.parent = parent
        self.centralWidget = QWidget()
        self.resize(1200,600)
        self.setCentralWidget(self.centralWidget)
        self.layout = QVBoxLayout()
        self.buttonS = QPushButton('start')
        self.buttonT = QPushButton('stop')
        self.myscene= DeviceDisplay(self)
        self.layout.addWidget(self.buttonS)
        self.layout.addWidget(self.buttonT)
        self.layout.addWidget(self.myscene)
        self.centralWidget.setLayout(self.layout)
        self.buttonS.clicked.connect(self.start)
        self.buttonT.clicked.connect(self.stop)

    def start(self):
        print("pressed start")
        self.myscene.run(filename)
        self.myscene.stopped = False

    def stop(self):
        print("pressed stop")
        self.myscene.stopped = True

class DeviceDisplay(QGraphicsView):
    def __init__(self, parent=None):
        super(DeviceDisplay, self).__init__(parent)
        self.parent=parent
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.figure = Figure(facecolor='white')
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        
        self.alarm = [False for d in range(ndev)]
        self.stopped = False
        self.live = True
        self.lines = [[] for d in range(ndev)]
        self.ax = [0 for d in range(ndev)]

        # date formatting
        formatter = mdates.DateFormatter("%d/%m %H:%M:%S")
        
        for j in range(ndev):
            self.ax[j] = self.figure.add_subplot(231+j)
            for i in range(nch):
                l, = self.ax[j].plot([],[], linewidth=0, marker='.', label=namedet[i])
                self.lines[j].append(l)
        
            # autoscale on unknown axis
            self.ax[j].set_autoscaley_on(True)
            self.ax[j].grid()
            self.ax[j].set_title('Device %d' % (j+1))
            self.ax[j].set_xlabel("Time", fontsize = 16)
            self.ax[j].set_ylabel("Voltage", fontsize = 16)
            self.ax[j].xaxis.set_major_formatter(formatter)

        
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.figure.tight_layout()

        
        self.figure.autofmt_xdate()
        handles, labels = self.ax[0].get_legend_handles_labels()
        self.figure.legend(handles, labels,loc="upper right", ncol=2, bbox_to_anchor=(0.98, 0.98))

    def onRunning(self, xdata, ydata):
        #print("updating plot")
        
        # plot all points
        for d in range(ndev):
            if d in donotdraw:
                continue
            onedayago = xdata[d][0][-1] + datetime.timedelta(hours = -24)
            #print(d)
            for i in range(nch):
                self.lines[d][i].set_data(xdata[d][i],ydata[d][i])
        
            # rescale plot
            if onedayago > xdata[d][0][0]:
                self.ax[d].set_xlim(xmin =onedayago, xmax= xdata[-1]+ datetime.timedelta(hours = 0.5))
        
            # check for alarm
            if self.alarm[d]:
                self.ax[d].set_facecolor("red")

            self.ax[d].relim()
            self.ax[d].autoscale_view()
            self.ax[d].autoscale()
        self.figure.tight_layout()
        self.canvas.draw()
        self.canvas.flush_events()

    def run(self,filename):        
        xdata = [[[] for i in range(nch)] for d in range(ndev)]
        ydata = [[[] for i in range(nch)] for d in range(ndev)]
        print("start updating from file ", filename)
        # read existing data
        datafile = open(filename, "r")
        for x in datafile.readlines():
            x = x.split()
            #check if line has date
            if len(x) == 2 and x[0][:4] == "2022":
                dateword = x[0]
                timeword = x[1]
                date_time_obj = datetime.datetime.strptime(dateword+" "+timeword, '%Y-%m-%d %H:%M:%S')
            elif len(x) == 9:
                d = int(x[0])-1
                if d in donotdraw:
                    continue
                for m in range(1, len(x)-1,2):
                    ydata[d][int(x[m])-4].append(float(x[m+1]))
                    xdata[d][int(x[m])-4].append(date_time_obj)
        self.onRunning(xdata, ydata) 

        if self.live:
            # keep reading from end of file
            l = self.readnewfromfile(datafile)
            for x in l:
                #print(x)
                if self.stopped:
                    print("stop updating")
                    return
                x = x.split()
                # check if line has date
                if len(x) == 2 and x[0][:4] == "2022":
                    dateword = x[0]
                    timeword = x[1]
                    date_time_obj = datetime.datetime.strptime(dateword+" "+timeword, '%Y-%m-%d %H:%M:%S')
                # otherwise there should be 9 values, device number, followed by nch times channel ID and value
                elif len(x) == 1+nch*2:
                    d = int(x[0])-1
                    if d in donotdraw:
                        continue
                    for m in range(1, len(x)-1,2):
                        ydata[d][int(x[m])-4].append(float(x[m+1]))
                        xdata[d][int(x[m])-4].append(date_time_obj)
                        # if value crosses thresold, set the alarm condition for device d
                        if float(x[m+1]) > threshold:
                            self.alarm[d] = True
                    # plot the new data
                    self.onRunning(xdata, ydata)
                    time.sleep(0.1)

    # read a new line from the file
    def readnewfromfile(self, datafile):
        # end of file
        datafile.seek(0,2) 
        while True:
            line = datafile.readline()
            if not line:
                # wait
                #time.sleep(5) 
                time.sleep(0.1) 
                continue
            yield line

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = HVDisplay(app)
    window.setWindowTitle('CsI HV Monitor')
    window.show()
    sys.exit(app.exec_( ))

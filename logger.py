#!/usr/bin/python3
import sys,os 
import time
import datetime
import subprocess
from signal import signal, SIGINT

verbose = True # False # 
ndev = 6
nch = 4

donotuse = [4]
deltaMinutes = 10
donotread = [[3,5], [3,6], [3,7], [5,7], [6,7]]

def handler(signal_received, frame):
    # close file here?
    print('CTRL-C pressed')
    exit(0)

def logHVstatus(logfile, now):
    logfile.write(str(now.strftime('%Y-%m-%d %H:%M:%S'))+'\n' )
    #for d in range(2,3):
    for d in range(1,1+ndev):
        if d in donotuse:
            continue
        if verbose:
            print("Device: ", d)
        logfile.write('%d' %d)

        # run the process with input command 'p' and pipe the stdout
        retval = subprocess.run(['/home/wasa/csihv', '/dev/ttyUSB%d' %d], stdout=subprocess.PIPE, input ='p\n'.encode('utf-8'))
        retval = retval.stdout.decode('utf-8')
        val = retval.split()
            
        # assuming that there are always ch, value pairs and a Ok at the end
        # print a warning if Ok tag is not found
        if len(val) < 1 or val[-1] != 'Ok' or len(val)%2 !=1:
            print("\033[1;31;40m WARNING  \033[0;0m")
            print("command return was:")
            print(retval)
            print("------------------")
            logfile.write('\n')
            continue

        # write values to file
        for m in range(0, (len(val)-1),2):
            if verbose:
                print(m,val[m],val[m+1])
                    
            logfile.write('\t%s\t%s' % (val[m],val[m+1]))
        logfile.write('\n')
        logfile.flush()
    
def logHVread(logfile):
    #for d in range(1,2):
    for d in range(1,1+ndev):
        if d in donotuse:
            continue
        if verbose:
            print("Device: ", d)
        logfile.write('Device %d\n' %d)
        for c in range(nch):
            if [d,c-4] in donotread:
                continue
            now =  datetime.datetime.now()
            # run the process with input command 'RX' and pipe the stdout
            command = 'R%d\n' % c
            # attention, this command gives the return on stderr
            retval = subprocess.run(['/home/wasa/csihv', '/dev/ttyUSB%d' %d], stderr=subprocess.PIPE, input =command.encode('utf-8'))
            retval = retval.stderr.decode('utf-8')
            if verbose:
                print("Branch: ",c)
                print(retval[4:])
            logfile.write(str(now.strftime('%Y-%m-%d %H:%M:%S'))+'\n' )
            logfile.write('Branch %d\n' %c)
            logfile.write(retval[4:])
            logfile.flush()
        logfile.write('-------------------------------------------------------------------------------\n')
        logfile.flush()
    logfile.write('-------------------------------------------------------------------------------\n')
    logfile.flush()

def main(argv):
    # define signal handler
    signal(SIGINT, handler)
    
    # current time
    now = datetime.datetime.now()
    
    # prepare and link the file for the HV status log
    HVlogfile = open("logs/csiHV.log.%s" % str(now.strftime('%Y-%m-%d_%H:%M:%S')), "w") 
    print("starting logger with file csiHV.log.%s" % str(now.strftime('%Y-%m-%d_%H:%M:%S')))
    os.system("ln -sf logs/csiHV.log.%s csiHV.log" % str(now.strftime('%Y-%m-%d_%H:%M:%S')))

    # prepare the file for the HV read log
    HVreadfile = open("logs/csireadHV.log.%s" % str(now.strftime('%Y-%m-%d_%H:%M:%S')), "w") 
    logHVread(HVreadfile)
    lastHVread = datetime.datetime.now()
    print("logger running, can start plotter now!")

    while True:

        # get the current time and date
        now =  datetime.datetime.now()
        if verbose:
            print(str(now.strftime('%Y-%m-%d %H:%M:%S')))
        logHVstatus(HVlogfile, now)
        
        if lastHVread < now + datetime.timedelta(minutes =-deltaMinutes):
            if verbose:
                print("last time HV was read: ", lastHVread.strftime('%Y-%m-%d_%H:%M:%S'))
                print("now : ", now.strftime('%Y-%m-%d_%H:%M:%S'))
            logHVread(HVreadfile)
            lastHVread = datetime.datetime.now()
        else:
            time.sleep(5)
        
    HVlogfile.close()
    HVreadfile.close()

if __name__ =="__main__":
    sys.exit(main(sys.argv))

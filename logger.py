#!/usr/bin/python3
import sys,os 
import time
import datetime
import subprocess
from signal import signal, SIGINT

verbose = True # False # 
donotuse = [4]

def handler(signal_received, frame):
    # close file here?
    print('CTRL-C pressed')
    exit(0)

def main(argv):
    # define signal handler
    signal(SIGINT, handler)
    

    now=  datetime.datetime.now()
    logfile = open("csiHV.log.%s" % str(now.strftime('%Y-%m-%d_%H:%M:%S')), "w") 
    print("starting logger with file csiHV.log.%s" % str(now.strftime('%Y-%m-%d_%H:%M:%S')))
    os.system("ln -sf csiHV.log.%s csiHV.log" % str(now.strftime('%Y-%m-%d_%H:%M:%S')))

    while True:

        # get the current time and date
        now=  datetime.datetime.now()
        if verbose:
            print(str(now.strftime('%Y-%m-%d %H:%M:%S')))
        logfile.write(str(now.strftime('%Y-%m-%d %H:%M:%S'))+'\n' )
        #for d in range(2,3):
        for d in range(1,7):
            if d in donotuse:
                continue
            if verbose:
                print(d)
            logfile.write('%d' %d)
            # run the process with input command 'p' and pipe the stdout
            retval = subprocess.run(['/home/wasa/csihv', '/dev/ttyUSB%d' %d], stdout=subprocess.PIPE, input ='p\n'.encode('utf-8'))
            retval = retval.stdout.decode('utf-8')
            val = retval.split()
            #print(val[-1])
            
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

        time.sleep(5)
        
    logfile.close()

if __name__ =="__main__":
    sys.exit(main(sys.argv))

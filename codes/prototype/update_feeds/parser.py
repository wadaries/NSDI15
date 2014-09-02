import sys
import time
import random
import os
import glob
import subprocess

def parseRouteviewUpdate ():
    print 'Parse routeview update\n'

    path = '.'
    filename = glob.glob(os.path.join(path, 'updates.20140701.0000.hr'))[0]

    def extract_up (input_f):
        fi = open(input_f, "r")
        fil = fi.readlines()

        p_prefix_pairs = []
        for feed in fil:
            fl = feed.split ('|')
            if len (fl) > 5:
                # extract peerIP, prefix, time, flag
                if fl[5][-1] == '\n':
                    p_prefix_pairs.append ([fl[3], fl[5][:-1], fl[1], fl[2]])
                else:
                    p_prefix_pairs.append ([fl[3], fl[5], fl[1], fl[2]])

        fi.close ()
        return p_prefix_pairs

    updates = extract_up (filename)

    outname = filename + ".extracted.updates"
    fo = open(outname, "w")

    fo.write ("# peerIP, \t prefix, \t time, \t flag\n")

    for u in updates :
        fo.write (u[0] + '\t' + u[1] + '\t\t' + u[2] + '\t' + u[3] + '\n')

    fo.close ()

if __name__ == "__main__":

    print 'parsing routeview updates feeds\n'
    parseRouteviewUpdate()

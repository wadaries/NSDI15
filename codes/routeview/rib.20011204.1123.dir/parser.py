import sys
import time
import random
import os
import glob

def extract_peerIP_prefix (input_f):
    fi = open(input_f, "r")
    fil = fi.readlines()

    peerIPs = []
    p_prefix_pairs = []
    for feed in fil:
        fl = feed.split ('|')
        if len (fl) > 5:
            p_prefix_pairs.append ([fl[3], fl[5]])
            if fl[3] not in peerIPs:
                peerIPs.append(fl[3])
    fi.close ()
    return [peerIPs, p_prefix_pairs]

def runParser ():
    peerIPs_all = []
    p_prefix_pairs_all = []
    
    path = '.'
    for filename in glob.glob(os.path.join(path, 'xa?')):
        [tp, tpp] = extract_peerIP_prefix (filename)
        peerIPs_all = list (set (peerIPs_all + tp))
        p_prefix_pairs_all.extend (tpp)

    return [peerIPs_all, p_prefix_pairs_all]

if __name__ == "__main__":
    print 'parsing xa? files, the 10 files constituting rib snapshot \n'

    # runParser()
    # for filename in ["xaa", "xab", "xac", "xad", "xae", "xaf", "xag", "xah", "xai", "xaj"]:

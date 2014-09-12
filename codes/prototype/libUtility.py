import sys
import time
import random
import os
import glob

# add parent directory of [psycopg2, igraph] on anduo's machine
sys.path.append('/usr/local/lib/python2.7/site-packages/') 
import psycopg2
import psycopg2.extras

import igraph
import logging

def tfsr (start, end, base) :
    return round ((end - start) / base, 6) * 1000

def tfsf (start, end) :
    return round (end - start, 6) * 1000

def tfs (start, end) :
    return str (round (end - start, 6) * 1000)

def tf (delta) :
    return "Time: " + str (round (delta, 6) * 1000) + " ms"

def tfm (delta) :
    return "(" + str ((round (delta/60, 3))) + " min)"

def setlogdata (logfile):
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        logging.basicConfig(filename = os.getcwd() + '/dat/' + logfile, filemode='w', level=logging.DEBUG, format='%(message)s')

def setlog (logfile):

    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
        logging.basicConfig(filename = os.getcwd() + '/logging/' + logfile, filemode='w', level=logging.DEBUG, format='%(filename)s:%(lineno)s %(levelname)s:    %(message)s')

    # start = time.time ()
    # logging.info('Started')
    # end = time.time ()
    # logging.info('Finished ' + tf (start, end))
# os.system ("/usr/local/bin/psql -U postgres -f /usr/local/share/postgis/postgis.sql test2")
# input file names

def peerIP_ISP_map (peerIP_nodes_file, ISP_nodes_file):
    pf = open (peerIP_nodes_file, "r").readlines ()
    ispf = open (ISP_nodes_file, "r").readlines ()

    node_map = {}
    for pn in pf:
        ISP_node = random.choice (ispf)
        ispf.remove (ISP_node)
        node_map[pn[:-1]] = ISP_node[:-1]

    return node_map

def path_to_edge (path):
    edges = []
    i = 0
    if path != []:
        while i < (len (path) - 1):
            edges.append ([path[i], path[i+1]])
            i = i+1
    return edges



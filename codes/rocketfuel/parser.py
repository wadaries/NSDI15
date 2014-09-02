import sys
import time
import random
import os
import glob
import subprocess

def extract_edges_nodes_r0r1 (input_f, output_edge, output_node):
    fi = open(input_f, "r")
    fil = fi.readlines()
    fe = open(output_edge, "w")
    fn = open(output_node, "w")

    edges = []
    nodes = []
    
    for line in fil:
        if (line[0] != '-') and ((line[-3:] == 'r0\n') or (line[-3:] == 'r1\n')):
            # fo.write (line)
            lstr = line.split()
            from_node = lstr[0]

            # if from_node not in nodes:
            #     nodes.append (from_node)
            
            for to_node in lstr:
                if (to_node[0] == '<') and (to_node[-1:] == '>'):
                    edges.append ([from_node, to_node[1:-1]])

    for edge in edges:
        fe.write (str(edge[0]) + ' ' + str (edge[1]) + '\n' )

    nodes1 = [n[0] for n in edges]
    nodes2 = [n[1] for n in edges]
    nodes = list (set (nodes1 + nodes2))

    for node in nodes:
        fn.write (str (node) + '\n')

    fi.close ()
    fe.close ()
    fn.close ()

def runParser ():
    path = '.'
    file_list = []
    for filename in glob.glob(os.path.join(path, '*.cch')):
        if (filename[2:].count ('.') == 1) and (filename[2:].count ("README") == 0):
            fe_out = filename[2:-4] + '_edges.txt'
            fn_out = filename[2:-4] + '_nodes.txt'
            file_list.append ([filename[2:], fe_out, fn_out])
            
    for f in file_list:
        extract_edges_nodes_r0r1 (f[0], f[1], f[2])

    stat_f = open("stat", "w")
    stat_f.write ("# AS (number)\t\tedges (number)\t\t nodes (number)\n")

    for f in file_list:
        e_num_string = subprocess.check_output(["wc", "-l", f[1]])
        e_num = int (e_num_string.split ()[0]) 
        n_num_string = subprocess.check_output(["wc", "-l", f[2]])
        n_num = int (n_num_string.split ()[0])

        as_num = f[0].split ('.')[0]

        stat_f.write (as_num + "\t\t\t" + str (e_num) + " \t\t\t" + str (n_num) + "\n")

    stat_f.close ()

if __name__ == "__main__":

    print 'parsing [0-9]{0,3}.cch files, generate the topology, output write to [0-9]{0,3}_edges.txt\n'

    runParser()

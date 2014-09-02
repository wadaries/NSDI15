import sys
import time
import random
import os
import glob

# add parent directory of [psycopg2, igraph] on anduo's machine
sys.path.append('/usr/local/lib/python2.7/site-packages/') 
import psycopg2
import igraph

# input file names
rocketfuel_file = ["1221.cch"]
routeview_file = ["xaa", "xab", "xac", "xad", "xae", "xaf", "xag", "xah", "xai", "xaj"]
rib = "rib.20011204.1123.bz2"

ISP_graph = igraph.Graph ()

def initializer2 ():

    sql_script = "rsdn.sql"
    username = "anduo"
    dbname = "small"
    rib_edges = "rib20011204_edges_200.txt"
    # rib_edges = "rib20011204_edges.txt"
    rib_prefixes = "rib20011204_prefixes.txt"
    rib_nodes = "rib20011204_nodes.txt"
    ISP_nodes = "4755_nodes.txt"
    ISP_edges = "4755_edges.txt"

    create_schema (username, dbname, sql_script)
    
    init_topology (username, dbname, ISP_edges)
    
    init_configuration (username, dbname, rib_edges, rib_prefixes, rib_nodes, ISP_nodes, ISP_edges)

def initializer ():
# after 7 hours of execution ...     
# SELECT count(*) FROM configuration ;
#   count   
# ----------
#  57735914
# (1 row)
# Time: 10053.740 ms
    createDBschema ("anduo", "anduo", "rsdn.sql")
    
    init_topology ("anduo", "anduo", "1221_edges.txt")
    
    init_configuration ("rib20011204_edges.txt", "rib20011204_prefixes.txt", "rib20011204_nodes.txt", "1221_nodes.txt", "1221_edges.txt", "anduo", "anduo")

def create_schema (username, dbname, SQLscript):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        # conn = psycopg2.connect("dbname='anduo' user='anduo' host='localhost'")
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        # conn.autocommit = True
        cur = conn.cursor()
    except:
        print "Unable to connect to database " + dbname + ", as user " + username

    try:
        dbscript  = open(SQLscript,'r').read() 
        cur.execute(dbscript)
    except psycopg2.DatabaseError, e:
        print "Unable to create schemas :%s" % str(e)

    cur.close()
    conn.close()
    print "createDBschema:"
    print "Connect to database " + dbname + ", as user " + username
    print "Create schemas with SQL script " + SQLscript + '\n'

def init_topology (username, dbname, ISP_edges_file):
    global ISP_graph

    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
    except:
        print "init_topology: Unable to connect to database " + dbname + " ,as user " + username
        
    f = open (ISP_edges_file, "r").readlines ()

    ISP_node = []
    for edge in f:
        ed = edge[:-1].split()
        ISP_node.append ((int (ed[0]), int (ed[1])))

    ISP_graph = igraph.Graph (ISP_node)
        
    for edge in f:
        ed = edge[:-1].split()
        try:
            cur.execute("""INSERT INTO topology VALUES (%s, %s, 0, 0)""", (ed[0], ed[1]))
        except psycopg2.DatabaseError, e:
            print "Unable to insert into topology table: %s" % str(e)

    cur.close()
    conn.close()

    print "init_topology:"
    print "Load topology table " + "with edges in " + ISP_edges_file + '\n'

def peerIP_ISP_map (peerIP_nodes_file, ISP_nodes_file):
    pf = open (peerIP_nodes_file, "r").readlines ()
    ispf = open (ISP_nodes_file, "r").readlines ()
    print 'peerID size: ' + str (len (pf))  + '\n' + 'ISP network size: ' + str (len (ispf)) + '\n'

    node_map = {}
    for pn in pf:
        ISP_node = random.choice (ispf)
        ispf.remove (ISP_node)
        node_map[pn[:-1]] = ISP_node[:-1]

    print 'ISP network size: ' + str (len (ispf))
    return node_map

# peerIP_ISP_map ("rib20011204_nodes.txt", "1221_nodes.txt")    

init_configuration ("rib20011204_edges_200.txt", "rib20011204_prefixes.txt", "rib20011204_nodes.txt", "1221_nodes.txt", "1221_edges.txt", "anduo", "anduo")

def path_to_edge (path):
    edges = []
    i = 0
    if path != []:
        while i < (len (path) - 1):
            edges.append ([path[i], path[i+1]])
            i = i+1
    return edges

def init_configuration (username, dbname, rib_edges_file, rib_prefixes_file, rib_peerIPs_file, ISP_nodes_file, ISP_edges_file):
    global ISP_graph

    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
    except:
        print "init_topology: Unable to connect to database " + dbname + " ,as user " + username

    nm = peerIP_ISP_map (rib_peerIPs_file, ISP_nodes_file)
    ISP_borders = nm.values ()

    ribs = open (rib_edges_file, "r").readlines ()
    for r in ribs:
        switch_ID = nm [r.split ()[0]]
        header = r.split ()[1]
        random_border = random.choice (ISP_borders)
        # for n in ISP_borders:
        for n in [random_border]:
            if n != switch_ID:
                path_list = ISP_graph.get_shortest_paths (int (switch_ID), int (n))[0]
                path_edges = path_to_edge (path_list)

                for ed in path_edges:
                    try:
                        cur.execute("""INSERT INTO configuration VALUES (%s, %s, %s, 0)""", (header, str (ed[0]), str (ed[1])))
                    except psycopg2.DatabaseError, e:
                        print "Unable to insert into configuration table: %s" % str(e)

    cur.close()
    conn.close()
    print "init_configuration:"
    print "Load configuration table with edges\n"

def extract_peerIP_prefix (input_f):
    fi = open(input_f, "r")
    fil = fi.readlines()

    peerIPs = []
    prefixs = []
    p_prefix_pairs = []
    for feed in fil:
        fl = feed.split ('|')
        if len (fl) > 5:
            # extract peerIP, prefix, time
            p_prefix_pairs.append ([fl[3], fl[5], fl[1]])

            if fl[5] not in prefixs:
                prefixs.append (fl[5])
            if fl[3] not in peerIPs:
                peerIPs.append(fl[3])

    fi.close ()
    return [peerIPs, p_prefix_pairs, prefixs]

def parseRouteviewRib ():
    print 'Parse routeview rib data: parsing xa? files, the 10 files constituting rib snapshot, output write to rib*_edges.txt, rib*_nodes.txt \n'

    peerIPs_all = []
    prefixes_all = []
    p_prefix_pairs_all = []
    
    path = '.'
    # for filename in glob.glob(os.path.join(path, 'xa?')):
    for filename in routeview_file:
        [tp, tpp, tpr] = extract_peerIP_prefix (filename)
        peerIPs_all = list (set (peerIPs_all + tp))
        prefixes_all = list (set (prefixes_all + tpr))
        p_prefix_pairs_all.extend (tpp)

    rl = rib.split ('.')
    fe_out = rl[0] + rl[1] + '_edges.txt'
    fn_out = rl[0] + rl[1] + '_nodes.txt'
    fr_out = rl[0] + rl[1] + '_prefixes.txt'

    fe = open(fe_out, "w")
    fn = open(fn_out, "w")
    fr = open(fr_out, "w")

    for node in peerIPs_all:
        fn.write (str(node) + '\n')
    for node in prefixes_all:
        fr.write (str (node) + '\n')
    for edge in p_prefix_pairs_all:
        fe.write (edge[0] + ' ' + edge[1] + ' ' + edge[2] + '\n')

    fe.close ()
    fn.close ()
    fr.close ()

def extract_edges_nodes_r0r1 (input_f, output_edge, output_node):
    fi = open(input_f, "r")
    fil = fi.readlines()
    fe = open(output_edge, "w")
    fn = open(output_node, "w")

    edges = []
    nodes = []
    
    for line in fil:
        if (line[0] != '-') and ((line[-3:] == 'r0\n') or (line[-3:] == 'r1\n')):
            lstr = line.split()
            from_node = lstr[0]

            if from_node not in nodes:
                nodes.append (from_node)
            
            for to_node in lstr:
                if (to_node[0] == '<') and (to_node[-1:] == '>'):
                    edges.append ([from_node, to_node[1:-1]])

    for edge in edges:
        fe.write (str(edge[0]) + ' ' + str (edge[1]) + '\n' )

    for node in nodes:
        fn.write (str (node) + '\n')

    fi.close ()
    fe.close ()
    fn.close ()


def parseRocketfuelISP ():
    print 'parsing [0-9]{0,3}.cch files, generate the topology, output write to [0-9]{0,3}_edges.txt, [0-9]{0,3}_nodes.txt\n'

    path = '.'
    file_list = []
    for filename in glob.glob(os.path.join(path, '*.cch')):
        if (filename[2:].count ('.') == 1) and (filename[2:].count ("README") == 0):
            fe_out = filename[2:-4] + '_edges.txt'
            fn_out = filename[2:-4] + '_nodes.txt'
            file_list.append ([filename[2:], fe_out, fn_out])
            
    for f in file_list:
        extract_edges_nodes_r0r1 (f[0], f[1], f[2])

# def runScript():
#     print 'Parsing rocketfuel data\n'
#     extract_edges_r0r1 ("1221.cch", "test")

# directory = os.path.join("c:\\","path")
# for root,dirs,files in os.walk(directory):
#     for file in files:
#        if file.endswith(".log") or file.endswith(".txt"):
#            f=open(file, 'r')
#            for line in f:
#               if userstring in line:
#                  print "file: " + os.path.join(root,file)             
#                  break
#            f.close()

# if __name__ == "__main__":

#     parseRouteviewRib ()

#     parseRocketfuelISP ()

#     createDBschema ()
#     init_topology ()

# def create_schema():
#     print '\nCreating schema'
#     dbname    = 'rsdn'
#     db_script = 'rsdn.sql'
    
#     os.system ("export PATH=/opt/local/lib/postgresql90/bin/:$PATH")
# 	ret = os.system("PGOPTIONS='--client-min-messages=warning' psql -X"
#             " -q  --pset pager=off -d " +
#             dbname + " -f " + db_script)
#     assert ret == 0

    # try: 
    #     cur.execute ("""INSERT INTO traffic_seed VALUES ('flow1', 'A'), ('flow3', 'A'), ('flow4', 'C') """)
    # except:
    #     print "Cannot insert into switches table"
    # cur.execute ("""SELECT * from topology""")
    # topology = cur.fetchall ()
    # cur.execute ("""SELECT * from configuration""")
    # configuration = cur.fetchall ()

    # cur.execute ("""SELECT * from switches""")
    # switches = cur.fetchall ()
    # try: 
    #     cur.execute ("""INSERT INTO switches VALUES (5)""")
    # except:
    #     print "Cannot insert into switches table"

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
                    if to_node[1:-1] not in nodes:
                        nodes.append (to_node[1:-1])

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


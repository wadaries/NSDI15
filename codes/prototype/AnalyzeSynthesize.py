execfile ("./libUtility.py")
execfile ("./libAnalyzeSynthesize.py")
import libAnalyzeSynthesize
import pyGnuplot as gp

def time_obs (dict_cur):
    dict_cur.execute ("SELECT switch_id FROM borders;")
    borders = [n[0] for n in dict_cur.fetchall ()]
    # print borders

    dict_cur.execute ("SELECT * FROM obs_nodes;")
    obs_nodes = [n[0] for n in dict_cur.fetchall ()]
    # print "nodes: "
    # print obs_nodes
    
    dict_cur.execute ("SELECT flow_id FROM obs_reachability_internal;")
    obs_reach = dict_cur.fetchall ()
    if obs_reach != []:
        flow_id = random.sample (obs_reach, 1)[0][0]
        # print "random picked flow appeared in obs_reachability_internal:"
        # print flow_id

        dict_cur.execute ("SELECT source FROM obs_reachability_internal where flow_id = %s", ([flow_id]))
        ingress_nodes = [n[0] for n in dict_cur.fetchall ()]

        if len (ingress_nodes) != 0:
            ingress_node = random.sample (ingress_nodes, 1)[0]
            # print "ingress_node for the flow: "
            # print ingress_node

            exit_node = random.sample ([n for n in obs_nodes if n not in [ingress_node]], 1)[0]
            # print "exit_node:"
            # print exit_node

            dict_cur.execute ("ALTER VIEW obs_reachability_out ALTER COLUMN source SET DEFAULT %s ;", ([exit_node]))

    else:
        dict_cur.execute ("SELECT * FROM obs_flows;")
        obs_flows = [f[0] for f in dict_cur.fetchall ()]
        # print "flows: "
        # print obs_flows
        flow_id = random.sample (obs_flows, 1)[0]
        # print flow_id
        ingress_node = random.sample (obs_nodes, 1)[0]
        # print ingress_node
        exit_node = random.sample ([n for n in obs_nodes if n not in [ingress_node]], 1)[0]
        # print exit_node

    external_node = random.sample ([n for n in borders if n not in obs_nodes],1)[0]
    # print "randomly-pick external_node to add for flow: "
    # print external_node

    s_i = time.time ()
    dict_cur.execute ("INSERT INTO obs_reachability_external values (%s, %s);", ([flow_id, external_node]))

    dict_cur.execute ("INSERT INTO obs_reachability_internal values (%s, %s, %s);", ([flow_id, ingress_node, exit_node]))
    e_i = time.time ()
    delta_i = tfsf (s_i, e_i)

    s_d = time.time ()
    dict_cur.execute ("DELETE FROM obs_reachability_external where flow_id = %s AND target = %s;", ([flow_id, external_node]))
    dict_cur.execute ("DELETE FROM obs_reachability_internal where flow_id = %s AND source = %s AND target = %s;", ([flow_id, ingress_node, exit_node]))
    e_d = time.time ()
    delta_d = tfsf (s_d, e_d)

    dict_cur.execute ("INSERT INTO obs_reachability_external values (%s, %s);", ([flow_id, external_node]))
    dict_cur.execute ("INSERT INTO obs_reachability_internal values (%s, %s, %s);", ([flow_id, ingress_node, exit_node]))

    external_node2 = random.sample ([n for n in borders if n not in [external_node] + obs_nodes], 1)[0]

    # raw_input ("pause, enter to continue")

    s_u = time.time ()
    dict_cur.execute ("UPDATE obs_reachability_external SET target = %s Where flow_id = %s AND target = %s;", ([external_node2, flow_id, external_node]))
    e_u = time.time ()
    delta_u = tfsf (s_u, e_u)

    return [delta_i, delta_d, delta_u]

def time_e2e_vn (dict_cur):

    dict_cur.execute ("SELECT * FROM vn_reachability;")
    vns = random.sample (dict_cur.fetchall (), 1)[0]
    flow_id = vns[0]
    # print flow_id

    switchb_start = time.time ()
    dict_cur.execute ("SELECT * FROM configuration_switch WHERE flow_id = %s;", ([flow_id]))
    switchb = dict_cur.fetchall ()
    switchb_end = time.time ()

    del_start = time.time ()
    dict_cur.execute ("DELETE FROM vn_reachability WHERE flow_id = %s and ingress = %s and egress = %s ;", ([vns[0], vns[1], vns[2]]))
    del_end = time.time ()

    switcha_start = time.time ()
    dict_cur.execute ("SELECT * FROM configuration_switch WHERE flow_id = %s;", ([flow_id]))
    switcha = dict_cur.fetchall ()
    switcha_end = time.time ()

    del_time = tfsf (del_start, del_end)
    switch_delta_time = tfsf (switchb_start, switchb_end) + tfsf (switcha_start, switcha_end)

    switch_delta = [s for s in switchb if s not in switcha]
    # print "switch delta after del of " + str (flow_id) + " between " + str (vns[1]) + " and "+ str (vns[2])
    # print switch_delta

    # switchb_start2 = time.time ()
    # dict_cur.execute ("SELECT * FROM configuration_switch WHERE flow_id = %s;", ([flow_id]))
    # switchb2 = dict_cur.fetchall ()
    # switchb_end2 = time.time ()

    ins_start = time.time ()
    dict_cur.execute ("INSERT INTO vn_reachability VALUES (%s, %s, %s);", ([vns[0], vns[1], vns[2]]))
    ins_end = time.time ()
    ins_time = tfsf (ins_start, ins_end)

    # switcha_start2 = time.time ()
    # dict_cur.execute ("SELECT * FROM configuration_switch WHERE flow_id = %s;", ([flow_id]))
    # switcha2 = dict_cur.fetchall ()
    # switcha_end2 = time.time ()
    
    # switch_delta2 = [s for s in switcha2 if s not in switchb2]
    # print "switch delta after ins of " + str (flow_id) + " between " + str (vns[1]) + " and "+ str (vns[2])
    # print switch_delta2

    dict_cur.execute ("SELECT * FROM vn_nodes ;")
    nodes = dict_cur.fetchall ()
    dict_cur.execute ("SELECT egress FROM vn_reachability WHERE flow_id = %s;", ([flow_id]))
    egress = dict_cur.fetchall ()
    dict_cur.execute ("SELECT ingress FROM vn_reachability WHERE flow_id = %s;", ([flow_id]))
    ingress = dict_cur.fetchall ()
    newi = random.sample (ingress, 1)[0][0]

    new_nodes = [n for n in nodes if n not in egress]
    if new_nodes != []:
        dict_cur.execute ("SELECT egress from vn_reachability where flow_id = %s and ingress = %s", ([flow_id, newi]))
        olde = dict_cur.fetchall ()[0][0]
        if olde in new_nodes:
            newe = random.sample (new_nodes.remove (olde), 1)[0][0]
        else:
            newe = random.sample (new_nodes, 1)[0][0]
        # print newe

        # print "update for flow_id " + str (flow_id) + " from ingress " + str (newi) + " to egress " + str (olde)
        # raw_input ("pause, enter to continue")

        up_start = time.time ()
        dict_cur.execute ("UPDATE vn_reachability SET egress = %s where flow_id = %s and ingress = %s;", ([newe, flow_id, newi]))
        up_end = time.time ()

        # print "update egress to " + str (newe)
        # raw_input ("pause, enter to continue")
        
        up_time = tfsf (up_start, up_end)
        dict_cur.execute ("UPDATE vn_reachability SET egress = %s where flow_id = %s and ingress = %s;", ([olde, flow_id, newi]))
    else:
        up_time = 0

        # dict_cur.execute ("UPDATE vn_reachability SET egress = %s where flow_id = %s and ingress = %s;", ([newe, flow_id, newi]))
    # switch_delta_time2 = tfsf (switchb_start2, switchb_end2) + tfsf (switcha_start2, switcha_end2)

    return [del_time, switch_delta_time, ins_time, up_time]
# def plot_synthesize (username, dbname, rounds):
#     pass

def verify (username, dbname, rounds):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        print "Connect to database " + dbname + ", as user " + username

        dat = []
        for i in range( rounds):

            [f1, f2] = pick_flow (dict_cur, 2)

            start = time.time ()
            fg = get_forwarding_graph (dict_cur, f1)
            end = time.time ()
            fg_t = tfsf (start, end)

            start = time.time ()
            ed = check_disjoint_edge (dict_cur, f1, f2)
            end = time.time ()
            cde_t = tfsf (start, end)

            start = time.time ()
            lp = check_dag (dict_cur, f1)
            end = time.time ()
            cd_t = tfsf (start, end)

            start = time.time ()
            t = check_blackhole (dict_cur, f1)
            end = time.time ()
            cb_t = tfsf (start, end)

            dat.append ([fg_t, cde_t, cd_t, cb_t])
            
    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e

    finally:
        if conn:
            conn.close()

    dat_b = [d[0] for d in dat]
    dat_y1 = [d[1] for d in dat]
    dat_y2 = [d[2] for d in dat]
    dat_y3 = [d[3] for d in dat]

    return [dat_b, dat_y1, dat_y2, dat_y3]

def black_hole (username, dbname, rounds):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        dat = []
        for i in range( rounds):

            [f1, f2] = pick_flow (dict_cur, 2)

            start = time.time ()
            t = check_blackhole (dict_cur, f1)
            end = time.time ()
            cb_t = tfsf (start, end)

            dat.append (cb_t)
        dat.sort ()
            
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e

    finally:
        if conn: conn.close()

    return dat

def loop_free (username, dbname, rounds):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        dat = []
        for i in range( rounds):
            [f1, f2] = pick_flow (dict_cur, 2)
            start = time.time ()
            lp = check_dag (dict_cur, f1)
            end = time.time ()
            cd_t = tfsf (start, end)
            dat.append (cd_t)
        dat.sort ()
            
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e

    finally:
        if conn: conn.close()

    return dat

def get_path_len (username, dbname, xsize):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        dict_cur.execute ("SELECT hops FROM reachability limit %s;", ([xsize]))
        ph = [int (p[0]) for p in dict_cur.fetchall ()]

        path_hops = []
        for i in set (ph):
            path_hops.append ([i, ph.count (i)])
            
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e

    finally:
        if conn: conn.close()
    return path_hops

def fg_cdf (username, dbname, xsize):

    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        fg_time = [dbname]
        fg_size = []
        for i in range (0, xsize):
            f1 = pick_flow (dict_cur, 1)[0]

            start = time.time ()
            fg = get_forwarding_graph (dict_cur, f1)
            end = time.time ()

            fgs = len (fg)
            fgt = tfsf (start, end)
            fg_time.append (fgt)
            fg_size.append (fgs)
        fg_time.sort ()

        fg_count = []
        for i in set (fg_size):
            fg_count.append ([i, fg_size.count (i)])

    except psycopg2.DatabaseError, e:
        print 'Error %s' % e

    finally:
        if conn: conn.close()

    return [fg_time, fg_count]

def analyze (username, dbname, log):
    setlogdata (log)
    # logging.info ("------------------------------------------------------------")
    # logging.info ("Start analyze network configuration")
    # logging.info ("------------------------------------------------------------")
    # logging.info ("Successfully set log file\n")

    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        print "Connect to database " + dbname + ", as user " + username
        
        [f1, f2] = pick_flow (dict_cur, 2)

        for x in range(0, rounds):
            logging.info ('"Round ' + str (x) + '"                      ' + '"Time (ms)"')

            start = time.time ()
            fg = get_forwarding_graph (dict_cur, f1)
            end = time.time ()
            logging.info ('"forwarding graph"       ' + tfs (start, end))

            start = time.time ()
            ed = check_disjoint_edge (dict_cur, f1, f2)
            end = time.time ()
            logging.info ('"disjoint edge"            ' + tfs (start, end))

            start = time.time ()
            lp = check_dag (dict_cur, f1)
            end = time.time ()
            logging.info ('"loop free"                     ' + tfs (start, end))

            start = time.time ()
            t = check_blackhole (dict_cur, f1)
            end = time.time ()
            logging.info ('"blackhole"                ' + tfs (start, end))
            logging.info ("\n")

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e
    finally:
        if conn:
            conn.close()
        print "Finish analyze_config"

    # g = gp.gnuplot(persist = True)
    # g ('set term pdfcairo')
    # g ("set logscale y")
    # # g ("set key top left")
    # g ('set key bottom right')

    # g ('set terminal pdfcairo font "Gill Sans,9" linewidth 4 rounded fontscale 1.0')
    # g ('set style line 80 lt rgb "#808080"')
    # g ('set style line 81 lt 0  # dashed')
    # g ('set style line 81 lt rgb "#808080"')
    # g ('set grid back linestyle 81')
    # g ('set border 3 back linestyle 80')
    # g ('set style line 1 lt rgb "#A00000" lw 2 pt 1')
    # g ('set style line 2 lt rgb "#00A000" lw 2 pt 6')
    # g ('set style line 3 lt rgb "#5060D0" lw 2 pt 2')
    # g ('set style line 4 lt rgb "#F25900" lw 2 pt 9')

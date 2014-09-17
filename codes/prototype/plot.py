execfile ("./libUtility.py")
execfile ("./libAnalyzeSynthesize.py")
import libAnalyzeSynthesize
import pyGnuplot as gp

def gen_cdf_x (y_list):
    x = []
    xlen = len (y_list)
    for i in range (xlen):
        xt = float(i+1)/ xlen
        x.append (xt)
    return x

def time_obs (dict_cur):
    dict_cur.execute ("SELECT switch_id FROM borders;")
    borders = [n[0] for n in dict_cur.fetchall ()]
    print borders

    dict_cur.execute ("SELECT * FROM obs_nodes;")
    obs_nodes = [n[0] for n in dict_cur.fetchall ()]
    print "nodes: "
    print obs_nodes
    
    dict_cur.execute ("SELECT flow_id FROM obs_reachability_internal;")
    obs_reach = dict_cur.fetchall ()
    if obs_reach != []:
        flow_id = random.sample (obs_reach, 1)[0][0]
        print "random picked flow appeared in obs_reachability_internal:"
        print flow_id

        dict_cur.execute ("SELECT source FROM obs_reachability_internal where flow_id = %s", ([flow_id]))
        ingress_nodes = [n[0] for n in dict_cur.fetchall ()]

        if len (ingress_nodes) != 0:
            ingress_node = random.sample (ingress_nodes, 1)[0]
            print "ingress_node for the flow: "
            print ingress_node

            exit_node = random.sample ([n for n in obs_nodes if n not in [ingress_node]], 1)[0]
            print "exit_node:"
            print exit_node

            dict_cur.execute ("ALTER VIEW obs_reachability_out ALTER COLUMN source SET DEFAULT %s ;", ([exit_node]))

    else:
        dict_cur.execute ("SELECT * FROM obs_flows;")
        obs_flows = [f[0] for f in dict_cur.fetchall ()]
        print "flows: "
        print obs_flows
        flow_id = random.sample (obs_flows, 1)[0]
        print flow_id
        ingress_node = random.sample (obs_nodes, 1)[0]
        print ingress_node
        exit_node = random.sample ([n for n in obs_nodes if n not in [ingress_node]], 1)[0]
        print exit_node

    external_node = random.sample ([n for n in borders if n not in obs_nodes],1)[0]
    print "randomly-pick external_node to add for flow: "
    print external_node

    dict_cur.execute ("INSERT INTO obs_reachability_external values (%s, %s);", ([flow_id, external_node]))

    dict_cur.execute ("INSERT INTO obs_reachability_internal values (%s, %s, %s);", ([flow_id, ingress_node, exit_node]))

    dict_cur.execute ("DELETE FROM obs_reachability_external where flow_id = %s AND target = %s;", ([flow_id, external_node]))

    dict_cur.execute ("DELETE FROM obs_reachability_internal where flow_id = %s AND source = %s AND target = %s;", ([flow_id, ingress_node, exit_node]))

    dict_cur.execute ("INSERT INTO obs_reachability_external values (%s, %s);", ([flow_id, external_node]))
    dict_cur.execute ("INSERT INTO obs_reachability_internal values (%s, %s, %s);", ([flow_id, ingress_node, exit_node]))

    external_node2 = random.sample ([n for n in borders if n not in [external_node] + obs_nodes], 1)[0]
    print "external_node 2:"
    print external_node2

    raw_input ("pause, enter to continue")

    dict_cur.execute ("UPDATE obs_reachability_external SET target = %s Where flow_id = %s AND target = %s;", ([external_node2, flow_id, external_node]))
        # dict_cur.execute ("UPDATE obs_reachability_internal SET target = %s Where flow_id = %s AND source = %s;", ([external_node2, flow_id, external_node]))

        # dict_cur.execute ("SELECT * FROM obs_flows;")
        # obs_flows = [f[0] for f in dict_cur.fetchall ()]
        # print "flows: "
        # print obs_flows

def plot_obs_synthesize2 (username, dbname, rounds):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        print "Connect to database " + dbname + ", as user " + username

        time_obs (dict_cur)

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e

    finally:
        if conn:
            conn.close()

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

def plot_vn_synthesize2 (username, dbname, rounds):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        print "Connect to database " + dbname + ", as user " + username

        def gen_cdf_x (y_list):
            x = []
            xlen = len (y_list)
            for i in range (xlen):
                xt = float(i+1)/ xlen
                x.append (xt)
            return x

        datfile = './dat/vn_synthesis_cdf' + str (rounds) + '.dat'
        if os.path.isfile (datfile) == False:
            dat = []
            for i in range( rounds):
                flow_size = 100
                topo_size = 10
                vn_init (dict_cur, topo_size, flow_size)
                [del_time, del_swith_time, ins_time, up_time] = time_e2e_vn (dict_cur)
                if up_time != 0:
                    dat_i = [del_time, up_time, ins_time, del_swith_time]
                else:
                    dat_i = []
                dat.append (dat_i)
            y_del = [d[0] for d in dat]
            y_del.sort ()
            y_up = [d[1] for d in dat]
            y_up.sort ()
            y_ins = [d[2] for d in dat]
            y_ins.sort ()
            y_switch = [d[3] for d in dat]
            y_switch.sort ()

            x = gen_cdf_x (y_del)
            df = open(datfile, "w")
            for i in range (len(x)) :
                print "current i: " + str (i)
                print x[i]
                print y_del[i]
                df.write (str (x[i]) + '\t' + str (y_del[i]) + '\t' + str (y_ins[i]) + '\t' + str (y_up[i]) + '\t' + str (y_switch[i]) + '\n')
            df.close ()

        pltfile = './dat/vn_synthesis_cdf' + str (rounds) + '.plt'
        outputfile = './dat/vn_synthesis_cdf' + str (rounds) + '.pdf'
        print "plot vn synthesize: start gnuplot"

        pf = open (pltfile, "w")
        pf.write ('''
reset
set terminal pdfcairo font "Gill Sans,9" linewidth 2 rounded fontscale 1

set logscale y

set style line 80 lt rgb "#808080"
set style line 81 lt 0  # dashed
set style line 81 lt rgb "#808080"
set grid back linestyle 81
set border 3 back linestyle 80

set style line 1 lt rgb "#A00000" lw 1 pt 1 ps 1
set style line 2 lt rgb "#00A000" lw 1 pt 6 ps 1
set style line 3 lt rgb "#5060D0" lw 1 pt 2 ps 1
set style line 4 lt rgb "#F25900" lw 1 pt 9 ps 1

set xtics nomirror
set ytics nomirror
set key bottom right

set ylabel "Cumulative distribution of time (ms)"
set output "''' + outputfile + '''"

plot "'''+ datfile +'''" using 2 title "synthesize policy deletion" with lp ls 1,\\
 '' using 3 title "synthesize policy insertion" with lp ls 2,\\
 '' using 4 title "synthesize policy update" with lp ls 3,\\
 '' using 5 title "compute per-switch configuration delta" with lp ls 4''')

        os.system ("gnuplot " + pltfile)
        print "successfully vn_synthesis_cdf2"

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e

    finally:
        if conn:
            conn.close()

def plot_vn_synthesize (username, dbname, rounds, g):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        print "Connect to database " + dbname + ", as user " + username

        add_configuration_view (dict_cur)

        dat = []
        for i in range( rounds):
            flow_size = 100
            topo_size = 10
            vn_init (dict_cur, topo_size, flow_size)

            [del_time, del_swith_time, ins_time, up_time] = time_e2e_vn (dict_cur)

            if up_time != 0:
                dat_i = [del_time, del_swith_time, ins_time, up_time]
            else:
                dat_i = []

            dat.append (dat_i)

        # [y_del, y_switch, y_ins, y_up] = dat
        y_del = [d[0] for d in dat]
        y_del.sort ()

        y_switch = [d[1] for d in dat]
        y_switch.sort ()

        y_ins = [d[2] for d in dat]
        y_ins.sort ()

        y_up = [d[3] for d in dat]
        y_up.sort ()

        def gen_cdf_x (y_list):
            x = []
            xlen = len (y_list)
            for i in range (xlen):
                xt = float(i+1)/ xlen
                x.append (xt)
            return x

        x_del = gen_cdf_x (y_del)
        x_switch = gen_cdf_x (y_switch)
        x_ins = gen_cdf_x (y_ins)
        x_up = gen_cdf_x (y_up)

        outputfile = './dat/vn_synthesis_cdf' + str (rounds) + '.pdf'
        print "plot vn synthesize: start gnuplot"

        g('set xlabel "Total of ' + str (rounds) + ' randomly picked insertion / deletion / updates"')
        g('set ylabel "Time (millisecond)"')

        xvals = x_del
        yvals = y_del
        p=g.plot(xvals,yvals,style = 'lp ls 1', title="synthesize policy deletion")

        xvals = x_switch
        yvals = y_switch
        p.add(xvals,yvals,style = 'lp ls 2', title="compute per-switch configuration delta")

        xvals = x_ins
        yvals = y_ins
        p.add(xvals,yvals,style = 'lp ls 3', title="synthesize policy insertion")

        xvals = x_up
        yvals = y_up
        p.add(xvals,yvals,style = 'lp ls 4', title="synthesize policy update")

        p.title ("Synthesis for virtual network policy, AS " + str (dbname[2:6]))

        g.hardcopy(p,file=outputfile,truecolor=True) 
        print g.readlines()  
        print "plot_verify_cdf: finish"

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e

    finally:
        if conn:
            conn.close()

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

def plot_verify_cdf2 (username, dbname, rounds):

    datfile = './dat/verify_cdf' + str (rounds) + '.dat'
    if os.path.isfile (datfile) == False:

        df = open(datfile, "w")

        [b, y1, y2, y3] = verify (username, dbname, rounds)
        b.sort ()
        y1.sort ()
        y2.sort ()
        y3.sort ()
        x = gen_cdf_x (b)

        for i in range (len(x)) :
            print "current i: " + str (i)
            df.write (str (x[i]) + '\t' + str (b[i]) + '\t' + str (y1[i]) + '\t' + str (y2[i]) + '\t' + str (y3[i]) + '\n')
        df.close ()

    pltfile = './dat/verify_cdf' + str (rounds) + '.plt'
    outputfile = './dat/verify_cdf' + str (rounds) + '.pdf'
    print "plot verify_cdf: start gnuplot"

    pf = open (pltfile, "w")
    pf.write ('''
reset
set terminal pdfcairo font "Gill Sans,9" linewidth 2 rounded fontscale 1

set logscale y

set style line 80 lt rgb "#808080"
set style line 81 lt 0  # dashed
set style line 81 lt rgb "#808080"
set grid back linestyle 81
set border 3 back linestyle 80

set style line 1 lt rgb "#A00000" lw 1 pt 1 ps 1
set style line 2 lt rgb "#00A000" lw 1 pt 6 ps 1
set style line 3 lt rgb "#5060D0" lw 1 pt 2 ps 1
set style line 4 lt rgb "#F25900" lw 1 pt 9 ps 1

set xtics nomirror
set ytics nomirror
set key top left

set ylabel "Cumulative distribution of time (ms)"
set xlabel "Total of ''' + str (rounds) + ''' randomly picked flows"
set title "Verification time for AS ''' + str (dbname[2:6]) + '''"
set output "''' + outputfile + '''"

plot "'''+ datfile +'''" using 2 title "forwarding graph" with lp ls 1,\\
 '' using 3 title "disjoint path" with lp ls 2,\\
 '' using 4 title "loop free" with lp ls 3,\\
 '' using 5 title "black hole" with lp ls 4''')

    pf.close ()

    print "successfully plot_verify_cdf2"

    # xvals = xb
    # yvals = b
    # p=g.plot(xvals,yvals,style = 'lp ls 1', title="forwarding graph")

    # xvals = x1
    # yvals = y1
    # p.add (yvals,xvals,style = 'lp ls 2',title="disjoint path")

    # xvals = x2
    # yvals = y2
    # p.add (yvals,xvals,style = 'lp ls 3',title="loop free")

    # xvals = x3
    # yvals = y3
    # p.add (yvals,xvals,style = 'lp ls 4',title="black hole")

    print "plot_verify_cdf: finish"


def plot_verify_cdf (username, dbname, rounds, g):

    [b, y1, y2, y3] = verify (username, dbname, rounds)

    b.sort ()
    y1.sort ()
    y2.sort ()
    y3.sort ()

    def gen_cdf_x (y_list):
        x = []
        xlen = len (y_list)
        for i in range (xlen):
            xt = float(i+1)/ xlen
            x.append (xt)
        return x

    xb = gen_cdf_x (b)
    x1 = gen_cdf_x (y1)
    x2 = gen_cdf_x (y2)
    x3 = gen_cdf_x (y3)

    outputfile = './dat/verify_cdf' + str (rounds) + '.pdf'
    print "plot synthesize: start gnuplot"

    g('set xlabel "Total of ' + str (rounds) + ' randomly picked flows"')
    g('set ylabel "Time (millisecond)"')

    xvals = xb
    yvals = b
    p=g.plot(xvals,yvals,style = 'lp ls 1', title="forwarding graph")

    xvals = x1
    yvals = y1
    p.add (yvals,xvals,style = 'lp ls 2',title="disjoint path")

    xvals = x2
    yvals = y2
    p.add (yvals,xvals,style = 'lp ls 3',title="loop free")

    xvals = x3
    yvals = y3
    p.add (yvals,xvals,style = 'lp ls 4',title="black hole")

    p.title ("Verification time for AS " + str (dbname[2:6]) + " relative to forwarding graph generation")

    g.hardcopy(p,file=outputfile,truecolor=True) 
    print g.readlines()  
    print "plot_verify_cdf: finish"

def plot_fg_cdf (username, dbname, xsize):

    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        print "plot_fg_cdf: Connect to database " + dbname + ", as user " + username

        dict_cur.execute ("""
        DROP TABLE IF EXISTS fg_time CASCADE;
        CREATE UNLOGGED TABLE fg_time (
        fg_id      integer,
        time	   float (8),
        size       integer,
        PRIMARY KEY (fg_id)
        );
        """)

        # xsize = 5
        for i in range (0, xsize):
            f1 = pick_flow (dict_cur, 1)[0]
            # print f1
            start = time.time ()
            fg = get_forwarding_graph (dict_cur, f1)
            # print fg
            end = time.time ()
            fg_s = len (fg)

            fg_time = tfs (start, end)
            dict_cur.execute ("INSERT INTO fg_time values (%s, %s, %s);", (i, fg_time, fg_s))

        dict_cur.execute ("""
        SELECT
        time AS y,
        COUNT(fg_time) OVER (ORDER BY time) / 
        (SELECT COUNT(*) FROM fg_time)::real AS x
        FROM fg_time
        """)
        fg_cdf = dict_cur.fetchall ()
        fg_x = [f['x'] for f in fg_cdf]
        fg_y = [f['y'] for f in fg_cdf]

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e

    finally:
        if conn:
            conn.close()

    return [fg_x, fg_y]

def plot_fg_all (username, dbname_list, xsize, g):

    fg_cdf_list = []
    for i in range (len(dbname_list)):
        fg_cdf_list.append (plot_fg_cdf (username, dbname_list[i], xsize))

    print fg_cdf_list[0]

    outputfile = './dat/fg_cdf_' + str (xsize) + '.pdf'

    g ('set xlabel "Number of forwarding graphs (for a total of ' + str (xsize) + ' randomly picked flows)')
    g ('set ylabel "Cumulative Distribution, Time (millisecond)"')

    xvals = fg_cdf_list[0][0]
    yvals = fg_cdf_list[0][1]
    p=g.plot(xvals,yvals,style = 'lp ls 1', title="AS " + str (dbname_list[0][2:6]))

    for i in range (len (fg_cdf_list))[1:]:
        xvals = fg_cdf_list[i][0]
        yvals = fg_cdf_list[i][1]
        p.add (yvals,xvals,style = 'lp ls ' + str (i+1),title="AS " + str (dbname_list[i][2:6]))

    p.title ("Forwarding graph generation")    

    g.hardcopy(p,file=outputfile,truecolor=True) 
    print g.readlines()  
    print "plot_init: finish"

def plot_fg_all2 (username, dbname_list, xsize):

    datfile = './dat/fg_cdf' + str (xsize) + '.dat'
    print datfile
    if os.path.isfile (datfile) == False:
        df = open(datfile, "w")

        fg_cdf_list = []
        for i in range (len(dbname_list)):
            fg_cdf_list.append (plot_fg_cdf (username, dbname_list[i], xsize))
        print fg_cdf_list[0]
        print len (fg_cdf_list)
        print len (fg_cdf_list[0][1])

        for i in range (len (fg_cdf_list[1][0])):
            print "current i: " + str (i)
            df.write (str (i) + '\t' + str (fg_cdf_list[0][1][i]) + '\t' + str (fg_cdf_list[1][1][i]) + '\t' + str (fg_cdf_list[2][1][i]) + '\n')
        df.close ()

    pltfile = './dat/fg_cdf' + str (xsize) + '.plt'
    outputfile = './dat/fg_cdf' + str (xsize) + '.pdf'
    print "plot fg_cdf_all: start gnuplot"



    pf = open (pltfile, "w")
    pf.write ('''
reset
set terminal pdfcairo font "Gill Sans,9" linewidth 2 rounded fontscale 1

set logscale y

set style line 80 lt rgb "#808080"
set style line 81 lt 0  # dashed
set style line 81 lt rgb "#808080"
set grid back linestyle 81
set border 3 back linestyle 80

set style line 1 lt rgb "#A00000" lw 1 pt 1 ps 1
set style line 2 lt rgb "#00A000" lw 1 pt 6 ps 1
set style line 3 lt rgb "#5060D0" lw 1 pt 2 ps 1
set style line 4 lt rgb "#F25900" lw 1 pt 9 ps 1

set xtics nomirror
set ytics nomirror
set key top left

set ylabel "Cumulative distribution of time (ms)"
set xlabel "Number of forwarding graphs (total of ''' + str (xsize) + ''' randomly picked)"
set title "Forwarding graph generation time"
set output "''' + outputfile + '''"

plot "'''+ datfile +'''" using 2 title "AS '''+ str (dbname_list[0][2:6])+ '''" with lp ls 1,\\
 '' using 3 title "AS ''' +str (dbname_list[1][2:6])+ '''" with lp ls 2,\\
 '' using 4 title "AS ''' +str (dbname_list[2][2:6])+'''" with lp ls 3''')

    pf.close ()

    print "successfully fg_cdf_all2"

def plot_init (username, dbname, dat):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        print "plot_init: Connect to database " + dbname + ", as user " + username
        
        # dat.write ('"number"\t "AS ' + dbname[2:6] + '"\n')
        dat[0].append ('"AS' + dbname[2:6] + '"')

        dict_cur.execute ("SELECT count (*) FROM topology ;")
        edge_size = dict_cur.fetchall () [0][0]
        # dat.write ('"links"     \t' + str (edge_size) + '\n')
        dat[1].append (int(edge_size))

        dict_cur.execute ("SELECT count (*) FROM switches ;")
        node_size = dict_cur.fetchall () [0][0]
        # dat.write ('"nodes"     \t' + str (node_size) + '\n')
        dat[2].append (int(node_size))


        dict_cur.execute ("SELECT count (*) FROM configuration ;")
        conf_num = dict_cur.fetchall ()[0][0]
        # dat.write ('"configurations" \t' + str (conf_num) + '\n')
        dat[3].append (int(conf_num))

        dict_cur.execute ("SELECT count (*) FROM flow_constraints ;")
        flow_num = dict_cur.fetchall ()[0][0]
        # dat.write ('"flows"     \t' + str (flow_num) + '\n\n')
        dat[4].append (int(flow_num))

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e
    finally:
        if conn:
            conn.close()
        print "plot_init: finish"

def plot_all_init (username, dbname_list):
    
        dat_file = './dat/init.dat'
        datf = open(dat_file, "w")

        dat = [["AS_number"],["links"],["nodes"],["configurations"],["flows"]]

        for d in dbname_list:
            plot_init (username, d, dat)


        # d = dat[0]
        # datf.write (d[0] + "\t" + str (d[1]) + "\t" + str (d[2]) + "\t" + str (d[3]) + "\n")

        for d in dat[1:]:
            datf.write (d[0] + "\t" + str (d[1]) + "\t" + str (d[2]) + "\t" + str (d[3]) + "\n")

        gnuplot_script = '/Users/anduo/Documents/NSDI15/codes/prototype/dat/init.plt'
        gsf = open(gnuplot_script, "w")
        gsf.write ('# gnuplot script\n')

        gsf.write ('''
reset
set term pdfcairo
set output '/Users/anduo/Documents/NSDI15/codes/prototype/dat/init.pdf'\n''')

        # gsf.write ('set title "Verification time for AS ' + str (ISP_number) + " initialized with " + dbname + '"\n')
        gsf.write ('''
set xrange [-0.3 : 3.5]
# set xtics border in scale 1,0.5 # nomirror rotate by -30  offset character 0, 0, 0 autojustify
# set key autotitle columnhead
set logscale y

set boxwidth 0.8 absolute
set style data histograms
set style histogram cluster
set style fill solid 1.00 noborder

set terminal pdfcairo font "Gill Sans,9" linewidth 4 rounded fontscale 1.0
set style line 80 lt rgb "#808080"
set style line 81 lt 0  # dashed
set style line 81 lt rgb "#808080"
set grid back linestyle 81
set border 3 back linestyle 80
set style line 1 lt rgb "#A00000" lw 2 pt 1
set style line 2 lt rgb "#00A000" lw 2 pt 6
set style line 3 lt rgb "#5060D0" lw 2 pt 2
set style line 4 lt rgb "#F25900" lw 2 pt 9
set xtics
set key top left

plot "./dat/init.dat" using 2:xticlabels(1) title "AS ''' +dbname_list[0][2:6]+ '''",\\
 '' using 3:xticlabels(1) title "AS ''' +dbname_list[1][2:6]+ '''",\\
 '' using 4:xticlabels(1) title "AS ''' +dbname_list[2][2:6]+ '''" ''')

        # gsf.write ('\nplot "' + dat_file + '" ')
        # gsf.write ('using 2:xtic(1), \\')
        # gsf.write ("\n''using 3:xtic(1), \\")
        # gsf.write ("\n''using 4:xtic(1)")
        gsf.close ()

        # os.system ("cd ./dat")
        os.system ("gnuplot " + gnuplot_script)

        # subprocess.check_output(["gnuplot", gnuplot_script])

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

def plot_verification (dbname_list):

    for dbname in dbname_list:
        gnu_log = 'verify_' + dbname + '.dat'
        analyze (username, dbname, gnu_log)
        ISP_number = dbname[2:6]

        gnuplot_script = './dat/verify_' + dbname + '.plt'
        gsf = open(gnuplot_script, "w")
        gsf.write ('# gnuplot script\n')
        gsf.write ('reset\n')

        gsf.write ('''
    set terminal png
    set output './dat/verify_''' + dbname + ".png'\n")
        gsf.write ('set title "Verification time for AS ' + str (ISP_number) + " initialized with " + dbname + '"\n')
        gsf.write ('''
    set xrange [ -0.5 : 3.5]
    set xtics border in scale 1,0.5 nomirror rotate by -30  offset character 0, 0, 0 autojustify
    set key autotitle columnhead
    set xlabel "Verification tasks"
    set ylabel "Time (ms)"
    set style line 1 lc rgb '#0060ad' lt 1 lw 2 pt 7 ps .5   # --- blue
    set style line 2 lc rgb '#dd181f' lt 1 lw 2 pt 5 ps .5   # --- red\n''')

        gsf.write ('\nplot "./dat/' + gnu_log + '" ')
        gsf.write ('using 2:xtic(1) index 1 with linespoints notitle, \\')
        for i in range (2, rounds-1):
            gsf.write ("\n''		using 2 index " + str (i) + " with linespoints notitle, \\")
        gsf.write ("\n''		using 2 index " + str (rounds-1) + " with linespoints notitle")
        gsf.close ()

        # os.system ("cd ./dat")
        os.system ("gnuplot " + gnuplot_script)

if __name__ == '__main__':

    rounds = 1
    flow_num = 1000
    dbname_list = ["as4755ribd", "as6461ribd", "as7018ribd"]
    username = "anduo"

    g = gp.gnuplot(persist = True)
    g ('set term pdfcairo')
    g ("set logscale y")
    # g ("set key top left")
    g ('set key bottom right')

    g ('set terminal pdfcairo font "Gill Sans,9" linewidth 4 rounded fontscale 1.0')
    g ('set style line 80 lt rgb "#808080"')
    g ('set style line 81 lt 0  # dashed')
    g ('set style line 81 lt rgb "#808080"')
    g ('set grid back linestyle 81')
    g ('set border 3 back linestyle 80')
    g ('set style line 1 lt rgb "#A00000" lw 2 pt 1')
    g ('set style line 2 lt rgb "#00A000" lw 2 pt 6')
    g ('set style line 3 lt rgb "#5060D0" lw 2 pt 2')
    g ('set style line 4 lt rgb "#F25900" lw 2 pt 9')

    # plot_all_init (username, dbname_list)

    # plot_fg_all (username, dbname_list, flow_num, g)
    # plot_fg_all2 (username, dbname_list, flow_num)
    
    # plot_verify_cdf (username, dbname, flow_num, g)
    # plot_verify_cdf2 (username, dbname, flow_num)

    # plot_vn_synthesize (username, dbname, rounds, g)
    # plot_vn_synthesize2 (username, dbname, rounds)

    plot_obs_synthesize2 (username, dbname, rounds)

    ############################################################
    # outdated
    # plot_verify (username, dbname_list[2], flow_num)
    # plot_verification (dbname_list)



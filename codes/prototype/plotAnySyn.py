# import sys
# import time
# import random
# import os
# import glob
import libAnalyzeSynthesize
import Gnuplot
import Gnuplot.funcutils
# import subprocess
# sys.path.append('/usr/local/lib/python2.7/site-packages/')
# import psycopg2
# import psycopg2.extras

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

def plot_vn_synthesize (username, dbname, rounds):
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

        outputfile = './dat/vn_synthesis_cdf' + str (rounds) + '.png'
        print "plot vn synthesize: start gnuplot"

        g = Gnuplot.Gnuplot ()
        g.reset ()
        g.title ("Synthesis for virtual network policy, AS " + str (dbname[2:6]))
        g.xlabel('Total of ' + str (rounds) + ' randomly picked insertion / deletion / updates')
        g.ylabel('Time (millisecond)')
        g ("set logscale y")
        g ("set key top left")

        d1 = Gnuplot.Data (x_del, y_del, with_="linespoints lw .1", title = "policy deletion")
        d2 = Gnuplot.Data (x_switch, y_switch, with_="linespoints lw .1", title = "compute per-switch configuration delta")

        d3 = Gnuplot.Data (x_ins, y_ins, with_="linespoints lw .1", title = "policy insertion")
        d4 = Gnuplot.Data (x_up, y_up, with_="linespoints lw .1", title = "policy update")

        # x4 = x + [len (x)]
        # y4 = [1] * (len (x) + 1)
        g.plot (d1, d3, d4, d2)
        g.hardcopy(outputfile, terminal = 'png')

        g.clear ()



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

# class discrete_cdf:
#     def __init__(data):
#         self._data = data # must be sorted
#         self._data_len = float(len(data))

#     def __call__(point):
#         return (len(self._data[:bisect_left(self._data, point)]) / 
#                 self._data_len)

def plot_verify_cdf (username, dbname, rounds):

    [b, y1, y2, y3] = verify (username, dbname, rounds)
    # yk = [0] * len (x)

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

    outputfile = './dat/verify_cdf' + str (rounds) + '.png'
    print "plot synthesize: start gnuplot"

    try:
        g = Gnuplot.Gnuplot ()
        g.reset ()
        g.title ("Verification time for AS " + str (dbname[2:6]) + " relative to forwarding graph generation")
        g.xlabel('Total of ' + str (rounds) + ' randomly picked flows')
        g.ylabel('Time (millisecond)')
        g ("set logscale y")
        g ("set key top left")

        # xrange_max = len (x)
        # g('set xrange[0:' + str (xrange_max) +']')

        y1.sort ()
        d1 = Gnuplot.Data (x1, y1, with_="linespoints lw .1", title = "disjoint path")
        print x1
        print y1

        y2.sort ()
        d2 = Gnuplot.Data (x2, y2, with_="linespoints lw .1", title = "loop free")

        y3.sort ()
        d3 = Gnuplot.Data (x3, y3, with_="linespoints lw .1", title = "black hole")

        # x4 = x + [len (x)]
        # y4 = [1] * (len (x) + 1)
        b.sort ()
        d4 = Gnuplot.Data (xb, b, with_="lines lt -1", title = "forwarding graph")
        print xb
        print b

        g.plot (d1, d2, d3, d4)
        g.hardcopy(outputfile, terminal = 'png')

        g.clear ()
        
    except:
        print "plot verification erro"


# def plot_verify (username, dbname, rounds):

#     [x, y1, y2, y3] = verify (username, dbname, rounds)
#     yk = [0] * len (x)
#     # print x
#     # print y3

#     outputfile = './dat/verify' + str (rounds) + '.png'
#     print "plot synthesize: start gnuplot"

#     try:
#         g = Gnuplot.Gnuplot (persist = 1)
#         g.reset ()
#         g.title ("Verification time for AS " + str (dbname[2:6]) + " relative to forwarding graph generation")
#         g.xlabel('Total of ' + str (rounds) + ' randomly picked flows')
#         # g.ylabel('Time, relative to time for forwarding graph generation')
#         g ("set key top left")

#         xrange_max = len (x)
#         g('set xrange[0:' + str (xrange_max) +']')
#         # g ("set key font ",8")

#         # d1k = Gnuplot.Data ([-1], [0], with_="points pt 5 ps 2", title = "disjoint path")
#         # d1 = Gnuplot.Data (x, y1, with_="points pt 5 ps .3 rgb 'red'", title = None)

#         # d2k = Gnuplot.Data ([-1], [0], with_="points pt 7 ps 2", title = "loop free")
#         # d2 = Gnuplot.Data (x, y2, with_="points pt 7 ps .3", title = None)

#         d1 = Gnuplot.Data (x, y1, with_="linespoints lw .1", title = "disjoint path")
#         d2 = Gnuplot.Data (x, y2, with_="linespoints lw .1", title = "loop free")
#         d3 = Gnuplot.Data (x, y3, with_="linespoints lw .1", title = "black hole")

#         # d3k = Gnuplot.Data ([-1], [0], with_="points pt 9 ps 2", title = "black hole")
#         # d3 = Gnuplot.Data (x, y3, with_="points pt 9 ps .3", title = None)
#         # d1 = Gnuplot.Data (x, y1, with_="points pt 5 ps .3", notitle)
#         # d2 = Gnuplot.Data (x, y2, with_="points pt 7 ps .3", notitle)
#         # d3 = Gnuplot.Data (x, y3, with_="points pt 9 ps .3", notitle)
#         # d Gnuplot.Data (x[i], y[i], with_="linespoints lw 3 pt 3", title = "AS " + dbname_list[i][2:6]))

#         x4 = x + [len (x)]
#         y4 = [1] * (len (x) + 1)
#         d4 = Gnuplot.Data (x4, y4, with_="lines lt -1", title = "forwarding graph")

#         # g.plot (d1k, d1, d2k, d2, d3k, d3, d4)
#         g.plot (d1, d2, d3, d4)
#         g.hardcopy(outputfile, terminal = 'png')

#         g.clear ()
        
#     except:
#         print "plot verification erro"

def plot_fg_cdf (username, dbname, xsize):

    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        print "plot_init: Connect to database " + dbname + ", as user " + username

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

def plot_fg_all (username, dbname_list, xsize):

    fg_cdf_list = []
    for i in range (len(dbname_list)):
        fg_cdf_list.append (plot_fg_cdf (username, dbname_list[i], xsize))

    # print fg_cdf_list[0]

    outputfile = './dat/fg_cdf_' + str (xsize) + '.png'

    try:
        g = Gnuplot.Gnuplot ()
        g.reset ()
        g.title ("Cumulative Distribution")

        d = []
        x = []
        y = []

        for i in range (len (fg_cdf_list)):
            
            x.append(fg_cdf_list[i][0])
            print "x[i]"
            print x[i]
            y.append(fg_cdf_list[i][1])
            print "y[i]"
            print y[i]
            # x1= [f['x'] for f in fg_cdf]
            # y1= [f['y'] for f in fg_cdf]
            # d1=Gnuplot.Data(x1,y1,with_="line")
            d.append( Gnuplot.Data (x[i], y[i], with_="linespoints lw 3 pt 3", title = "AS " + dbname_list[i][2:6]))

            # x2= [f['x'] for f in fg_cdf]
            # y2= [f['y']+1 for f in fg_cdf]
            # d2 =Gnuplot.Data(x2,y2,with_="line")
        g.xlabel('Fraction of forwarding graphs (total of ' + str (xsize) + ' randomly picked flows)')
        g.ylabel('Generation Time (millisecond)')

        g ("set key top left")

        g.plot (d[0], d[1], d[2])
        g.hardcopy(outputfile, terminal = 'png')

        g.clear ()
        
    except:
        print "Erro"

    # # g.plot(d1)   #uncomment this line if you want to see the gnuplot window

    print "plot_init: finish"


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
set terminal png
set output '/Users/anduo/Documents/NSDI15/codes/prototype/dat/init.png'\n''')

        # gsf.write ('set title "Verification time for AS ' + str (ISP_number) + " initialized with " + dbname + '"\n')
        gsf.write ('''
set xrange [-0.3 : 3.5]
# set xtics border in scale 1,0.5 # nomirror rotate by -30  offset character 0, 0, 0 autojustify
# set key autotitle columnhead
set logscale y

set boxwidth 0.9 relative
set style data histograms
set style histogram cluster
set style fill solid .5 border lt -1
set xtics
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

    rounds = 1000

    dbname_list = ["as4755ribd", "as6461ribd", "as7018ribd"]
    # dbname_list = ["as4755rib1000", "as6461rib1000", "as7018rib1000"]
    username = "anduo"
    flow_num = 10000

    # plot_verify (username, dbname_list[2], flow_num)

    # plot_verification (dbname_list)

    # plot_all_init (username, dbname_list)

    # plot_fg_cdf (username, dbname_list[2], flow_num)

    # plot_fg_all (username, dbname_list, flow_num)

    plot_verify_cdf (username, dbname, flow_num)
    # plot_vn_synthesize (username, dbname, rounds)

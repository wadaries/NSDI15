import libAnalyze

# rib_prefixes = "rib20011204_prefixes.txt"
# rib_peerIPs = "rib20011204_nodes.txt"
# ISP_number = 1221
# ISP_nodes = "1221_nodes.txt"
# ISP_edges = "1221_edges.txt"
# global dbname

def plot_all_init (username, dbname_list):
    
        dat_file = './dat/init.dat'
        dat = open(dat_file, "w")

        for d in dbname_list:
            plot_init (username, d, dat)






def plot_init (username, dbname, dat):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        print "plot_init: Connect to database " + dbname + ", as user " + username

        dat.write ('"number"\t "AS ' + dbname[2:6] + '"\n')

        dict_cur.execute ("SELECT count (*) FROM topology ;")
        edge_size = dict_cur.fetchall () [0][0]
        dat.write ('"links"     \t' + str (edge_size) + '\n')

        dict_cur.execute ("SELECT count (*) FROM switches ;")
        node_size = dict_cur.fetchall () [0][0]
        dat.write ('"nodes"     \t' + str (node_size) + '\n')


        dict_cur.execute ("SELECT count (*) FROM configuration ;")
        conf_num = dict_cur.fetchall ()[0][0]
        dat.write ('"configurations" \t' + str (conf_num) + '\n')

        dict_cur.execute ("SELECT count (*) FROM flow_constraints ;")
        flow_num = dict_cur.fetchall ()[0][0]
        dat.write ('"flows"     \t' + str (flow_num) + '\n\n')

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e
    finally:
        if conn:
            conn.close()
        print "plot_init: finish"


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

        os.system ("cd ./dat")
        os.system ("gnuplot " + gnuplot_script)

if __name__ == '__main__':

    username = "anduo"
    rounds = 200

    dbname_list = ["as4755ribd", "as6461ribd", "as7018ribd"]

    # plot_verification (dbname_list)

    plot_all_init (username, dbname_list)

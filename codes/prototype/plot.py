execfile ("./libAnalyzeSynthesize.py")
import libAnalyzeSynthesize

gnuplot_script = '''
reset

set style line 80 lt -1 lc rgb "#808080"
set style line 81 lt 0  # dashed
set style line 81 lt rgb "#808080"
set grid back linestyle 81
set border 3 back linestyle 80

set style line 1 lt rgb "#A00000" lw 1 pt 1 ps 1
set style line 2 lt rgb "#00A000" lw 1 pt 6 ps 1
set style line 3 lt rgb "#5060D0" lw 1 pt 2 ps 1
set style line 4 lt rgb "#F25900" lw 1 pt 9 ps 1

set termoption dashed
set style line 11 lt rgb "#A00000" lw 3 
set style line 12 lt rgb "#00A000" lw 3
set style line 13 lt rgb "#5060D0" lw 3
set style line 14 lt rgb "#F25900" lw 3

set xtics nomirror
set ytics nomirror'''
# '''set output "''' + outputfile + '''"

def db_aslist ():
    username = "anduo"
    dbname = 'postgres'
    try:
        conn = psycopg2.connect(database=dbname, user=username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        print "db_aslist"

        dict_cur.execute ('''SELECT datname FROM pg_database
        WHERE datname LIKE '%d';''')
        dbs = [d[0] for d in dict_cur.fetchall ()]
        dbs = [dbs[0]] + dbs[2:]
        return dbs
            
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e

def db_conflist (asn):
    username = "anduo"
    dbname = 'postgres'
    try:
        conn = psycopg2.connect(database=dbname, user=username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        print "db_aslist"

        dict_cur.execute ('''SELECT datname FROM pg_database
        WHERE datname LIKE %s;''', (['%'+ str(asn) + '%']))  
        dbs = [d[0] for d in dict_cur.fetchall ()]
        # dbs = [dbs[0]] + dbs[2:]
        return dbs
            
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e


def db_configlist ():
    username = "anduo"
    dbname = 'postgres'
    try:
        conn = psycopg2.connect(database=dbname, user=username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        print "db_configlist"

        dict_cur.execute ('''SELECT datname FROM pg_database
        WHERE datname LIKE '%3356%';''')
        db_configlist = [d[0] for d in dict_cur.fetchall ()]
        if conn: conn.close ()

        db_config_dic = {}
        for db in db_configlist:
            conn = psycopg2.connect(database=db, user=username)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
            dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            print "Connect to database " + db + ", as user " + username

            dict_cur.execute ("SELECT count(*) FROM configuration;")
            db_config_dic[db] = dict_cur.fetchall ()[0][0]

        return db_config_dic
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e

def plot_data_set (dbs):
    print "start plot_data_set"
    datfile = os.getcwd () + '/dat/datset.dat'
    rounds = 200
    datfile2 = os.getcwd () + '/dat/fg_size_count'+ str (rounds) + '.dat'
    datfile3 = os.getcwd () + '/dat/path_len'+ str (rounds) + '.dat'
    pdffigfile = os.getcwd () + '/dat/pdf_figures/datset.pdf'
    plotfile = os.getcwd () + '/dat/datset.plt'

    if os.path.isfile (datfile) == False:    
        df = open(datfile, "w")
        try:
            for db in dbs:
                conn = psycopg2.connect (database = db, user = username)
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
                dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
                num_AS = 'AS' + str (db[2:6])
                dict_cur.execute ("SELECT count(*) FROM switches;")
                num_switch = dict_cur.fetchall ()[0][0]
                dict_cur.execute ("SELECT count (*) FROM configuration;")
                num_configuration = dict_cur.fetchall ()[0][0]
                dict_cur.execute ("SELECT count (*) FROM topology;")
                num_link = dict_cur.fetchall ()[0][0]
                if conn: conn.close ()
                if num_AS != 'AS6461':
                    df.write ('"' + num_AS + '"' + '\t' + str (num_switch) + '\t' + str (num_configuration) + '\t' + str (num_link) + '\n')
            
        except psycopg2.DatabaseError, e:
            print 'Error %s' % e
        df.close ()

    as_dic = {'as4755ribd':1, 'as7018ribd':4, 'as3356ribd':2, 'as2914ribd':3}
    if os.path.isfile (datfile2) == False:
        df2 = open (datfile2, "w")
        try:
            for db in dbs:
                fsc = fg_cdf ('anduo', db, rounds)[1]
                index = as_dic[db]
                for i in range (len (fsc)):
                    df2.write (str (index) + '\t' + '"'+db[0:6].upper ()+ '"' + '\t' + str (fsc[i][0]) + '\t'+str (float (fsc[i][1])/5) + '\n')
            df2.close ()
        except psycopg2.DatabaseError, e: print 'Error %s' % e

    if os.path.isfile (datfile3) == False:
        df3 = open (datfile3, "w")
        try:
            for db in dbs:
                path_hops = get_path_len ('anduo', db, rounds)
                index = as_dic[db]
                for i in range (len (path_hops)):
                    df3.write (str (index) + '\t' + '"'+db[0:6].upper ()+ '"' + '\t' + str (path_hops[i][0]) + '\t'+str (float (path_hops[i][1])/5) + '\n')
            df3.close ()
        except psycopg2.DatabaseError, e: print 'Error %s' % e

    pf = open(plotfile, "w")
    pf.write (gnuplot_script)
    pf.write ('''
set output "''' + pdffigfile + '''"
set terminal pdfcairo size 8,3 font "Gill Sans,9" linewidth 2 rounded fontscale 1
# default 5 by 3 (inches)

set multiplot layout 1,3
set lmargin -2
set rmargin -3

set xtics rotate
set key top left
set ylabel "Configuration (# entries)" offset .5,0
set xlabel "Network size (# switches)"

set xrange [-2000:14000]
set yrange [5000000:14000000]

plot "'''+ datfile +'''" using 2:3 pt 7 notitle,\\
'' using 2:3:1:xtic(2):ytic(3) with labels offset 0,.8 notitle

set xrange [0:5]
set yrange [0:150]
set ylabel "Forwarding graph (# nodes)" offset 1,0
set xlabel "AS number"
plot "'''+ datfile2 +'''" using 1:3 pt 3 ps .3 notitle,\\
''using 1:3:4:xtic(2) with points pointsize variable lt 1 pt 19 notitle

set ylabel "Path length (# hops)" offset 1,0
set yrange [0:50]
plot "'''+ datfile3 +'''" using 1:3 pt 3 ps .3 notitle,\\
''using 1:3:4:xtic(2) with points pointsize variable lt 1 pt 19 notitle
unset multiplot''')

    pf.close ()
    os.system ("gnuplot " + plotfile)
    print "finish plot_data_set"

def plot_aslist (rounds, gen_dat, dbname_list):
    print "start plot_aslist " + gen_dat.__name__
    datfile = os.getcwd () + '/dat/'+ gen_dat.__name__ +'_ases_' + str (rounds) + '.dat'
    pdffigfile = os.getcwd () + '/dat/pdf_figures/' +gen_dat.__name__+ '_ases_' + str (rounds)+'.pdf'
    plotfile = os.getcwd () + '/dat/'+ gen_dat.__name__ + '_ases_' +str (rounds) + '.plt'

    if os.path.isfile (datfile) == False:
        df = open(datfile, "w")
        ys = []
        for db in dbname_list:
            if gen_dat.__name__ == 'fg_cdf':
                dat = gen_dat ('anduo', db, rounds)[0]
            else:
                dat = gen_dat ('anduo', db, rounds)
            ys.append (dat)
        x = gen_cdf_x (ys[0])

        for i in range (len (x)):
            y_string = ''
            for j in range (len (ys)):
                y_string = y_string + '\t' + str (ys[j][i])
            df.write (str (x[i]) + y_string + '\n')
        df.close ()

    pf = open (plotfile, "w")
    pf.write (gnuplot_script)
    pf.write ('''
set output "''' +pdffigfile+ '''"
set terminal pdfcairo font "Gill Sans,9" linewidth 2 rounded fontscale 1

set key top left
set xlabel "Time (millisecond)"
set ylabel "CDF"
set logscale x

plot "'''+ datfile +'''" using 2:1 with lines ls 11 title "AS4755",\\
'' using 4:1 with lines ls 13 title "AS3356",\\
'' using 5:1 with lines ls 14 title "AS2914",\\
'' using 3:1 with lines ls 12 title "AS7018"''')

    pf.close ()
    os.system ("gnuplot " + plotfile)
    print "finish plot_aslist" + gen_dat.__name__

def plot_verify (rounds, gen_dat_list, dbname_list):
    datfile = []
    for g in gen_dat_list:
        datfile.append (os.getcwd () + '/dat/dat/'+ g.__name__ +'_ases_' + str (rounds) + '.dat')
    pdffigfile = os.getcwd () + '/dat/pdf_figures/verify_ases_' + str (rounds)+'.pdf'
    plotfile = os.getcwd () + '/dat/verify_ases_' +str (rounds) + '.plt'

    for i in range (len (gen_dat_list)):
        if os.path.isfile (datfile[i]) == False:
            df = open(datfile[i], "w")
            ys = []
            for db in dbname_list:
                print db
                if gen_dat_list[i].__name__ == 'fg_cdf':
                    dat = gen_dat_list[i] ('anduo', db, rounds)[0]
                else:
                    dat = gen_dat_list[i] ('anduo', db, rounds)
                ys.append (dat)
                print dat
            x = gen_cdf_x (ys[0])

            for j in range (len (x)):
                y_string = ''
                for k in range (len (ys)):
                    y_string = y_string + '\t' + str (ys[k][j])
                df.write (str (x[j]) + y_string + '\n')
            df.close ()

    title_dict = {gen_dat_list[0].__name__: 'forwarding graph', gen_dat_list[1].__name__: 'black hole', gen_dat_list[2].__name__: 'loop free'}

    plot_script = ''
    for i in range (len (gen_dat_list)):
        if i == 1:
            plot_script = plot_script + '''
set key bottom right box opaque
set xlabel "Time (millisecond)" '''
        else:
            plot_script = plot_script + '''
unset key
set xlabel "   " '''

        plot_script = plot_script + '''
set title "''' + title_dict[gen_dat_list[i].__name__] + '''"        
plot "'''+ datfile[i] +'''" using 2:1 with lines ls 11 title "AS4755",\\
'' using 4:1 with lines ls 13 title "AS3356",\\
'' using 5:1 with lines ls 14 title "AS2914",\\
'' using 3:1 with lines ls 12 title "AS7018"
unset key
unset ylabel
set lmargin 0''' + '\n'
        
    pf = open (plotfile, "w")
    pf.write (gnuplot_script)
    pf.write ('''
set output "''' +pdffigfile+ '''"
set terminal pdfcairo size 9,3 font "Gill Sans,9" linewidth 2 rounded fontscale 1
set multiplot layout 1,3
set lmargin -2
set rmargin -3

set ylabel "CDF"
set logscale x
''' + plot_script)
    pf.close ()

    os.system ("gnuplot " + plotfile)
    print "finish plot_vs"

def trans_syn_time (rounds, syn_time, dbname_list):
    def add_list_item (lt, it):
        size = len (lt)
        for i in range (size):
            lt[i] = lt[i] + [it[i]]
        return lt

    def trans_matrix (lt):
        size = len (lt[0])
        tdlt = []
        for s in range (size):
            dlt = []
            for i in range (len (lt)):
                dlt.append (lt[i][s])
            tdlt.append (dlt)
        return tdlt
            
    try:
        dys = []
        dbs = []

        conn = psycopg2.connect (database = dbname_list[0], user = 'anduo')
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        node_size = 10
        flow_size = 100
        [nodes, flows] = select_nodes_flows (dict_cur, node_size, flow_size)
        conn.close ()

        for d in range (len (dbname_list)):
            print d
            conn = psycopg2.connect (database = dbname_list[d], user = 'anduo')
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
            dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            if syn_time.__name__ == 'time_obs':
                print "obs_init for " + dbname_list[d]
                obs_init (dict_cur, nodes, flows)
                ys = [[]] * 2
            elif syn_time.__name__ == 'time_e2e_vn':
                print "vn_init for " + dbname_list[d]
                vn_init (dict_cur, nodes, flows)
                ys = [[]] * 3

            print "get syntheis time for " + dbname_list[d]
            for i in range (rounds):
                print "round " + str (i)
                y = syn_time (dict_cur)
                ys = add_list_item (ys, y)

            print ys

            for i in range (len (ys)):
                ys[i].sort ()
            print ys

            dys.append (ys)
    
        new_dys = trans_matrix (dys)
        return new_dys

    except psycopg2.DatabaseError, e:
        print 'Error %s' % e

def plot_synthesize (rounds, dbname_list, syn_time):

    print "start plot_synthesize " 
    if syn_time.__name__ == 'time_e2e_vn':
        tasks = ['vn_policy_deletion', 'vn_switch_delta', 'vn_policy_insert']
        pdffigfile = os.getcwd () + '/dat/pdf_figures/obs_synthesize_ases_' + str (rounds)+'.pdf'
        plotfile = os.getcwd () + '/dat/obs_synthesize_ases_' +str (rounds) + '.plt'
        pdfwidth = 8
        pdftitle = 'synthesize virtual network policy'
    elif syn_time.__name__ == 'time_obs':
        tasks = ['obs_policy_insert', 'obs_policy_deletion']
        pdffigfile = os.getcwd () + '/dat/pdf_figures/vn_synthesize_ases_' + str (rounds)+'.pdf'
        plotfile = os.getcwd () + '/dat/vn_synthesize_ases_' +str (rounds) + '.plt'
        pdfwidth = 5
        pdftitle = 'synthesize one big switch policy'

    datfile = []
    for i in range (len (tasks)):
        datfile.append (os.getcwd () + '/dat/dat/'+ tasks[i] +'_ases_' + str (rounds) + '.dat')

    if os.path.isfile (datfile[0]) == False:
        dat = trans_syn_time (rounds, syn_time, dbname_list)
        print "dat"
        print dat
        x = gen_cdf_x (dat[0][0])
        
        for i in range (len (tasks)):
            df = open(datfile[i], "w")
            for k in range (len (x)):
                df.write (str (x[k]))
                for j in range (len (dbname_list)):
                    df.write ('\t' + str(dat[i][j][k]))
                df.write ('\n')
            df.close ()

    # pdffigfile = os.getcwd () + '/dat/pdf_figures/synthesize_ases_' + str (rounds)+'.pdf'
    # plotfile = os.getcwd () + '/dat/synthesize_ases_' +str (rounds) + '.plt'

    title_dict = {'obs_policy_insert': 'add new policy', 'obs_policy_deletion': 'remove old policy'}
    plot_script = ''
    for i in range (len(tasks)) :
        plot_script = plot_script + '''
set title "''' + tasks[i] + '''"        
plot "'''+ datfile[i] +'''" using 2:1 with lines ls 11 title "10000",\\
'' using 3:1 with lines ls 13 title "100000",\\
'' using 4:1 with lines ls 14 title "300000"\n''' 
# ,\\
# '' using 2:1 with lines ls 12 title "AS3356d"''' + '\n'
    
    pf = open (plotfile, "w")
    pf.write (gnuplot_script)
    pf.write ('''
set output "''' +pdffigfile+ '''"
set terminal pdfcairo size '''+str (pdfwidth)+ ''',3 font "Gill Sans,9" linewidth 2 rounded fontscale 1
set multiplot layout 1,''' + str (len (tasks)) + '''title "''' + pdftitle + '''" 
set lmargin -2
set rmargin -3

set key top left
set xlabel "Time (millisecond)"
set ylabel "CDF"
set logscale x
''' + plot_script)
    pf.close ()

    os.system ("gnuplot " + plotfile)

    print "finish plot_synthesize"

if __name__ == '__main__':

    rounds = 99
    db_aslist = ['as4755ribd', 'as7018ribd', 'as3356ribd', 'as2914ribd']
    db_conflist = ['as3356rib10000', 'as3356rib100000', 'as3356rib300000']

    # for db in db_aslist:
    #     print "prepare_vn_obs_views for " + db
    #     prepare_vn_obs_views ('anduo', db)

    for db in db_conflist:
        print "prepare_vn_obs_views for " + db
        prepare_vn_obs_views ('anduo', db)

    plot_data_set (db_aslist)

    # plot_verify(rounds, [fg_cdf, black_hole, loop_free], db_aslist)

    plot_synthesize (100, db_conflist, time_obs)
    plot_synthesize (5, db_conflist, time_e2e_vn)


    ############################################################
    # db_conflist = db_conflist (3356)
    # db_aslist = db_aslist ()
    # plot_aslist (rounds, fg_cdf, db_aslist)
    # plot_aslist (rounds, black_hole, db_aslist)
    # plot_aslist (rounds, loop_free, db_aslist)

    ############################################################
    # plot_all_init (username, dbname_list)

    # plot_fg_all (username, dbname_list, rounds, g)
    # plot_fg_cdf2 (username, dbname_list, rounds)

    # dbname = "as4755ribd"
    # plot_verify_cdf (username, dbname, rounds, g)
    # plot_verify_cdf2 (username, dbname, rounds)

    # plot_vn_synthesize (username, dbname, rounds, g)
    # plot_vn_synthesize2 (username, dbname, rounds)

    # dbname = "as7018ribd"
    # dbname = "as6461ribd"
    # plot_obs_synthesize2 (username, dbname, rounds)

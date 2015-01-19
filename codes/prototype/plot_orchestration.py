execfile ("./create_playground.py")
import create_playground

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

def gen_cdf_x (y_list):
    x = []
    xlen = len (y_list)
    for i in range (xlen):
        xt = float(i+1)/ xlen
        x.append (xt)
    return x

def sort_as ():
    asfile = open (os.getcwd() + '/ISP_topo/' + "stat", "r")
    asl = []
    for af in asfile:
        if af[0] != "#":
            items = [int (i) for i in af.split ()]
            asl.append ([items[0], items[1], items[2]])
    asl.sort(key = lambda row: row[2])
    return asl

def initialize_db (sql_script, username, dbname, X):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
        print "Connect to database " + dbname + ", as user " + username

        # this function provided by libRouteviewReplay
        add_pgrouting_extension (cur, dbname)

        # load sql schema and toy network data
        dbscript  = open (sql_script,'r').read()
        cur.execute(dbscript)

        # initialize topology
        asl = sort_as ()
        as_picked = asl[int(X)][0]
        ISP_edges = os.getcwd() + '/ISP_topo/' + str(as_picked) + "_edges.txt"
        init_topology (cur, ISP_edges)

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e    
    finally:
        if conn: conn.close()

if __name__ == '__main__':

    username = 'anduo'
    xs = [0,5,7,9]
    dbs = ['as4755','as3356','as2914','as7018']
    sql_script = os.getcwd() + '/sql_files/' + "playground.sql"
    for i in range (4):
        create_db (dbs[i])
        initialize_db (sql_script, username, dbs[i], xs[i])
    
    del_flag = raw_input ('Clean the added database (y/n): ')
    if del_flag == 'y':
        for i in range (4):
            clean_db (dbs[i])

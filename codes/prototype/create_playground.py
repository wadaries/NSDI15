execfile ("libUtility.py")
execfile ("libRouteviewReplay.py")
execfile ("libParsers.py")
execfile ("libAnalyzeSynthesize.py")
import libRouteviewReplay
import libAnalyzeSynthesize
import subprocess

def sort_as ():
    asfile = open (os.getcwd() + '/ISP_topo/' + "stat", "r")
    asl = []
    for af in asfile:
        if af[0] != "#":
            items = [int (i) for i in af.split ()]
            asl.append ([items[0], items[1], items[2]])

    asl.sort(key = lambda row: row[2])
    return asl

def init_topology (cursor, ISP_edges_file):
        
    f = open (ISP_edges_file, "r").readlines ()

    for edge in f:
        ed = edge[:-1].split()
        try:
            cursor.execute("""INSERT INTO tp(sid, nid) VALUES (%s, %s);""", (int(ed[0]), int(ed[1])))
        except psycopg2.DatabaseError, e:
            print "Unable to insert into topology table: %s" % str(e)

    try:
        cursor.execute ("""
        INSERT INTO tm VALUES (4,23, 33, 1);
        INSERT INTO tm VALUES (5,100, 50, 1);
        INSERT INTO p1 VALUES (1,'on');
        """)
    except psycopg2.DatabaseError, e:
        print "Unable to add post-mortem tuples: %s" % str(e)

    print "Initialize topology table with edges in " + ISP_edges_file + "\n"


def initialize_playground (sql_script, username, dbname):
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
        as_n = int (raw_input ('Input the x-th largest AS: '))
        as_picked = asl[int(as_n)][0]
        ISP_edges = os.getcwd() + '/ISP_topo/' + str(as_picked) + "_edges.txt"
        init_topology (cur, ISP_edges)

        # the following three functions provided by libRouteviewReplay
        # add_reachability_perflow_fun (cur)
        # add_reachability_table (cur, 1000)
        # add_configuration_view (cur)

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e    

    finally:
        if conn: conn.close()

def add_pl_extension (dbname):
    try:
        conn = psycopg2.connect(database= dbname, user= "postgres")
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()

        # add plpython extension by superuser
        cur.execute ("CREATE EXTENSION plpythonu;")

        # add permission for everyone
        cur.execute ("update pg_language SET lanpltrusted = true WHERE lanname = 'plpythonu';")

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname 
        print 'Error %s' % e    

    finally:
        if conn: conn.close()

if __name__ == '__main__':

    sql_script = os.getcwd() + '/sql_files/' + "playground.sql"
    
    # username = raw_input ('Input user name: ')
    username = 'anduo'
    dbname = raw_input ('Input database name: ')

    # this function provided by libRouteviewReplay
    create_db (dbname)
    # add_pl_extension (dbname)

    initialize_playground (sql_script, username, dbname)

    del_flag = raw_input ('Clean the added database (y/n): ')
    if del_flag == 'y':
        clean_db (dbname)

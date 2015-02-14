execfile ("libUtility.py")
execfile ("libRouteviewReplay.py")
execfile ("libParsers.py")
execfile ("libAnalyzeSynthesize.py")
import libRouteviewReplay
import libAnalyzeSynthesize
import subprocess
import datetime

def create_mininet_topo (dbname):
    try:
        conn = psycopg2.connect(database= dbname, user= "postgres")
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cur.execute ("SELECT * FROM switches;")
        cs = cur.fetchall ()
        switches = [s['sid'] for s in cs]
        print switches

        cur.execute ("SELECT * FROM hosts;")
        cs = cur.fetchall ()
        hosts = [h['hid'] for h in cs]
        print hosts

        cur.execute ("SELECT * FROM tp;")
        cs = cur.fetchall ()
        links = [[l['sid'],l['nid']] for l in cs]
        print links

    except psycopg2.DatabaseError, e:
        print "Unable to add_pl_extension to database " + dbname 
        print 'Error %s' % e    
    finally:
        if conn: conn.close()

    def nid_name (nid, s, h):
        if nid in s:
            outid = 's' + str (nid)
        if nid in h:
            outid = 'h' + str (nid)
        return outid

    filename = os.getcwd () + '/mininet/dtp.py'
    fo = open(filename, "w")
    fo.write ('"""' + str (datetime.datetime.now ()))
    fo.write ('\n$ sudo mn --custom ~/sdndb/dtp.py --topo mytopo --test pingall')
    fo.write ('\n$ sudo mn --custom ~/sdndb/dtp.py --topo mytopo --mac --switch ovsk --controller remote')
    fo.write ('"""')

    fo.write ('\n')
    fo.write ("""
from mininet.topo import Topo

class MyTopo( Topo ):
    "Simple topology example."

    def __init__( self ):
        "Create custom topo."

        # Initialize topology
        Topo.__init__( self )
    """)

    for hid in hosts:
        h = 'h' + str (hid)
        fo.write ("""
        """ + h + """ = self.addHost('""" + h + """')""")
    fo.write ('\n')

    for sid in switches:
        s = 's' + str (sid)
        fo.write ("""
        """ + s + """ = self.addSwitch('""" + s + """')""")
    fo.write ('\n')

        
    for [nid1, nid2] in links:
        nname1 = nid_name (nid1, switches, hosts)
        nname2 = nid_name (nid2, switches, hosts)
        fo.write ("""
        self.addLink(""" + nname1 + "," + nname2+ """)""")

    fo.write ("""\n
topos = { 'mytopo': ( lambda: MyTopo() ) }
    """)
    fo.write ('\n')
    fo.close ()
    os.system ("scp " + filename + " mininet@mininet-vm:~/sdndb")

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

def load_data (dbname, username):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
        print "Connect to database " + dbname + ", as user " + username

        cur.execute ("""
        TRUNCATE TABLE tp cascade;
        TRUNCATE TABLE cf cascade;
        TRUNCATE TABLE tm cascade;
        INSERT INTO tp(sid, nid) VALUES (1,2), (2,1), (1,3), (3,1), (2,4), (4,2), (3,4), (4,3);
        INSERT INTO tp(sid, nid) VALUES (1,5), (5,1), (1,6), (6,1), (2,6), (6,2), (7,2), (2,7);
        INSERT INTO tp(sid, nid) VALUES (3,8), (8,3), (3,9), (9,3), (4,9), (9,4), (4,10), (10,4);
        INSERT INTO switches(sid) VALUES (4),(5),(6),(7);
        INSERT INTO hosts(hid) VALUES (1),(2),(3),(8),(9),(10);
        INSERT INTO tm(fid,src,dst,vol) VALUES (1,5,8,5), (2,7,10,9), (3,6,10,2);""")

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e    

    finally:
        if conn: conn.close()

def load_data2 (dbname, username):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
        print "Connect to database " + dbname + ", as user " + username

        cur.execute ("""
        TRUNCATE TABLE tp cascade;
        TRUNCATE TABLE cf cascade;
        TRUNCATE TABLE tm cascade;
        INSERT INTO switches(sid) VALUES (4),(5),(6);
        INSERT INTO hosts(hid) VALUES (1),(2),(3);
        INSERT INTO tp(sid, nid) VALUES (1,4), (2,5), (3,6);
        INSERT INTO tp(sid, nid) VALUES (4,5), (5,6), (6,4);
        INSERT INTO tm(fid,src,dst,vol) VALUES (1,1,2,1), (2,1,3,2);""")

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e    

    finally:
        if conn: conn.close()

def create_init_db_schema (dbname, username):

    def init_schema (sql_script, username, dbname):
        try:
            conn = psycopg2.connect(database= dbname, user= username)
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
            cur = conn.cursor()
            print "Connect to database " + dbname + ", as user " + username

            add_pgrouting_extension (cur, dbname)             # this function provided by libRouteviewReplay
            dbscript  = open (sql_script,'r').read()            # load sql schema
            cur.execute(dbscript)

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
            cur.execute ("CREATE EXTENSION IF NOT EXISTS plpythonu;")
            print "CREATE EXTENSION plpythonu; OK"

            # add permission for everyone
            cur.execute ("update pg_language SET lanpltrusted = true WHERE lanname = 'plpythonu';")
            print "update pg_language SET lanpltrusted = true WHERE lanname = 'plpythonu'; OK"
        except psycopg2.DatabaseError, e:
            print "Unable to add_pl_extension to database " + dbname 
            print 'Error %s' % e    
        finally:
            if conn: conn.close()

    create_db (dbname)
    add_pl_extension (dbname)

    sql_script = os.getcwd() + '/sql_files/' + "playground.sql"
    init_schema (sql_script, username, dbname)

if __name__ == '__main__':

    dbname = raw_input ('Input database name: ')
    username = 'anduo'

    create_init_db_schema (dbname, username)

    load_data2 (dbname, username)

    create_mininet_topo (dbname)

    del_flag = raw_input ('Clean the added database (y/n): ')
    if del_flag == 'y':
        clean_db (dbname)



execfile ("libUtility.py")
execfile ("libRouteviewReplay.py")
execfile ("libParsers.py")
execfile ("libAnalyzeSynthesize.py")
import libRouteviewReplay
import libAnalyzeSynthesize
import subprocess

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


def clean_db (dbname):
    try:
        conn = psycopg2.connect(database= "postgres", user= "postgres")
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()

        cur.execute ("drop database " + dbname)
        print 'Successfully drop database ' + dbname + '\n'

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
    add_pl_extension (dbname)

    initialize_playground (sql_script, username, dbname)

    del_flag = raw_input ('Clean the added database (y/n): ')
    if del_flag == 'y':
        clean_db (dbname)

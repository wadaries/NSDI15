import libUtility

def initialize (sql_script, username, dbname,
                rib_edges, rib_prefixes, rib_peerIPs,
                ISP_nodes, ISP_edges,
                log):

    setlog (log)
    logging.info ("------------------------------------------------------------")
    logging.info ("Successfully set log file\n")

    logging.info ("ISP instance (rocketfuel):  AS " + ISP_nodes.split ('.')[0].split ('_')[0])
    # logging.info ("RIB instance (routeview): " + rib_edges.split ('.')[0].split ('_')[0])
    # logging.info ("RIB instance size (number of routeview feeds): " + rib_edges.split ('.')[0].split ('_')[2])

    create_db (dbname)
    logging.info ("------------------------------------------------------------")
    logging.info ("Successfully create database in postgres\n")

    initialize_db (sql_script, username, dbname,
                   rib_edges, rib_prefixes, rib_peerIPs,
                   ISP_nodes, ISP_edges)
    logging.info ("------------------------------------------------------------")
    logging.info ("Successfully initialize database with RIB\n")

def create_db (dbname):
    try:
        conn = psycopg2.connect(database= 'postgres', user= 'postgres')
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
        print "Connect to database postgres, as user postgres"

        cur.execute ("SELECT datname FROM pg_database WHERE datistemplate = false;")
        c = cur.fetchall ()
        if dbname not in c:
            try:
                cur.execute ("CREATE DATABASE " + dbname + ";")
                print "Create database " + dbname

            except psycopg2.DatabaseError, e:
                print "Unable to create database " + dbname
                print 'Warning %s' % e

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database postgres, as user postgres"
        print 'Error %s' % e

    finally:
        if conn:
            conn.close()


def initialize_db (sql_script, username, dbname,
                   rib_edges, rib_prefixes, rib_peerIPs,
                   ISP_nodes, ISP_edges):

    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        cur = conn.cursor()
        print "Connect to database " + dbname + ", as user " + username

        add_pgrouting_extension (cur, dbname)

        create_schema (cur, sql_script)
    
        init_topology (cur, ISP_edges)
        
        init_configuration (cur,
                            rib_edges, rib_prefixes, rib_peerIPs,
                            ISP_nodes, ISP_edges)

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e    

    finally:
        if conn:
            conn.close()

def add_pgrouting_extension (cursor, dbname):
    
    cursor.execute ("SELECT 1 FROM pg_catalog.pg_namespace n JOIN pg_catalog.pg_proc p ON pronamespace = n.oid WHERE proname = 'pgr_dijkstra';")

    c = cursor.fetchall ()
    if c == []:
        os.system ("/usr/local/bin/psql -U postgres -f /usr/local/share/postgis/postgis.sql " + dbname)
        os.system ("/usr/local/bin/psql -U postgres -f /usr/local/share/postgis/spatial_ref_sys.sql " + dbname)
        os.system ("/usr/local/bin/psql -U postgres -f /usr/local/share/postgis/legacy.sql " + dbname)
        os.system ("/usr/local/bin/psql -U postgres -f /usr/local/pgsql-9.3/share/contrib/pgrouting-2.0/pgrouting.sql " + dbname)

def create_schema (cursor, SQLscript):

    try:
        start = time.time ()
        dbscript  = open(SQLscript,'r').read()
        cursor.execute(dbscript)
        end = time.time ()
        
        logging.info ("Create schema " + tf (end - start))
        print "Create schemas with SQL script " + SQLscript + '\n'

    except psycopg2.DatabaseError, e:
        print "Unable to create schemas: %s" % str(e)

def init_topology (cursor, ISP_edges_file):
    global ISP_graph
        
    f = open (ISP_edges_file, "r").readlines ()

    nodes = []
    edges = []
    for edge in f:
        ed = edge[:-1].split()
        edges.append ((int (ed[0]), int (ed[1])))
        if int(ed[0]) not in nodes:
            nodes.append (int(ed[0]))
        if int(ed[1]) not in nodes:
            nodes.append (int(ed[1]))

    ISP_graph = igraph.Graph (edges)

    start = time.time ()

    for n in nodes:
        try:
            cursor.execute("""INSERT INTO switches VALUES (%s, %s)""", (n, 100000)) 
        except psycopg2.DatabaseError, e:
            pass

    for edge in f:
        ed = edge[:-1].split()
        try:
            cursor.execute("""INSERT INTO topology(switch_id, next_id) VALUES (%s, %s)""", (int(ed[0]), int(ed[1])))
        except psycopg2.DatabaseError, e:
            print "Unable to insert into topology table: %s" % str(e)

    end = time.time ()

    logging.info ("Initialize topology " + tf (end - start))
    print "Initialize topology table with edges in " + ISP_edges_file + "\n"

def init_configuration (cursor, rib_edges_file, rib_prefixes_file, rib_peerIPs_file, ISP_nodes_file, ISP_edges_file):
    global ISP_graph

    nm = peerIP_ISP_map (rib_peerIPs_file, ISP_nodes_file)
    ISP_borders = nm.values ()

    # for b in ISP_borders:
    #     try: 
    #         cursor.execute ("""INSERT INTO borders VALUES (%s)""", ([int(b)]))
    #     except psycopg2.DatabaseError, e:
    #         logging.warning ("Insert into borders" + e)
    for key in nm.keys():
        try: 
            cursor.execute ("""INSERT INTO borders (switch_id, peerip) VALUES (%s,  %s)""", (nm[key], key))
            # cursor.execute ("""INSERT INTO borders VALUES (%s, %s)""", (int(nm[peerIP]), str(peerIP)))
        except psycopg2.DatabaseError, e:
            print "Unable to insert into borders "
            print 'Warning %s' % e


    prefixes_id_map = {}
    def set_prefixes_id_map ():
        pre = open (rib_prefixes_file, "r").readlines ()
        cid = 0
        for p in pre:
            cid = cid + 1
            prefixes_id_map[p[:-1]] = cid

    set_prefixes_id_map ()

    time_lapse = 0

    ribs = open (rib_edges_file, "r").readlines ()
    for r in ribs:
        switch_id = int (nm [r.split ()[0]]) 
        prefix = r.split ()[1]
        random_border = int(random.choice (ISP_borders))

        for n in [random_border]:
            if n != switch_id:
                path_list = ISP_graph.get_shortest_paths (switch_id, n)[0]
                path_edges = path_to_edge (path_list)

                start_t = time.time ()

                try: 
                    cursor.execute ("""SELECT flow_id from flow_constraints WHERE flow_id = %s""", ([prefixes_id_map[prefix]]))
                    c = cursor.fetchall ()
                    # logging.info (str (prefixes_id_map[prefix]) + str (c))

                    if c == []:
                        try: 
                            cursor.execute ("""INSERT INTO flow_constraints (flow_id, flow_name) VALUES (%s,  %s)""", (prefixes_id_map[prefix], prefix))
                        except psycopg2.DatabaseError, e:
                            logging.warning (e)

                    for ed in path_edges:                            
                        cursor.execute ("""INSERT INTO configuration (flow_id, switch_id, next_id) VALUES (%s,%s,%s)""", (prefixes_id_map[prefix], ed[0], ed[1]))

                except psycopg2.DatabaseError, e:
                    # logging.warning (e)
                    pass

                end_t = time.time ()
                time_lapse = time_lapse + end_t - start_t

    cursor.execute ("""SELECT count (*) FROM configuration""")
    c = cursor.fetchall ()

    logging.info ("Load configuration " + str (tf (time_lapse)) + " " + str (tfm (time_lapse)))
    logging.info ("Load configuration (" + str (c[0][0]) + " rows) average " + tf (time_lapse / int(c[0][0])))
    print "Load configuration table with edges\n"


def update_configuration (cursor, update_edges_file):
    print "update_configuration function"
    f = open (update_edges_file, "r").readlines ()
    print f[0]

    for u in f[1:]:
        peerIP = u.split ()[0]
        prefix = u.split ()[1]
        flag = u.split ()[3]
        if flag == 'W':
            pass
        elif flag == 'A':
            pass


import libUtility

def preprocess (dict_cur, updates):
    try:
        dict_cur.execute ("""
        DROP TABLE IF EXISTS isp_peerip CASCADE;
        CREATE UNLOGGED TABLE isp_peerip (
        switch_id      integer,
        peerip	      text,	
        PRIMARY KEY (switch_id)
        );
        """)

        topo = get_topo (dict_cur)
        # print type (topo[8])
        tmp = set([t[0] for t in topo] + [t[1] for t in topo])
        isp_nodes = list(tmp)
        borders = get_borders (dict_cur)
        nodes = [n for n in isp_nodes if n not in borders.keys ()]

        print len (nodes)
        print len (isp_nodes)
        print len (borders)

        peerips = list(set([u.split ()[0] for u in updates]))

        for peerip in peerips:
            if peerip not in borders.values ():
                pick_n = random.choice (nodes)
                nodes.remove (pick_n) 
                dict_cur.execute ("""
                INSERT INTO isp_peerip VALUES (%s, %s)
                """, (int(pick_n), str (peerip)))

    except psycopg2.DatabaseError, e:
        print "Unable to create isp_peerip table"
        print 'Error %s' % e

def e2e_add (dict_cur, flow, src, dst):

    path_list = ISP_graph.get_shortest_paths (src, dst)[0]
    path_edges = path_to_edge (path_list)

    try: 
        cursor.execute ("""SELECT flow_id from flow_constraints WHERE flow_id = %s""", ([prefixes_id_map[prefix]]))
        c = cursor.fetchall ()
        if c == []:
            try: 
                cursor.execute ("""INSERT INTO flow_constraints (flow_id, flow_name) VALUES (%s,  %s)""", (prefixes_id_map[prefix], prefix))
            except psycopg2.DatabaseError, e:
                logging.warning (e)

        for ed in path_edges:                            
            cursor.execute ("""INSERT INTO configuration (flow_id, switch_id, next_id) VALUES (%s,%s,%s)""", (prefixes_id_map[prefix], ed[0], ed[1]))

    except psycopg2.DatabaseError, e:
        pass

def e2e_del (dict_cur, flow, src, dst):
    pass

def obs_add (cursor, updates):
    pass

def obs_del (cursor, updates):
    pass

def synthesize (username, dbname,
               update_edges):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        print "Connect to database " + dbname + ", as user " + username

        # print borders

        uf = open (update_edges, "r").readlines ()
        updates = uf[1:20]

        preprocess (dict_cur, updates)

        borders = get_borders (dict_cur)
        topology = get_topo (dict_cur)
        isp_peerip = get_isp_peerip (dict_cur)

        # for update in updates:
        #     peerIP = update.split ()[0]
        #     prefix = update.split ()[1]
        #     flag = update.split ()[3]

        #     destIP = int (random.choice (borders.keys ()))

        #     if flag == 'A':
        #         e2e_add (dict_cur, prefix, peerIP, destIP)
        
        # e2e_add (dict_cur, [uf[1], uf[2]])
        # e2e_del (dict_cur, update)
        # update_configuration (cur, update_edges)
        

    except psycopg2.DatabaseError, e:
        print "Unable to connect to database " + dbname + ", as user " + username
        print 'Error %s' % e    

    finally:
        if conn:
            conn.close()

if __name__ == '__main__':

    username = "anduo"
    dbname = "as4755rib50"
    update_all = os.getcwd () + "/update_feeds/updates.20140701.0000.hr.extracted.updates"

    size = 100
    updates = update_all + str (size) + ".txt"
    os.system ("head -n " + str(size) + " " + update_all + " > " + updates)

    synthesize (username, dbname, updates)

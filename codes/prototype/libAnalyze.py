import libUtility

def get_borders (cursor):
    try:
        cursor.execute("SELECT * FROM borders;")
        bs = cursor.fetchall ()
    except:
        print "Unable to get border list"

    borders = {b['switch_id']: b['peerip'] for b in bs}
    # print "get_borders: borders are " + str (borders)

    return borders

def get_nodes (cursor):
    try:
        cursor.execute("SELECT * FROM switches;")
        cs = cursor.fetchall ()
    except:
        print "Unable to get switches table"

    nodes = [c['switch_id'] for c in cs]
    return nodes


def get_topo (cursor):
    try:
        cursor.execute("SELECT * FROM topology;")
        cs = cursor.fetchall ()
    except:
        print "Unable to get topology table"

    topology = [(c['switch_id'], c['next_id'], c['subnet_id']) for c in cs]
    return topology

def get_isp_peerip (cursor):
    try:
        cursor.execute("SELECT * FROM isp_peerip;")
        bs = cursor.fetchall ()
    except:
        print "Unable to get isp_peerip table"

    isp_peerip = {b['switch_id']: b['peerip'] for b in bs}
    return isp_peerip

def pick_flow (cursor, num):
    try:
        cursor.execute("SELECT * FROM (SELECT flow_id FROM flow_constraints) as foo;")
        flow_id_list = cursor.fetchall()
    except:
        print "Unable to get flow_id list"

    tmp = random.sample (flow_id_list, num)
    random_flow_id = [t[0] for t in tmp]
    # print "pick_flow: " + str (random_flow_id)
    
    return random_flow_id

def get_forwarding_graph (cursor, flow_id):
    try:
        cursor.execute ("SELECT * FROM configuration WHERE flow_id = " + str (flow_id) + ";")
        fg = cursor.fetchall ()

    except psycopg2.DatabaseError, e:
        print "Unable to extract forwarding graph for " + str (flow_id)
        print 'Error %s' % e

    forwarding_graph = [(f['switch_id'], f['next_id']) for f in fg]
    # print "get_forwarding_graph: for flow " + str (flow_id) # + " : " + str (forwarding_graph)

    return forwarding_graph

def get_ingress (cursor, flow_id):
    try:
        cursor.execute ("""
        WITH fg AS
        (
         SELECT * FROM configuration
         WHERE flow_id = """ + str (flow_id) +
        """
        )
        select switch_id AS ingress
        FROM fg NATURAL JOIN borders
        WHERE switch_id NOT IN (SELECT next_id FROM fg) 
        ORDER BY ingress;""")

        c = cursor.fetchall ()
        ingress_nodes = [i[0] for i in c]
        return ingress_nodes

    except:
        print "Unable to get flow_id list and border list"
        print 'Error %s' % e

def get_egress (cursor, flow_id):
    try:
        cursor.execute ("""
        WITH fg AS
        (
         SELECT * FROM configuration
         WHERE flow_id = """ + str (flow_id) +
        """
        )
        select next_id AS egress
        FROM fg
        WHERE next_id IN (SELECT * FROM borders) 
        ORDER BY egress;""")

        c = cursor.fetchall ()
        egress_nodes = [i[0] for i in c]
        return egress_nodes

    except psycopg2.DatabaseError, e:
        print "Unable to get egress nodes"
        print 'Error %s' % e

def check_e2e_path (cursor, flow_id, border1, border2):

    pgr_dijk_sql = "SELECT 1 as id, switch_id as source, next_id as target, 1.0::float8 as cost FROM configuration WHERE flow_id = " + str (flow_id)

    if border1 != border2:
        try:
            cursor.execute ("SELECT id1 as switch_id FROM pgr_dijkstra ('" + pgr_dijk_sql + "'," + str (border1) + "," + str (border2) + ", True, False" + ");")
            p = cursor.fetchall ()
            if p != []:
                print "check_e2e_path: for flow " + str (flow_id) + "between borders " + str (border1) + " and " + str (border2) + ", the path is" + str (p)
            return p
            # else:
            #     print "print p:" + str(p)

        except psycopg2.DatabaseError, e:
            print "check_e2e_path"
            print 'Error %s' % e
    
def check_dag (cursor, flow_id):

    edge_list = get_forwarding_graph (cursor, flow_id)
    fgr = igraph.Graph (edge_list, directed = True)
    # print fgr

    is_dag = fgr.is_dag ()
    print "check_dag: flow " + str (flow_id) + " is DAG? " + str (is_dag)
    
    return is_dag

def check_waypoint (cursor, flow_id, node):

    edge_list = get_forwarding_graph (cursor, flow_id)
    fgr = igraph.Graph (edge_list, directed = True)
    
def check_disjoint_edge (cursor, flow_id1, flow_id2):

    fg1 = get_forwarding_graph (cursor, flow_id1)
    fg2 = get_forwarding_graph (cursor, flow_id2)

    edges = [e for e in fg1 if e in fg2]
    # print "check_disjoint_edge: flows " + str (flow_id1) + " and " + str (flow_id2) + " overlap by " + str (edges)

    return edges

def check_blackhole (cursor, flow_id):

    try:
        cursor.execute ("""
        WITH fg AS
        (
         SELECT * FROM configuration
         WHERE flow_id = """ + str (flow_id) +
        """
        )
        select next_id AS blackhole
        FROM fg
        WHERE (NOT (next_id IN (SELECT switch_id FROM borders))) AND
                (NOT (next_id IN (SELECT switch_id FROM fg)))
        ORDER BY blackhole;""")

        c = cursor.fetchall ()
        blackholes = [i[0] for i in c]
        print "check_blackhole: blackholes are " + str (blackholes)

        return blackholes

    except psycopg2.DatabaseError, e:
        print "Unable to get blackholes"
        print 'Error %s' % e

# def check_config_e2e (cursor):
#     try:
#         cursor.execute("SELECT * FROM (SELECT flow_id FROM flow_constraints) as foo;")
#         flow_id_list = cursor.fetchall()

#         cursor.execute("SELECT * FROM borders;")
#         borders = cursor.fetchall ()

#     except:
#         print "Unable to get flow_id list and border list"

#     flow_id = flow_id_list[0][0]

#                         # print "Unable to run pgr_dijkstra"
#                         # print 'Error %s' % e

#     for flow_id in flow_id_list:
#         print "Analyze flow_id:" + str(flow_id[0])
#         flow_e2e (flow_id[0], borders)

def preprocess_feeds (dict_cur, updates):
    try:
        dict_cur.execute ("""
        CREATE UNLOGGED TABLE subnet (
        subnet_id      integer,
        type	       text,	
        PRIMARY KEY (subnet_id)
        );
        """)
    except psycopg2.DatabaseError, e:
        print "Unable to create subnet table"
        print 'Error %s' % e

    try:
        dict_cur.execute ("""
        CREATE UNLOGGED TABLE isp_peerip (
        switch_id      integer,
        peerip	      text,	
        PRIMARY KEY (switch_id)
        );
        """)
    except psycopg2.DatabaseError, e:
        print "Unable to create isp_peerip table"
        print 'Error %s' % e

    topo = get_topo (dict_cur)
    tmp = set([t[0] for t in topo] + [t[1] for t in topo])
    isp_nodes = list(tmp)
    borders = get_borders (dict_cur)
    nodes = [n for n in isp_nodes if n not in borders.keys ()]

    peerips = list(set([u.split ()[0] for u in updates]))

    for peerip in peerips:
        if peerip not in borders.values ():
            pick_n = random.choice (nodes)
            nodes.remove (pick_n) 
            dict_cur.execute ("""
            INSERT INTO isp_peerip VALUES (%s, %s)
            """, (int(pick_n), str (peerip)))

    try:
        dict_cur.execute ("""
        ALTER TABLE flow_constraints ADD COLUMN subnet_id integer ;
        """)
    except psycopg2.DatabaseError, e:
        print "Unable to add subnet_id column to flow_constraints table"
        print 'Error %s' % e

    try:
        dict_cur.execute ("""
        ALTER TABLE switches ADD COLUMN subnet_id integer ;
        """)
    except psycopg2.DatabaseError, e:
        print "Unable to add subnet_id column to switches table"
        print 'Error %s' % e

    try:
        dict_cur.execute ("""
        ALTER TABLE topology ADD COLUMN subnet_id integer ;
        """)
    except psycopg2.DatabaseError, e:
        print "Unable to add subnet_id column to topology table"
        print 'Error %s' % e

def e2e_add (dict_cur, flow_id, src, dst):

    fgr_sql = """
    WITH fg AS
    (
    SELECT * FROM configuration
    WHERE flow_id = """ + str (flow_id) + ")"

    pgr_dijk_sql = """
    SELECT 1 as id, switch_id as source, next_id as target, 1.0::float8 as cost
    FROM topology;"""

    try: 
        dict_cur.execute (fgr_sql + """select * FROM fg
            WHERE switch_id = """ + str (src) + """
            OR next_id = """ + str (dst) + ";")
        s = dict_cur.fetchall ()

        if len(s) != 2:
            print "source and destination not in the forwarding graph"
            try: 
                dict_cur.execute ("SELECT id1 as switch_id FROM pgr_dijkstra ('"
                                  + pgr_dijk_sql + "'," + str (src) + "," + str (dst) +
                                  ", True, False" + ");")
                path = dict_cur.fetchall ()
                print "find new path: " + str (path)
                if path != []:
                    path_edges = path_to_edge (path)
                    for ed in path_edges:
                        try: 
                            dict_cur.execute ("""
                            INSERT INTO configuration (flow_id, switch_id, next_id)
                            VALUES (%s,%s,%s)""", (flow_id, ed[0][0], ed[1][0]))
                        except:
                            pass
            except psycopg2.DatabaseError, e:
                print 'Error %s' % e

        else:
            c = check_e2e_path (dict_cur, flow_id, src, dst)
            print "source and destination are already in the forwarding graph"
            print "flow " + str (flow_id) + " can go from " + str (src) + " to " + str (dst) + ": " + str (c)

    except psycopg2.DatabaseError, e:
        print 'Error %s' % e

def e2e_del_src (dict_cur, flow_id, src):
    # fgr_sql = """
    # SELECT * FROM configuration
    # WHERE flow_id = """ + str (flow_id) +
    # """
    # AND switch_id = 
    # """ + str (src) + ";"

    del_sql = """
    DELETE FROM configuration WHERE
    flow_id = 
    """ + str (flow_id) + " AND switch_id = " + str (src) + ";"

    try:
        dict_cur.execute (del_sql)
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e

def e2e_del_dst (dict_cur, flow_id, dst):
    del_sql = """
    DELETE FROM configuration WHERE
    flow_id = 
    """ + str (flow_id) + " AND next_id = " + str (dst) + ";"

    try: 
        dict_cur.execute (del_sql)
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e

# def vn_add (dict_cur):
#     pass
    
def obs_init (dict_cur, size):

    topology = get_topo (dict_cur)    
    topo = [(c[0], c[1]) for c in topology if c[2] == None]
    if len (topo) > size:
        obs_top = random.sample (topo, size)
        print obs_top

        dict_cur.execute ("""
        SELECT max(subnet_id) from subnet ;
        """)
        c = dict_cur.fetchall ()
        if c[0][0] == None:
            subnet_id = 1
        else:
            subnet_id = c[0][0] + 1

        dict_cur.execute ("""
        INSERT INTO subnet VALUES (%s, %s) ;  
        """, (subnet_id, "obs"))

        for edge in obs_top :
            dict_cur.execute ("""
            UPDATE topology SET subnet_id = %s WHERE switch_id = %s AND next_id = %s
            """, (subnet_id, edge[0], edge[1]))

        where_sql = "(switch_id = " + str(obs_top[0][0]) + " AND next_id = " + str (obs_top[0][1]) + ")"
        for edge in obs_top[1:]:
            where_sql = where_sql + " OR (switch_id = " + str(edge[0]) + " AND next_id = " + str (edge[1]) + ")"

        try:
            dict_cur.execute ("""
            CREATE OR REPLACE VIEW obs_""" + str (subnet_id) + """_config AS (
            SELECT *
            FROM configuration
            WHERE """ + where_sql + ");")

        except psycopg2.DatabaseError, e:
            print "Unable to create obs view" 
            print 'Error %s' % e

def e2e_obs_create_fg (dict_cur, obs_id, flow_id):
    try:
        dict_cur.execute("""
        CREATE OR REPLACE VIEW obs_""" + str (obs_id) + "_fg_" + str (flow_id) + """ AS (
        SELECT * FROM obs_""" + str(obs_id) + """_config
        WHERE flow_id = """ + str (flow_id) + ");")
    except psycopg2.DatabaseError, e:
        print "Unable to generate e2e_obs_view"
        print 'Error %s' % e

def e2e_obs_drop_fg (dict_cur, obs_id, flow_id):
    try:
        dict_cur.execute ("DROP VIEW obs_" + str (obs_id) + "_fg_" + str (flow_id) + ";")
    except: pass

def e2e_obs_check (dict_cur, obs_id, flow_id, src, dst):
    pgr_dijk_sql = """
    SELECT 1 as id, switch_id as source, next_id as target, 1.0::float8 as cost
    FROM obs_""" + str (obs_id) + "_fg_" + str (flow_id) + ";"

    reach = False
    try:
        dict_cur.execute ("SELECT id1 as switch_id FROM pgr_dijkstra ('"
                          + pgr_dijk_sql + "'," + str (src) + "," + str (dst) +
                          ", True, False" + ");")
        path = dict_cur.fetchall ()
        if path != []:
            reach = True
        else:
            reach = False

    except psycopg2.DatabaseError, e:
        print "Cannot e2e_obs_check"
        print "Error %s" % e

    return reach
        
def e2e_obs_add (dict_cur, obs_id, flow_id, src, dst):
    pgr_dijk_sql = """
    SELECT 1 as id, switch_id as source, next_id as target, 1.0::float8 as cost
    FROM topology WHERE subnet_id = """ + str (obs_id) + ";"

    try:
        e2e_obs_create_fg (dict_cur, obs_id, flow_id)
        fg_view_name = "obs_" + str (obs_id) + "_fg_" + str (flow_id)

        reach = e2e_obs_check (dict_cur, obs_id, flow_id, src, dst)
        if reach == False:
            dict_cur.execute ("SELECT id1 as switch_id FROM pgr_dijkstra ('"
                              + pgr_dijk_sql + "'," + str (src) + "," + str (dst) +
                              ", True, False" + ");")
            path = dict_cur.fetchall ()
            if path != []:
                print "find new path: " + str (path)
                path_edges = path_to_edge (path)
                for ed in path_edges:
                    print ed
                    try: 
                        dict_cur.execute ("""
                        INSERT INTO obs_""" + str (obs_id) + "_fg_" + str (flow_id) +
                                          """ (flow_id, switch_id, next_id)
                        VALUES (%s,%s,%s);""", (flow_id, ed[0][0], ed[1][0]))
                    except: pass
                    # psycopg2.DatabaseError, e:
                    # print "Cannot insert into fg_view:"
                    # print 'Error %s' % e
            else: print "no available path in the obs topology"
        else: print "e2e_obs_add: path already exits"

        e2e_obs_drop_fg (dict_cur, obs_id, flow_id)

    except psycopg2.DatabaseError, e:
        print "Cannot e2e_obs_add"
        print "Error %s" % e

def obs_del (dict_cur, obs_id):
    try:
        dict_cur.execute ("UPDATE topology SET subnet_id = Null WHERE subnet_id = "+ str (obs_id) + ";")
    except: pass

    try:
        dict_cur.execute ("DELETE FROM subnet WHERE subnet_id = %s;", ([obs_id]))
    except: pass

    try:
        dict_cur.execute ("DROP VIEW obs_" + str (obs_id) + "_config ;")
    except: pass

def synthesize (username, dbname,
               update_edges):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        print "Connect to database " + dbname + ", as user " + username

        uf = open (update_edges, "r").readlines ()
        updates = uf[1:20]

        # preprocess_feeds (dict_cur, updates)

        borders = get_borders (dict_cur)
        topology = get_topo (dict_cur)
        isp_peerip = get_isp_peerip (dict_cur)
        nodes = get_nodes (dict_cur)

        [f1, f2] = pick_flow (dict_cur, 2)
        [n1, n2] = random.sample (nodes, 2)
        print "nodes: " + str (n1) + ", " + str (n2)
        
        # e2e_add (dict_cur, f1, n1, n2)
        # e2e_del_src (dict_cur, f1, n1)
        # e2e_del_dst (dict_cur, f1, n2)
        # obs_init (dict_cur, 20)
        # e2e_obs_create_fg (dict_cur, 1, f1)

        f1 = 36093
        # r1 = e2e_obs_check (dict_cur, 1, f1, 113, 230)
        # print "for obs 1, flow " + str (f1) + ", can go from 113 to 230: " + str (r1)

        # r2 = e2e_obs_check (dict_cur, 1, f1, 113, 456)
        # print "for obs 1, flow " + str (f1) + ", can go from 113 to 456: " + str (r2)

        # e2e_obs_add (dict_cur, obs_id, flow_id, , )

        e2e_obs_add (dict_cur, 1, f1, 108, 553)
        e2e_obs_create_fg (dict_cur, 1, f1)

        # obs_del (dict_cur, 11)
        # obs_del (dict_cur, 13)
        # obs_del (dict_cur, 14)
        # obs_del (dict_cur, 15)

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

# if __name__ == '__main__':

#     username = "anduo"
#     dbname = "as4755rib50"
#     update_all = os.getcwd () + "/update_feeds/updates.20140701.0000.hr.extracted.updates"

#     size = 100
#     updates = update_all + str (size) + ".txt"
#     os.system ("head -n " + str(size) + " " + update_all + " > " + updates)

#     synthesize (username, dbname, updates)

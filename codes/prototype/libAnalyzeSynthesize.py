execfile ("libUtility.py")
import libUtility
import pyGnuplot as gp

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
    
    return random_flow_id

def get_forwarding_graph (cursor, flow_id):
    try:
        cursor.execute ("SELECT * FROM configuration WHERE flow_id = " + str (flow_id) + ";")
        fg = cursor.fetchall ()

    except psycopg2.DatabaseError, e:
        print "Unable to extract forwarding graph for " + str (flow_id)
        print 'Error %s' % e

    forwarding_graph = [(f['switch_id'], f['next_id']) for f in fg]

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
    # print "check_dag: flow " + str (flow_id) + " is DAG? " + str (is_dag)
    
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
        return blackholes

    except psycopg2.DatabaseError, e:
        print "Unable to get blackholes"
        print 'Error %s' % e

def preprocess_feeds (dict_cur):
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

def select_nodes_flows (dict_cur, node_size, flow_size):
    try:
        dict_cur.execute ("SELECT * FROM borders ;")
        borders = [b['switch_id'] for b in dict_cur.fetchall ()]

        dict_cur.execute ("SELECT * FROM flow_constraints ;")
        flows = [f['flow_id'] for f in dict_cur.fetchall ()]

        sel_nodes = random.sample (borders, node_size)
        sel_flows = random.sample (flows, flow_size)

        return [sel_nodes, sel_flows]

    except psycopg2.DatabaseError, e:
        print 'Error %s' % e
        
def obs_new_init (dict_cur, obs_nodes, obs_flows):
    try:
        # dict_cur.execute ("SELECT * FROM borders ;")
        # borders = [b['switch_id'] for b in dict_cur.fetchall ()]

        # dict_cur.execute ("SELECT * FROM flow_constraints ;")
        # flows = [f['flow_id'] for f in dict_cur.fetchall ()]

        # obs_nodes = random.sample (borders, topo_size)
        # obs_flows = random.sample (flows, flow_size)
        print "obs_new_init"

        dict_cur.execute ("""
        DROP TABLE IF EXISTS obs_nodes CASCADE;
        CREATE UNLOGGED TABLE obs_nodes (
        switch_id      integer);
        """)

        for n in obs_nodes:
            dict_cur.execute ("INSERT INTO obs_nodes VALUES (%s);", ([n]))

        dict_cur.execute ("""
        DROP TABLE IF EXISTS obs_flows CASCADE;
        CREATE UNLOGGED TABLE obs_flows (
        flow_id      integer);
        """)

        for f in obs_flows:
            dict_cur.execute ("INSERT INTO obs_flows VALUES (%s);", ([f]))

        obs_nodes_sql = "NOT (source != " + str (obs_nodes[0])
        for n in obs_nodes[1:]:
            obs_nodes_sql = obs_nodes_sql + ("  AND source != " + str (n))
        obs_nodes_sql = obs_nodes_sql + " )"

        obs_flows_sql = "NOT (flow_id != " + str (obs_flows[0]) 
        for f in obs_flows[1:]:
            obs_flows_sql = obs_flows_sql + (" AND flow_id != " + str (f))
        obs_flows_sql = obs_flows_sql + ")"
            
        dict_cur.execute ("""
        DROP VIEW IF EXISTS obs_reachability_out CASCADE;
        CREATE OR REPLACE VIEW obs_reachability_out AS (
        SELECT flow_id, source, target
        FROM reachability
        WHERE """ + obs_nodes_sql + """ AND 
              """ + obs_flows_sql + """            
        ORDER BY flow_id);
        """)

        dict_cur.execute ("""
        DROP VIEW IF EXISTS obs_reachability_external CASCADE;
        CREATE OR REPLACE VIEW obs_reachability_external AS (
        SELECT flow_id, target
        FROM obs_reachability_out);
        """)

        obs_nodes_sql2s = "NOT (source != " + str (obs_nodes[0])
        for n in obs_nodes[1:]:
            obs_nodes_sql2s = obs_nodes_sql2s + ("  AND source != " + str (n))
        obs_nodes_sql2s = obs_nodes_sql2s + " )"
        obs_nodes_sql2t = "NOT (target != " + str (obs_nodes[0]) 
        for n in obs_nodes[1:]:
            obs_nodes_sql2t = obs_nodes_sql2t + ("  AND target != " + str (n))
        obs_nodes_sql2t = obs_nodes_sql2t + " )"
        obs_nodes_sql2 = obs_nodes_sql2s + " AND " + obs_nodes_sql2t

        dict_cur.execute ("""
        DROP VIEW IF EXISTS obs_reachability_internal CASCADE;
        CREATE OR REPLACE VIEW obs_reachability_internal AS (
        SELECT *
        FROM reachability
        WHERE """ + obs_nodes_sql2 + """ AND 
              """ + obs_flows_sql + """            
        );
        """)

# source IN (SELECT * FROM obs_nodes) AND
# flow_id IN (SELECT * FROM obs_flows)
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e

def vn_init (dict_cur, vn_nodes, vn_flows):
    try: 
        # dict_cur.execute ("SELECT * FROM borders ;")
        # borders = [b['switch_id'] for b in dict_cur.fetchall ()]

        # dict_cur.execute ("SELECT * FROM flow_constraints ;")
        # flows = [f['flow_id'] for f in dict_cur.fetchall ()]

        # vn_nodes = random.sample (borders, topo_size)
        # vn_flows = random.sample (flows, flow_size)

        # print vn_nodes

        dict_cur.execute ("""
        DROP TABLE IF EXISTS vn_nodes CASCADE;
        CREATE UNLOGGED TABLE vn_nodes (
        switch_id      integer);
        """)

        for n in vn_nodes:
            dict_cur.execute ("INSERT INTO vn_nodes VALUES (%s);", ([n]))

        dict_cur.execute ("""
        DROP TABLE IF EXISTS vn_flows CASCADE;
        CREATE UNLOGGED TABLE vn_flows (
        flow_id      integer);
        """)

        for f in vn_flows:
            dict_cur.execute ("INSERT INTO vn_flows VALUES (%s);", ([f]))

        print "vn_reachability view"

        flow_id_sql = "flow_id = " + str (vn_flows[0])
        for f in vn_flows[1:]:
            flow_id_sql = flow_id_sql + " OR flow_id = " + str (f)

        # print flow_id_sql
            
        source_sql = "source = " + str (vn_nodes[0])
        for n in vn_nodes[1:]:
            source_sql = source_sql + " OR source = " + str (n)

        target_sql = "target = " + str (vn_nodes[0])
        for n in vn_nodes[1:]:
            target_sql = target_sql + " OR target = " + str (n)

        dict_cur.execute ("""
        DROP VIEW IF EXISTS vn_reachability CASCADE;
        CREATE OR REPLACE VIEW vn_reachability AS (
               SELECT flow_id,
                      source as ingress,
                      target as egress
               FROM reachability
               WHERE (""" + flow_id_sql +""") AND
                     (""" + source_sql + """) AND
                     (""" + target_sql + """)
        );
        """)
            
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e
    
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


def add_reachability_table (cursor, flow_size):
    if flow_size == 0:
        reach_table = 'reachability'
    else:
        reach_table = 'reachability' + str (flow_size)

    try:
        cursor.execute ("select * from information_schema.tables where table_name = %s;", ([reach_table]))

        if (len (cursor.fetchall ()) == 0):
            cursor.execute("SELECT flow_id FROM flow_constraints;")
            flows = cursor.fetchall()
            if flow_size != 0:
                flows = flows[:flow_size]

            cursor.execute ("""
            CREATE TABLE """ +reach_table+ """ AS (
             SELECT * FROM reachability_perflow (""" + str (flows[0][0]) + """) );
             """)

            for f in flows[1:]:
                cursor.execute ("""
                INSERT INTO """ +reach_table+""" (flow_id, source, target, hops)
                SELECT flow_id, source, target, hops FROM reachability_perflow (""" + str (f[0]) + """);""")

    except psycopg2.DatabaseError, e:
        print "Unable to generate_reachability"
        print "Error %s" % e

def generate_forwarding_graph (cursor, flow_id):

    fg_view_name = "fg_" + str (flow_id)

    try:
        cursor.execute("""
        CREATE OR REPLACE view """ + fg_view_name + """ AS (
        SELECT 1 as id,
               switch_id as source,
	       next_id as target,
	       1.0::float8 as cost
        FROM configuration
        WHERE flow_id = %s
        );
        """, ([flow_id]))

        print "generate_forwarding_graph VIEW for flow: " + str (flow_id)
        
    except psycopg2.DatabaseError, e:
        print "Unable to create fg_view table for flow " + str (flow_id)
        print 'Error %s' % e

def add_configuration_view (cursor):
    try:
        cursor.execute ("""
DROP VIEW IF EXISTS configuration_pv CASCADE;
CREATE OR REPLACE VIEW configuration_pv AS (
       SELECT flow_id,
       	      source,
	      target,
	      (SELECT count(*) FROM pgr_dijkstra('SELECT 1 as id,
	      	      	     	       	             switch_id as source,
						     next_id as target,
						     1.0::float8 as cost
			                             FROM topology', source, target,FALSE, FALSE)) as hops,
	      (SELECT array(SELECT id1 FROM pgr_dijkstra('SELECT 1 as id,
	      	      	     	       	             switch_id as source,
						     next_id as target,
						     1.0::float8 as cost
			                             FROM topology', source, target,FALSE, FALSE))) as pv
       FROM reachability
);

DROP VIEW IF EXISTS configuration_edge CASCADE;
CREATE OR REPLACE VIEW configuration_edge AS (
       WITH num_list AS (
        SELECT UNNEST (ARRAY[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50]) AS num
       )
       SELECT DISTINCT flow_id, num, ARRAY[pv[num], pv[num+1]] as edge
       FROM configuration_pv, num_list
       WHERE pv != '{}' AND num < array_length (pv, 1) 
       ORDER BY flow_id, num
);

DROP VIEW IF EXISTS configuration_switch CASCADE;
CREATE OR REPLACE VIEW configuration_switch AS (
       SELECT DISTINCT flow_id,
       	      edge[1] as switch_id,
	      edge[2] as next_id
       FROM configuration_edge
       ORDER BY flow_id
);        
        """)

    except psycopg2.DatabaseError, e:
        print "Unable to generate configuration_view"
        print "Error %s" % e

def add_reachability_perflow_fun (cursor):
    try:
        cursor.execute ("""
DROP FUNCTION reachability_perflow(integer);
        
CREATE OR REPLACE FUNCTION reachability_perflow(f integer)
RETURNS TABLE (flow_id int, source int, target int, hops bigint, pv int[]) AS 
$$
BEGIN
	DROP TABLE IF EXISTS tmpone;
	CREATE TABLE tmpone AS (
	SELECT * FROM configuration c WHERE c.flow_id = f) ;

	RETURN query 
        WITH ingress_egress AS (
		SELECT DISTINCT b1.switch_id as source, b2.switch_id as target
       	      	FROM borders b1, borders b2, tmpone
	      	WHERE b1.switch_id != b2.switch_id AND
		      b1.switch_id IN (SELECT DISTINCT switch_id FROM tmpone) AND
	              b2.switch_id IN (SELECT DISTINCT next_id FROM tmpone)
                ORDER by source, target),
	     reach_can AS(
                SELECT i.source, i.target,
	      	       (SELECT count(*)
                        FROM pgr_dijkstra('SELECT 1 as id,
			     	           switch_id as source,
					   next_id as target,
					   1.0::float8 as cost FROM tmpone',
			     i.source, i.target,TRUE, FALSE)) as hops,
	      	       (SELECT array(SELECT id1 FROM pgr_dijkstra('SELECT 1 as id,
			     	           switch_id as source,
					   next_id as target,
					   1.0::float8 as cost FROM tmpone',
			     i.source, i.target,TRUE, FALSE))) as pv
	        FROM ingress_egress i)
	SELECT DISTINCT f as flow_id, r.source, r.target, r.hops, r.pv FROM reach_can r where r.hops != 0;
END
$$ LANGUAGE plpgsql;
        """)
    except psycopg2.DatabaseError, e:
        print "Unable to add reachability_perflow fun"
        print 'Error %s' % e

def generate_obs_forwarding_graph (cursor, flow_id, obs):

    fg_view_name = "tmp..."

    try:
        cursor.execute("""
        CREATE OR REPLACE view """ + fg_view_name + """ AS (
        SELECT 1 as id,
               switch_id as source,
               next_id as target,
               1.0::float8 as cost
        FROM configuration
        WHERE flow_id = %s AND subnet_id
        );
        """, ([flow_id]))

        print "generate_forwarding_graph VIEW for flow: " + str (flow_id)

    except psycopg2.DatabaseError, e:
        print "Unable to create fg_view table for flow " + str (flow_id)
        print 'Error %s' % e

def prepare_vn_obs_views (username, dbname):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        add_reachability_perflow_fun (dict_cur)
        add_reachability_table (dict_cur, 100)
        add_configuration_view (dict_cur)

        dict_cur.execute ("select * from information_schema.tables where table_name = %s;", (['reachability']))
        c = dict_cur.fetchall ()

    except psycopg2.DatabaseError, e:
        print 'Error %s' % e    

    finally:
        if conn:
            conn.close()

# if __name__ == '__main__':

#     username = "anduo"
#     dbname = "as4755ribd"
    # dbname = "as7018ribd"
    # dbname = "as6461ribd"

    
#     update_all = os.getcwd () + "/update_feeds/updates.20140701.0000.hr.extracted.updates"
#     size = 100
#     updates = update_all + str (size) + ".txt"
#     os.system ("head -n " + str(size) + " " + update_all + " > " + updates)
    
    # createViews (username, dbname)






def time_obs (dict_cur):
    dict_cur.execute ("SELECT switch_id FROM borders;")
    borders = [n[0] for n in dict_cur.fetchall ()]

    dict_cur.execute ("SELECT * FROM obs_nodes;")
    obs_nodes = [n[0] for n in dict_cur.fetchall ()]

    dict_cur.execute ("SELECT flow_id FROM obs_reachability_internal;")
    obs_reach = dict_cur.fetchall ()
    if obs_reach != []:
        flow_id = random.sample (obs_reach, 1)[0][0]

        dict_cur.execute ("SELECT source FROM obs_reachability_internal where flow_id = %s", ([flow_id]))
        ingress_nodes = [n[0] for n in dict_cur.fetchall ()]

        if len (ingress_nodes) != 0:
            ingress_node = random.sample (ingress_nodes, 1)[0]

            exit_node = random.sample ([n for n in obs_nodes if n not in [ingress_node]], 1)[0]

            dict_cur.execute ("ALTER VIEW obs_reachability_out ALTER COLUMN source SET DEFAULT %s ;", ([exit_node]))

    else:
        dict_cur.execute ("SELECT * FROM obs_flows;")
        obs_flows = [f[0] for f in dict_cur.fetchall ()]
        flow_id = random.sample (obs_flows, 1)[0]
        ingress_node = random.sample (obs_nodes, 1)[0]
        exit_node = random.sample ([n for n in obs_nodes if n not in [ingress_node]], 1)[0]

    external_node = random.sample ([n for n in borders if n not in obs_nodes],1)[0]
    s_i = time.time ()
    dict_cur.execute ("INSERT INTO obs_reachability_external values (%s, %s);", ([flow_id, external_node]))

    dict_cur.execute ("INSERT INTO obs_reachability_internal values (%s, %s, %s);", ([flow_id, ingress_node, exit_node]))
    e_i = time.time ()
    delta_i = tfsf (s_i, e_i)

    s_d = time.time ()
    dict_cur.execute ("DELETE FROM obs_reachability_external where flow_id = %s AND target = %s;", ([flow_id, external_node]))
    dict_cur.execute ("DELETE FROM obs_reachability_internal where flow_id = %s AND source = %s AND target = %s;", ([flow_id, ingress_node, exit_node]))
    e_d = time.time ()
    delta_d = tfsf (s_d, e_d)

    dict_cur.execute ("INSERT INTO obs_reachability_external values (%s, %s);", ([flow_id, external_node]))
    dict_cur.execute ("INSERT INTO obs_reachability_internal values (%s, %s, %s);", ([flow_id, ingress_node, exit_node]))

    external_node2 = random.sample ([n for n in borders if n not in [external_node] + obs_nodes], 1)[0]

    s_u = time.time ()
    dict_cur.execute ("UPDATE obs_reachability_external SET target = %s Where flow_id = %s AND target = %s;", ([external_node2, flow_id, external_node]))
    e_u = time.time ()
    delta_u = tfsf (s_u, e_u)

    return [delta_i, delta_d, delta_u]

def time_e2e_vn (dict_cur):

    dict_cur.execute ("SELECT * FROM vn_reachability;")
    vns = random.sample (dict_cur.fetchall (), 1)[0]
    flow_id = vns[0]

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

    ins_start = time.time ()
    dict_cur.execute ("INSERT INTO vn_reachability VALUES (%s, %s, %s);", ([vns[0], vns[1], vns[2]]))
    ins_end = time.time ()
    ins_time = tfsf (ins_start, ins_end)

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

        up_start = time.time ()
        dict_cur.execute ("UPDATE vn_reachability SET egress = %s where flow_id = %s and ingress = %s;", ([newe, flow_id, newi]))
        up_end = time.time ()
        
        up_time = tfsf (up_start, up_end)
        dict_cur.execute ("UPDATE vn_reachability SET egress = %s where flow_id = %s and ingress = %s;", ([olde, flow_id, newi]))
    else:
        up_time = 0

    return [del_time, switch_delta_time, ins_time, up_time]


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

def black_hole (username, dbname, rounds):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        dat = []
        for i in range( rounds):

            [f1, f2] = pick_flow (dict_cur, 2)

            start = time.time ()
            t = check_blackhole (dict_cur, f1)
            end = time.time ()
            cb_t = tfsf (start, end)

            dat.append (cb_t)
        dat.sort ()
            
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e

    finally:
        if conn: conn.close()
    return dat

def loop_free (username, dbname, rounds):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        dat = []
        for i in range( rounds):
            [f1, f2] = pick_flow (dict_cur, 2)
            start = time.time ()
            lp = check_dag (dict_cur, f1)
            end = time.time ()
            cd_t = tfsf (start, end)
            dat.append (cd_t)
        dat.sort ()
            
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e

    finally:
        if conn: conn.close()
    return dat

def get_path_len (username, dbname, xsize):
    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        dict_cur.execute ("SELECT hops FROM reachability limit %s;", ([xsize]))
        ph = [int (p[0]) for p in dict_cur.fetchall ()]

        path_hops = []
        for i in set (ph):
            path_hops.append ([i, ph.count (i)])
            
    except psycopg2.DatabaseError, e:
        print 'Error %s' % e

    finally:
        if conn: conn.close()
    return path_hops

def fg_cdf (username, dbname, xsize):

    try:
        conn = psycopg2.connect(database= dbname, user= username)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT) 
        dict_cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        fg_time = [dbname]
        fg_size = []
        for i in range (0, xsize):
            f1 = pick_flow (dict_cur, 1)[0]

            start = time.time ()
            fg = get_forwarding_graph (dict_cur, f1)
            end = time.time ()

            fgs = len (fg)
            fgt = tfsf (start, end)
            fg_time.append (fgt)
            fg_size.append (fgs)
        fg_time.sort ()

        fg_count = []
        for i in set (fg_size):
            fg_count.append ([i, fg_size.count (i)])

    except psycopg2.DatabaseError, e:
        print 'Error %s' % e

    finally:
        if conn: conn.close()

    return [fg_time, fg_count]

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

    # g = gp.gnuplot(persist = True)
    # g ('set term pdfcairo')
    # g ("set logscale y")
    # # g ("set key top left")
    # g ('set key bottom right')

    # g ('set terminal pdfcairo font "Gill Sans,9" linewidth 4 rounded fontscale 1.0')
    # g ('set style line 80 lt rgb "#808080"')
    # g ('set style line 81 lt 0  # dashed')
    # g ('set style line 81 lt rgb "#808080"')
    # g ('set grid back linestyle 81')
    # g ('set border 3 back linestyle 80')
    # g ('set style line 1 lt rgb "#A00000" lw 2 pt 1')
    # g ('set style line 2 lt rgb "#00A000" lw 2 pt 6')
    # g ('set style line 3 lt rgb "#5060D0" lw 2 pt 2')
    # g ('set style line 4 lt rgb "#F25900" lw 2 pt 9')

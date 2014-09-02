/* Base tables */

DROP TABLE IF EXISTS borders CASCADE;
CREATE UNLOGGED TABLE borders (
       switch_id      integer,
       peerIP	      text,	
       PRIMARY KEY (switch_id)
);

DROP TABLE IF EXISTS switches CASCADE;
CREATE UNLOGGED TABLE switches (
       switch_id    integer,
       mem_size     integer,
       PRIMARY KEY (switch_id)
);

DROP TABLE IF EXISTS switch_ports CASCADE;
CREATE UNLOGGED TABLE switch_ports (
       switch_id    integer,
       port_number  integer,
       port_address macaddr,  
       PRIMARY KEY (switch_id, port_number)
);


/* Add edges in both directions */
DROP TABLE IF EXISTS topology CASCADE;
CREATE UNLOGGED TABLE topology (
       switch_id    integer references switches(switch_id),
       switch_port  integer,
       next_id      integer references switches(switch_id),
       next_port    integer,
       available_bw integer DEFAULT 1000 CHECK (available_bw>=0),
       utilized_bw  integer DEFAULT    0 CHECK (utilized_bw>=0),
       detect_time  timestamp,
       PRIMARY KEY (switch_id, next_id)
);
CREATE INDEX ON topology(next_id);
-- No index on bw as full scan might be better
--CREATE INDEX ON topology(available_bw);

-- Define a flow
-- Can specify waypoints, src, dst
DROP TABLE IF EXISTS flow_constraints CASCADE;
CREATE UNLOGGED TABLE flow_constraints (
       flow_id     integer,
       flow_name   text       UNIQUE,
       constraints integer[], -- Waypoints to be considered
       rate        integer  NOT NULL DEFAULT 0,
       auto_route  boolean  DEFAULT FALSE
       -- PRIMARY KEY (flow_id)
);

-- Inverse mapping of switches to constraints.
DROP TABLE IF EXISTS flow_inverse CASCADE;
CREATE UNLOGGED TABLE flow_inverse (
       switch_id   integer  references switches(switch_id),
       flow_id     integer,
       PRIMARY KEY (switch_id, flow_id)
);

DROP TABLE IF EXISTS flow_status CASCADE;
CREATE UNLOGGED TABLE flow_status (
       flow_id    integer,
       rechable   boolean,
       PRIMARY KEY (flow_id)
);
CREATE INDEX ON flow_status(rechable);


DROP TABLE IF EXISTS configuration CASCADE;
CREATE UNLOGGED TABLE configuration (
       flow_id		integer,
       switch_id	integer,
       next_id 		integer,
       valid      boolean DEFAULT TRUE,
       PRIMARY KEY (flow_id, switch_id, next_id)
       -- PRIMARY KEY (flow_id, switch_id)
);
CREATE INDEX ON configuration(flow_id, switch_id, next_id);

------------------------------------------------------------
------------------------------------------------------------
-- switches management
------------------------------------------------------------
------------------------------------------------------------

------------------------------------------------------------
------------------------------------------------------------
-- Topology management
------------------------------------------------------------
------------------------------------------------------------

------------------------------------------------------------
------------------------------------------------------------
-- Flow Constraints management
------------------------------------------------------------
------------------------------------------------------------

------------------------------------------------------------
------------------------------------------------------------
-- Configuration management
------------------------------------------------------------
------------------------------------------------------------

------------------------------------------------------------
------------------------------------------------------------
-- Flow policy
------------------------------------------------------------
------------------------------------------------------------

CREATE OR REPLACE FUNCTION flow_policy_fun(flow_id_in integer)
RETURNS TABLE (path_vector integer[]) AS $$
  WITH RECURSIVE reach AS (
      (SELECT next_id, 
              ARRAY[switch_id, next_id] AS path_vector
       FROM   configuration
       WHERE  flow_id = flow_id_in
       AND    switch_id NOT IN 
          (SELECT next_id 
           FROM   configuration 
           WHERE  flow_id = flow_id_in))
       UNION
       (SELECT x.next_id,
       	       CASE (ARRAY[x.next_id] <@ r.path_vector)
	       	    WHEN true THEN r.path_vector
		    WHEN false THEN r.path_vector || ARRAY[x.next_id]
		    ELSE r.path_vector
	            END AS path_vector
               -- r.path_vector || ARRAY[x.next_id]
        FROM   configuration x,  reach r
        WHERE  x.flow_id   = flow_id_in
        AND    x.switch_id = r.next_id)
  )
  SELECT DISTINCT r.path_vector
  FROM   reach r;
  -- WHERE r.path_vector ;
  -- WHERE  r.next_id NOT IN
  --       (SELECT switch_id 
  --        FROM   configuration 
  --        WHERE  flow_id = flow_id_in);
$$ LANGUAGE SQL STABLE STRICT;

-- CREATE OR REPLACE FUNCTION flow_policy_fun(flow_id_in integer)
-- RETURNS TABLE (path_vector integer[]) AS $$
--   WITH RECURSIVE reach AS (
--       (SELECT next_id, 
--               ARRAY[switch_id, next_id] AS path_vector
--        FROM   configuration
--        WHERE  flow_id = flow_id_in
--        AND    switch_id NOT IN 
--           (SELECT next_id 
--            FROM   configuration 
--            WHERE  flow_id = flow_id_in))
--        UNION
--        -- (SELECT x.next_id,	
--        --         r.path_vector || ARRAY[x.next_id]
--        --  FROM   configuration x,  reach r
--        --  WHERE  x.flow_id   = flow_id_in
--        --  AND    x.switch_id = r.next_id)
--        (SELECT x.next_id,
--        	       CASE (ARRAY[x.next_id] <@ r.path_vector)
-- 	       	    WHEN true THEN r.path_vector
-- 		    WHEN false THEN r.path_vector || ARRAY[x.next_id]
-- 		    ELSE r.path_vector
-- 	            END AS path_vector
--                -- r.path_vector || ARRAY[x.next_id]
--         FROM   configuration x,  reach r
--         WHERE  x.flow_id   = flow_id_in
--         AND    x.switch_id = r.next_id)
--        -- UNION	
--        -- (SELECT x.next_id, 
--        --         r.path_vector -- || ARRAY[x.next_id]
--        --  FROM   configuration x,  reach r
--        --  WHERE  x.flow_id   = flow_id_in
--        --  AND    x.switch_id = r.next_id
--        -- 	AND (r.path_vector @> ARRAY[x.next_id]))
--   )
--   SELECT r.path_vector
--   FROM   reach r
--   WHERE  r.next_id NOT IN
--         (SELECT switch_id 
--          FROM   configuration 
--          WHERE  flow_id = flow_id_in);
-- $$ LANGUAGE SQL STABLE STRICT;

CREATE OR REPLACE VIEW flow_policy AS (
      SELECT flow_id,
             flow_name,
             rate,
             path_vector
             -- rechable
      FROM   flow_constraints -- NATURAL JOIN flow_status
      LEFT OUTER JOIN flow_policy_fun(flow_id) ON TRUE
      ORDER BY flow_id
);

-- Flow policy Maintainance

------------------------------------------------------------
------------------------------------------------------------
--  End to End flow policy
------------------------------------------------------------
------------------------------------------------------------

CREATE OR REPLACE VIEW e2e_flow_policy AS (
      SELECT flow_id,
             flow_name, 
             path_vector[1] AS src,
             path_vector[array_length(path_vector,1)] AS dst,
             rate
      FROM   flow_constraints -- NATURAL JOIN flow_status
      LEFT OUTER JOIN flow_policy_fun(flow_id) ON TRUE
      WHERE path_vector IS NOT NULL
      ORDER BY flow_id
);


-- E2E Flow policy Maintainance


------------------------------------------------------------
------------------------------------------------------------
--  One big switch Virtulization
------------------------------------------------------------
------------------------------------------------------------
DROP TABLE IF EXISTS obs_mapping CASCADE;
-- V_node needs to be same for all entries.
CREATE TABLE obs_mapping (
       p_node integer,
       v_node integer,
       PRIMARY KEY (p_node)
);
CREATE INDEX ON obs_mapping(v_node);

/* This view will not support updates as it reflects the physical connections */
CREATE OR REPLACE VIEW obs_topology AS (
  SELECT COALESCE(NULLIF(t.switch_id, ob.p_node), v_node) switch_id,
         COALESCE(NULLIF(t.next_id, ob.p_node),   v_node) next_id,
         available_bw, utilized_bw
  FROM   topology t INNER JOIN obs_mapping ob
  ON     t.switch_id = ob.p_node 
  OR     t.next_id   = ob.p_node
);


CREATE OR REPLACE VIEW obs_configuration AS (
  SELECT flow_id,
         COALESCE(NULLIF(t.switch_id, ob.p_node), v_node) switch_id,
         COALESCE(NULLIF(t.next_id, ob.p_node),   v_node) next_id
  FROM   configuration t INNER JOIN obs_mapping ob
  ON     t.switch_id = ob.p_node 
  OR     t.next_id   = ob.p_node
);

CREATE OR REPLACE VIEW e2e_obs_flow_policy AS (
      WITH v_switches AS (SELECT DISTINCT v_node FROM obs_mapping)
      SELECT obs1.flow_id, flow_name, obs1.switch_id src,
             obs2.next_id dst, rate
      FROM   obs_configuration obs1 NATURAL JOIN flow_constraints 
             INNER JOIN obs_configuration obs2 
             ON  obs1.flow_id = obs2.flow_id
             AND obs1.next_id = obs2.switch_id
      WHERE  obs1.switch_id NOT IN (SELECT * FROM v_switches)
);

-- E2E update on configuration


------------------------------------------------------------
------------------------------------------------------------
--  Virtulization
------------------------------------------------------------
------------------------------------------------------------
-- User only sees the virtualized switches
DROP TABLE IF EXISTS vn_mapping;
CREATE TABLE vn_mapping (
       p_node integer NOT NULL,
       v_node integer,
       PRIMARY KEY (p_node, v_node)
);
--Might be an index is not needed
--CREATE INDEX ON vn_mapping(v_node);

CREATE OR REPLACE VIEW e2e_vn_flow_policy AS (
      SELECT fc.flow_id, fc.flow_name,
             vn1.v_node as src,
             vn2.v_node as dst,
             fc.rate
      FROM   flow_policy fp INNER JOIN flow_constraints fc
      ON     fp.flow_id = fc.flow_id
             INNER JOIN vn_mapping vn1
      ON     vn1.p_node = path_vector[1]
             INNER JOIN vn_mapping vn2
      ON     vn2.p_node = path_vector[array_length(path_vector,1)]
);

-- CREATE OR REPLACE VIEW traffic_seed AS (
--        SELECT f.flow_id, c.switch_id
--        FROM flow_constraints f, configuration c
--        WHERE f.flow_id = c.flow_id
--        AND c.switch_id NOT IN
--        	     (
-- 	     SELECT DISTINCT next_id FROM configuration
-- 	     )
-- );

-- CREATE OR REPLACE VIEW policy_view AS (
-- 	WITH RECURSIVE reach AS (
-- 	     (SELECT *, 0 as hop, ARRAY[location] as path_vector FROM traffic_seed)
-- 	      UNION
-- 	     (SELECT x.header, x.next_ID AS location, 1 as hop,
-- 	     	     ARRAY[s.location, x.next_ID] AS path_vector
-- 	      FROM configuration x, traffic_seed s
-- 	      WHERE x.header = s.header AND x.switch_ID = s.location
-- 	      )
--               UNION
-- 	     (SELECT r.header, x.next_ID AS location,
-- 	     	     r.hop+1 as hop, r.path_vector || ARRAY[x.next_ID] AS path_vector
-- 	      FROM reach r, configuration x
-- 	      WHERE r.header = x.header AND r.location = x.switch_ID
-- 	      	    AND NOT (ARRAY[x.next_ID] <@ r.path_vector) 
-- 	     )
-- 	)
--         SELECT * FROM reach ORDER BY header, hop
-- );

DROP FUNCTION IF EXISTS to_nodes (int) ;
CREATE OR REPLACE FUNCTION to_nodes (h int)
RETURNS TABLE (location int) AS
$$
	SELECT DISTINCT next_id AS location
	FROM configuration
	WHERE switch_id = $1
$$
LANGUAGE SQL IMMUTABLE STRICT ;

DROP VIEW IF EXISTS get_ingress CASCADE;
CREATE OR REPLACE VIEW get_ingress AS (
       SELECT c.flow_id AS flow_id,
       	      c.switch_id AS ingress
       FROM configuration c
       WHERE c.switch_id NOT IN (SELECT * FROM to_nodes (c.flow_id)) 
       ORDER BY ingress, flow_id		  
) ;

DROP FUNCTION IF EXISTS from_nodes (int) ;
CREATE OR REPLACE FUNCTION from_nodes (h int)
RETURNS TABLE (location int) AS
$$
	SELECT DISTINCT switch_ID AS location
	FROM configuration
	WHERE flow_id = $1
$$
LANGUAGE SQL IMMUTABLE STRICT ;


DROP VIEW IF EXISTS get_egress CASCADE;
CREATE OR REPLACE VIEW get_egress AS (
       SELECT c.flow_id AS flow_id,
       	      c.next_id AS egress
       FROM configuration c
       WHERE c.next_id NOT IN (SELECT * FROM from_nodes (c.flow_id)) 
       ORDER BY egress, flow_id		
) ;

DROP FUNCTION IF EXISTS e2e(integer,integer,integer) ;
CREATE OR REPLACE FUNCTION e2e(s1 int, s2 int, f int) 
RETURNS TABLE (seq int, switch_id int) AS
$$
DECLARE
BEGIN
	DROP TABLE IF EXISTS fgt ;
	CREATE TEMP TABLE fgt AS (
		SELECT 1 as id, c.switch_id as source, c.next_id as target, 1.0::float8 as cost
		FROM configuration c
		WHERE flow_id = f
	) ;

	Return query
	SELECT b.seq as seq, b.id1 as switch_id
	FROM pgr_dijkstra('SELECT * FROM fgt',
	       s1, s2,
	       TRUE, FALSE) AS b;
END
$$
LANGUAGE plpgsql;



DROP FUNCTION IF EXISTS e2eview (int, int, int) CASCADE ;
CREATE OR REPLACE FUNCTION e2eview (s1 int, s2 int, f int)
RETURNS TABLE (seq int, switch_id int) AS
$$
       WITH fggt AS (
       		SELECT 1 as id, c.switch_id as source, c.next_id as target, 1.0::float8 as cost
		FROM configuration c
		WHERE flow_id = f
       )
       SELECT b.seq as seq, b.id1 as switch_id
	FROM pgr_dijkstra('fggt',
	       s1, s2,
	       TRUE, FALSE) as b ;
$$ 
LANGUAGE SQL STABLE STRICT;


-- DROP TABLE IF EXISTS fg CASCADE ;
-- CREATE TABLE fg (
--        id    	int,
--        source 	int,
--        target 	int,
--        cost	float
-- );

-- SELECT  1
-- FROM    pg_catalog.pg_namespace n
-- JOIN    pg_catalog.pg_proc p
-- ON      pronamespace = n.oid
-- WHERE   proname = 'pgr_dijkstra' ;


------------------------------------------------------------

CREATE OR REPLACE VIEW test2 AS (
       SELECT id1 AS from, id2 AS to, cost
       FROM pgr_apspJohnson(
            'SELECT switch_id as source, next_id as target, 1.0::float8 as cost FROM configuration WHERE flow_id = 72433'
    )
);

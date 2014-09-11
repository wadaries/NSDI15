-- toy data

TRUNCATE TABLE flow_constraints cascade;
TRUNCATE TABLE switches cascade;
TRUNCATE TABLE topology cascade;

INSERT INTO switches VALUES (1);
INSERT INTO switches VALUES (2);
INSERT INTO switches VALUES (3);
INSERT INTO switches VALUES (4);
INSERT INTO switches VALUES (5);
INSERT INTO switches VALUES (6);
INSERT INTO switches VALUES (7);
INSERT INTO switches VALUES (8);
INSERT INTO switches VALUES (9);
INSERT INTO switches VALUES (10);
INSERT INTO switches VALUES (11);

INSERT INTO topology(switch_id, next_id) VALUES (1,2), (2,1);
INSERT INTO topology(switch_id, next_id) VALUES (2,3), (3,2);
INSERT INTO topology(switch_id, next_id) VALUES (3,4), (4,3);
INSERT INTO topology(switch_id, next_id) VALUES (4,5), (5,4);
INSERT INTO topology(switch_id, next_id) VALUES (1,6), (6,1);
INSERT INTO topology(switch_id, next_id) VALUES (6,7), (7,6);
INSERT INTO topology(switch_id, next_id) VALUES (7,5), (5,7);
INSERT INTO topology(switch_id, next_id) VALUES (8,5), (5,8);
INSERT INTO topology(switch_id, next_id) VALUES (7,8), (8,7);
INSERT INTO topology(switch_id, next_id) VALUES (9,6), (6,9);
INSERT INTO topology(switch_id, next_id) VALUES (9,8), (9,8);

INSERT INTO flow_constraints (flow_id, flow_name) VALUES (1, 'flow1');
INSERT INTO flow_constraints (flow_id, flow_name) VALUES (2, 'flow2');
INSERT INTO flow_constraints (flow_id, flow_name) VALUES (3, 'flow3');
INSERT INTO flow_constraints (flow_id, flow_name) VALUES (4, 'flow4');
INSERT INTO flow_constraints (flow_id, flow_name) VALUES (5, 'flow5');

--1 - 2 - 3  - 4 - 5
-- \             /
--  6 - 7 - 8
--   \   /
--    9

INSERT INTO configuration (flow_id, switch_id, next_id) VALUES (1,1,2), (1,2,3), (1,3,4) ;
INSERT INTO configuration (flow_id, switch_id, next_id) VALUES (1,6,7), (1,7,8) ;
INSERT INTO configuration (flow_id, switch_id, next_id) VALUES (1,1,6), (1,6,9) ;
INSERT INTO configuration (flow_id, switch_id, next_id) VALUES (1,8,9), (1,9,6) ;

CREATE OR REPLACE VIEW obs_1_topo AS (
      SELECT switch_id, next_id
      FROM  topology
      WHERE subnet_id = 1
);

DROP TABLE IF EXISTS obs_1_topo_t CASCADE;
CREATE UNLOGGED TABLE obs_1_topo_t (
       switch_id      integer,
       next_id	      integer,	
       PRIMARY KEY (switch_id)	
      -- FOREIGN KEY (switch_id, next_id) REFERENCES obs_1_topo_t (switch_id, next_id)
);

-- CREATE OR REPLACE VIEW obs_configuration_test AS (
--       SELECT flow_id, switch_id, next_id
--       FROM  obs_1_config
--       WHERE -- FOREIGN KEY (switch_id, next_id) REFERENCES obs_1_topo_t (switch_id, next_id)
-- );

DROP VIEW IF EXISTS vn_reachability CASCADE;
CREATE OR REPLACE VIEW vn_reachability AS (
       SELECT flow_id,
       	      source as ingress,
       	      target as egress
       FROM reachability, topology, 
       WHERE flow_id in (SELECT * FROM vn_flows) AND
       	     source in (SELECT * FROM vn_nodes) AND
	     target in (SELECT * FROM vn_nodes)
);

CREATE OR REPLACE view obs_1_reach AS (
       SELECT switch_id, next_id, 
       FROM obs_1_config
       WHERE next_id IN (select next_id FROM obs_1_topo)
);

CREATE OR REPLACE VIEW reachability_72433 AS (
       WITH pair_hop AS (
              SELECT source, target,
       	      	     (SELECT count(*) FROM pgr_dijkstra('SELECT * FROM fg_72433',
	       			     source, target, 
 	       			    TRUE, FALSE)) as hops
              FROM ingress_egress_72433)
       SELECT * FROM pair_hop WHERE hops != 0
);

CREATE OR REPLACE VIEW topo2 AS (
       SELECT 1 as id,
       	      switch_id as source,
	      next_id as target,
	      1.0::float8 as cost
       FROM topology
);

DROP VIEW IF EXISTS configuration_pv CASCADE;
CREATE OR REPLACE VIEW configuration_pv AS (
       SELECT flow_id,
       	      source,
	      target,
	      (SELECT array(SELECT id1 FROM pgr_dijkstra('SELECT 1 as id,
	      	      	     	       	             switch_id as source,
						     next_id as target,
						     1.0::float8 as cost
			                             FROM topology', source, target,TRUE, FALSE))) as pv
       FROM reachability
);

DROP VIEW IF EXISTS configuration_edge CASCADE;
CREATE OR REPLACE VIEW conf_switch_edge AS (
       WITH num_list AS (
       SELECT UNNEST (ARRAY[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]) AS num
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


CREATE OR REPLACE FUNCTION fg_perflow(f integer)
RETURNS TABLE (id int, source int, target int, cost float8) AS $$
	       SELECT 1 as id,
	       	      switch_id as source,
		      next_id as target,
		      1.0::float8 as cost
               FROM configuration WHERE flow_id = f
$$ LANGUAGE SQL STABLE STRICT;

-- CREATE OR REPLACE FUNCTION reachability_perflow(f integer)
-- RETURNS TABLE (source int, target int, hops bigint) AS $$
--   SELECT DISTINCT
--   	 b1.switch_id AS source,
-- 	 b2.switch_id AS target,
-- 	 (SELECT count(*) FROM pgr_dijkstra('SELECT 1 as id, switch_id as source,
-- 	 	 	       			    next_id as target, 1.0::float8 as cost
-- 						    FROM configuration WHERE flow_id = $1',
-- 	       			     b1.switch_id, b2.switch_id, 
--  	       			    TRUE, FALSE)) as hops
--   FROM borders b1, borders b2
--   WHERE (b1.switch_id != b2.switch_id) ;
-- $$ LANGUAGE SQL STABLE STRICT;

DROP TABLE IF EXISTS reachability CASCADE;
CREATE UNLOGGED TABLE reachability AS
  SELECT DISTINCT
  	 flow_id,
	 source, 
	 target,
	 hops
  FROM flow_constraints NATURAL JOIN reachability_perflow (flow_id);


CREATE OR REPLACE view fg_72433 AS (
       select 1 as id,
       	      switch_id as source,
	      next_id as target,
	      1.0::float8 as cost
       FROM configuration
       WHERE flow_id = 72433
);

CREATE OR REPLACE VIEW ingress_egress_72433 AS (
       SELECT DISTINCT f1.source, f2.target
       FROM fg_72433 f1, fg_72433 f2
       WHERE f1.source != f2.target AND
       	     f1.source NOT IN (SELECT DISTINCT target FROM fg_72433) AND
	     f2.target NOT IN (SELECT DISTINCT source FROM fg_72433)
       ORDER by f1.source, f2.target
);

CREATE OR REPLACE VIEW reachability_72433 AS (
       WITH pair_hop AS (
              SELECT source, target,
       	      	     (SELECT count(*) FROM pgr_dijkstra('SELECT * FROM fg_72433',
	       			     source, target, 
 	       			    TRUE, FALSE)) as hops
              FROM ingress_egress_72433)
       SELECT * FROM pair_hop WHERE hops != 0
);

CREATE OR REPLACE VIEW reachability_72433 AS (
           WITH ingress_egress AS (
              SELECT DISTINCT f1.source, f2.target
       	      FROM fg_72433 f1, fg_72433 f2
	      WHERE f1.source != f2.target AND
       	            f1.source NOT IN (SELECT DISTINCT target FROM fg_72433) AND
	            f2.target NOT IN (SELECT DISTINCT source FROM fg_72433)
              ORDER by f1.source, f2.target),
           ingress_egress_reachability AS (
              SELECT source, target,
       	      	     (SELECT count(*)
		      FROM pgr_dijkstra('SELECT * FROM fg_72433',
		      	   source, target, TRUE, FALSE)) AS hops
              FROM ingress_egress)
       SELECT * FROM ingress_egress_reachability WHERE hops != 0
);


CREATE OR REPLACE VIEW obs_1_fg_36093_2 AS (
       select 1 as id,
       	      switch_id as source,
	      next_id as target,
	      1.0::float8 as cost
       FROM configuration NATURAL JOIN obs_1_topo
       WHERE flow_id = 36093
       ORDER BY source, target
);

CREATE OR REPLACE VIEW obs_1_fg_36093_3 AS (
       select 1 as id,
       	      switch_id as source,
	      next_id as target,
	      1.0::float8 as cost
       FROM obs_1_topo, fg_36093
       WHERE switch_id = source AND next_id = target
       ORDER BY source, target
);

CREATE OR REPLACE VIEW obs_1_fg_36093_4 AS (
       select 1 as id, source, target, 
	      1.0::float8 as cost
       FROM obs_1_topo, fg_36093
       WHERE switch_id = source AND next_id = target
       ORDER BY source, target
);



CREATE OR REPLACE VIEW obs_1_reachability_72433 AS (
)

SELECT count(*) FROM pgr_dijkstra('SELECT * FROM fg_72433',
	       			     98, 471, 
 	       			    TRUE, FALSE);

SELECT * FROM pgr_dijkstra('SELECT * FROM fg_72433',
	       			     71, 91, 
 	       			    TRUE, FALSE);

SELECT * FROM pgr_dijkstra('SELECT * FROM fg_72433',
	       			     71, 301, 
 	       			    TRUE, FALSE);

 
CREATE OR REPLACE view e2e_reach_perflow AS (
       SELECT source, target
);
-- CREATE OR REPLACE view e2e_reach_perflow AS (
--        WITH fg AS (
--        	    select switch_id, next_id
-- 	    from configuration
-- 	    where flow_id = 72433
--        ), topo_sql AS (
--        	    select 1 as id,
-- 	    	   switch_id as source,
-- 	    	   next_id as target,
-- 		   1.0::float8 as cost
--             FROM fg
--        ), fg_pairs AS (
--        	  select fg1.switch_id, fg2.next_id
-- 	  from fg fg1, fg fg2
--        )
--        select switch_id as src,
--        	      next_id as dest
--        from fg_pairs,
--        	    (select seq, id1 as node from 
-- 	       pgr_dijkstra('SELECT * FROM topo_sql',
-- 	       			    switch_id, next_id, 
-- 	       			    TRUE, FALSE)) AS e2e_reach
--        where 0 in (select seq FROM e2e_reach)
-- );

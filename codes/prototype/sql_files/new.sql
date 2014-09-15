CREATE OR REPLACE FUNCTION reachability_perflow2(f integer)
RETURNS TABLE (flow_id int, source int, target int, hops bigint, pv int[]) AS 
$$
BEGIN
	-- CREATE TABLE tmpone AS (
	-- SELECT 1 as id,	
	--        switch_id as source,
	--        next_id as target,
	--        1.0::float8 as cost
        -- FROM configuration WHERE flow_id = f
	-- ) ;
	DROP TABLE IF EXISTS tmpone;
	CREATE TABLE tmpone AS (
	SELECT * FROM configuration c WHERE c.flow_id = f
	) ;

	RETURN query 
        WITH ingress_egress AS (
		SELECT DISTINCT f1.switch_id as source, f2.next_id as target
       	      	FROM tmpone f1, tmpone f2
	      	WHERE f1.switch_id != f2.next_id AND
		      f1.switch_id NOT IN (SELECT DISTINCT next_id FROM tmpone) AND
	              f2.next_id NOT IN (SELECT DISTINCT switch_id FROM tmpone)
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
	SELECT f as flow_id, r.source, r.target, r.hops, r.pv FROM reach_can r where r.hops != 0;
  -- SELECT DISTINCT
  -- 	 source , target,
  -- 	 (SELECT count(*) FROM pgr_dijkstra('SELECT * FROM tmpone',
  -- 	       			     source, target, 
  -- 	       			    TRUE, FALSE)) as hops
  -- FROM ingress_egress;
	-- DROP TABLE tmpone ;
END
$$ LANGUAGE plpgsql;

DROP VIEW IF EXISTS vn_reachability CASCADE;
CREATE OR REPLACE VIEW vn_reachability AS (
       SELECT flow_id,
       	      source as ingress,
       	      target as egress
       FROM reachability
       WHERE flow_id in (SELECT * FROM vn_flows) AND
       	     source in (SELECT * FROM vn_nodes) AND
	     target in (SELECT * FROM vn_nodes)
);


select * from pgr_dijkstra('SELECT 1 as id, switch_id as source,
						     next_id as target,
						     1.0::float8 as cost
			                             FROM topology', 19, 230,FALSE, FALSE);

select * from pgr_dijkstra('SELECT 1 as id, switch_id as source,
						     next_id as target,
						     1.0::float8 as cost
			                             FROM topology', 230, 19,TRUE, FALSE);

-- DROP VIEW IF EXISTS obs_reach_new CASCADE;
-- CREATE OR REPLACE VIEW obs_reach_new AS (
--        SELECT flow_id,
--        	      target
--        FROM reachability
--        WHERE source IN (SELECT * FROM obs_nodes)
--        ORDER by flow_id, target
-- );

DROP VIEW IF EXISTS reachability2 CASCADE;
CREATE OR REPLACE VIEW reachability2 AS (
       SELECT r1.flow_id,
       	      r1.source,
	      r1. target as middle,
	      r2.target
       FROM reachability r1, reachability r2
       WHERE r1.target = r2.source AND r1.flow_id = r2.flow_id
       -- WHERE source IN (SELECT * FROM obs_nodes)
       -- ORDER by flow_id, target
);


DROP VIEW IF EXISTS obs_reachability CASCADE;
CREATE OR REPLACE VIEW obs_reachability AS (
       SELECT flow_id,
       	      o1.mapped_id AS source,
	      o2.mapped_id AS target
       FROM reachability, obs_mapping o1, obs_mapping o2
       WHERE reachability.source = o1.switch_id AND
       	     reachability.target = o2.switch_id AND
	     flow_id IN (SELECT * FROM obs_flows) AND
	     (o1.mapped_id = 1 OR o2.mapped_id = 1)
       ORDER by flow_id, source, target
);

DROP VIEW IF EXISTS reachability_rel_obs CASCADE;
CREATE OR REPLACE VIEW reachability_rel_obs AS (
       SELECT *
       FROM reachability
       WHERE (source IN (SELECT * FROM obs_nodes) OR
       	      target IN (SELECT * FROM obs_nodes)) AND
	      flow_id IN (SELECT * FROM obs_flows)
);

DROP VIEW IF EXISTS reachability_rel_obs_in CASCADE;
CREATE OR REPLACE VIEW reachability_rel_obs_in AS (
       SELECT *
       FROM reachability
       WHERE  target IN (SELECT * FROM obs_nodes) AND
	      flow_id IN (SELECT * FROM obs_flows)
);

DROP VIEW IF EXISTS reachability_rel_obs_out CASCADE;
CREATE OR REPLACE VIEW reachability_rel_obs_out AS (
       SELECT *
       FROM reachability
       WHERE  source IN (SELECT * FROM obs_nodes) AND
	      flow_id IN (SELECT * FROM obs_flows)
);

DROP VIEW IF EXISTS obs_reachability_out CASCADE;
CREATE OR REPLACE VIEW obs_reachability_out AS (
       SELECT flow_id,
	      target
       FROM reachability_rel_obs_out2
);


-- DROP VIEW IF EXISTS obs_reachability_in CASCADE;
-- CREATE OR REPLACE VIEW obs_reachability_in AS (
--        SELECT flow_id,
--        	      source,
-- 	      1 as target
--        FROM reachability, obs_mapping
--        WHERE source NOT IN (SELECT * FROM obs_nodes) AND
--        	     target IN (SELECT * FROM obs_nodes) AND
-- 	     flow_id IN (SELECT * FROM obs_flows)
--        ORDER by flow_id, source, target
-- );

-- DROP VIEW IF EXISTS obs_reachability_out CASCADE;
-- CREATE OR REPLACE VIEW obs_reachability_out AS (
--        SELECT flow_id,
--        	      1 as source,
-- 	      target
--        FROM reachability, obs_mapping
--        WHERE source IN (SELECT * FROM obs_nodes) AND
--        	     target NOT IN (SELECT * FROM obs_nodes) AND
-- 	     flow_id IN (SELECT * FROM obs_flows) 
--        ORDER by flow_id, source, target
-- );

DROP VIEW IF EXISTS configuration_pv_2 CASCADE;
CREATE OR REPLACE VIEW configuration_pv_2 AS (
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




INSERT INTO reachability_rel_obs_out2  (flow_id, source, target)
SELECT flow_id, source, target FROM (SELECT * FROM (SELECT 89406 as flow_id, switch_id as source, 483 as target, 
	(SELECT count(*) FROM pgr_dijkstra('SELECT 1 as id,
			                    switch_id as source,
					    next_id as target,
						     1.0::float8 as cost
			                             FROM topology', switch_id, 483,FALSE, FALSE)) as hops 
FROM obs_nodes) AS tmp WHERE hops !=0) AS tmp2 ORDER by hops LIMIT 1;


-- SELECT 89406 as flow_id,
--        (SELECT	switch_id, 
-- 		SELECT count(*) as hops FROM pgr_dijkstra('SELECT 1 as id,
-- 	      	      	     	       	             switch_id as source,
-- 						     next_id as target,
-- 						     1.0::float8 as cost
-- 			                             FROM topology', source, 483,TRUE, FALSE) as hop
--         FROM obs_nodes
--        )


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
CREATE OR REPLACE VIEW configuration_edge AS (
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


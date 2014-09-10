CREATE OR REPLACE FUNCTION reachability_perflow(f integer)
RETURNS TABLE (flow_id int, source int, target int, hops bigint) AS 
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
			     i.source, i.target,TRUE, FALSE)) as hops
	        FROM ingress_egress i)
	SELECT f as flow_id, r.source, r.target, r.hops FROM reach_can r where r.hops != 0;
  -- SELECT DISTINCT
  -- 	 source , target,
  -- 	 (SELECT count(*) FROM pgr_dijkstra('SELECT * FROM tmpone',
  -- 	       			     source, target, 
  -- 	       			    TRUE, FALSE)) as hops
  -- FROM ingress_egress;
	-- DROP TABLE tmpone ;
END
$$ LANGUAGE plpgsql;



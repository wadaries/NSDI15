DROP TABLE IF EXISTS configuration CASCADE;
CREATE TABLE configuration (
       header		text ,
       switch_ID	text ,
       next_ID 		text ,
       Rate		integer 
);

-- \copy configuration FROM '~/workspace/Relational-Networking/data/fib_config' WITH DELIMITER ','
-- \copy configuration_X FROM '~/workspace/Relational-Networking/data/fat_tree/fat_tree24_flows.txt' WITH DELIMITER ','
-- \copy configuration_X FROM '~/workspace/Relational-Networking/data/caida/caida-config-10000' WITH DELIMITER ','

DROP TABLE IF EXISTS topology CASCADE;
CREATE TABLE topology (
       switch_ID	text ,
       next_ID		text ,
       mem_size		integer ,
       bd_size		integer
);
-- topology_X is now bidirectional
-- \copy topology_X FROM '~/workspace/Relational-Networking/data/fat_tree/fat_tree24.txt' WITH DELIMITER ','
-- \copy topology FROM '~/workspace/Relational-Networking/data/topo' WITH DELIMITER ','

-- \copy topology_X FROM '~/workspace/Relational-Networking/data/caida/caida-top-10000' WITH DELIMITER ','

-- *** statistics, number of file size, edges (links), and nodes (AS)
-- *** Number selected nodes/links: 6946/9459
-- SELECT * FROM mem_usage ;
-- Time: 41.322 ms
------------------------------------------------------------
-- traffic view
------------------------------------------------------------

DROP TABLE IF EXISTS traffic_seed CASCADE;
CREATE TABLE traffic_seed (
       header		text,
       location		text
);
-- \copy traffic_seed FROM '~/workspace/Relational-Networking/data/fat_tree/traffic_seed' WITH DELIMITER ','
-- INSERT INTO traffic_seed VALUES ('flow1', 'A'), ('flow3', 'A'), ('flow4', 'C') ;

DROP TABLE IF EXISTS waypoint_node CASCADE;
CREATE TABLE waypoint_node (
       location text
);
-- INSERT INTO waypoint_node VALUES ('R1'), ('R2'), ('R3');

DROP TABLE IF EXISTS reach_node CASCADE;
CREATE TABLE reach_node (
       location text
);
-- INSERT INTO reach_node VALUES ('D'), ('B');

-- SELECT * FROM configuration ;
-- SELECT * FROM topology ;
-- SELECT * FROM traffic_seed ;
-- SELECT * FROM waypoint_node ;
-- SELECT * FROM reach_node ;
------------------------------------------------------------
------------------------------------------------------------
-- traffic view
---- located packets
------------------------------------------------------------
------------------------------------------------------------

CREATE OR REPLACE VIEW policy_view2 AS (
	WITH RECURSIVE reach AS (
	     (SELECT *, 0 as hop, ARRAY[location] as path_vector, 'no' AS loop_flag FROM traffic_seed)
	      UNION
	     (SELECT x.header, x.next_ID AS location, 1 as hop,
	     	     ARRAY[s.location, x.next_ID] AS path_vector,
		     'no' AS loop_flag
	      FROM configuration x, traffic_seed s
	      WHERE x.header = s.header AND x.switch_ID = s.location
	      )
              UNION
	     (SELECT r.header, x.next_ID AS location,
	     	     r.hop+1 as hop, r.path_vector || ARRAY[x.next_ID] AS path_vector,
		     CASE (ARRAY[x.next_ID] <@ r.path_vector)
		     	  WHEN true THEN 'yes'
			  WHEN false THEN 'no'
			  ELSE 'error'
		     END AS loop_flag
	      FROM reach r, configuration x
	      WHERE r.header = x.header AND r.location = x.switch_ID
	      	    AND (NOT (ARRAY[x.next_ID] <@ r.path_vector) OR r.loop_flag = 'no')
	     )
	)
        SELECT * FROM reach ORDER BY header, hop
);

CREATE OR REPLACE VIEW policy_view AS (
	WITH RECURSIVE reach AS (
	     (SELECT *, 0 as hop, ARRAY[location] as path_vector FROM traffic_seed)
	      UNION
	     (SELECT x.header, x.next_ID AS location, 1 as hop,
	     	     ARRAY[s.location, x.next_ID] AS path_vector
	      FROM configuration x, traffic_seed s
	      WHERE x.header = s.header AND x.switch_ID = s.location
	      )
              UNION
	     (SELECT r.header, x.next_ID AS location,
	     	     r.hop+1 as hop, r.path_vector || ARRAY[x.next_ID] AS path_vector
	      FROM reach r, configuration x
	      WHERE r.header = x.header AND r.location = x.switch_ID
	      	    AND NOT (ARRAY[x.next_ID] <@ r.path_vector) 
	     )
	)
        SELECT * FROM reach ORDER BY header, hop
);

-- CREATE OR REPLACE VIEW policy_view AS (
-- 	WITH RECURSIVE reach AS (
-- 	     (SELECT *, 0 as hop FROM traffic_seed)
-- 	      UNION
-- 	     (SELECT x.header, x.next_ID AS location, 1 as hop
-- 	      FROM configuration x, traffic_seed s
-- 	      WHERE x.header = s.header AND x.switch_ID = s.location
-- 	      )
--               UNION
-- 	     (SELECT r.header, x.next_ID AS location, r.hop+1 as hop
-- 	      FROM reach r, configuration x
-- 	      WHERE r.header = x.header AND r.location = x.switch_ID
-- 	     )
-- 	)	    
--         SELECT * FROM reach ORDER BY header, hop
-- );

-- SELECT * FROM policy_view ;
-- SELECT * FROM policy_view ORDER BY header, hop;
-- SELECT * FROM policy_view ORDER BY header, count ;

-- CREATE OR REPLACE VIEW traffic_view AS(
--        SELECT f.header, l.location
--        FROM traffic_seed f, get_locations() l
--        WHERE f.header = l.header
-- );

-- CREATE OR REPLACE VIEW located_packets AS(
--        SELECT f.header, l.location
--        FROM traffic_seed f, get_locations(f.header) l
--        WHERE f.header = l.header
-- );
-- SELECT * FROM located_packets ;

------------------------------------------------------------
-- reachability policy
------------------------------------------------------------

CREATE OR REPLACE FUNCTION ACL_REACH(hd text, src text, dst text) RETURNS text AS 
$$
DECLARE
    tmp_row1 policy_view%ROWTYPE;
    tmp_row2 policy_view%ROWTYPE;
    acl_flag text ;
BEGIN
    SELECT * INTO tmp_row1 FROM policy_view tv WHERE tv.header = hd AND tv.location = src ;
    -- RAISE NOTICE 'print tmp_row1 %, %', tmp_row1.header, tmp_row1.location ;
    SELECT * INTO tmp_row2 FROM policy_view tv WHERE tv.header = hd AND tv.location = dst ;
    -- RAISE NOTICE 'print tmp_row2 %, %', tmp_row2.header, tmp_row2.location ;
    IF ((tmp_row1 is not NULL) AND (tmp_row2 is not NULL) AND tmp_row1.hop < tmp_row2.hop) THEN
	-- RAISE NOTICE 'source can reach destination' ;
	acl_flag := 'allow' ;
    ELSE
    	-- RAISE NOTICE 'source can not reach destination' ;
	acl_flag := 'disallow' ;
    END IF ;
    RETURN acl_flag ;
END
$$
LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION from_nodes (h text)
RETURNS TABLE (location text) AS
$$
	SELECT switch_ID AS location
	FROM configuration
	WHERE header = $1
$$
LANGUAGE SQL IMMUTABLE STRICT ;

CREATE OR REPLACE FUNCTION to_nodes (h text)
RETURNS TABLE (location text) AS
$$
	SELECT next_ID AS location
	FROM configuration
	WHERE header = $1
$$
LANGUAGE SQL IMMUTABLE STRICT ;

CREATE OR REPLACE FUNCTION REACH_POLICY_PERFLOW (h text)
RETURNS TABLE (header text, src_node text, dst_node text, policy text)
AS
$$
	WITH from_nodes AS (
	     SELECT switch_ID AS location
	     FROM configuration
	     WHERE header = $1 
	), to_nodes AS (
             SELECT next_ID AS location
	     FROM configuration
	     WHERE header = $1
	)
        SELECT $1 as header, f.location as src_node, t.location as dst_node, ACL_REACH ($1, f.location, t.location) as policy
	FROM from_nodes f, to_nodes t
	WHERE f.location != t.location
$$
LANGUAGE SQL IMMUTABLE STRICT ;

CREATE OR REPLACE VIEW REACH_PAIRWISE_POLICY AS (
	WITH flows AS (SELECT DISTINCT header FROM policy_view)
        SELECT f.header, n1.location AS location1, n2.location AS location2,
	       ACL_REACH (f.header, n1.location, n2.location) AS REACH_POLICY
	FROM flows f, from_nodes (f.header) n1, to_nodes (f.header) n2
	WHERE n1.location <> n2.location
	ORDER BY header, location1, location2
);

-- INSERT INTO reach_node VALUES ('A');

CREATE OR REPLACE VIEW REACHABLE_FLOW_POlICY AS (
       	WITH flows AS (SELECT DISTINCT header FROM policy_view)
        SELECT DISTINCT n2.location, f.header
	FROM flows f, from_nodes (f.header) n1, to_nodes (f.header) n2
	WHERE n1.location <> n2.location AND ACL_REACH (f.header, n1.location, n2.location) = 'allow'
	ORDER BY location, header	        
) ;

------------------------------------------------------------
------------------------------------------------------------
-- waypoint policy
------------------------------------------------------------
------------------------------------------------------------

CREATE OR REPLACE FUNCTION ACL_WAYPOINT(hd text, node text) RETURNS text AS 
$$
DECLARE
    tmp_row1 policy_view%ROWTYPE;
    acl_flag text ;
BEGIN
    SELECT * INTO tmp_row1 FROM policy_view tv WHERE tv.header = hd AND tv.location = node ;
    -- RAISE NOTICE 'print tmp_row1 %, %', tmp_row1.header, tmp_row1.location ;
    IF ((tmp_row1 is not NULL)) THEN
	-- RAISE NOTICE 'waypoint' ;
	acl_flag := 'yes' ;
    ELSE
    	-- RAISE NOTICE 'not waypoint' ;
	acl_flag := 'no' ;
    END IF ;
    RETURN acl_flag ;
END
$$
LANGUAGE plpgsql;

CREATE OR REPLACE VIEW WAYPOINT_POLICY AS (
       WITH flows AS (SELECT DISTINCT header FROM policy_view)
       SELECT location AS waypoint, header
       FROM flows, waypoint_node
       WHERE ACL_WAYPOINT (header,location) = 'yes'
       ORDER BY waypoint, header
) ;

------------------------------------------------------------
------------------------------------------------------------
-- disjoint policy
------------------------------------------------------------
------------------------------------------------------------

CREATE OR REPLACE FUNCTION ACL_DISJOINT(hd1 text, hd2 text) RETURNS text AS 
$$
DECLARE
	acl_flag text ;
	overlap_node policy_view%ROWTYPE ;
BEGIN
	CREATE TABLE tmpone AS (
	WITH path1 AS (
	     	SELECT location FROM policy_view WHERE header = hd1 
	), path2 AS (
		SELECT location FROM policy_view WHERE header = hd2
	)
	SELECT path1.location FROM path1 WHERE path1.location IN (SELECT * FROM path2)
	) ;

        PERFORM * FROM tmpone ;
        IF FOUND THEN acl_flag := 'overlap' ;
    	ELSE acl_flag := 'disjoint' ;
    	END IF ;
	
	DROP TABLE tmpone ;
    	RETURN acl_flag ;
END
$$
LANGUAGE plpgsql;

CREATE OR REPLACE VIEW DISJOINT_POLICY AS (
       WITH flows AS (
       	    SELECT DISTINCT header from policy_view
       )
       SELECT f1.header AS header1, f2.header AS header2, ACL_DISJOINT (f1.header, f2.header) AS disjoint_policy
       FROM flows f1, flows f2
       WHERE f1.header <> f2.header
       ORDER BY header1, header2
) ;

------------------------------------------------------------
------------------------------------------------------------
--  cycle/loop policy
------------------------------------------------------------
------------------------------------------------------------

CREATE OR REPLACE VIEW cycle_policy AS (
       SELECT * FROM policy_view2
       WHERE loop_flag = 'yes'
);

------------------------------------------------------------
------------------------------------------------------------
--  equivalent class policy
------------------------------------------------------------
------------------------------------------------------------

CREATE OR REPLACE FUNCTION EQUI_CLASS(hd1 text, hd2 text) RETURNS text AS
$$
DECLARE
	eq_flag text ;
	ttt integer ;
BEGIN
	CREATE TABLE p12 AS (
	WITH path1 AS (
	     	SELECT location FROM policy_view WHERE header = hd1 
	), path2 AS (
		SELECT location FROM policy_view WHERE header = hd2
	), path12 AS (
		SELECT * FROM path1 NATURAL JOIN path2
	)
	SELECT (SELECT count(*) FROM path1) AS p1size,
	       (SELECT count(*) FROM path2) AS p2size,
	       (SELECT count (*) FROM path12) AS p12size
	) ;
	-- IF (SELECT p1size FROM p1notp2) = (SELECT p2size FROM p1notp2)
	-- THEN eq_flag = 'false' ;
	-- ELSE eq_flag = '1' ;
	PERFORM * FROM p12 WHERE p1size = p2size AND p2size = p12size ;
	IF FOUND THEN eq_flag = 'yes' ;
	ELSE eq_flag = 'false' ;
	END IF ;
	
	Drop TABLE p12 ;
    	Return eq_flag ;
END
$$
LANGUAGE plpgsql;

-- INSERT INTO configuration VALUES ('flow5', 'C', 'R3', 1), ('flow5', 'R3', 'D', 1) ;
-- INSERT INTO traffic_seed VALUES ('flow5', 'C') ;

CREATE OR REPLACE VIEW EQUI_CLASS_POLICY AS (
       WITH flows AS (
       	    SELECT DISTINCT header FROM policy_view 
       )
       SELECT f1.header AS header1, f2.header AS header2,
       	      EQUI_CLASS (f1.header, f2.header) AS equi_class
       FROM flows f1, flows f2
       WHERE f1.header != f2.header
);

DROP VIEW IF EXISTS get_ingress CASCADE;
CREATE OR REPLACE VIEW get_ingress AS (
       SELECT c.header AS header,
       	      c.switch_ID AS ingress
       FROM configuration c
       WHERE c.switch_ID NOT IN (SELECT * FROM to_nodes (c.header)) 
) ;

DROP VIEW IF EXISTS get_egress CASCADE;
CREATE OR REPLACE VIEW get_egress AS (
       SELECT c.header AS header,
       	      c.next_ID AS egress
       FROM configuration c
       WHERE c.next_ID NOT IN (SELECT * FROM from_nodes (c.header)) 
) ;

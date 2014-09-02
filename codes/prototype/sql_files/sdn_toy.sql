-- Load the data
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
INSERT INTO topology(switch_id, next_id) VALUES (7,8), (8,7);
INSERT INTO topology(switch_id, next_id) VALUES (9,6), (6,9);


INSERT INTO topology(switch_id, next_id) VALUES (10,11), (11,10);


--1 - 2 - 3  - 4 - 5
-- -             -
--    6    -   7 - 8
--  9--


-- INSERT INTO flow_constraints VALUES (1,'flow1','{1,4}',20);
-- INSERT INTO flow_constraints VALUES (2,'flow2','{1,5}',20);
-- INSERT INTO flow_constraints VALUES (3,'flow3','{1,5}',20,TRUE);
-- INSERT INTO flow_constraints VALUES (4,'flow4','{1,3,2}',20);
-- SELECT * FROM flow_policy;


-- INSERT INTO switches VALUES (100);
-- TRUNCATE TABLE obs_mapping cascade;
-- INSERT INTO obs_mapping VALUES (2,100);
-- INSERT INTO obs_mapping VALUES (4,100);


-- INSERT INTO obs_configuration VALUES (4,1,100);

-- TRUNCATE TABLE vn_mapping cascade;
-- INSERT INTO vn_mapping VALUES (1,1);
-- INSERT INTO vn_mapping VALUES (9,10);
-- INSERT INTO vn_mapping VALUES (8,8);

-- INSERT INTO e2e_obs_flow_policy VALUES (5,'flow5',1,5,20);


DROP VIEW IF EXISTS e2e_flow_policy CASCADE;
CREATE OR REPLACE VIEW e2e_flow_policy AS (

WITH fg AS (
     SELECT 1 as id, switch_id as source, next_id as target,
     	    1.0::float8 as cost
     FROM configuration
     WHERE flow_id = 3880)
SELECT seq, id1 as switch_id
FROM pgr_dijkstra('SELECT * FROM fg',
       444, 819,
       TRUE, FALSE) ;
-- -- ) ;

SELECT 1 as id, switch_id as source,
       next_id as target, 1.0::float8 as cost
       FROM configuration
       WHERE flow_id = 3880;

SELECT seq, id1 as switch_id
FROM pgr_dijkstra('SELECT 1 as id, switch_id as source,
       next_id as target, 1.0::float8 as cost
       FROM configuration
       WHERE flow_id = 100700',
       4302, 2803, 819,
       TRUE, FALSE) ;

SELECT 1 as id, switch_id as source,
       next_id as target, 1.0::float8 as cost
       FROM configuration
       WHERE flow_id = 100700 ;


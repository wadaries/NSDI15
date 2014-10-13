-- TRUNCATE TABLE switches cascade;
-- TRUNCATE TABLE topology cascade;
-- TRUNCATE TABLE flow_constraints cascade;
-- TRUNCATE TABLE configuration cascade;

-- 1 - 2 - - 3 
-- \       /
-- 4 ----5 
--  \  /
--   6

-- 1,3,6 are border routers

INSERT INTO switches VALUES (1);
INSERT INTO switches VALUES (2);
INSERT INTO switches VALUES (3);
INSERT INTO switches VALUES (4);
INSERT INTO switches VALUES (5);
INSERT INTO switches VALUES (6);

INSERT INTO topology(switch_id, next_id) VALUES (1,2), (2,1);
INSERT INTO topology(switch_id, next_id) VALUES (2,3), (3,2);
INSERT INTO topology(switch_id, next_id) VALUES (3,4), (4,3);
INSERT INTO topology(switch_id, next_id) VALUES (4,5), (5,4);
INSERT INTO topology(switch_id, next_id) VALUES (1,4), (4,1);
INSERT INTO topology(switch_id, next_id) VALUES (4,6), (6,4);
INSERT INTO topology(switch_id, next_id) VALUES (5,6), (6,5);

INSERT INTO flow_constraints (flow_id, flow_name) VALUES (1,'flow1');
INSERT INTO flow_constraints (flow_id, flow_name) VALUES (2,'flow2');
INSERT INTO flow_constraints (flow_id, flow_name) VALUES (3,'flow3');
INSERT INTO flow_constraints (flow_id, flow_name) VALUES (4,'flow4');

INSERT INTO configuration VALUES (1,1,2);
INSERT INTO configuration VALUES (1,2,3);

INSERT INTO configuration VALUES (2,1,4);
INSERT INTO configuration VALUES (2,4,5);
INSERT INTO configuration VALUES (2,5,6);

INSERT INTO configuration VALUES (3,1,4);
INSERT INTO configuration VALUES (3,4,6);

INSERT INTO configuration VALUES (4,3,5);
INSERT INTO configuration VALUES (4,5,6);

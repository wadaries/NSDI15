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

CREATE OR REPLACE view obs_1_reach AS (
       SELECT switch_id, next_id, 
       FROM obs_1_config
       WHERE next_id IN (select next_id FROM obs_1_topo)
);

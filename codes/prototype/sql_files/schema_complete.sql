/* Base tables */

DROP TABLE IF EXISTS switches CASCADE;
CREATE UNLOGGED TABLE switches (
       switch_id    integer,
       mem_size     integer,
       PRIMARY KEY (switch_id)
);

DROP TABLE IF EXISTS borders CASCADE;
CREATE UNLOGGED TABLE borders (
       switch_id      integer
);

/* edges in both directions */
DROP TABLE IF EXISTS topology CASCADE;
CREATE UNLOGGED TABLE topology (
       switch_id    integer references switches(switch_id),
       next_id      integer references switches(switch_id),
       available_bw integer DEFAULT 1000,
       -- available_bw integer DEFAULT 1000 CHECK (available_bw>=0),
       -- utilized_bw  integer DEFAULT    0 CHECK (utilized_bw>=0),
       PRIMARY KEY (switch_id, next_id)
);
CREATE INDEX ON topology(next_id);

DROP TABLE IF EXISTS configuration CASCADE;
CREATE UNLOGGED TABLE configuration (
       flow_id		integer,
       switch_id	integer,
       next_id 		integer,
       PRIMARY KEY (flow_id, switch_id, next_id)
);
CREATE INDEX ON configuration(flow_id, switch_id, next_id);

-- todo: rename flow_constraints to flows
DROP TABLE IF EXISTS flow_constraints CASCADE;
CREATE UNLOGGED TABLE flow_constraints (
       flow_id     integer,
       flow_name   text       UNIQUE,
       rate        integer  NOT NULL DEFAULT 1
       -- PRIMARY KEY (flow_id)
);

-- toy network data

TRUNCATE TABLE switches cascade;
TRUNCATE TABLE topology cascade;
TRUNCATE TABLE flow_constraints cascade;
TRUNCATE TABLE configuration cascade;

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

INSERT INTO borders VALUES (1), (3), (6);

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

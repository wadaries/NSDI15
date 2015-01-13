DROP TABLE IF EXISTS p1 CASCADE;
CREATE UNLOGGED TABLE p1 (
       counts  	integer,
       -- priority	integer,
       status 	text,
       PRIMARY key (counts)
);
INSERT into p1 (counts) values (0) ;

DROP TABLE IF EXISTS p2 CASCADE;
CREATE UNLOGGED TABLE p2 (
       counts  	integer,
       -- priority	integer,
       status 	text,
       PRIMARY key (counts)
);
INSERT into p2 (counts) values (0) ;

DROP TABLE IF EXISTS p3 CASCADE;
CREATE UNLOGGED TABLE p3 (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);
INSERT into p3 (counts) values (0) ;

CREATE OR REPLACE RULE tick1 AS
       ON UPDATE TO p1
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO p2 values (NEW.counts, 'on');

CREATE OR REPLACE RULE tick2 AS
       ON UPDATE TO p2
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO p3 values (NEW.counts, 'on');

DROP TABLE IF EXISTS tp CASCADE;
CREATE UNLOGGED TABLE tp (
       sid	integer,
       nid	integer,
       PRIMARY KEY (sid, nid)
);
CREATE INDEX ON tp(sid);

DROP TABLE IF EXISTS cf CASCADE;
CREATE UNLOGGED TABLE cf (
       fid	integer,
       sid	integer,
       nid	integer,
       PRIMARY KEY (fid, sid)
);
CREATE INDEX ON cf(fid,sid);

DROP TABLE IF EXISTS tm CASCADE;
CREATE UNLOGGED TABLE tm (
       fid      integer,
       src	integer,
       dst	integer,
       vol	integer,
       PRIMARY KEY (fid)
);

-- obs application, view and rules

CREATE OR REPLACE VIEW obs AS (
       SELECT DISTINCT fid, dst as nid
       FROM tm
);

CREATE OR REPLACE RULE obs_in AS 
       ON INSERT TO obs
       DO INSTEAD
       	  INSERT INTO tm VALUES (NEW.fid,5,NEW.nid,1);

CREATE OR REPLACE RULE obs_del AS 
       ON DELETE TO obs
       DO INSTEAD
          DELETE from tm WHERE fid = OLD.fid ;

CREATE RULE obs_constaint AS
       ON INSERT TO p1
       WHERE NEW.status = 'on'
       DO ALSO
           UPDATE p1 SET status = 'off' WHERE counts = NEW.counts;

-- acl, view and rules

CREATE OR REPLACE VIEW acl AS (
       SELECT DISTINCT src, dst
       FROM tm
);

CREATE OR REPLACE RULE acl_in AS
       ON INSERT TO acl
       DO INSTEAD
       	  INSERT INTO tm VALUES ((SELECT max (fid) FROM tm) + 1 , NEW.src, NEW.dst, 2);

CREATE OR REPLACE RULE acl_del AS
       ON DELETE TO acl
       DO INSTEAD
       	  DELETE from tm WHERE src = OLD.src AND dst = OLD.dst;


CREATE OR REPLACE RULE acl_constaint AS
       ON INSERT TO p2
       WHERE NEW.status = 'on'
       DO ALSO
           (DELETE FROM tm WHERE (src = 5 AND dst = 10);
	    DELETE FROM tm WHERE (src = 7 AND dst = 8);
            UPDATE p2 SET status = 'off' WHERE counts = NEW.counts;
	    );

-- load balancer, view and rules
-- CREATE OR REPLACE VIEW lb AS (
--        SELECT DISTINCT fid, dst as nid
--        FROM tm
-- );


TRUNCATE TABLE tp cascade;
TRUNCATE TABLE cf cascade;
TRUNCATE TABLE tm cascade;

INSERT INTO tp(sid, nid) VALUES (1,2), (2,1), (1,3), (3,1), (2,4), (4,2), (3,4), (4,3);
INSERT INTO tp(sid, nid) VALUES (1,5), (5,1), (1,6), (6,1), (2,6), (6,2), (7,2), (2,7);
INSERT INTO tp(sid, nid) VALUES (3,8), (8,3), (3,9), (9,3), (4,9), (9,4), (4,10), (10,4);

INSERT INTO tm(fid,src,dst,vol) VALUES (1,5,8,5);
INSERT INTO tm(fid,src,dst,vol) VALUES (2,7,10,9);
INSERT INTO tm(fid,src,dst,vol) VALUES (3,6,10,2);

CREATE OR REPLACE FUNCTION pystrip(x text)
  RETURNS text
AS $$
  global x
  x = x.strip()  # ok now
  return x
$$ LANGUAGE plpythonu;

-- CREATE OR REPLACE FUNCTION list_incoming_files() RETURNS SETOF text AS
-- $$
-- import os
-- -- return os.listdir('/Users/anduo/Documents')
-- print 'hello world\n'
-- $$
-- LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;



-- CREATE OR REPLACE RULE acl_in_3 AS
--        ON INSERT TO acl
--        WHERE NEW.src = 5 AND NEW.dst = 10
--        DO INSTEAD
--        DELETE from tm WHERE src = 5 AND dst = 10;

-- CREATE OR REPLACE RULE acl_in_4 AS
--        ON INSERT TO acl
--        WHERE NEW.src = 7 AND NEW.dst = 8
--        DO INSTEAD
--        DELETE from tm WHERE src = 7 AND dst = 8;

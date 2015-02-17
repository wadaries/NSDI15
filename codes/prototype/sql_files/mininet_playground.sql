DROP TABLE IF EXISTS clock CASCADE;
CREATE UNLOGGED TABLE clock (
       counts  	integer,
       PRIMARY key (counts)
);
-- INSERT into clock (counts) values (0) ; -- initialize clock

DROP TABLE IF EXISTS p1 CASCADE;
CREATE UNLOGGED TABLE p1 (
       counts  	integer,
       -- priority	integer,
       status 	text,
       PRIMARY key (counts)
);
-- INSERT into p1 (counts) values (0) ;

DROP TABLE IF EXISTS p2 CASCADE;
CREATE UNLOGGED TABLE p2 (
       counts  	integer,
       -- priority	integer,
       status 	text,
       PRIMARY key (counts)
);
-- INSERT into p2 (counts) values (0) ;

DROP TABLE IF EXISTS p3 CASCADE;
CREATE UNLOGGED TABLE p3 (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);
-- INSERT into p3 (counts) values (0) ;

-- CREATE OR REPLACE RULE clock_ins AS 
--        ON INSERT TO clock
--        WHERE NEW.counts = 0
--        DO ALSO
--        (
--        	  INSERT INTO p1 VALUES (NEW.counts, 'clock');
--        	  INSERT INTO p2 VALUES (NEW.counts, 'clock');
--        	  INSERT INTO p3 VALUES (NEW.counts, 'clock'););

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

CREATE OR REPLACE RULE tick3 AS
       ON UPDATE TO p3
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO clock values (NEW.counts);

DROP TABLE IF EXISTS tp CASCADE;
CREATE UNLOGGED TABLE tp (
       sid	integer,
       nid	integer,
       PRIMARY KEY (sid, nid)
);
CREATE INDEX ON tp(sid);

DROP TABLE IF EXISTS switches CASCADE;
CREATE UNLOGGED TABLE switches (
       sid	integer
);

DROP TABLE IF EXISTS hosts CASCADE;
CREATE UNLOGGED TABLE hosts (
       hid	integer
);

DROP TABLE IF EXISTS cf CASCADE;
CREATE UNLOGGED TABLE cf (
       fid	integer,
       pid	integer,
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

----------------------------------------------------------------------
-- obs application
----------------------------------------------------------------------

CREATE OR REPLACE VIEW obs AS (
       SELECT  fid, dst as nid, vol as rate
       FROM tm
       WHERE src < 20
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

----------------------------------------------------------------------
-- recursive views on top of obs	   
----------------------------------------------------------------------

DROP TABLE IF EXISTS o1 CASCADE;
CREATE UNLOGGED TABLE o1 (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);
-- INSERT into o1 (counts) values (0) ;

DROP TABLE IF EXISTS o2 CASCADE;
CREATE UNLOGGED TABLE o2 (
       counts  	integer,
       status 	text,
       PRIMARY key (counts)
);
-- INSERT into o2 (counts) values (0) ;

CREATE OR REPLACE RULE otick1 AS
       ON UPDATE TO o1
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO o2 values (NEW.counts, 'on');

CREATE OR REPLACE RULE otick2 AS
       ON UPDATE TO o2
       WHERE (NEW.status = 'off')
       DO ALSO
           INSERT INTO p1 values (NEW.counts, 'on');

CREATE OR REPLACE VIEW obs_acl AS (
       SELECT DISTINCT nid as dst
       FROM obs
);

CREATE OR REPLACE RULE obs_acl_del AS
       ON DELETE TO obs_acl
       DO INSTEAD
	  DELETE from obs WHERE nid = OLD.dst;

CREATE OR REPLACE RULE obs_acl_constraint AS
       ON INSERT TO o2
       WHERE NEW.status = 'on'
       DO ALSO
       	  (DELETE FROM obs_acl WHERE (dst = 30 OR dst = 50 OR dst = 100) ;
	   UPDATE o2 SET status = 'off' WHERE counts = NEW.counts;
	  );

CREATE OR REPLACE VIEW obs_lb AS (
       SELECT nid, sum (rate) as sum_rate
       FROM obs
       GROUP BY nid
);

CREATE OR REPLACE RULE obs_lb_del AS
       ON DELETE TO obs_lb
       DO INSTEAD
	  DELETE from obs WHERE fid IN
	  	 (SELECT fid FROM obs
		  WHERE nid = OLD.nid
		  ORDER BY rate	  
		  LIMIT 1
		 );

----------------------------------------------------------------------
-- acl, view and rules
----------------------------------------------------------------------

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
           (DELETE FROM tm WHERE (src = 1 AND dst = 2);
	    DELETE FROM tm WHERE (src = 7 AND dst = 8);
            UPDATE p2 SET status = 'off' WHERE counts = NEW.counts;
	    );

CREATE OR REPLACE RULE acl_constaint2 AS
       ON INSERT TO acl
       DO ALSO
           (DELETE FROM acl WHERE (src = 5 AND dst = 10);
	    DELETE FROM acl WHERE (src = 7 AND dst = 8);
	    );

-- load balancer, view and rules
-- CREATE OR REPLACE VIEW lb AS (
--        SELECT DISTINCT fid, dst as nid
--        FROM tm
-- );
----------------------------------------------------------------------
-- routing application
----------------------------------------------------------------------

DROP VIEW IF EXISTS spv CASCADE;
CREATE OR REPLACE VIEW spv AS (
       SELECT fid,
       	      src,
	      dst,
	      (SELECT array(SELECT id1 FROM pgr_dijkstra('SELECT 1 as id,
	      	      	     	       	             sid as source,
						     nid as target,
						     1.0::float8 as cost
			                             FROM tp', src, dst,FALSE, FALSE))) as pv
       FROM tm
);

DROP VIEW IF EXISTS spv2 CASCADE;
CREATE OR REPLACE VIEW spv2 AS (
       SELECT fid,
       	      src,
	      dst,
	      (SELECT array(SELECT id1 FROM pgr_dijkstra('SELECT 1 as id,
	      	      	     	       	             sid as source,
						     nid as target,
						     1.0::float8 as cost
			                             FROM cf c
						     WHERE fid = c.fid', src, dst,FALSE, FALSE))) as pv
       FROM tm
);

DROP VIEW IF EXISTS spv_edge CASCADE;
CREATE OR REPLACE VIEW spv_edge AS (
       WITH num_list AS (
       SELECT UNNEST (ARRAY[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]) AS num
       )
       SELECT DISTINCT fid, num, ARRAY[pv[num], pv[num+1], pv[num+2]] as edge
       FROM spv, num_list
       WHERE pv != '{}' AND num < array_length (pv, 1) - 1
       ORDER BY fid, num
);

DROP VIEW IF EXISTS spv_switch CASCADE;
CREATE OR REPLACE VIEW spv_switch AS (
       SELECT DISTINCT fid,
       	      edge[1] as pid,
	      edge[2] as sid,
       	      edge[3] as nid
       FROM spv_edge
       ORDER BY fid
);

-- DROP VIEW IF EXISTS spv_delta CASCADE;
-- CREATE OR REPLACE VIEW spv_delta AS (
--        (SELECT *, 'ins' as flag FROM 
--        (SELECT * FROM spv_switch
-- 	EXCEPT (SELECT * FROM cf)
-- 	ORDER BY fid) AS foo1)
-- 	UNION	
--        (SELECT *, 'del' as flag FROM 
--        (SELECT * FROM cf
-- 	EXCEPT (SELECT * FROM spv_switch)
-- 	ORDER BY fid) AS foo2)
-- );

DROP VIEW IF EXISTS spv_ins CASCADE;
CREATE OR REPLACE VIEW spv_ins AS (
       SELECT * FROM spv_switch
       EXCEPT (SELECT * FROM cf)
       ORDER BY fid
);

DROP VIEW IF EXISTS spv_del CASCADE;
CREATE OR REPLACE VIEW spv_del AS (
       SELECT * FROM cf
       EXCEPT (SELECT * FROM spv_switch)
       ORDER BY fid
);

CREATE OR REPLACE RULE spv_constaint AS
       ON INSERT TO p3
       WHERE NEW.status = 'on'
       DO ALSO
           (INSERT INTO cf (fid,pid,sid,nid) (SELECT * FROM spv_ins);
	    DELETE FROM cf WHERE (fid,pid,sid,nid) IN (SELECT * FROM spv_del);
            UPDATE p3 SET status = 'off' WHERE counts = NEW.counts;
	    );

------------------------------------------------------------
-- auxiliary function
------------------------------------------------------------

CREATE OR REPLACE FUNCTION get_port(s integer)
RETURNS TABLE (sid integer, nid integer, port bigint) AS 
$$

WITH TMP AS (
SELECT *, row_number () OVER () as port FROM tp
WHERE tp.sid = s OR tp.nid = s
)
(SELECT * 
FROM TMP
WHERE TMP.sid = s)
UNION
(SELECT TMP.nid as sid, TMP.sid as nid, TMP.port as port
FROM TMP
WHERE TMP.nid = s);
$$ LANGUAGE SQL;

------------------------------------------------------------
-- triggers
------------------------------------------------------------

CREATE OR REPLACE FUNCTION notify_trigger()
     RETURNS TRIGGER AS $$
   BEGIN
       RAISE NOTICE 'Hi, I got % invoked FOR % % % on %',
                                  TG_NAME,
                                  TG_LEVEL,
                                  TG_WHEN,
                                  TG_OP,
                                  TG_TABLE_NAME;
       RAISE NOTICE 'contents: fid %, sid %, nid %', NEW.fid, NEW.sid, NEW.nid;
       RETURN NEW;					
   END;
   $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION add_flow_fun ()
RETURNS TRIGGER
AS $$
f = TD["new"]["pid"]
s = TD["new"]["sid"]
n = TD["new"]["nid"]

u = plpy.execute("""\
         select port
         from get_port (""" +str (s)+""")  
         where nid = """ +str (n))
outport = str(u[0]['port'])

v = plpy.execute("""\
         select port
         from get_port (""" +str (s)+""")
         where nid = """ +str (f))
inport = str (v[0]['port'])

plpy.notice("add sid = "+ str (s) + ", nid = " +str (n) + ", out_port =" + outport + ", in_port = "+ inport)

mnstring = 'sudo ovs-ofctl add-flow s' + str (s) + ' in_port=' + inport + ',actions=output:' + outport
mnstring2 = 'sudo ovs-ofctl add-flow s' + str (s) + ' in_port=' + outport + ',actions=output:' + inport

import os
import sys
sys.path.append('/usr/local/lib/python2.7/site-packages/')
import pxssh
ssh = pxssh.pxssh()
ssh.login ('mininet-vm', 'mininet', 'mininet')
ssh.sendline (mnstring)
plpy.notice (mnstring)
ssh.sendline (mnstring2)
plpy.notice (mnstring2)
ssh.logout ()

return None;
$$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;
-- LANGUAGE plpythonu;
-- ssh.sendline ('sudo ovs-ofctl add-flow s4 in_port=2,actions=output:1')
-- plpy.notice("sid is:" + str (s))
-- plpy.notice("nid is:" + str (n))

CREATE TRIGGER add_flow_trigger
     AFTER INSERT ON cf
     FOR EACH ROW
   EXECUTE PROCEDURE add_flow_fun();

CREATE TRIGGER notify_insert_trigger
     AFTER INSERT ON cf
     FOR EACH ROW
   EXECUTE PROCEDURE notify_trigger();

-- CREATE TRIGGER trig1
--   AFTER INSERT ON cf
--   FOR EACH ROW
--   EXECUTE PROCEDURE dummy();

-- CREATE TRIGGER trig3
--   AFTER DELETE ON cf
--   FOR EACH ROW
--   EXECUTE PROCEDURE delflow_trigger();

-- select tp.*, row_number() OVER () as rnum from tp ;
-- with tmp as (select distinct sid as sid from tp order by sid)
-- select tmp.sid, tp.sid, tp.nid, row_number () OVER ()
-- from tp, tmp
-- where tp.sid = tmp.sid or tp.nid = tmp.sid;

-- with tmp as (select distinct sid as sid from tp order by sid)
-- select tmp.sid, tp.sid, tp.nid
-- from tp, tmp
-- where tp.sid = tmp.sid or tp.nid = tmp.sid;


-- -- with tmp2 as (select distinct sid as sid from tp order by sid),

-- WITH TMP AS (
-- SELECT *, row_number () OVER () as port FROM tp
-- WHERE tp.sid = 4 OR tp.nid = 4
-- )
-- (SELECT * 
-- FROM TMP
-- WHERE sid = 4)
-- UNION
-- (SELECT TMP.nid as sid, TMP.sid as nid, port
-- FROM TMP
-- WHERE TMP.nid = 4);

CREATE OR REPLACE FUNCTION del_flow_fun ()
RETURNS TRIGGER
AS $$
f = TD["old"]["pid"]
s = TD["old"]["sid"]
n = TD["old"]["nid"]

u = plpy.execute("""\
         select port
         from get_port (""" +str (s)+""")  
         where nid = """ +str (n))
outport = str(u[0]['port'])

v = plpy.execute("""\
         select port
         from get_port (""" +str (s)+""")
         where nid = """ +str (f))
inport = str (v[0]['port'])

plpy.notice("remove sid = "+ str (s) + ", nid = " +str (n) + ", out_port =" + outport + ", in_port = "+ inport)

mnstring = 'sudo ovs-ofctl del-flows s' + str (s) + ' in_port=' + inport
mnstring2 = 'sudo ovs-ofctl del-flow s' + str (s) + ' in_port=' + outport

import os
import sys
sys.path.append('/usr/local/lib/python2.7/site-packages/')
import pxssh
ssh = pxssh.pxssh()
ssh.login ('mininet-vm', 'mininet', 'mininet')
ssh.sendline (mnstring)
ssh.sendline (mnstring2)
ssh.logout ()

return None;
$$ LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;


CREATE TRIGGER del_flow_trigger
     AFTER DELETE ON cf
     FOR EACH ROW
   EXECUTE PROCEDURE del_flow_fun();

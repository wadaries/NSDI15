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
           (DELETE FROM tm WHERE (src = 5 AND dst = 10);
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
			                             FROM tp', src, dst,TRUE, FALSE))) as pv
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
						     WHERE fid = c.fid', src, dst,TRUE, FALSE))) as pv
       FROM tm
);

DROP VIEW IF EXISTS spv_edge CASCADE;
CREATE OR REPLACE VIEW spv_edge AS (
       WITH num_list AS (
       SELECT UNNEST (ARRAY[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]) AS num
       )
       SELECT DISTINCT fid, num, ARRAY[pv[num], pv[num+1]] as edge
       FROM spv, num_list
       WHERE pv != '{}' AND num < array_length (pv, 1) 
       ORDER BY fid, num
);

DROP VIEW IF EXISTS spv_switch CASCADE;
CREATE OR REPLACE VIEW spv_switch AS (
       SELECT DISTINCT fid,
       	      edge[1] as sid,
	      edge[2] as nid
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
           (INSERT INTO cf (fid,sid,nid) (SELECT * FROM spv_ins);
	    DELETE FROM cf WHERE (fid,sid,nid) IN (SELECT * FROM spv_del);
            UPDATE p3 SET status = 'off' WHERE counts = NEW.counts;
	    );

----------------------------------------------------------------------
-- load toy data
----------------------------------------------------------------------

-- TRUNCATE TABLE tp cascade;
-- TRUNCATE TABLE cf cascade;
-- TRUNCATE TABLE tm cascade;

-- INSERT INTO tp(sid, nid) VALUES (1,2), (2,1), (1,3), (3,1), (2,4), (4,2), (3,4), (4,3);
-- INSERT INTO tp(sid, nid) VALUES (1,5), (5,1), (1,6), (6,1), (2,6), (6,2), (7,2), (2,7);
-- INSERT INTO tp(sid, nid) VALUES (3,8), (8,3), (3,9), (9,3), (4,9), (9,4), (4,10), (10,4);

-- INSERT INTO switches(sid) VALUES (4),(5),(6),(7);
-- INSERT INTO hosts(hid) VALUES (1),(2),(3),(8),(9),(10);

-- INSERT INTO tm(fid,src,dst,vol) VALUES (1,5,8,5);
-- INSERT INTO tm(fid,src,dst,vol) VALUES (2,7,10,9);
-- INSERT INTO tm(fid,src,dst,vol) VALUES (3,6,10,2);

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
       RETURN NEW;					
   END;
   $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION dummy() 
  RETURNS TRIGGER
AS $$
import os
import sys
sys.path.append('/usr/local/lib/python2.7/site-packages/')
import pxssh
mn = 'mininet-vm'
mnu = 'mininet'
mnp = 'mininet'
s = pxssh.pxssh()
s.login (mn, mnu, mnp)
s.sendline ('sudo ovs-ofctl add-flow s1 in_port=1,actions=output:2')
s.sendline ('sudo ovs-ofctl add-flow s1 in_port=2,actions=output:1')
s.logout ()
return None;
$$ LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION delflow_trigger() 
  RETURNS TRIGGER
AS $$
import os
import sys
sys.path.append('/usr/local/lib/python2.7/site-packages/')
import pxssh
mn = 'mininet-vm'
mnu = 'mininet'
mnp = 'mininet'
s = pxssh.pxssh()
s.login (mn, mnu, mnp)
s.sendline ('sudo ovs-ofctl del-flows s1')
s.logout ()
return None;
$$ LANGUAGE plpythonu;


CREATE TRIGGER notify_insert_trigger
     AFTER INSERT ON cf
     FOR EACH ROW
   EXECUTE PROCEDURE notify_trigger();

CREATE TRIGGER trig1
  AFTER INSERT ON cf
  FOR EACH ROW
  EXECUTE PROCEDURE dummy();

CREATE TRIGGER trig3
  AFTER DELETE ON cf
  FOR EACH ROW
  EXECUTE PROCEDURE delflow_trigger();

CREATE OR REPLACE FUNCTION addflow_trigger(inport integer, outport integer) RETURNS TRIGGER AS
$$
import os
import sys
sys.path.append('/usr/local/lib/python2.7/site-packages/')
import pxssh
mn = 'mininet-vm'
mnu = 'mininet'
mnp = 'mininet'
s = pxssh.pxssh()
s.login (mn, mnu, mnp)
s.sendline ('sudo ovs-ofctl add-flow s1 in_port=' + str(inport) +',actions=output:'+ str(outport))
s.sendline ('sudo ovs-ofctl add-flow s1 in_port=2,actions=output:1')
s.logout ()
return None;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;


CREATE OR REPLACE FUNCTION addflow(inport integer, outport integer) RETURNS integer AS
$$
import os
import sys
sys.path.append('/usr/local/lib/python2.7/site-packages/')
import pxssh
mn = 'mininet-vm'
mnu = 'mininet'
mnp = 'mininet'
s = pxssh.pxssh()
s.login (mn, mnu, mnp)
s.sendline ('sudo ovs-ofctl add-flow s1 in_port=' + str(inport) +',actions=output:'+ str(outport))
s.sendline ('sudo ovs-ofctl add-flow s1 in_port=2,actions=output:1')
s.logout ()
return inport;
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;


CREATE OR REPLACE FUNCTION delflow(sid integer) RETURNS integer AS
$$
import os
import sys
sys.path.append('/usr/local/lib/python2.7/site-packages/')
import pxssh
mn = 'mininet-vm'
mnu = 'mininet'
mnp = 'mininet'
s = pxssh.pxssh()
s.login (mn, mnu, mnp)
s.sendline ('sudo ovs-ofctl del-flows s' + str(sid))
s.logout ()
return sid
$$
LANGUAGE 'plpythonu' VOLATILE SECURITY DEFINER;


------------------------------------------------------------

CREATE OR REPLACE FUNCTION userinfo(
                    INOUT username name,
                    OUT user_id oid,
                    OUT is_superuser boolean)
AS $$
    u = plpy.execute("""\
            select usename,usesysid,usesuper
              from pg_user
             where usename = '%s'""" % username)[0]
    return (u['usename'], u['usesysid'], u['usesuper'])
$$ LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION create_mininet_topo(
                    -- INOUT username name,
                    OUT sid integer
                    -- OUT is_superuser boolean
		    )
AS $$
    import os
    u = plpy.execute("""\
            select sid as sid
            from switches""")
    return (u[1]['sid']) 
$$ LANGUAGE plpythonu;


    -- filename = '/Users/anduo/Documents/NSDI15/codes/prototype/mininet_topo' + str (datetime.datetime.now ()) + '.py'

CREATE OR REPLACE FUNCTION cmt(
                    OUT sid integer
		    )
AS $$
    import os
    import sys
    import datetime

    sys.path.append('/usr/local/lib/python2.7/site-packages/')	
    import pxssh							

    filename = '/tmp/mininet_topo_new.py'
    #filename = '~/mininet_topo_new.py'	

    fo = open(filename, "w")
    fo.write ('hello world \n')
    fo.write (str (datetime.datetime.now ()))
    fo.write ('\n')
    
    u = plpy.execute("""\
            select sid as sid
            from switches""")

    fo.close()
    # os.system ("scp " + '/Users/anduo/Documents/NSDI15/codes/prototype/mininet_topo.py' + " mininet@mininet-vm:~/")

    from pexpect import *
    # filename2 = '/Users/anduo/Documents/NSDI15/codes/prototype/mininet_topo.py'
    run ('scp ' + filename + ' mininet@192.168.56.101:/home/mininet/sdndb', events={'(?i)password': "mininet"})

    return (u[2]['sid']) 

$$ LANGUAGE plpythonu;

CREATE OR REPLACE FUNCTION cmt2(
                    OUT sid integer
		    )
AS $$
    import os
    import sys
    import datetime
    sys.path.append('/usr/local/lib/python2.7/site-packages/')	
    import pxssh

    s = pxssh.pxssh()
    s.login ('mininet-vm', 'mininet', 'mininet')
    s.sendline ('echo ' + h + ' > test')
    s.logout ()

    u = plpy.execute("""\
            select sid as sid
            from switches""")
    return (u[2]['sid']) 

$$ LANGUAGE plpythonu;

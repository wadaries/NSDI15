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

------------------------------------------------------------
------------------------------------------------------------
------------------------------------------------------------

CREATE OR REPLACE FUNCTION create_mininet_topo(
                    OUT sid integer)
AS $$
    import os
    u = plpy.execute("""\
            select sid as sid
            from switches""")
    return (u[1]['sid']) 
$$ LANGUAGE plpythonu;

-- plpy.notice ("hello")

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

-- CREATE OR REPLACE FUNCTION userinfo(
--                     INOUT username name,
--                     OUT user_id oid,
--                     OUT is_superuser boolean)
-- AS $$
--     u = plpy.execute("""\
--             select usename,usesysid,usesuper
--               from pg_user
--              where usename = '%s'""" % username)[0]
--     return (u['usename'], u['usesysid'], u['usesuper'])
-- $$ LANGUAGE plpythonu;

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


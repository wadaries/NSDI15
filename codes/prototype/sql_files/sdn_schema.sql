/* Base tables */

DROP TABLE IF EXISTS switches CASCADE;
CREATE UNLOGGED TABLE switches (
       switch_id    integer,
       mem_size     integer,
       PRIMARY KEY (switch_id)
);

DROP TABLE IF EXISTS switch_ports CASCADE;
CREATE UNLOGGED TABLE switch_ports (
       switch_id    integer,
       port_number  integer,
       port_address macaddr,  
       PRIMARY KEY (switch_id, port_number)
);


/* Add edges in both directions */
DROP TABLE IF EXISTS topology CASCADE;
CREATE UNLOGGED TABLE topology (
       switch_id    integer references switches(switch_id),
       switch_port  integer,
       next_id      integer references switches(switch_id),
       next_port    integer,
       available_bw integer DEFAULT 1000 CHECK (available_bw>=0),
       utilized_bw  integer DEFAULT    0 CHECK (utilized_bw>=0),
       detect_time  timestamp,
       PRIMARY KEY (switch_id, next_id)
);
CREATE INDEX ON topology(next_id);
-- No index on bw as full scan might be better
--CREATE INDEX ON topology(available_bw);

-- Define a flow
-- Can specify waypoints, src, dst
DROP TABLE IF EXISTS flow_constraints CASCADE;
CREATE UNLOGGED TABLE flow_constraints (
       flow_id     integer,
       flow_name   text       UNIQUE,
       constraints integer[], -- Waypoints to be considered
       rate        integer  NOT NULL DEFAULT 0,
       auto_route  boolean  DEFAULT FALSE,
       PRIMARY KEY (flow_id)
);

-- Inverse mapping of switches to constraints.
DROP TABLE IF EXISTS flow_inverse CASCADE;
CREATE UNLOGGED TABLE flow_inverse (
       switch_id   integer  references switches(switch_id),
       flow_id     integer,
       PRIMARY KEY (switch_id, flow_id)
);

DROP TABLE IF EXISTS flow_status CASCADE;
CREATE UNLOGGED TABLE flow_status (
       flow_id    integer,
       rechable   boolean,
       PRIMARY KEY (flow_id)
);
CREATE INDEX ON flow_status(rechable);


DROP TABLE IF EXISTS configuration CASCADE;
CREATE UNLOGGED TABLE configuration (
       flow_id		integer,
       switch_id	integer,
       next_id 		integer,
       valid      boolean DEFAULT TRUE,
       PRIMARY KEY (flow_id, switch_id, next_id)
);
CREATE INDEX ON configuration(switch_id, next_id, flow_id);

------------------------------------------------------------
------------------------------------------------------------
-- switches management
------------------------------------------------------------
------------------------------------------------------------

CREATE OR REPLACE FUNCTION switches_before_delete_func() RETURNS 
    trigger AS $$
BEGIN
  -- Check if node part of constraint.
  IF EXISTS (SELECT 1 
             FROM   flow_inverse
             WHERE  switch_id = OLD.switch_id) THEN
    RAISE EXCEPTION 'Node used in atleast one constraint';
    RETURN NULL;
  END IF;

  -- Delete all the ports
  DELETE FROM switch_ports
  WHERE  switch_id = OLD.switch_id;

  -- Delete all the edges
  DELETE FROM topology
  WHERE  switch_id = OLD.switch_id
  OR     next_id   = OLD.switch_id;
  RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER switches_before_delete
    BEFORE DELETE ON switches
    FOR EACH ROW
    EXECUTE PROCEDURE switches_before_delete_func();


CREATE OR REPLACE FUNCTION switches_truncate_func() RETURNS 
    trigger AS $$
BEGIN
  IF EXISTS (SELECT 1 
             FROM   flow_inverse) THEN
    RAISE EXCEPTION 'Constraints defined on switches';
    RETURN NULL;
  END IF;

  TRUNCATE TABLE configuration;
  RETURN null;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER switches_truncate
    BEFORE TRUNCATE ON switches
    FOR EACH STATEMENT
    EXECUTE PROCEDURE switches_truncate_func();

------------------------------------------------------------
------------------------------------------------------------
-- Topology management
------------------------------------------------------------
------------------------------------------------------------
CREATE OR REPLACE FUNCTION topology_update_func() RETURNS 
    trigger AS $$
BEGIN
  IF OLD.switch_id <> NEW.switch_id 
  OR OLD.next_id   <> NEW.next_id THEN
    RAISE EXCEPTION 'Cannot update switches';
    RETURN NULL;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION topology_after_delete_func() RETURNS 
    trigger AS $$
BEGIN
  -- Remove the configuration
  DELETE FROM configuration
  WHERE  switch_id = OLD.switch_id
  AND    next_id   = OLD.next_id;
  RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER topology_before_delete
    AFTER DELETE ON topology
    FOR EACH ROW
    EXECUTE PROCEDURE topology_after_delete_func();

CREATE TRIGGER topology_update
    BEFORE UPDATE ON topology
    FOR EACH ROW
    EXECUTE PROCEDURE topology_update_func();


CREATE OR REPLACE FUNCTION topology_truncate_func() RETURNS 
    trigger AS $$
BEGIN
  TRUNCATE TABLE configuration;
  RETURN null;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER topology_truncate
    BEFORE TRUNCATE ON topology
    FOR EACH STATEMENT
    EXECUTE PROCEDURE topology_truncate_func();



------------------------------------------------------------
------------------------------------------------------------
-- Flow Constraints management
------------------------------------------------------------
------------------------------------------------------------

CREATE OR REPLACE FUNCTION flow_constraints_before_update_func() RETURNS 
    trigger AS $$
BEGIN
  IF TG_OP = 'DELETE' OR TG_OP = 'UPDATE' THEN
    -- Clear depedent tables
    DELETE FROM flow_inverse
    WHERE  switch_id = ANY (OLD.constraints) 
    AND    flow_id   = OLD.flow_id;

    UPDATE configuration
    SET    valid = FALSE
    WHERE  flow_id = OLD.flow_id;
    
    DELETE FROM configuration
    WHERE  flow_id = OLD.flow_id;
   
    DELETE FROM flow_status
    WHERE flow_id =  OLD.flow_id;
  END IF;
  IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
    RETURN NEW;
  ELSE 
    RETURN OLD;
  END IF;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION flow_constraints_after_update_func() RETURNS 
    trigger AS $$
DECLARE
  full_path integer[];
  current_path integer[];
  src integer;
  dst integer;
  rate integer;
BEGIN
  IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
    -- Update the inverse table
    INSERT INTO flow_inverse(switch_id, flow_id)
    SELECT unnest(NEW.constraints), NEW.flow_id;

    IF array_length(NEW.constraints,1) > 1 THEN
      full_path := '{}';

      FOR i IN 1..(array_length(NEW.constraints, 1)-1) LOOP
        BEGIN
          src  := NEW.constraints[i];
          dst  := NEW.constraints[i+1];
          rate := NEW.rate;
          SELECT array_agg(id1)
          INTO   current_path 
          FROM   pgr_dijkstra('SELECT 1 id, switch_id as source,
                        next_id as target, 1.0::float8 as cost
                        FROM topology
                        WHERE available_bw >= ' || rate,
                        src, dst,
                        TRUE, FALSE);
           full_path:=full_path[1:(array_length(full_path,1)-1)] || current_path;
        EXCEPTION
        WHEN OTHERS THEN
          RAISE NOTICE 'Route not found';
          INSERT INTO flow_status
          VALUES (NEW.flow_id, FALSE);
          RETURN NEW;
        END;
      END LOOP;
      -- Check if the obtained route has a loop
      IF EXISTS (SELECT 1 
                 FROM unnest(full_path) AS d 
                 GROUP by d having count(1) > 1) THEN
          RAISE NOTICE 'Auto-route for constraint causes loop';
          INSERT INTO flow_status
          VALUES (NEW.flow_id, FALSE);
          RETURN NEW;
      END IF;

      -- If path not found make it as unrechable
      IF full_path IS NULL THEN
          RAISE NOTICE 'Route not found';
          INSERT INTO flow_status
          VALUES (NEW.flow_id, FALSE);
          RETURN NEW;
      END IF;      

      FOR i IN 1..(array_length(full_path, 1)-1) LOOP
       INSERT INTO configuration(flow_id, switch_id, next_id)
       SELECT NEW.flow_id, full_path[i], full_path[i+1]
       WHERE NOT EXISTS (
        SELECT 1 FROM configuration c
        WHERE c.flow_id   =  NEW.flow_id
        AND   c.switch_id = full_path[i]
        AND   c.next_id   = full_path[i+1]);
      END LOOP;
      INSERT INTO flow_status
      VALUES (NEW.flow_id, TRUE);
    ELSE
      IF NEW.auto_route = TRUE THEN
        RAISE EXCEPTION 'Auto-route only possible if atleast src and dst are given';
        RETURN NULL;
      END IF;
      -- No configuration update
      INSERT INTO flow_status
      VALUES (NEW.flow_id, FALSE);
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER flow_constraints_before_update
    BEFORE UPDATE OR DELETE ON flow_constraints
    FOR EACH ROW
    EXECUTE PROCEDURE flow_constraints_before_update_func();


CREATE TRIGGER flow_constraints_after_update
    AFTER INSERT OR UPDATE ON flow_constraints
    FOR EACH ROW
    EXECUTE PROCEDURE flow_constraints_after_update_func();


CREATE OR REPLACE FUNCTION flow_constraints_truncate_func() RETURNS 
    trigger AS $$
BEGIN
  TRUNCATE TABLE configuration;
  TRUNCATE TABLE flow_status;
  TRUNCATE TABLE flow_inverse;
  RETURN null;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER flow_constraints_truncate
    BEFORE TRUNCATE ON flow_constraints
    FOR EACH STATEMENT
    EXECUTE PROCEDURE flow_constraints_truncate_func();


------------------------------------------------------------
------------------------------------------------------------
-- Configuration management
------------------------------------------------------------
------------------------------------------------------------

CREATE OR REPLACE FUNCTION configuration_delete_func() RETURNS 
    trigger AS $$
DECLARE
  flow_rec flow_constraints%ROWTYPE;
  src integer;
  dst integer;
  rate integer;
  full_path integer[];
  current_path integer[];
  lrechable boolean;

BEGIN
  -- If flow not maked for auto route do nothing.
  SELECT * INTO flow_rec
  FROM   flow_constraints
  WHERE  flow_id = OLD.flow_id;

  IF flow_rec.auto_route = FALSE THEN
    -- No auto routing do nothing.
    UPDATE flow_status
    SET    rechable = FALSE
    WHERE  flow_id  = OLD.flow_id;
  ELSE
    SELECT rechable INTO lrechable
    FROM   flow_status
    WHERE  flow_id = OLD.flow_id;

    -- Update with shortest path
    IF lrechable = TRUE AND array_length(flow_rec.constraints,1) > 1 THEN
      -- Delete old path
      UPDATE configuration 
      SET    valid = FALSE
      WHERE  flow_id = OLD.flow_id;

      DELETE FROM configuration 
      WHERE  flow_id = OLD.flow_id;

      DELETE FROM flow_status 
      WHERE  flow_id = OLD.flow_id;

      -- Find new path
      full_path := '{}';

      FOR i IN 1..(array_length(flow_rec.constraints, 1)-1) LOOP
        BEGIN
          src  := flow_rec.constraints[i];
          dst  := flow_rec.constraints[i+1];
          rate := flow_rec.rate;
          SELECT array_agg(id1)
          INTO   current_path
          FROM   pgr_dijkstra('SELECT 1 id, switch_id as source,
                        next_id as target, 1.0::float8 as cost
                        FROM topology
                        WHERE available_bw >= ' || rate,
                        src, dst,
                        TRUE, FALSE);
          full_path:=full_path[1:(array_length(full_path,1)-1)] || current_path;
        EXCEPTION
        WHEN OTHERS THEN
          RAISE NOTICE 'Route not found for flow_id % ', OLD.flow_id;
          INSERT INTO flow_status
          VALUES (OLD.flow_id, FALSE);
          RETURN OLD;
        END;
      END LOOP;
      -- Check if the obtained route has a loop
      IF EXISTS (SELECT 1 
                 FROM unnest(full_path) AS d 
                 GROUP by d having count(1) > 1) THEN
          RAISE NOTICE 'Auto-route for constraint causes loop';
          INSERT INTO flow_status
          VALUES (OLD.flow_id, FALSE);
          RETURN OLD;
      END IF;
      FOR i IN 1..(array_length(full_path, 1)-1) LOOP
       INSERT INTO configuration(flow_id, switch_id, next_id)
       SELECT OLD.flow_id, full_path[i], full_path[i+1]
       WHERE NOT EXISTS (
        SELECT 1 FROM configuration c
        WHERE c.flow_id   =  OLD.flow_id
        AND   c.switch_id = full_path[i]
        AND   c.next_id   = full_path[i+1]);
      END LOOP;
      INSERT INTO flow_status
      VALUES (OLD.flow_id, TRUE);
    END IF;
  END IF;
  RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER configuration_delete
    AFTER DELETE ON configuration
    FOR EACH ROW
    WHEN (OLD.valid = TRUE)
    EXECUTE PROCEDURE configuration_delete_func();

CREATE OR REPLACE FUNCTION configuration_bw_update_func() RETURNS 
        trigger AS $$
DECLARE
  lrate integer;
  lavailable_bw  integer;
BEGIN
  IF TG_OP = 'DELETE' OR TG_OP = 'UPDATE' THEN

    -- Release the used bw
    SELECT rate INTO lrate
    FROM   flow_constraints f
    WHERE  f.flow_id = OLD.flow_id;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'Flow id % not found', OLD.flow_id;
      RETURN NULL;
    END IF;
    UPDATE topology 
    SET    available_bw = available_bw + lrate,
           utilized_bw  = utilized_bw  - lrate
    WHERE  switch_id    = OLD.switch_id
    AND    next_id      = OLD.next_id;
  END IF;

  IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
    SELECT available_bw INTO lavailable_bw
    FROM   topology t
    WHERE  t.switch_id = NEW.switch_id
    AND    t.next_id   = NEW.next_id;
    IF NOT FOUND THEN
      RAISE EXCEPTION '% to % does not validate against topology', 
          NEW.switch_id, NEW.next_id;
      RETURN NULL;
    END IF;


    -- Check if the entry causes a loop
    IF EXISTS (SELECT 1 FROM configuration
               WHERE flow_id   = NEW.flow_id
               AND   switch_id = NEW.next_id) THEN
          RAISE EXCEPTION 'Configuration causes a loop at %' , NEW.next_id;
          RETURN NULL;
    END IF;

    SELECT rate INTO lrate
    FROM   flow_constraints f
    WHERE  f.flow_id = NEW.flow_id;
    IF NOT FOUND THEN
          RAISE EXCEPTION 'Flow id % not found', NEW.flow_id;
    END IF;

    IF lrate <= lavailable_bw THEN
      UPDATE topology 
      SET    available_bw = available_bw - lrate,
             utilized_bw  = utilized_bw  + lrate
      WHERE  switch_id    = NEW.switch_id
      AND    next_id      = NEW.next_id;
    ELSE
      RAISE EXCEPTION 'Available BW % is less then required % between % % ',
                   lavailable_bw, lrate, NEW.switch_id, NEW.next_id ;
    END IF;
  END IF;
  IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
    RETURN NEW;
  ELSE 
    RETURN OLD;
  END IF;
END;
$$ LANGUAGE plpgsql STRICT;

CREATE OR REPLACE FUNCTION configuration_truncate_func() RETURNS 
    trigger AS $$
BEGIN
  UPDATE flow_status
  SET    rechable = FALSE;
  UPDATE topology
  SET    available_bw = available_bw + utilized_bw,
         utilized_bw = 0;
  RETURN null;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER configuration_bw_update1
    AFTER INSERT OR DELETE ON configuration
    FOR EACH ROW
    EXECUTE PROCEDURE configuration_bw_update_func();


CREATE TRIGGER configuration_bw_update2
    AFTER UPDATE ON configuration
    FOR EACH ROW
    WHEN (OLD.valid = NEW.valid)
    EXECUTE PROCEDURE configuration_bw_update_func();


CREATE TRIGGER configuration_truncate
    AFTER TRUNCATE ON configuration
    FOR EACH STATEMENT
    EXECUTE PROCEDURE configuration_truncate_func();

------------------------------------------------------------
------------------------------------------------------------
-- Flow policy
------------------------------------------------------------
------------------------------------------------------------
CREATE OR REPLACE FUNCTION flow_policy_fun(flow_id_in integer)
RETURNS TABLE (path_vector integer[]) AS $$
  WITH RECURSIVE reach AS (
      (SELECT next_id, 
              ARRAY[switch_id, next_id] AS path_vector
       FROM   configuration
       WHERE  flow_id = flow_id_in
       AND    switch_id NOT IN 
          (SELECT next_id 
           FROM   configuration 
           WHERE  flow_id = flow_id_in))
       UNION
       (SELECT x.next_id, 
               r.path_vector || ARRAY[x.next_id]
        FROM   configuration x,  reach r
        WHERE  x.flow_id   = flow_id_in
        AND    x.switch_id = r.next_id)
  )
  SELECT r.path_vector
  FROM   reach r
  WHERE  r.next_id NOT IN
        (SELECT switch_id 
         FROM   configuration 
         WHERE  flow_id = flow_id_in);
$$ LANGUAGE SQL STABLE STRICT;

CREATE OR REPLACE VIEW flow_policy AS (
      SELECT flow_id,
             flow_name,
             rate,
             path_vector,
             rechable
      FROM   flow_constraints NATURAL JOIN flow_status
      LEFT OUTER JOIN flow_policy_fun(flow_id) ON TRUE
      ORDER BY flow_id
);

-- Flow policy Maintainance


CREATE OR REPLACE FUNCTION flow_policy_update_func() RETURNS 
    trigger AS $$
DECLARE
  full_path integer[];
  current_path integer[];
  src integer;
  dst integer;
  rate integer;
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM flow_constraints
    WHERE  flow_id = OLD.flow_id;
  END IF;


  IF TG_OP = 'INSERT' THEN
    -- Reject insert if flows exists
    INSERT INTO flow_constraints 
                (flow_id, flow_name, rate)
    VALUES (NEW.flow_id, NEW.flow_name, NEW.rate);

    IF NEW.path_vector IS NOT NULL THEN
      FOR i IN 1..(array_length(NEW.path_vector, 1)-1) LOOP
       INSERT INTO configuration(flow_id, switch_id, next_id)
       SELECT NEW.flow_id, NEW.path_vector[i], NEW.path_vector[i+1]
       WHERE NOT EXISTS (
        SELECT 1 FROM configuration c
        WHERE  c.flow_id   =  NEW.flow_id
        AND    c.switch_id = NEW.path_vector[i]
        AND    c.next_id   = NEW.path_vector[i+1]);
      END LOOP;
      UPDATE flow_status 
      SET    rechable = TRUE
      WHERE  flow_id  = NEW.flow_id;

    END IF;
  END IF;

  IF TG_OP = 'UPDATE' THEN
    -- Cannot change IDs
    IF OLD.flow_id <> NEW.flow_id
      OR OLD.flow_name <> NEW.flow_name THEN
      RAISE EXCEPTION 'Cannot update flow_id or flow_name';
      RETURN NULL;
    END IF;

    -- path_vectr update only allowed in case of no constraints
    IF OLD.path_vector <> NEW.path_vector THEN
      IF EXISTS (SELECT 1
                 FROM   flow_constraints
                 WHERE  flow_id = NEW.flow_id
                 AND    constraints IS NOT NULL) THEN
        RAISE EXCEPTION 'Cannot specify path_vector in presence of constraints';
        RETURN NULL;
      END IF;

      -- Delete old path
      FOR i IN 1..(array_length(OLD.path_vector, 1)-1) LOOP
        DELETE FROM configuration
        WHERE  flow_id   =  OLD.flow_id
        AND    switch_id = OLD.path_vector[i]
        AND    next_id   = OLD.path_vector[i+1];
      END LOOP;

      -- Create new path
      FOR i IN 1..(array_length(NEW.path_vector, 1)-1) LOOP
       INSERT INTO configuration(flow_id, switch_id, next_id)
       SELECT NEW.flow_id, NEW.path_vector[i], NEW.path_vector[i+1]
       WHERE NOT EXISTS (
        SELECT 1 FROM configuration c
        WHERE  c.flow_id   =  NEW.flow_id
        AND    c.switch_id = NEW.path_vector[i]
        AND    c.next_id   = NEW.path_vector[i+1]);
      END LOOP;
      UPDATE flow_status 
      SET    rechable = TRUE
      WHERE  flow_id  = NEW.flow_id;

    END IF;
  END IF;
  IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
    RETURN NEW;
  ELSE 
    RETURN OLD;
  END IF;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER flow_policy_update
    INSTEAD OF INSERT OR UPDATE OR DELETE ON flow_policy
    FOR EACH ROW
    EXECUTE PROCEDURE flow_policy_update_func();


------------------------------------------------------------
------------------------------------------------------------
--  End to End flow policy
------------------------------------------------------------
------------------------------------------------------------

CREATE OR REPLACE VIEW e2e_flow_policy AS (
      SELECT flow_id,
             flow_name, 
             path_vector[1] AS src,
             path_vector[array_length(path_vector,1)] AS dst,
             rate
      FROM   flow_constraints NATURAL JOIN flow_status
      LEFT OUTER JOIN flow_policy_fun(flow_id) ON TRUE
      WHERE path_vector IS NOT NULL
      ORDER BY flow_id
);


-- E2E Flow policy Maintainance

CREATE OR REPLACE FUNCTION e2e_flow_policy_update_func() RETURNS 
    trigger AS $$
DECLARE
  full_path integer[];
  src integer;
  dst integer;
  rate integer;
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM flow_constraints
    WHERE  flow_id = OLD.flow_id;
  END IF;


  IF TG_OP = 'INSERT' THEN
    IF NEW.flow_id   IS NULL OR
       NEW.flow_name IS NULL OR
       NEW.rate      IS NULL OR
       NEW.src       IS NULL OR
       NEW.dst       IS NULL THEN
      RAISE EXCEPTION 'All attributes are required';
      RETURN NULL;
    END IF;  

    -- Reject insert if flows exists
    INSERT INTO flow_constraints 
                (flow_id, flow_name, rate)
    VALUES (NEW.flow_id, NEW.flow_name, NEW.rate);

    src  := NEW.src;
    dst  := NEW.dst;
    rate := NEW.rate;

    BEGIN
      SELECT array_agg(id1)
      INTO   full_path
      FROM   pgr_dijkstra('SELECT 1 id, switch_id as source,
                    next_id as target, 1.0::float8 as cost
                    FROM topology
                    WHERE available_bw >= ' || rate,
                    src, dst,
                    TRUE, FALSE);
    EXCEPTION
    WHEN OTHERS THEN
      RAISE EXCEPTION 'Route not found from % to %', NEW.src, NEW.dst;
      RETURN NULL;
    END;

    IF full_path IS NOT NULL THEN
      FOR i IN 1..(array_length(full_path, 1)-1) LOOP
       INSERT INTO configuration(flow_id, switch_id, next_id)
       SELECT NEW.flow_id, full_path[i], full_path[i+1]
       WHERE NOT EXISTS (
        SELECT 1 FROM configuration c
        WHERE  c.flow_id   = NEW.flow_id
        AND    c.switch_id = full_path[i]
        AND    c.next_id   = full_path[i+1]);
      END LOOP;
      UPDATE flow_status 
      SET    rechable = TRUE
      WHERE  flow_id  = NEW.flow_id;
    ELSE
      RAISE EXCEPTION 'Route not found from % to %', NEW.src, NEW.dst;
      RETURN NULL;
    END IF;
  END IF;

  IF TG_OP = 'UPDATE' THEN
    -- Cannot change IDs
    IF OLD.flow_id     <> NEW.flow_id
      OR OLD.flow_name <> NEW.flow_name 
      OR OLD.src       <> NEW.src 
      OR OLD.dst       <> NEW.dst THEN 
      RAISE EXCEPTION 'Can only update rate';
      RETURN NULL;
    END IF;

    IF OLD.rate <> NEW.rate THEN
      UPDATE flow_constraints
      SET    rate = NEW.rate
      WHERE  flow_id = NEW.flow_id;
    END IF;
  END IF;
  IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
    RETURN NEW;
  ELSE 
    RETURN OLD;
  END IF;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER e2e_flow_policy_update
    INSTEAD OF INSERT OR UPDATE OR DELETE ON e2e_flow_policy
    FOR EACH ROW
    EXECUTE PROCEDURE e2e_flow_policy_update_func();


------------------------------------------------------------
------------------------------------------------------------
--  One big switch Virtulization
------------------------------------------------------------
------------------------------------------------------------
DROP TABLE IF EXISTS obs_mapping CASCADE;
-- V_node needs to be same for all entries.
CREATE TABLE obs_mapping (
       p_node integer,
       v_node integer,
       PRIMARY KEY (p_node)
);
CREATE INDEX ON obs_mapping(v_node);

/* This view will not support updates as it reflects the physical connections */
CREATE OR REPLACE VIEW obs_topology AS (
  SELECT COALESCE(NULLIF(t.switch_id, ob.p_node), v_node) switch_id,
         COALESCE(NULLIF(t.next_id, ob.p_node),   v_node) next_id,
         available_bw, utilized_bw
  FROM   topology t INNER JOIN obs_mapping ob
  ON     t.switch_id = ob.p_node 
  OR     t.next_id   = ob.p_node
);


CREATE OR REPLACE VIEW obs_configuration AS (
  SELECT flow_id,
         COALESCE(NULLIF(t.switch_id, ob.p_node), v_node) switch_id,
         COALESCE(NULLIF(t.next_id, ob.p_node),   v_node) next_id
  FROM   configuration t INNER JOIN obs_mapping ob
  ON     t.switch_id = ob.p_node 
  OR     t.next_id   = ob.p_node
);

CREATE OR REPLACE VIEW e2e_obs_flow_policy AS (
      WITH v_switches AS (SELECT DISTINCT v_node FROM obs_mapping)
      SELECT obs1.flow_id, flow_name, obs1.switch_id src,
             obs2.next_id dst, rate
      FROM   obs_configuration obs1 NATURAL JOIN flow_constraints 
             INNER JOIN obs_configuration obs2 
             ON  obs1.flow_id = obs2.flow_id
             AND obs1.next_id = obs2.switch_id
      WHERE  obs1.switch_id NOT IN (SELECT * FROM v_switches)
);

-- E2E update on configuration

CREATE OR REPLACE FUNCTION obs_configuration_update_func() RETURNS 
    trigger AS $$
DECLARE
  virtual_node integer;
  lswitch_id    integer;
  lnext_id      integer;
BEGIN
  -- If virtual node, there will be many physical node.
  -- Pick up one based on topology.
  SELECT v_node INTO virtual_node
  FROM   obs_mapping
  LIMIT 1;

  IF TG_OP = 'DELETE' THEN
    lswitch_id = OLD.switch_id;
    lnext_id   = OLD.next_id;
  END IF;

  IF TG_OP = 'INSERT' THEN
    lswitch_id = NEW.switch_id;
    lnext_id   = NEW.next_id;

    -- Either of the switches should be virtual_node
    IF  lswitch_id <> virtual_node
    AND lnext_id   <> virtual_node THEN
      RAISE EXCEPTION 'Atleast one node shold be virtual';
      RETURN NULL;
    END IF;

  END IF;

  IF lnext_id = virtual_node THEN
    SELECT next_id
    INTO   lnext_id
    FROM   topology
    WHERE  next_id IN 
          (SELECT p_node 
           FROM   obs_mapping)
    AND switch_id = lswitch_id;
  ELSE
    SELECT switch_id
    INTO   lswitch_id
    FROM   topology
    WHERE  switch_id IN 
          (SELECT p_node 
           FROM   obs_mapping)
    AND next_id = lnext_id;
  END IF;

  IF TG_OP = 'DELETE' THEN
    DELETE FROM configuration
    WHERE  flow_id   = OLD.flow_id
    AND    switch_id = lswitch_id
    AND    next_id   = lnext_id;
    RETURN OLD;
  END IF;

  IF TG_OP = 'INSERT' THEN
    INSERT INTO configuration(flow_id, switch_id, next_id)
    VALUES (NEW.flow_id, lswitch_id, lnext_id);
    RETURN NEW;
  END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER obs_configuration_update
    INSTEAD OF INSERT OR DELETE ON obs_configuration
    FOR EACH ROW
    EXECUTE PROCEDURE obs_configuration_update_func();

-- E2E Flow policy Maintainance
-- Does not create the intermedate path
CREATE OR REPLACE FUNCTION e2e_obs_flow_policy_update_func() RETURNS 
    trigger AS $$
DECLARE
  middle_node integer;
  ingres_node integer;
  egres_node  integer;
  full_path   integer[];
  rate        integer;
BEGIN
  IF TG_OP = 'DELETE' THEN
    -- We only delete forwarding for our p_switches
    DELETE FROM configuration
    WHERE  flow_id = OLD.flow_id
    AND    switch_id IN (SELECT p_node FROM obs_mapping);
  END IF;

  IF TG_OP = 'INSERT' THEN
    IF NEW.flow_id   IS NULL OR
       NEW.flow_name IS NULL OR
       NEW.rate      IS NULL OR
       NEW.src       IS NULL OR
       NEW.dst       IS NULL THEN
      RAISE EXCEPTION 'All attributes are required';
      RETURN NULL;
    END IF;  

    IF NOT EXISTS (SELECT switch_id FROM topology 
                   WHERE  switch_id = NEW.src
                   AND    next_id in 
                         (SELECT p_node
                          FROM obs_mapping)) THEN
      RAISE EXCEPTION 'src does not validate obs_topology';
      RETURN NULL;
    END IF;

    IF NOT EXISTS (SELECT next_id FROM topology 
                   WHERE  next_id = NEW.dst
                   AND    switch_id in 
                         (SELECT p_node
                          FROM obs_mapping)) THEN
      RAISE EXCEPTION 'dst does not validate obs_topology';
      RETURN NULL;
    END IF;

    -- Reject insert if flows exists
    INSERT INTO flow_constraints 
                (flow_id, flow_name, rate)
    VALUES (NEW.flow_id, NEW.flow_name, NEW.rate);

    -- Since it is a star we just need to create two links
    -- Get v_node
    SELECT v_node INTO middle_node
    FROM   obs_mapping
    LIMIT  1;

    INSERT INTO obs_configuration(flow_id, switch_id, next_id)
    VALUES (NEW.flow_id, NEW.src, middle_node);

    -- Add the intermediate path
    SELECT next_id
    INTO   ingres_node
    FROM   topology
    WHERE  next_id IN 
          (SELECT p_node 
           FROM   obs_mapping)
    AND switch_id = NEW.src;

    SELECT switch_id
    INTO   egres_node
    FROM   topology
    WHERE  switch_id IN 
          (SELECT p_node 
           FROM   obs_mapping)
    AND next_id = NEW.dst;

    rate = NEW.rate;
    IF ingres_node <>  egres_node THEN   
      BEGIN
        SELECT array_agg(id1)
        INTO   full_path
        FROM   pgr_dijkstra('SELECT 1 id, switch_id as source,
                      next_id as target, 1.0::float8 as cost
                      FROM topology
                      WHERE available_bw >= ' || rate,
                      ingres_node, egres_node,
                      TRUE, FALSE);
      EXCEPTION
      WHEN OTHERS THEN
        RAISE EXCEPTION 'Route not found from % to %', ingres_node, egres_node;
        RETURN NULL;
      END;

      IF full_path IS NOT NULL THEN
        FOR i IN 1..(array_length(full_path, 1)-1) LOOP
         INSERT INTO configuration(flow_id, switch_id, next_id)
         SELECT NEW.flow_id, full_path[i], full_path[i+1]
         WHERE NOT EXISTS (
          SELECT 1 FROM configuration c
          WHERE  c.flow_id   = NEW.flow_id
          AND    c.switch_id = full_path[i]
          AND    c.next_id   = full_path[i+1]);
        END LOOP;
        UPDATE flow_status 
        SET    rechable = TRUE
        WHERE  flow_id  = NEW.flow_id;
      ELSE
        RAISE EXCEPTION 'Route not found from % to %', ingres_node, egres_node;
        RETURN NULL;
      END IF;
    END IF;

    INSERT INTO obs_configuration(flow_id, switch_id, next_id)
    VALUES (NEW.flow_id, middle_node, NEW.dst);

  END IF;

  IF TG_OP = 'UPDATE' THEN
    -- Cannot change IDs
    IF OLD.flow_id     <> NEW.flow_id
      OR OLD.flow_name <> NEW.flow_name 
      OR OLD.src       <> NEW.src 
      OR OLD.dst       <> NEW.dst THEN 
      RAISE EXCEPTION 'Can only update rate';
      RETURN NULL;
    END IF;

    IF OLD.rate <> NEW.rate THEN
      UPDATE flow_constraints
      SET    rate    = NEW.rate
      WHERE  flow_id = NEW.flow_id;
    END IF;
  END IF;
  IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
    RETURN NEW;
  ELSE 
    RETURN OLD;
  END IF;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER e2e_obs_flow_policy_update
    INSTEAD OF INSERT OR UPDATE OR DELETE ON e2e_obs_flow_policy
    FOR EACH ROW
    EXECUTE PROCEDURE e2e_obs_flow_policy_update_func();

------------------------------------------------------------
------------------------------------------------------------
--  Virtulization
------------------------------------------------------------
------------------------------------------------------------
-- User only sees the virtualized switches
DROP TABLE IF EXISTS vn_mapping;
CREATE TABLE vn_mapping (
       p_node integer NOT NULL,
       v_node integer,
       PRIMARY KEY (p_node, v_node)
);
--Might be an index is not needed
--CREATE INDEX ON vn_mapping(v_node);

CREATE OR REPLACE VIEW e2e_vn_flow_policy AS (
      SELECT fc.flow_id, fc.flow_name,
             vn1.v_node as src,
             vn2.v_node as dst,
             fc.rate
      FROM   flow_policy fp INNER JOIN flow_constraints fc
      ON     fp.flow_id = fc.flow_id
             INNER JOIN vn_mapping vn1
      ON     vn1.p_node = path_vector[1]
             INNER JOIN vn_mapping vn2
      ON     vn2.p_node = path_vector[array_length(path_vector,1)]
);

CREATE OR REPLACE FUNCTION e2e_vn_flow_policy_update_func() RETURNS 
    trigger AS $$
DECLARE
  full_path  integer[];
  src_p_node integer;
  dst_p_node integer;
  rate       integer;
BEGIN
  IF TG_OP = 'DELETE' THEN
    DELETE FROM e2e_flow_policy
    WHERE  flow_id = OLD.flow_id;
  END IF;

  IF TG_OP = 'INSERT' THEN
    IF NEW.flow_id   IS NULL OR
       NEW.flow_name IS NULL OR
       NEW.rate      IS NULL OR
       NEW.src       IS NULL OR
       NEW.dst       IS NULL THEN
      RAISE EXCEPTION 'All attributes are required';
      RETURN NULL;
    END IF;  

    -- Reject insert if source and dst are not in vn_mapping
    SELECT p_node
    INTO   src_p_node
    FROM   vn_mapping
    WHERE  v_node = NEW.src;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'Src % not found', NEW.src;
      RETURN NULL;
    END IF;

    SELECT p_node
    INTO   dst_p_node
    FROM   vn_mapping
    WHERE  v_node = NEW.dst;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'Dst % not found', NEW.dst;
      RETURN NULL;
    END IF;

    INSERT INTO e2e_flow_policy 
                (flow_id, flow_name, src, dst, rate)
    VALUES (NEW.flow_id, NEW.flow_name, src_p_node, dst_p_node,NEW.rate);
  END IF;

  IF TG_OP = 'UPDATE' THEN
    -- Cannot change IDs
    IF OLD.flow_id     <> NEW.flow_id
      OR OLD.flow_name <> NEW.flow_name 
      OR OLD.src       <> NEW.src 
      OR OLD.dst       <> NEW.dst THEN 
      RAISE EXCEPTION 'Can only update rate';
      RETURN NULL;
    END IF;

    IF OLD.rate <> NEW.rate THEN
      UPDATE e2e_flow_policy
      SET    rate    = NEW.rate
      WHERE  flow_id = NEW.flow_id;
    END IF;
  END IF;
  IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
    RETURN NEW;
  ELSE 
    RETURN OLD;
  END IF;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER e2e_vn_flow_policy_update
    INSTEAD OF INSERT OR UPDATE OR DELETE ON e2e_vn_flow_policy
    FOR EACH ROW
    EXECUTE PROCEDURE e2e_vn_flow_policy_update_func();


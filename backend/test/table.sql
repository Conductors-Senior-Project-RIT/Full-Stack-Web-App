DROP TABLE IF Exists UserPreferences CASCADE;
DROP TABLE IF EXISTS NotificationConfig CASCADE;
DROP TABLE IF EXISTS Pins CASCADE;
DROP TABLE IF EXISTS EOTRecords CASCADE;
DROP TABLE IF EXISTS HOTRecords CASCADE;
DROP TABLE IF EXISTS Stations CASCADE;
DROP TABLE IF EXISTS Engine_Numbers CASCADE;
DROP TABLE IF EXISTS Symbols CASCADE;
DROP TABLE IF EXISTS Users CASCADE;
DROP TABLE IF EXISTS USER_ROLES CASCADE;

CREATE TABLE IF NOT EXISTS USER_ROLES(
    id              SERIAL PRIMARY KEY,
    title           VARCHAR(20)
);

INSERT INTO USER_ROLES (id, title) VALUES
(0, 'Admin'),
(1, 'Volunteer'),
(2, 'User');

CREATE TABLE IF NOT EXISTS Stations (
    id              SERIAL PRIMARY KEY,
    station_name    VARCHAR(240) NOT NULL,
    passwd          varchar(240) NOT NULL,
    last_seen       TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS Users(
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(240) NOT NULL UNIQUE,
    passwd          VARCHAR(240) NOT NULL,
    token           VARCHAR(480) DEFAULT NULL,     -- unnecessary as jwt is handled with cookies (might be useful for blacklisting?)
    acc_status      INT NOT NULL DEFAULT 2, -- 2 is normal user, 1 is volunteer, 0 is admin (ken) | This is user_roles table i guess lol
    starting_time   TIME WITH TIME ZONE DEFAULT '00:00 EST', 
    ending_time     TIME WITH TIME ZONE DEFAULT '23:59 EST',
    pushover_id     VARCHAR(240) DEFAULT NULL -- only used for volunteers and ken, normal users arent using this
);

CREATE TABLE IF NOT EXISTS Reset_Requests(
    id              SERIAL PRIMARY KEY,
    uid             INTEGER REFERENCES Users(id) NOT NULL,
    token           CHAR(64) NOT NULL, -- maybe this should be called "password_reset_token" as it's different from JWT
    expiration      TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS Symbols (
    id              SERIAL PRIMARY KEY,
    symb_name       VARCHAR(240) NOT NULL
);

CREATE TABLE IF NOT EXISTS Engine_Numbers ( --for now same as symbol, want to make sure it is something that will work since I am not sure if there are leading characters or dashes
    id              SERIAL PRIMARY KEY,
    eng_num         VARCHAR(240) NOT NULL
);

CREATE TABLE IF NOT EXISTS EOTRecords(
    -- currently there are a few things that ken wants that we arent tracking here - namely movement railroad, power setting, reverser, and all HOT signals. Thats a later issue.
    id                      SERIAL NOT NULL PRIMARY KEY,
    date_rec                TIMESTAMP NOT NULL,
    station_recorded        INT REFERENCES Stations(id) NOT NULL,
    symbol_id               INT REFERENCES Symbols(id) DEFAULT NULL,
    engine_num              INT REFERENCES Engine_Numbers(id) DEFAULT NULL,
    unit_addr               VARCHAR(240) DEFAULT 'unknown' NOT NULL ,
    brake_pressure          VARCHAR(240) DEFAULT 'unknown' NOT NULL,
    motion                  VARCHAR(240) DEFAULT 'unknown' NOT NULL,
    marker_light            VARCHAR(240) DEFAULT 'unknown' NOT NULL,
    turbine                 VARCHAR(240) DEFAULT 'unknown' NOT NULL,
    battery_cond            VARCHAR(240) DEFAULT 'unknown' NOT NULL,
    battery_charge          VARCHAR(240) DEFAULT 'unknown' NOT NULL,
    arm_status              VARCHAR(240) DEFAULT 'unknown' NOT NULL,
    signal_strength         FLOAT DEFAULT 0.0 NOT NULL,
    verified                BOOLEAN DEFAULT FALSE,
    verifier_id             INT REFERENCES Users(id) DEFAULT NULL,
    most_recent             BOOLEAN DEFAULT TRUE,
    locomotive_num          VARCHAR(240) DEFAULT 'unknown' NOT NULL
);

CREATE TABLE IF NOT EXISTS HOTRecords(
    id                      SERIAL NOT NULL PRIMARY KEY,
    date_rec                TIMESTAMP NOT NULL,
    station_recorded        INT REFERENCES Stations(id) NOT NULL,
    symbol_id               INT REFERENCES Symbols(id) DEFAULT NULL,
    engine_num              INT REFERENCES Engine_Numbers(id) DEFAULT NULL,
    frame_sync              VARCHAR(240) DEFAULT 'unknown' NOT NULL,
    unit_addr               VARCHAR(240) DEFAULT 'unknown' NOT NULL,
    command                 VARCHAR(240) DEFAULT 'unknown' NOT NULL,
    checkbits               VARCHAR(240) DEFAULT 'unknown' NOT NULL,
    parity                  VARCHAR(240) DEFAULT 'unknown' NOT NULL,
    verified                BOOLEAN DEFAULT FALSE,
    verifier_id             INT REFERENCES Users(id) DEFAULT NULL,
    most_recent             BOOLEAN DEFAULT TRUE,
    locomotive_num          VARCHAR(240) DEFAULT 'unknown' NOT NULL,
    signal_strength         FLOAT DEFAULT 0.0 NOT NULL
);

CREATE OR REPLACE VIEW EOTCollation AS (
	WITH StationChanges AS (
		SELECT
			e.id,
			e.date_rec,
			e.station_recorded,
			e.symbol_id,
			e.unit_addr,
			e.brake_pressure,
			e.motion,
			e.marker_light,
			e.turbine,
			e.battery_cond,
			e.battery_charge,
			e.arm_status,
			e.signal_strength,
			e.verified,
			e.locomotive_num,
			LAG(e.station_recorded) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) AS prev_station,
			LAG(e.date_rec) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) AS prev_date_rec,
			CASE
				WHEN LAG(e.station_recorded) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) IS DISTINCT FROM e.station_recorded THEN 1
				WHEN e.date_rec - LAG(e.date_rec) OVER (PARTITION BY e.unit_addr ORDER BY e.date_rec) > INTERVAL '2 hours' THEN 1
				ELSE 0
			END AS is_new_group
		FROM EOTRecords e
	),
	GroupedRecords AS (
		SELECT
			id,
			date_rec,
			station_recorded,
			symbol_id,
			unit_addr,
			brake_pressure,
			motion,
			marker_light,
			turbine,
			battery_cond,
			battery_charge,
			arm_status,
			signal_strength,
			verified,
			locomotive_num,
			SUM(is_new_group) OVER (PARTITION BY unit_addr ORDER BY date_rec) AS group_id
		FROM StationChanges
	),
	UnitAddrOccurrences AS (
		SELECT
			unit_addr,
			station_recorded,
			group_id,
			MIN(date_rec) AS first_seen,
			MAX(date_rec) AS last_seen
		FROM GroupedRecords
		GROUP BY unit_addr, station_recorded, group_id
	),
	UnitAddrDetails AS (
		SELECT
			g.id,
			g.date_rec,
			stat.station_name,
			g.symbol_id,
			g.unit_addr,
			g.brake_pressure,
			g.motion,
			g.marker_light,
			g.turbine,
			g.battery_cond,
			g.battery_charge,
			g.arm_status,
			g.signal_strength,
			g.verified,
			g.station_recorded,
			g.locomotive_num,
			uo.first_seen,
			uo.last_seen,
			ROW_NUMBER() OVER (PARTITION BY g.unit_addr, g.station_recorded, g.group_id ORDER BY g.date_rec DESC) AS row_num,
			COUNT(*) OVER (PARTITION BY g.unit_addr, g.station_recorded, g.group_id) AS occurrence_count
		FROM GroupedRecords g
		INNER JOIN Stations stat ON g.station_recorded = stat.id
		INNER JOIN UnitAddrOccurrences uo
			ON g.unit_addr = uo.unit_addr
			AND g.station_recorded = uo.station_recorded
			AND g.group_id = uo.group_id
	)
	SELECT
		d.id,
		TO_CHAR(d.date_rec, 'YYYY-MM-DD HH24:MI:SS') AS date_rec,
		d.station_name,
		d.unit_addr,
		d.brake_pressure,
		d.motion,
		d.marker_light,
		d.turbine,
		d.battery_cond,
		d.battery_charge,
		d.arm_status,
		d.signal_strength,
		d.verified,
		TO_CHAR(d.first_seen, 'YYYY-MM-DD HH24:MI:SS') AS first_seen,
		TO_CHAR(d.last_seen, 'YYYY-MM-DD HH24:MI:SS') AS last_seen,
		d.occurrence_count,
		AGE(d.last_seen, d.first_seen) AS duration,
		CASE WHEN d.symbol_id IS NULL THEN NULL ELSE f.symb_name END,
		d.locomotive_num
	FROM UnitAddrDetails d
	LEFT JOIN Symbols f
	ON d.symbol_id = f.id
	WHERE d.row_num = 1
);

CREATE OR REPLACE VIEW HOTCollation AS (
	WITH StationChanges AS (
		SELECT
			h.id,
			h.date_rec,
			h.station_recorded,
			h.symbol_id,
			h.unit_addr,
			h.signal_strength,
			h.command,
			h.frame_sync,
			h.checkbits,
			h.parity,
			h.verified,
			h.locomotive_num,
			LAG(h.station_recorded) OVER (PARTITION BY h.unit_addr ORDER BY h.date_rec) AS prev_station,
			LAG(h.date_rec) OVER (PARTITION BY h.unit_addr ORDER BY h.date_rec) AS prev_date_rec,
			CASE
				WHEN LAG(h.station_recorded) OVER (PARTITION BY h.unit_addr ORDER BY h.date_rec) IS DISTINCT FROM h.station_recorded THEN 1
				WHEN h.date_rec - LAG(h.date_rec) OVER (PARTITION BY h.unit_addr ORDER BY h.date_rec) > INTERVAL '2 hours' THEN 1
				ELSE 0
			END AS is_new_group
		FROM HOTRecords h
	),
	GroupedRecords AS (
		SELECT
			id,
			date_rec,
			station_recorded,
			symbol_id,
			unit_addr,
			signal_strength,
			command,
			frame_sync,
			checkbits,
			parity,
			verified,
			locomotive_num,
			SUM(is_new_group) OVER (PARTITION BY unit_addr ORDER BY date_rec) AS group_id
		FROM StationChanges
	),
	UnitAddrOccurrences AS (
		SELECT
			unit_addr,
			station_recorded,
			group_id,
			MIN(date_rec) AS first_seen,
			MAX(date_rec) AS last_seen
		FROM GroupedRecords
		GROUP BY unit_addr, station_recorded, group_id
	),
	UnitAddrDetails AS (
		SELECT
			g.id,
			g.date_rec,
			stat.station_name,
			g.symbol_id,
			g.unit_addr,
			g.signal_strength,
			g.command,
			g.frame_sync,
			g.checkbits,
			g.parity,
			g.verified,
			g.locomotive_num,
			g.station_recorded,
			uo.first_seen,
			uo.last_seen,
			ROW_NUMBER() OVER (PARTITION BY g.unit_addr, g.station_recorded, g.group_id ORDER BY g.date_rec DESC) AS row_num,
			COUNT(*) OVER (PARTITION BY g.unit_addr, g.station_recorded, g.group_id) AS occurrence_count
		FROM GroupedRecords g
		INNER JOIN Stations stat ON g.station_recorded = stat.id
		INNER JOIN UnitAddrOccurrences uo
			ON g.unit_addr = uo.unit_addr
			AND g.station_recorded = uo.station_recorded
			AND g.group_id = uo.group_id
	)
	SELECT
		d.id,
		TO_CHAR(d.date_rec, 'YYYY-MM-DD HH24:MI:SS') AS date_rec,
		d.station_name,
		d.unit_addr,
		d.signal_strength,
		d.command,
		d.frame_sync,
		d.checkbits,
		d.parity,
		d.verified,
		TO_CHAR(d.first_seen, 'YYYY-MM-DD HH24:MI:SS') AS first_seen,
		TO_CHAR(d.last_seen, 'YYYY-MM-DD HH24:MI:SS') AS last_seen,
		d.occurrence_count,
		AGE(d.last_seen, d.first_seen) AS duration,
		CASE WHEN d.symbol_id IS NULL THEN NULL ELSE f.symb_name END,
		d.locomotive_num
	FROM UnitAddrDetails d
	LEFT JOIN Symbols f
	ON d.symbol_id = f.id
	WHERE d.row_num = 1
);

CREATE TABLE IF NOT EXISTS NotificationConfig(
    id                      SERIAL NOT NULL PRIMARY KEY,
    station_id              INT REFERENCES Stations(id) NOT NULL,
    notification_user_ids   INT[]
);

CREATE TABLE IF NOT EXISTS Pins(
    id                      SERIAL NOT NULL PRIMARY KEY,
    station_location        INT REFERENCES Stations(id) NOT NULL,
    EOT_Signal              INT REFERENCES EOTRecords(id) DEFAULT NULL,
    HOT_Signal              INT REFERENCES HOTRecords(id) DEFAULT NULL,
    train_symbol            INT REFERENCES Symbols(id) DEFAULT NULL,
    engine_num              INT REFERENCES Engine_Numbers(id) DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS UserPreferences (
    user_id         INT NOT NULL,          -- The ID of the user
    station_id      INT NOT NULL,      -- The ID of the location
    PRIMARY KEY (user_id, station_id), -- Composite primary key to ensure uniqueness
    FOREIGN KEY (station_id) REFERENCES Stations(id) -- Ensures station_id exists in the station table
);

CREATE TABLE IF NOT EXISTS TestTable (
    id          SERIAL PRIMARY KEY,
    test_col    VARCHAR(240) DEFAULT 'testDefault' NOT NULL,
    date        TIMESTAMP NOT NULL
);

CREATE OR REPLACE FUNCTION update_station_last_seen()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE stations
  SET last_seen = NOW()
  WHERE id = NEW.station_recorded;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER eot_last_seen_update
AFTER INSERT ON eotrecords
FOR EACH ROW
EXECUTE FUNCTION update_station_last_seen();

CREATE TRIGGER hot_last_seen_update
AFTER INSERT ON hotrecords
FOR EACH ROW
EXECUTE FUNCTION update_station_last_seen(); 
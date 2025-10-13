DROP TABLE IF Exists UserPreferences;
DROP TABLE IF EXISTS NotificationConfig;
DROP TABLE IF EXISTS Pins;
DROP TABLE IF EXISTS EOTRecords;
DROP TABLE IF EXISTS HOTRecords;
DROP TABLE IF EXISTS Stations CASCADE;
DROP TABLE IF EXISTS Symbols;
DROP TABLE IF EXISTS Users CASCADE;
DROP TABLE IF EXISTS USER_ROLES;

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
    token           VARCHAR(480) DEFAULT NULL,            
    acc_status      INT NOT NULL DEFAULT 2, -- 2 is normal user, 1 is volunteer, 0 is admin (ken)
    starting_time   TIME WITH TIME ZONE DEFAULT '00:00 EST', 
    ending_time     TIME WITH TIME ZONE DEFAULT '23:59 EST',
    pushover_id     VARCHAR(240) DEFAULT NULL -- only used for volunteers and ken, normal users arent using this
);

CREATE TABLE IF NOT EXISTS Reset_Requests(
    id              SERIAL PRIMARY KEY,
    uid             INTEGER REFERENCES Users(id) NOT NULL,
    token           CHAR(64) NOT NULL,
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
    frame_sync              VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL,
    unit_addr               VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL,
    command                 VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL,
    checkbits               VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL,
    parity                  VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL,
    verified                BOOLEAN DEFAULT FALSE,
    verifier_id             INT REFERENCES Users(id) DEFAULT NULL,
    most_recent             BOOLEAN DEFAULT TRUE,
    locomotive_num          VARCHAR(240) DEFAULT 'unknown' NOT NULL,
    signal_strength         FLOAT DEFAULT 0.0 NOT NULL
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
DROP TABLE IF EXISTS EOTRecords;
DROP TABLE IF EXISTS HOTRecords;
DROP TABLE IF EXISTS Stations;
DROP TABLE IF EXISTS Symbols;
DROP TABLE IF EXISTS Users;
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
    station_lat     FLOAT NOT NULL,
    station_lon     FLOAT NOT NULL
);

CREATE TABLE IF NOT EXISTS Users(
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(240) NOT NULL,
    username        VARCHAR(240) NOT NULL,
    passwd          VARCHAR(240) NOT NULL,
    phone_number    VARCHAR(10) NOT NULL,
    loc_lat         FLOAT,
    loc_lon         FLOAT,             
    acc_status      INT NOT NULL DEFAULT 2 -- 2 is normal user, 1 is volunteer, 0 is admin (ken)
);

CREATE TABLE IF NOT EXISTS Symbols (
    id              SERIAL PRIMARY KEY,
    symb_name       VARCHAR(240) NOT NULL
);

CREATE TABLE IF NOT EXISTS EOTRecords(
    -- currently there are a few things that ken wants that we arent tracking here - namely movement railroad, power setting, reverser, and all HOT signals. Thats a later issue.
    id                      SERIAL NOT NULL PRIMARY KEY,
    date_rec                TIMESTAMP NOT NULL,
    station_recorded        INT REFERENCES Stations(id) NOT NULL,
    symbol_id               INT REFERENCES Symbols(id) DEFAULT NULL,
    unit_addr               VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL ,
    brake_pressure          VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL,
    motion                  VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL,
    marker_light            VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL,
    turbine                 VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL,
    battery_cond            VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL,
    battery_charge          VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL,
    arm_status              VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL,
    signal_stength          FLOAT DEFAULT 0.0 NOT NULL,
    verified                BOOLEAN DEFAULT FALSE,
    verifier_id             INT REFERENCES Users(id) DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS HOTRecords(
    id                      SERIAL NOT NULL PRIMARY KEY,
    date_rec                TIMESTAMP NOT NULL,
    station_recorded        INT REFERENCES Stations(id) NOT NULL,
    frame_sync              VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL,
    unit_addr               VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL,
    command                 VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL,
    checkbits               VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL,
    parity                  VARCHAR(240) DEFAULT 'UNKNOWN' NOT NULL
);




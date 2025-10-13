INSERT INTO Stations (id, station_name, station_lat, station_lon) VALUES
(0, 'test station', 41.22, 42.11);

INSERT INTO Symbols (id, symb_name) VALUES
(0, 'Test Symbol');

INSERT INTO Users (id, email, username, passwd, phone_number, acc_status) VALUES
(0, 'test@test.test', 'testname', 'hashed_pswd', '9999999999', 0);


INSERT INTO EOTRecords (id, date_rec, station_recorded, symbol_id) VALUES
(0, '1999-01-08 04:05:06', 0, 0);

ALTER SEQUENCE EOTRecords_ID_SEQ RESTART WITH 1;
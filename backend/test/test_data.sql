INSERT INTO Stations (id, station_name, passwd) VALUES
(0, 'test station', 'test'),
(1, 'test station2', 'test');

INSERT INTO Symbols (id, symb_name) VALUES
(0, 'Test Symbol'),
(1, 'Test Symbol2');

INSERT INTO Users (id, email, passwd, acc_status) VALUES
(0, 'test@test.test', 'hashed_pswd', 0);


INSERT INTO EOTRecords (id, unit_addr, date_rec, station_recorded, symbol_id, most_recent) VALUES
(0, 727,'1999-01-08 04:05:06', 0, 0, False),
(1, 1337, '2003-02-05 06:53:08', 0, NULL, False),
(2, 1234, '2025-03-25 5:00:00', 0, NULL, False),
(3, 1234, '2025-03-25 5:05:00', 0, NULL, False),
(4, 1234, '2025-03-25 5:10:00', 1, NULL, False),
(5, 1234, '2025-03-25 5:15:00', 0, NULL, False),
(6, 1234, '2025-03-25 5:20:00', 0, 0, True),
(7, 1234, '2025-05-25 5:20:00', 0, 0, True);



INSERT INTO HOTRecords (id, unit_addr, date_rec, station_recorded, most_recent) VALUES
(0, 1234, '1999-01-08 04:10:21', 0, False),
(1, 5678, '2001-02-04 01:23:45', 0, True),
(2, 9910, '2021-08-16 20:14:11', 0, True);

INSERT INTO Pins(id, station_location, EOT_Signal) VALUES (0,0,0);
INSERT INTO Pins(id, station_location, EOT_Signal) VALUES (1,0,0);
INSERT INTO Pins(id, station_location, EOT_Signal) VALUES (2,0,0);


-- update sequences for tables
ALTER SEQUENCE EOTRecords_ID_SEQ RESTART WITH 3;
ALTER SEQUENCE HOTRecords_ID_SEQ RESTART WITH 3;
ALTER SEQUENCE Pins_ID_SEQ RESTART WITH 1;
ALTER SEQUENCE Users_ID_SEQ RESTART WITH 1;
ALTER SEQUENCE Symbols_ID_SEQ RESTART WITH 1;
ALTER SEQUENCE Stations_ID_SEQ RESTART WITH 1;

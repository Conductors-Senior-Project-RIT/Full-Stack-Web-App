INSERT INTO Stations (id, station_name, passwd) VALUES
(1, 'test station1', 'test'),
(2, 'test station2', 'test');

INSERT INTO Symbols (id, symb_name) VALUES
(1, 'Test Symbol1'),
(2, 'Test Symbol2');

INSERT INTO Engine_Numbers (id, eng_num) VALUES
(1, 'R2D2'),
(2, 'C3PO');

INSERT INTO Users (id, email, passwd, acc_status) VALUES
(1, 'test@test.test', 'hashed_pswd', 0);


INSERT INTO EOTRecords (id, unit_addr, date_rec, station_recorded, symbol_id, most_recent) VALUES
(1, 727,'1999-01-08 04:05:06', 1, 1, False),
(2, 1337, '2003-02-05 06:53:08', 1, NULL, False),
(3, 1234, '2025-03-25 5:00:00', 1, NULL, False),
(4, 1234, '2025-03-25 5:05:00', 1, NULL, False),
(5, 1234, '2025-03-25 5:10:00', 2, NULL, False),
(6, 1234, '2025-03-25 5:15:00', 1, NULL, False),
(7, 1234, '2025-03-25 5:20:00', 1, 1, True),
(8, 1234, '2025-05-25 5:20:00', 1, 1, True);



INSERT INTO HOTRecords (id, unit_addr, date_rec, station_recorded, most_recent) VALUES
(1, '1234', '1999-01-08 04:10:21', 1, False),
(2, '5678', '2001-02-04 01:23:45', 1, True),
(3, '9910', '2021-08-16 20:14:11', 1, True),
(4, '9910', '2021-08-16 20:15:11', 1, True),
(5, '9910', '2021-08-16 20:16:11', 1, True),
(6, '9910', '2021-08-16 20:17:11', 2, True),
(7, '1234', '2026-08-16 20:17:11', 1, True);

INSERT INTO Pins(id, station_location, EOT_Signal) VALUES (1,1,1);
INSERT INTO Pins(id, station_location, EOT_Signal) VALUES (2,1,1);
INSERT INTO Pins(id, station_location, EOT_Signal) VALUES (3,1,1);


-- update sequences for tables
ALTER SEQUENCE EOTRecords_ID_SEQ RESTART WITH 9;
ALTER SEQUENCE HOTRecords_ID_SEQ RESTART WITH 8;
ALTER SEQUENCE Pins_ID_SEQ RESTART WITH 4;
ALTER SEQUENCE Users_ID_SEQ RESTART WITH 2;
ALTER SEQUENCE Symbols_ID_SEQ RESTART WITH 3;
ALTER SEQUENCE Engine_Numbers_ID_SEQ RESTART WITH 3;
ALTER SEQUENCE Stations_ID_SEQ RESTART WITH 3;

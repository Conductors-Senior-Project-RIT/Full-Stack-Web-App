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
(1, 'test@gmail.com', '$2b$12$REvUFYyQ.W13brwfMiDWYuYl1SmoxTJyCbdhCv9efuI9jgd4AO79u', 0);

INSERT INTO EOTRecords (id, unit_addr, date_rec, station_recorded, symbol_id, engine_num, most_recent) VALUES
(1, '727','1999-01-08 04:05:06', 1, 1, 1, FALSE),
(2, '1337', '2003-02-05 06:53:08', 1, NULL, 1, FALSE),
(3, '1234', '2025-03-25 5:00:00', 1, NULL, 1, FALSE),
(4, '1234', '2025-03-25 5:05:00', 1, NULL, 1, FALSE),
(5, '1234', '2025-03-25 5:10:00', 2, NULL, 2, FALSE),
(6, '1234', '2025-03-25 5:15:00', 1, NULL, 2, FALSE),
(7, '1234', '2025-03-25 5:20:00', 1, 1, 2, TRUE),
(8, '1234', '2025-05-25 5:20:01', 1, 2, 2, TRUE);

INSERT INTO HOTRecords (id, unit_addr, date_rec, station_recorded, symbol_id, engine_num, most_recent) VALUES
(1, '727','1999-01-08 04:05:06', 1, 1, 1, FALSE),
(2, '1337', '2003-02-05 06:53:08', 1, NULL, 1, FALSE),
(3, '1234', '2025-03-25 5:00:00', 1, NULL, 1, FALSE),
(4, '1234', '2025-03-25 5:05:00', 1, NULL, 1, FALSE),
(5, '1234', '2025-03-25 5:10:00', 2, NULL, 2, FALSE),
(6, '1234', '2025-03-25 5:15:00', 1, NULL, 2, FALSE),
(7, '1234', '2025-03-25 5:20:00', 1, 1, 2, TRUE),
(8, '1234', '2025-05-25 5:20:01', 1, 2, 2, TRUE);

INSERT INTO Pins(id, station_location, EOT_Signal) VALUES (1,1,1);
INSERT INTO Pins(id, station_location, EOT_Signal) VALUES (2,1,1);
INSERT INTO Pins(id, station_location, EOT_Signal) VALUES (3,1,1);


-- update sequences for tables
ALTER SEQUENCE EOTRecords_ID_SEQ RESTART WITH 9;
ALTER SEQUENCE HOTRecords_ID_SEQ RESTART WITH 9;
ALTER SEQUENCE Pins_ID_SEQ RESTART WITH 4;
ALTER SEQUENCE Users_ID_SEQ RESTART WITH 2;
ALTER SEQUENCE Symbols_ID_SEQ RESTART WITH 3;
ALTER SEQUENCE Engine_Numbers_ID_SEQ RESTART WITH 3;
ALTER SEQUENCE Stations_ID_SEQ RESTART WITH 3;

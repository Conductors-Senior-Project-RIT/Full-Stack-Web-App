from datetime import datetime
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import Session

from backend.test.db.test_utils import compare_results_pkey
from backend.src.db.db_core.exceptions import RepositoryExistingRowError, RepositoryInternalError, RepositoryInvalidArgumentError, RepositoryNotFoundError
from backend.database import db
from backend.src.db.station_repo import StationRepository
from backend.test.base_test_case import BaseTestCase

class TestStationRepository(BaseTestCase):
    def setUp(self):
        self.session = db.session
        self.repo = StationRepository(self.session)
        
    def tearDown(self):
        self.session.rollback() # revert changes made from every test_method ran
        self.session.close()
        
        
    def testGetStations(self):
        expected = [self.repo.get(i) for i in range(1, 3)]
        results = self.repo.get_stations()
        
        # Test to see if the fields and values from results match the expected
        valid, msg = compare_results_pkey(results, expected, "id")
        self.assertTrue(valid, msg)
        
        
    def testCreateNewStation(self):
        # Test that creating a new record returns the right id
        new_name = "Bob"
        new_pass = "Burger"
        
        result_id = self.repo.create_new_station(new_name, new_pass)
        self.assertEqual(3, result_id)
        
        # Test that the correct data was added
        resulting_row = self.repo.get(result_id)
        self.assertEqual(new_name, resulting_row["station_name"])
        self.assertEqual(new_pass, resulting_row["passwd"])
        
        # Test error handling in no id is returned (likely an error)
        with patch.object(Session, "execute") as mock_execute:
            mock_execute.return_value.scalar_one_or_none.return_value = None
            with self.assertRaises(RepositoryInternalError):
                self.repo.create_new_station("a", "b")
                
        # Test that error is raised when attempting to create a station with an already existing name
        with self.assertRaises(RepositoryExistingRowError):
            self.repo.create_new_station("test station1", "gg")
                
    def testUpdateStationPassword(self):
        # Test that the id of the updated station is correct
        new_pass = "bbbb"
        resulting_id = self.repo.update_station_password(1, new_pass)
        self.assertEqual(1, resulting_id)
        
        # Test that the updated password is reflected in session
        updated_row = self.repo.get(resulting_id)
        self.assertEqual(new_pass, updated_row["passwd"])
        
        # Test argument checking
        with self.assertRaises(RepositoryInvalidArgumentError):
            self.repo.update_station_password("1", "aaaa")
            self.repo.update_station_password(1, 3333)
            self.repo.update_station_password(None, None)
        
        # Test when a station is not found, an exception is raised
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.update_station_password(10, "cccc")
            
            
    def testGetStationID(self):
        # Test successfully finding id
        result_id = self.repo.get_station_id("test station1")
        self.assertEqual(1, result_id)
        
        # Test not finding id
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.get_station_id("kinda hungry rn")
        
        # Test handling exceptions
        with patch.object(Session, "execute") as mock_session:
            mock_session.side_effect = SQLAlchemyError
            with self.assertRaises(RepositoryInternalError):
                self.repo.get_station_id("thirsty too")
        
    
    def testGetLastSeen(self):
        # Test when a station's last seen is today is in the format "HH:MM AM/PM"
        expected = self.repo.get(1)["last_seen"].strftime("%I:%M %p")
        result = self.repo.get_last_seen("test station1")
        self.assertEqual(expected, result)
        
        # Test when a station was last seen is not today is in the format "MON DD, YYYY at HH:MM AM/PM"
        self.repo.update_with_pk(2, {"last_seen": datetime.strptime("2025-12-25 14:30:59", "%Y-%m-%d %H:%M:%S")})
        expected = self.repo.get(2)["last_seen"].strftime("%b %d, %Y at %I:%M %p")
        result = self.repo.get_last_seen("test station2")
        self.assertEqual(expected, result)
        
        # Test error when station is not found
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.get_last_seen("zzzzzzzzzz")
            
    
    def testUpdateLastSeen(self):
        # Test to see if last seen gets updated
        previous = self.repo.get(1)["last_seen"]
        result = self.repo.update_last_seen(1)
        self.assertNotEqual(previous, result)
        
        # Test to see if exception is raised if query returns None
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.update_last_seen(20)
        
        
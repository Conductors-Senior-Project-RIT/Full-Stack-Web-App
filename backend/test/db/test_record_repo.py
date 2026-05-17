from datetime import datetime
from pprint import pprint
import unittest
from unittest.mock import patch
import zoneinfo

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import Session

from backend.src.db.record_types import get_record_repository
from backend.src.db.record_repo import RecordRepository
from backend.src.db.db_core.exceptions import (
    RepositoryError,
    RepositoryInternalError,
    RepositoryInvalidArgumentError,
    RepositoryNotFoundError,
    RepositoryParsingError,
)
from backend.test.base_test_case import BaseTestCase
from .test_utils import compare_results_ordered, collation_valid

# Current test data has 8 records
TEST_RECORD_COUNT = 8


class RecordRepositoryTestMixin:
    """Contains the tests for RecordRepository that operates on `BaseRecord` models. The
    test data in `test_data.sql` should be the same throughout each model.
    """

    repo: RecordRepository = None
    test_data: list = []

    def test_total_record_count(self):
        """Test function for `get_total_record_count()` on provided `self.repo`."""
        self.assertEqual(TEST_RECORD_COUNT, self.repo.get_total_record_count())

    def test_create_train_record(self):
        """Test the various branches for `create_train_record()` on provided `self.repo`."""
        date_rec = datetime.strptime(
            "2026-01-08 04:05:06:-0400", "%Y-%m-%d %H:%M:%S:%z"
        )
        data = {"date_rec": date_rec, "unit_addr": "CT12", "station_recorded": 2}

        # Test recovery request creation
        result_id, result_recov = self.repo.create_train_record(data, None)
        self.assertEqual(TEST_RECORD_COUNT + 1, result_id)
        self.assertEqual(True, result_recov)

        # Test non-recovery request creation
        data["date_rec"] = None
        result_id, result_recov = self.repo.create_train_record(data, date_rec)
        self.assertEqual(TEST_RECORD_COUNT + 2, result_id)
        self.assertEqual(False, result_recov)

        # Test that fields not in model are removed
        data["armed"] = "and hammered"
        result_id, _ = self.repo.create_train_record(data, date_rec)
        new_record = self.repo.get(result_id, True)
        self.assertNotIn("armed", new_record)

        # Test datetime not provided raises exception
        with self.assertRaises(RepositoryInvalidArgumentError):
            self.repo.create_train_record(data, None)

        # Test create returning nothing raises error
        with patch.object(self.repo, "create") as mock:
            mock.return_value = None
            with self.assertRaises(RepositoryInternalError):
                self.repo.create_train_record(data, date_rec)

    def test_get_unit_record_ids(self):
        """Test the various branches in `get_unit_record_ids()` on provided `self.repo`."""
        # Check that valid list of ids are returned
        test_ret = list(range(3, TEST_RECORD_COUNT + 1))
        result = self.repo.get_unit_record_ids("1234", False)
        self.assertListEqual(test_ret, result)

        # Check that the most recent id returned
        result = self.repo.get_unit_record_ids("1234", True)
        self.assertEqual(TEST_RECORD_COUNT, result)

        # Test that an exception is raised when nothing is found
        with self.assertRaises(RepositoryNotFoundError):
            self.repo.get_unit_record_ids("unit", True)

    def test_get_recent_trains(self):
        """Test the various branches for `get_recent_trains()` on proivded `self.repo`."""
        # Create two new recent records
        data = {
            "date_rec": datetime.now(tz=zoneinfo.ZoneInfo("America/New_York")).replace(
                tzinfo=None
            ),
            "unit_addr": "3333",
            "station_recorded": 2,
            "most_recent": True,
        }
        expected = self.repo.create([data for _ in range(2)])

        # Test successful retrieval of new record
        results = self.repo.get_recent_trains("3333", 2)
        self.assertListEqual(expected, results)

        # Test failed retrieval of records
        results = self.repo.get_recent_trains("bruh", 1)
        self.assertListEqual([], results)

    def test_add_new_pin(self):
        """Test the various branches for `test_add_new_pin()` on provided `self.repo`."""
        # Test successful pin update
        result_id = self.repo.add_new_pin(TEST_RECORD_COUNT, "1234")
        self.assertListEqual([TEST_RECORD_COUNT - 1], result_id)

        # Update the last ID
        result_id = self.repo.add_new_pin(-1, "1234")
        self.assertListEqual([8], result_id)

    def _run_get_record_case(self, unit_addr, column, position, recent, expected):
        """Helper subtest for `test_get_record_column()`."""
        result = self.self.repo.get_record_column_by_unit_addr(
            unit_addr, column, position, recent
        )
        self.assertIsInstance(result, type(expected))
        self.assertEqual(expected, result)

    def test_get_record_column(self):
        """Test the various branches for `get_record_column_by_unit_addr()` on provided
        `self.repo`.
        """
        test_cases = [
            # Below are the tests for symbol_id
            ("1234", "symbol_id", True, [1, 2]),
            ("1234", "symbol_id", False, [None, None, None, None]),
            ("1234", "symbol_id", None, [None, None, None, None, 1, 2]),
            # Below are the tests for engine_num
            ("1234", "engine_num", True, [2, 2]),
            ("1234", "engine_num", False, [1, 1, 2, 2]),
            ("1234", "engine_num", None, [1, 1, 2, 2, 2, 2]),
            # Below are the not found cases
            ("0000", "engine_num", True, []),
            ("0000", "engine_num", False, []),
            ("0000", "engine_num", None, []),
        ]

        for unit, col, rec, exp in test_cases:
            # If this fails, the error message will include these params
            with self.subTest(unit=unit, col=col, rec=rec, exp=exp):
                result = self.repo.get_record_column_by_unit_addr(unit, col, rec)
                self.assertEqual(exp, result)

        # Make sure exception raised if not valid column
        with self.assertRaises(RepositoryInvalidArgumentError):
            self.repo.get_record_column_by_unit_addr("5545", "Bob")

        with self.assertRaises(RepositoryParsingError):
            self.repo.get_record_column_by_unit_addr("1111", "engine_num", "Bob")

    def test_update_signal_values(self):
        """Test the various branches for `update_signal_values()` on provided `self.repo`."""
        test_symbol = None
        test_engine = None

        # Test no values change
        result = self.repo.update_signal_values(1, test_symbol, test_engine)
        self.assertEqual(None, result)

        test_cases = [(2, None), (None, 2), (1, 1)]

        for sym, eng in test_cases:
            with self.subTest(sym=sym, eng=eng):
                updated = self.repo.update_signal_values(1, sym, eng)
                result = self.repo.get(1)
                self.assertEqual(updated, result)

    def test_verify_record(self):
        """Test the various branches for `verify_record()` on provided `self.repo`."""
        sym, loc = 2, "RG00"

        # Get the updated instance in session
        updated = self.repo.verify_record(1, sym, loc)

        # Make sure the changes are correctly reflected in the session
        result = self.repo.get(1)
        self.assertEqual(updated, result)

        with patch.object(RecordRepository, "update_with_pk") as mock:
            mock.side_effect = SQLAlchemyError
            with self.assertRaises(RepositoryInternalError):
                self.repo.verify_record(1, sym, loc)

    def test_get_records_at_station(self):
        """Test the various branches for `get_records_at_station()` on provided
        `self.repo`.
        """
        self.maxDiff = None

        # No filters, partial cols, all 8 records returned
        result = self.repo.get_records_at_station()
        self.assertEqual(8, len(result))
        self.assertIn("station_name", result[0])
        self.assertIn("symb_name", result[0])
        self.assertNotIn("most_recent", result[0])  # partial cols only

        # all_cols=True, all fields present
        result = self.repo.get_records_at_station(all_cols=True)
        self.assertEqual(8, len(result))
        self.assertIn("most_recent", result[0])

        # station_id filter
        result = self.repo.get_records_at_station(station_id=1)
        self.assertEqual(7, len(result))  # ids 1,2,3,4,6,7,8
        self.assertTrue(all(r["station_name"] == "test station1" for r in result))

        # Basic timeframe datetime
        dt = datetime.strptime("2005-01-08 04:05:06", "%Y-%m-%d %H:%M:%S")
        result = self.repo.get_records_at_station(dt=dt)
        self.assertEqual(6, len(result))  # ids 3-8

        # recent=True
        result = self.repo.get_records_at_station(recent=True)
        self.assertEqual(2, len(result))  # ids 7, 8

        # recent=False
        result = self.repo.get_records_at_station(recent=False)
        self.assertEqual(6, len(result))  # ids 1-6

        # Empty result
        result = self.repo.get_records_at_station(station_id=999)
        self.assertListEqual([], result)

        # Exception path
        with patch.object(self.repo, "objs_to_dicts", side_effect=Exception("boom")):
            with self.assertRaises(RepositoryError):
                self.repo.get_records_at_station()

    def test_get_train_history(self):
        """Test the various branches for `get_train_history()` on provided `self.repo`."""
        expected_record = self.test_data[0]
        expected_record["station_name"] = "test station1"
        expected_record["symb_name"] = "Test Symbol1"
        expected_record["date_rec"] = str(expected_record["date_rec"])

        results = self.repo.get_train_history(1)
        valid, msg = compare_results_ordered([results], [expected_record])
        self.assertTrue(valid, msg)

        results = self.repo.get_train_history(17)
        self.assertIsNone(results)

    def test_get_record_collation(self):
        """Test the various branches for `get_record_collation()` on provided `self.repo`."""
        expected = [
            {
                "id": 8,
                "date_rec": "2025-05-25 05:20:01",
                "first_seen": "2025-05-25 05:20:01",
                "last_seen": "2025-05-25 05:20:01",
                "duration": "0:00:00",
                "occurrence_count": "1",
                "unit_addr": "1234",
                "verified": False,
            },
            {
                "id": 7,
                "date_rec": "2025-03-25 05:20:00",
                "first_seen": "2025-03-25 05:15:00",
                "last_seen": "2025-03-25 05:20:00",
                "duration": "0:05:00",
                "occurrence_count": "2",
                "unit_addr": "1234",
                "verified": False,
            },
            {
                "id": 5,
                "date_rec": "2025-03-25 05:10:00",
                "first_seen": "2025-03-25 05:10:00",
                "last_seen": "2025-03-25 05:10:00",
                "duration": "0:00:00",
                "occurrence_count": "1",
                "unit_addr": "1234",
                "verified": False,
            },
            {
                "id": 4,
                "date_rec": "2025-03-25 05:05:00",
                "first_seen": "2025-03-25 05:00:00",
                "last_seen": "2025-03-25 05:05:00",
                "duration": "0:05:00",
                "occurrence_count": "2",
                "unit_addr": "1234",
                "verified": False,
            },
            {
                "id": 2,
                "date_rec": "2003-02-05 06:53:08",
                "first_seen": "2003-02-05 06:53:08",
                "last_seen": "2003-02-05 06:53:08",
                "duration": "0:00:00",
                "occurrence_count": "1",
                "unit_addr": "1337",
                "verified": False,
            },
            {
                "id": 1,
                "date_rec": "1999-01-08 04:05:06",
                "first_seen": "1999-01-08 04:05:06",
                "last_seen": "1999-01-08 04:05:06",
                "duration": "0:00:00",
                "occurrence_count": "1",
                "unit_addr": "727",
                "verified": False,
            },
        ]

        # All results in one page
        results = self.repo.get_record_collation(1, 250, None)
        valid, message = collation_valid(
            {"results": expected, "totalPages": 1}, results
        )
        self.assertTrue(valid, message)

        # First page of 2
        results = self.repo.get_record_collation(1, 2, None)
        valid, message = collation_valid(
            {"results": expected[0:2], "totalPages": 3}, results
        )
        self.assertTrue(valid, message)

        # Last page
        results = self.repo.get_record_collation(3, 2, None)
        valid, message = collation_valid(
            {"results": expected[4:], "totalPages": 3}, results
        )
        self.assertTrue(valid, message)

        # None verified yet
        results = self.repo.get_record_collation(1, 250, True)
        valid, message = collation_valid({"results": [], "totalPages": 0}, results)
        self.assertTrue(valid, message)

        # All unverified
        results = self.repo.get_record_collation(1, 250, False)
        valid, message = collation_valid(
            {"results": expected, "totalPages": 1}, results
        )
        self.assertTrue(valid, message)

    def test_get_record_collation_exceptions(self):
        """Test the exception for `get_record_collation()` on provided `self.repo`."""
        with patch.object(Session, "execute") as mock_session:
            mock_session.return_value.scalars.return_value.all.side_effect = (
                SQLAlchemyError
            )
            with self.assertRaises(RepositoryInternalError):
                self.repo.get_record_collation(1, 250, None)

        with patch("backend.src.db.record_repo.ceil", side_effect=ValueError()):
            with self.assertRaises(RepositoryParsingError):
                self.repo.get_record_collation(1, 250, None)


class TestEOTRepository(BaseTestCase, RecordRepositoryTestMixin):
    """Run `RecordRepository` tests for the `EOTRrecords` table."""

    def setUp(self):
        super().setUp()
        self.repo = get_record_repository(self.session, 1)
        self.test_data = [self.repo.get(i) for i in range(1, TEST_RECORD_COUNT + 1)]


class TestHOTRepository(BaseTestCase, RecordRepositoryTestMixin):
    """Run `RecordRepository` tests for the `HOTRrecords` table."""

    def setUp(self):
        super().setUp()
        self.repo = get_record_repository(self.session, 2)
        self.test_data = [self.repo.get(i) for i in range(1, TEST_RECORD_COUNT + 1)]


if __name__ == "__main__":
    unittest.main()

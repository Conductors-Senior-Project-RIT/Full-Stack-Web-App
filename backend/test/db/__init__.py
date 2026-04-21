# Run all tests specific to repo only with command below
# ./run_test.sh --verbose backend.test.db 

# from unittest import TestSuite

# from backend.test.db.test_base_record_repo import TestRecordRepository
# from backend.test.db.test_hot_record_repo import TestHOTRecordRepository
# from backend.test.db.test_eot_record_repo import TestEOTRecordRepository
# from backend.test.db.test_station_repo import TestStationRepository
# from backend.test.db.test_record_types import TestRecordTypes
# from backend.test.db.test_user_repo import TestUserRepository


# test_cases = (
#     TestRecordRepository, 
#     TestEOTRecordRepository, 
#     TestStationRepository, 
#     TestHOTRecordRepository, 
#     TestRecordTypes, 
#     TestUserRepository
# )

# def load_tests(loader, tests, pattern):
#     suite = TestSuite()
#     for test_class in test_cases:
#         tests = loader.loadTestsFromTestCase(test_class)
#         suite.addTests(tests)
#     return suite
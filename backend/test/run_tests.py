import unittest
from pyunitreport import HTMLTestRunner

suite = unittest.defaultTestLoader.discover(".")
runner = HTMLTestRunner(output="reports", report_name="test-results")
result = runner.run(suite)

raise SystemExit(not result.wasSuccessful())
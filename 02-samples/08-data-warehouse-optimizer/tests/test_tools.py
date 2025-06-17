"""
Unit tests for SQLite database tools.
"""

import unittest
import json
import os
from scripts.init_db import init_db
from utils.tools import get_query_execution_plan


class TestTools(unittest.TestCase):
    def setUp(self):
        init_db()
        self.assertTrue(os.path.exists("query_optimizer.db"))

    def test_get_query_execution_plan(self):
        query = "SELECT * FROM sales_data WHERE order_date > '2025-01-01'"
        result = get_query_execution_plan(query)
        result_dict = json.loads(result)
        self.assertEqual(result_dict["status"], "success")
        self.assertIn("query_id", result_dict)
        self.assertIn("execution_plan", result_dict)
        self.assertIn("Full table scan detected", result_dict["bottlenecks"])


if __name__ == "__main__":
    unittest.main()

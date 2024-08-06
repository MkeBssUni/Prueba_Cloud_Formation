import unittest
from unittest.mock import patch
import json
import pymysql
from get_low_stock_products import app

class TestLowStockProducts(unittest.TestCase):
    def test_low_stock_products(self):
        result = app.lambda_handler(None, None)
        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "PRODUCTS_FETCHED")


    @patch("get_low_stock_products.app.connect_to_database")
    def test_end_of_day_balance_error_500(self, mock_connect):
        mock_connect.side_effect = Exception('Error')
        result = app.lambda_handler(None, None)
        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INTERNAL_SERVER_ERROR")

    @patch("get_low_stock_products.app.pymysql.connect")
    def test_end_of_day_balance_error_connecting(self, mock_connect):
        mock_connect.side_effect = pymysql.MySQLError("Simulated connection error")
        with self.assertRaises(Exception) as context:
            app.connect_to_database()
        self.assertIn("ERROR CONNECTING TO DATABASE", str(context.exception))
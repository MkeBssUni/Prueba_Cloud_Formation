import unittest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal
import pymysql
from view_sales_history_per_day import app


class TestLambdaHandler(unittest.TestCase):

    @patch('view_sales_history_per_day.app.pymysql.connect')
    def test_lambda_handler_success(self, mock_connect):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "sale_id": 1,
                "createdAt": datetime(2023, 6, 1, 10, 30, 0),
                "status": 1,
                "total": Decimal('100.00'),
                "product_id": 101,
                "name": "Product A",
                "price": Decimal('50.00')
            },
            {
                "sale_id": 1,
                "createdAt": datetime(2023, 6, 1, 10, 30, 0),
                "status": 1,
                "total": Decimal('100.00'),
                "product_id": 102,
                "name": "Product B",
                "price": Decimal('50.00')
            }
        ]
        mock_connect.return_value.cursor.return_value = mock_cursor

        event = {
            "body": json.dumps({
                "startDate": "2023-06-01",
                "endDate": "2023-06-01"
            })
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["sale_id"], 1)
        self.assertEqual(body[0]["createdAt"], "2023-06-01 10:30:00")
        self.assertEqual(body[0]["status"], 1)
        self.assertEqual(body[0]["total"], 100.0)
        self.assertEqual(len(body[0]["products"]), 2)
        self.assertEqual(body[0]["products"][0]["product_id"], 101)
        self.assertEqual(body[0]["products"][0]["name"], "Product A")
        self.assertEqual(body[0]["products"][0]["price"], 50.0)

    @patch('view_sales_history_per_day.app.pymysql.connect')
    def test_lambda_handler_missing_fields(self, mock_connect):
        event = {
            "body": json.dumps({
                "endDate": "2023-06-01"
            })
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "MISSING_FIELDS")

    @patch('view_sales_history_per_day.app.pymysql.connect')
    def test_lambda_handler_invalid_date_format(self, mock_connect):
        event = {
            "body": json.dumps({
                "startDate": "2023/06/01",
                "endDate": "2023-06-01"
            })
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INVALID_DATE_FORMAT_OR_FUTURE_DATE")

    @patch('view_sales_history_per_day.app.pymysql.connect')
    def test_lambda_handler_end_date_before_start_date(self, mock_connect):
        event = {
            "body": json.dumps({
                "startDate": "2023-06-02",
                "endDate": "2023-06-01"
            })
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "END_DATE_BEFORE_START_DATE")

    @patch('view_sales_history_per_day.app.pymysql.connect')
    def test_lambda_handler_database_error(self, mock_connect):
        mock_connect.side_effect = pymysql.MySQLError("Database connection error")

        event = {
            "body": json.dumps({
                "startDate": "2023-06-01",
                "endDate": "2023-06-01"
            })
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INTERNAL_SERVER_ERROR")

    @patch('view_sales_history_per_day.app.pymysql.connect')
    def test_lambda_handler_unhandled_exception(self, mock_connect):
        mock_connect.side_effect = Exception("Unexpected error")

        event = {
            "body": json.dumps({
                "startDate": "2023-06-01",
                "endDate": "2023-06-01"
            })
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INTERNAL_SERVER_ERROR")


if __name__ == '__main__':
    unittest.main()

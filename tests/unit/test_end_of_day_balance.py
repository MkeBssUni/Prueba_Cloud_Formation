import unittest
from unittest.mock import patch
import json
import pymysql
from end_of_day_balance import app

mock_date = {
    "body": json.dumps({
        "date": "2024-07-19"
    })
}

mock_no_date = {
    "body": json.dumps({
    })
}

mock_future_date = {
    "body": json.dumps({
        "date": "2024-09-20"
    })
}

mock_wrong_date = {
    "body": json.dumps({
        "date": "ajsdbaksjdbaskdj"
    })
}

class TestEndOfDayBalance(unittest.TestCase):
    def test_end_of_day_balance(self):
        result = app.lambda_handler(mock_date, None)
        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "END_OF_DAY_BALANCE_FETCHED")

    def test_end_of_day_balance_no_date(self):
        result = app.lambda_handler(mock_no_date, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "MISSING_FIELDS")

    def test_end_of_day_balance_future_date(self):
        result = app.lambda_handler(mock_future_date, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INVALID_DATE_FORMAT_OR_FUTURE_DATE")

    @patch("end_of_day_balance.app.connect_to_database")
    def test_end_of_day_balance_internal_error(self, mock_connect_to_database):
        mock_connect_to_database.side_effect = Exception('Error')
        result = app.lambda_handler(mock_date, None)
        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INTERNAL_SERVER_ERROR")

    def test_end_of_day_balance_error_validate_date(self):
        result = app.lambda_handler(mock_wrong_date, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INVALID_DATE_FORMAT_OR_FUTURE_DATE")

    @patch("end_of_day_balance.app.pymysql.connect")
    def test_end_of_day_balance_error_connecting(self, mock_connect):
        mock_connect.side_effect = pymysql.MySQLError("Simulated connection error")
        with self.assertRaises(Exception) as context:
            app.connect_to_database()
        self.assertIn("ERROR CONNECTING TO DATABASE", str(context.exception))
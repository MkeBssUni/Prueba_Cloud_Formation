import unittest
import json
from unittest.mock import patch, MagicMock
from cancel_sales import app  # Asumiendo que el módulo se llama cancel_sales

class TestCancelSales(unittest.TestCase):

    @patch("cancel_sales.app.pymysql.connect")
    def test_lambda_handler_successful_cancellation(self, mock_connect):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connect.return_value.cursor.return_value = mock_cursor

        event = {
            "pathParameters": {
                "id": "1"
            }
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "SUCCESSFUL_CANCELLATION")

    @patch("cancel_sales.app.pymysql.connect")
    def test_lambda_handler_missing_id(self, mock_connect):
        event = {}

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "MISSING_FIELDS")

    @patch("cancel_sales.app.pymysql.connect")
    def test_lambda_handler_invalid_id_format(self, mock_connect):
        event = {
            "pathParameters": {
                "id": "INVALID_ID"
            }
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INVALID_ID")

    @patch("cancel_sales.app.pymysql.connect")
    def test_lambda_handler_invalid_id(self, mock_connect):
        event = {
            "pathParameters": {
                "id": -1
            }
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INVALID_ID")

    @patch("cancel_sales.app.pymysql.connect")
    def test_lambda_handler_invalid_characters(self, mock_connect):
        event = {
            "pathParameters": {
                "id": "1<>"
            }
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INVALID_CHARACTERS")

    @patch("cancel_sales.app.pymysql.connect")
    def test_lambda_handler_id_not_found(self, mock_connect):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (0,)
        mock_connect.return_value.cursor.return_value = mock_cursor

        event = {
            "pathParameters": {
                "id": "999"
            }
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 404)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "ID_NOT_FOUND")

    @patch("cancel_sales.app.pymysql.connect")
    def test_lambda_handler_database_error(self, mock_connect):
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Database connection error")
        mock_connect.return_value.cursor.return_value = mock_cursor

        event = {
            "pathParameters": {
                "id": "1111111"
            }
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INTERNAL_SERVER_ERROR")

if __name__ == "__main__":
    unittest.main()

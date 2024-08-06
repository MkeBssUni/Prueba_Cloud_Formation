import unittest
import json
from save_category import app
from unittest.mock import patch, MagicMock

class TestSaveCategory(unittest.TestCase):

    @patch("save_category.app.pymysql.connect")
    def test_lambda_handler_duplicate_name(self, mock_connect):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_cursor.execute.return_value = None
        mock_connect.return_value.cursor.return_value = mock_cursor

        event = {
            "body": json.dumps({
                "name": "duplicate"
            })
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "DUPLICATE_NAME")

    @patch("save_category.app.pymysql.connect")
    def test_lambda_handler_valid(self, mock_connect):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (0,)
        mock_cursor.execute.return_value = None
        mock_connect.return_value.cursor.return_value = mock_cursor

        event = {
            "body": json.dumps({
                "name": "validname"
            })
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "CATEGORY_SAVED")

    @patch("save_category.app.pymysql.connect")
    def test_lambda_handler_invalid_json(self, mock_connect):
        event = {
            "body": "invalid json"
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INVALID_JSON_FORMAT")

    @patch("save_category.app.pymysql.connect")
    def test_lambda_handler_missing_name(self, mock_connect):
        event = {
            "body": "{}"
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "MISSING_FIELDS")

    @patch("save_category.app.pymysql.connect")
    def test_lambda_handler_invalid_characters(self, mock_connect):
        event = {
            "body": json.dumps({
                "name": "invalid<>name"
            })
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INVALID_CHARACTERS")

    @patch("save_category.app.pymysql.connect")
    def test_lambda_handler_database_error(self, mock_connect):
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Database connection error")
        mock_connect.return_value.cursor.return_value = mock_cursor

        event = {
            "body": json.dumps({
                "name": "validname"
            })
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INTERNAL_SERVER_ERROR")

    @patch("save_category.app.pymysql.connect")
    def test_is_name_duplicate_true(self, mock_connect):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connect.return_value.cursor.return_value = mock_cursor

        result = app.is_name_duplicate("duplicate")
        self.assertTrue(result)

    @patch("save_category.app.pymysql.connect")
    def test_is_name_duplicate_false(self, mock_connect):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (0,)
        mock_connect.return_value.cursor.return_value = mock_cursor

        result = app.is_name_duplicate("newcategory")
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()

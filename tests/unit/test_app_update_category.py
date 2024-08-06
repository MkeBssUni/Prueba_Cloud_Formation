import unittest
import json
from update_category import app
from unittest.mock import patch, MagicMock

mock_name_duplicated = {
    "body": json.dumps({
        "id": 1,
        "name": "Pasteles"
    })
}

mock_category_not_exists = {
    "body": json.dumps({
        "id": 1506,
        "name": "Nombre inexistente de categoria"
    })
}

mock_success = {
    "body": json.dumps({
        "id": 1,
        "name": "Test update category success"
    })
}

mock_missing_fields = {
    "body": json.dumps({
        "id": None,
        "name": "Nombre"
    })
}

mock_empty_fields = {
    "body": json.dumps({
        "id": 1,
        "name": ""
    })
}

mock_invalid_fields = {
    "body": json.dumps({
        "id": 1,
        "name": " "
    })
}

mock_invalid_json = {
    "body": "{id: 1, name: Test update category}"
}

mock_missing_body = {}

mock_none_fields = {
    "body": json.dumps({
        "id": 1,
        "name": None
    })
}

class TestUpdateCategory(unittest.TestCase):

    @patch("update_category.app.category_exist")
    @patch("update_category.app.duplicated_name")
    def test_lambda_category_not_exists(self, mock_category_exist, mock_duplicated_name):
        mock_category_exist.return_value = False
        mock_duplicated_name.return_value = False

        result = app.lambda_handler(mock_category_not_exists, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 404)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "CATEGORY_NOT_FOUND")

    @patch("update_category.app.category_exist")
    @patch("update_category.app.duplicated_name")
    def test_lambda_duplicated_name(self, mock_category_exist, mock_duplicated_name):
        mock_category_exist.return_value = True
        mock_duplicated_name.return_value = True

        result = app.lambda_handler(mock_name_duplicated, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 400)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "DUPLICATED_NAME")

    @patch("update_category.app.duplicated_name")
    @patch("update_category.app.category_exist")
    @patch("update_category.app.update_category")
    def test_lambda_success(self, mock_update_category, mock_category_exist, mock_duplicated_name):
        mock_duplicated_name.return_value = False
        mock_category_exist.return_value = True

        result = app.lambda_handler(mock_success, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 200)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "CATEGORY_UPDATED")

    @patch("update_category.app.duplicated_name")
    @patch("update_category.app.category_exist")
    def test_lambda_empty_fields(self, mock_category_exist, mock_duplicated_name):
        mock_duplicated_name.return_value = False
        mock_category_exist.return_value = True

        result = app.lambda_handler(mock_empty_fields, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 400)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "EMPTY_FIELDS")

    @patch("update_category.app.duplicated_name")
    @patch("update_category.app.category_exist")
    def test_lambda_invalid_fields(self, mock_category_exist, mock_duplicated_name):
        mock_duplicated_name.return_value = False
        mock_category_exist.return_value = True

        result = app.lambda_handler(mock_invalid_fields, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 400)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "INVALID_FIELDS")

    def test_lambda_invalid_json(self):
        result = app.lambda_handler(mock_invalid_json, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 500)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "INTERNAL_SERVER_ERROR")

    def test_lambda_missing_body(self):
        result = app.lambda_handler(mock_missing_body, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 400)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "MISSING_KEY")

    @patch("update_category.app.pymysql.connect")
    def test_lambda_internal_server_error(self, mock_connect):
        mock_connect.side_effect = Exception("Connection error")

        result = app.lambda_handler(mock_success, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 500)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "INTERNAL_SERVER_ERROR")

    @patch("update_category.app.pymysql.connect")
    def test_update_category_db_error(self, mock_connect):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Database error")

        result = app.update_category(1, "New Name")
        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "DATABASE_ERROR")

    @patch("update_category.app.pymysql.connect")
    def test_category_exist_true(self, mock_connect):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1, 'Category Name')

        result = app.category_exist(1)
        self.assertTrue(result)

    @patch("update_category.app.pymysql.connect")
    def test_category_exist_false(self, mock_connect):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        result = app.category_exist(1)
        self.assertFalse(result)

    @patch("update_category.app.pymysql.connect")
    def test_category_exist_db_error(self, mock_connect):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Database error")

        result = app.category_exist(1)
        self.assertFalse(result)
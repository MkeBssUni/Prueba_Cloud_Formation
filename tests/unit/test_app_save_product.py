import unittest
import json
from save_product import app
from unittest.mock import patch, MagicMock

class TestSaveProduct(unittest.TestCase):

    @patch("save_product.app.pymysql.connect")
    def test_lambda_handler_duplicate_product(self, mock_connect):
        #Prueba para manejar nombres de productos duplicados.

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_cursor.execute.return_value = None
        mock_connect.return_value.cursor.return_value = mock_cursor

        event = {
            "body": json.dumps({
                "name": "duplicate",
                "stock": 10,
                "price": 100.0,
                "category_id": 1,
                "image": "data:image/png;base64,validimage"
            })
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "PRODUCT_EXISTS")

    def test_lambda_handler_invalid_json(self):

        event = {
            "body": "invalid json"
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INVALID_JSON_FORMAT")

    def test_lambda_handler_missing_fields(self):
        #Prueba para manejar campos faltantes.
        event = {
            "body": "{}"
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "MISSING_FIELDS")

    def test_lambda_handler_invalid_characters(self):
        #Prueba para manejar caracteres inválidos en el nombre del producto.
        event = {
            "body": json.dumps({
                "name": "invalid<>name",
                "stock": 10,
                "price": 100.0,
                "category_id": 1,
                "image": "data:image/png;base64,validimage"
            })
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INVALID_NAME")

    @patch("save_product.app.pymysql.connect")
    def test_lambda_handler_database_error(self, mock_connect):

        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Database connection error")
        mock_connect.return_value.cursor.return_value = mock_cursor

        event = {
            "body": json.dumps({
                "name": "validname",
                "stock": 10,
                "price": 100.0,
                "category_id": 1,
                "image": "data:image/png;base64,validimage"
            })
        }

        result = app.lambda_handler(event, None)
        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INTERNAL_SERVER_ERROR")

    @patch("save_product.app.pymysql.connect")
    def test_is_name_duplicate_true(self, mock_connect):
        #Prueba para verificar si el nombre del producto ya existe.
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_connect.return_value.cursor.return_value = mock_cursor

        result = app.is_name_duplicate("duplicate")
        self.assertTrue(result)

    @patch("save_product.app.pymysql.connect")
    def test_is_name_duplicate_false(self, mock_connect):
    #Prueba para verificar si el nombre del producto no existe.
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (0,)
        mock_connect.return_value.cursor.return_value = mock_cursor

        result = app.is_name_duplicate("newproduct")
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()

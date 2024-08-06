import unittest
import json
from get_category import app
from unittest.mock import patch, MagicMock

mock_success_all = {
    "pathParameters": {
        "status": 0
    }
}

mock_success_active = {
    "pathParameters": {
        "status": 1
    }
}

mock_invalid_status = {
    "pathParameters": {
        "status": "invalid"
    }
}

mock_internal_error = {
    "pathParameters": {
        "status": 1
    }
}

class TestGetCategory(unittest.TestCase):
    @patch("get_category.app.get_all_categories")
    #Prueba para verificar la recuperación exitosa de todas las categorías.
    def test_get_all_categories_success(self, mock_get_all_categories):
        mock_get_all_categories.return_value = [
            {"id": 1, "name": "Snacks2", "status": 1},
            {"id": 2, "name": "Snacks", "status": 0}
        ]

        result = app.lambda_handler(mock_success_all, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 200)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "CATEGORIES_FETCHED")

    @patch("get_category.app.get_all_categories")
    #Prueba para verificar la recuperación exitosa de las categorías activas.
    def test_get_active_categories_success(self, mock_get_all_categories):
        mock_get_all_categories.return_value = [
            {"id": 1, "name": "Snacks2", "status": 1},
            {"id": 2, "name": "Desserts", "status": 1}
        ]

        result = app.lambda_handler(mock_success_active, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 200)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "CATEGORIES_FETCHED")

    # Prueba para verificar el manejo de un estado inválido.
    def test_get_all_categories_invalid_status(self):
        result = app.lambda_handler(mock_invalid_status, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 400)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "INVALID_STATUS")

    @patch("get_category.app.get_all_categories")
    #Prueba para verificar el manejo de un error interno del servidor.
    def test_get_all_categories_internal_error(self, mock_get_all_categories):
        mock_get_all_categories.side_effect = Exception('Error')
        result = app.lambda_handler(mock_internal_error, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 500)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "INTERNAL_SERVER_ERROR")

    # Prueba para verificar que se lanza una excepción cuando se intenta convertir un tipo no soportado a float.
    def test_decimal_to_float_invalid_type(self):
        with self.assertRaises(TypeError):
            app.decimal_to_float("string")

if __name__ == '__main__':
    unittest.main()

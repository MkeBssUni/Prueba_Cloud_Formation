import unittest
import json
from get_products import app
from unittest.mock import patch

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
        "status": 12
    }
}

mock_internal_error = {
    "pathParameters": {
        "status": 1
    }
}

class TestUpdateCategory(unittest.TestCase):

    @patch("get_products.app.get_secret")
    def setUp(self, mock_get_secret):
        mock_get_secret.return_value = {
            "host": "database-cafe-balu.cziym6ii4nn7.us-east-2.rds.amazonaws.com",
            "username": "baluroot",
            "password": "baluroot",
            "dbname": "cafe_balu"
        }

    def test_success(self):
        result = app.lambda_handler(mock_success_all, None)
        print(result)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 200)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "PRODUCTS_FETCHED")

    @patch("get_products.app.get_all_products")
    def test_get_all_products_success(self, mock_get_all_products):
        mock_get_all_products.return_value = [
            {
                "id": 1,
                "name": "Test product",
                "price": 10.0,
                "status": 1
            },{
                "id": 2,
                "name": "Test product 2",
                "price": 20.0,
                "status": 0
            }
        ]

        result = app.lambda_handler(mock_success_all, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 200)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "PRODUCTS_FETCHED")

    @patch("get_products.app.get_all_products")
    def test_get_active_products_success(self, mock_get_all_products):
        mock_get_all_products.return_value = [
            {
                "id": 1,
                "name": "Test product active",
                "price": 10.0,
                "status": 1
            },{
                "id": 2,
                "name": "Test product active 2",
                "price": 20.0,
                "status": 1
            }
        ]

        result = app.lambda_handler(mock_success_active, None)
        print(result)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 200)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "PRODUCTS_FETCHED")

    def test_get_all_products_invalid_status(self):
        result = app.lambda_handler(mock_invalid_status, None)
        print(result)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 400)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "INVALID_STATUS")

    @patch("get_products.app.get_all_products")
    def test_get_all_products_internal_error(self, mock_get_all_products):
        mock_get_all_products.side_effect = Exception('Error')
        result = app.lambda_handler(mock_internal_error, None)
        print(result)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 500)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "INTERNAL_SERVER_ERROR")

    def test_get_all_products_decimal_to_float_ok(self):
        result = app.lambda_handler(mock_success_all, None)
        print(result)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 200)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "PRODUCTS_FETCHED")

    def test_decimal_to_float_invalid_type(self):
        with self.assertRaises(TypeError):
            app.decimal_to_float("string")

if __name__ == "__main__":
    unittest.main()

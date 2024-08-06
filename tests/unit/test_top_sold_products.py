import unittest
import json
from unittest.mock import patch
from top_sold_products import app

mock_no_category = {
    "body": json.dumps({

    })
}

mock_category = {
    "body": json.dumps({
        "category" : 1
    })
}

mock_category_not_found = {
    "body": json.dumps({
        "category" : 999
    })
}

class TestTopSoldProducts(unittest.TestCase):
    def test_top_sold_products_no_category(self):
        result = app.lambda_handler(mock_no_category, None)
        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "PRODUCTS_FETCHED")

    def test_top_sold_products_with_category(self):
        result = app.lambda_handler(mock_category, None)
        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "PRODUCTS_FETCHED")
    def test_top_sold_products_category_not_found(self):
        result = app.lambda_handler(mock_category_not_found, None)
        self.assertEqual(result["statusCode"], 404)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "CATEGORY_NOT_FOUND")

    @patch("top_sold_products.app.connect_to_database")
    def test_top_sold_products_error_connecting(self, mock_connect_to_database):
        mock_connect_to_database.side_effect = Exception('Error')

        result = app.lambda_handler(mock_category, None)
        self.assertEqual(result["statusCode"], 500)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "INTERNAL_SERVER_ERROR")
import unittest
import json
from change_status_category_or_product import app
from unittest.mock import patch


mock_change_status_category_success = {
    "body": json.dumps({
        "id": 1,
        "status": 1,
        "type": "CATEGORY"
    })
}

mock_change_status_product_success = {
    "body": json.dumps({
        "id": 1,
        "status": 1,
        "type": "PRODUCT"
    })
}

mock_change_status_missing_fields = {
    "body": json.dumps({
        "id": None,
        "status": None,
        "type": "PRODUCT"
    })
}

mock_change_status_invalid_status = {
    "body": json.dumps({
        "id": 1,
        "status": 123,
        "type": "PRODUCT"
    })
}

mock_change_status_invalid_type = {
    "body": json.dumps({
        "id": 1,
        "status": 1,
        "type": "INVALID_TYPE"
    })
}

mock_change_status_type_not_found = {
    "body": json.dumps({
        "id": 502,
        "status": 1,
        "type": "PRODUCT"
    })
}

mock_change_status_internal_server_error = {
    "body": json.dumps({
        "id": 1,
        "status": 1,
        "type": "PRODUCT"
    })
}

class TestChangeStatusCategoryOrProduct(unittest.TestCase):

    def test_lambda_change_status_category_success(self):
        result = app.lambda_handler(mock_change_status_category_success, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 200)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "STATUS_CHANGED")

    def test_lambda_change_status_product_success(self):
        result = app.lambda_handler(mock_change_status_product_success, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 200)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "STATUS_CHANGED")


    def test_lambda_change_status_missing_fields(self):
        result = app.lambda_handler(mock_change_status_missing_fields, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 400)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "MISSING_FIELDS")

    def test_lambda_change_status_invalid_status(self):
        result = app.lambda_handler(mock_change_status_invalid_status, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 400)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "INVALID_STATUS")

    def test_lambda_change_status_invalid_type(self):
        result = app.lambda_handler(mock_change_status_invalid_type, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 400)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "INVALID_TYPE_"+json.loads(mock_change_status_invalid_type["body"])["type"])

    @patch("change_status_category_or_product.app.type_exists")
    def test_lambda_change_status_type_not_found(self, mock_type_exists):
        mock_type_exists.return_value = False

        result = app.lambda_handler(mock_change_status_type_not_found, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 404)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], json.loads(mock_change_status_type_not_found["body"])["type"]+"_NOT_FOUND")

    def test_decimal_to_float_invalid_type(self):
        with self.assertRaises(TypeError):
            app.decimal_to_float("string")

    @patch("change_status_category_or_product.app.change_status")
    def test_lambda_change_status_internal_server_error(self, mock_change_status):
        mock_change_status.side_effect = Exception("Internal Server Error 5")
        result = app.lambda_handler(mock_change_status_internal_server_error, None)
        print(result)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 500)
        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "INTERNAL_SERVER_ERROR_")
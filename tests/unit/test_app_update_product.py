import unittest
import json
from unittest.mock import patch
from update_product import app

mock_event_admin = {
    "requestContext": {
        "authorizer": {
            "claims": {
                "cognito:groups": ["admin"]
            }
        }
    },
    "body": json.dumps({
        "id": 1,
        "name": "New Product",
        "stock": 10,
        "price": 100,
        "status": 1,
        "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA",
        "category_id": 1
    })
}

mock_event_missing_fields = {
    "requestContext": {
        "authorizer": {
            "claims": {
                "cognito:groups": ["admin"]
            }
        }
    },
    "body": json.dumps({
        "name": "New Product",
        "stock": 10,
        "price": 100,
        "status": 1,
        "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA",
        "category_id": 1
    })
}

mock_event_invalid_image = {
    "requestContext": {
        "authorizer": {
            "claims": {
                "cognito:groups": ["admin"]
            }
        }
    },
    "body": json.dumps({
        "id": 1,
        "name": "New Product",
        "stock": 10,
        "price": 100,
        "status": 1,
        "image": "invalid_image_data",
        "category_id": 1
    })
}

mock_event_forbidden = {
    "requestContext": {
        "authorizer": {
            "claims": {
                "cognito:groups": ["user"]
            }
        }
    },
    "body": json.dumps({
        "id": 1,
        "name": "New Product",
        "stock": 10,
        "price": 100,
        "status": 1,
        "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA",
        "category_id": 1
    })
}

mock_event_category_not_found = {
    "requestContext": {
        "authorizer": {
            "claims": {
                "cognito:groups": ["admin"]
            }
        }
    },
    "body": json.dumps({
        "id": 1,
        "name": "New Product",
        "stock": 10,
        "price": 100,
        "status": 1,
        "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA",
        "category_id": 999
    })
}

class TestUpdateProduct(unittest.TestCase):
    # Prueba de actualización exitosa del producto
    @patch("update_product.app.update_product")
    @patch("update_product.app.category_exists")
    @patch("update_product.app.upload_image_to_s3")
    def test_update_product_success(self, mock_upload_image_to_s3, mock_category_exists, mock_update_product):
        mock_category_exists.return_value = True
        mock_upload_image_to_s3.return_value = "https://example.com/image.jpg"
        mock_event_admin["body"] = json.dumps({
            "id": 1,
            "name": "New Product",
            "stock": 10,
            "price": 100,
            "status": 1,
            "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA",
            "category_id": 1,
            "description": "A new product"
        })

        result = app.lambda_handler(mock_event_admin, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 200, f"Se esperaba el código de estado 200 pero se obtuvo {status_code}. Respuesta: {result}")

        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "PRODUCT_UPDATED")

    # Prueba de actualización del producto con campos faltantes
    def test_update_product_missing_fields(self):
        result = app.lambda_handler(mock_event_missing_fields, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 400, f"Se esperaba el código de estado 400 pero se obtuvo {status_code}. Respuesta: {result}")

        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "MISSING_FIELDS")

    # Prueba de actualización del producto con datos de imagen inválidos
    def test_update_product_invalid_image(self):
        result = app.lambda_handler(mock_event_invalid_image, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 400, f"Se esperaba el código de estado 400 pero se obtuvo {status_code}. Respuesta: {result}")

        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "INVALID_IMAGE")

    # Prueba de actualización del producto con acceso prohibido
    def test_update_product_forbidden(self):
        result = app.lambda_handler(mock_event_forbidden, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 403, f"Se esperaba el código de estado 403 pero se obtuvo {status_code}. Respuesta: {result}")

        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "FORBIDDEN")

    # Prueba de actualización del producto cuando la categoría no se encuentra
    @patch("update_product.app.update_product")
    @patch("update_product.app.category_exists")
    def test_update_product_category_not_found(self, mock_category_exists, mock_update_product):
        mock_category_exists.return_value = False
        result = app.lambda_handler(mock_event_category_not_found, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 400, f"Se esperaba el código de estado 400 pero se obtuvo {status_code}. Respuesta: {result}")

        body = json.loads(result["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "CATEGORY_NOT_FOUND")

    # Prueba de la función de validación de imagen
    def test_is_invalid_image(self):
        valid_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA"
        invalid_image = "invalid_image_data"
        self.assertFalse(app.is_invalid_image(valid_image))
        self.assertTrue(app.is_invalid_image(invalid_image))

if __name__ == '__main__':
    unittest.main()

import json
import unittest
from newPassword import app
from unittest.mock import patch
from botocore.exceptions import ClientError

mock_success = {
    "body": json.dumps({
        "username": "marianne",
        "temporary_password": "Aa123456.",
        "new_password": "Marianne1568481."
    })
}


class TestResetPassword(unittest.TestCase):
    @patch("newPassword.app.boto3.client")
    def test_new_password_success(self, mock_boto_client):
        mock_client_instance = mock_boto_client.return_value
        mock_client_instance.admin_initiate_auth.return_value = {
            "ChallengeName": "NEW_PASSWORD_REQUIRED",
            "Session": "session"
        }
        result = app.lambda_handler(mock_success, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 200)

    @patch("newPassword.app.boto3.client")
    def test_unexpected_challege(self, mock_boto_client):
        mock_client_instance = mock_boto_client.return_value
        mock_client_instance.admin_initiate_auth.return_value = {
            "ChallengeName": "UNEXPECTED_CHALLENGE",
            "Session": "session"
        }
        result = app.lambda_handler(mock_success, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 400)

    @patch("newPassword.app.boto3.client")
    def test_client_error(self, mock_boto_client):
        mock_client_instance = mock_boto_client.return_value
        error_response ={
            'Error':{
                'Code': 'InvalidParameterException',
                'Message': 'An error ocurred'
            }
        }

        mock_client_instance.admin_initiate_auth.side_effect = ClientError(error_response, 'admin_initiate_auth')

        result = app.lambda_handler(mock_success, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 400)

    @patch("newPassword.app.boto3.client")
    def test_error_500(self, mock_boto_client):
        mock_client_instance = mock_boto_client.return_value
        error_response ={
            'Error':{
                'Code': 'InvalidParameterException',
                'Message': 'An error ocurred'
            }
        }

        mock_client_instance.admin_initiate_auth.side_effect = Exception(error_response, 'admin_initiate_auth')

        result = app.lambda_handler(mock_success, None)
        status_code = result["statusCode"]
        self.assertEqual(status_code, 500)

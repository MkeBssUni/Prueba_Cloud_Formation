import json
import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, __):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "PATCH, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token"
    }
    client = boto3.client('cognito-idp', region_name='us-east-2')
    user_pool_id = "us-east-2_WxG0qudnH"
    client_id = "13a00gp0ti81p4m6prtdl34jpm"
    try:
        body_parameters = json.loads(event["body"])
        username = body_parameters.get('username')
        temporary_password = body_parameters.get('temporary_password')
        new_password = body_parameters.get('new_password')

         # Autentica al usuario con la contraseña temporal
        response = client.admin_initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=client_id,
            AuthFlow='ADMIN_USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': temporary_password
            }
        )

        if response['ChallengeName'] == 'NEW_PASSWORD_REQUIRED':
            client.respond_to_auth_challenge(
                ClientId=client_id,
                ChallengeName='NEW_PASSWORD_REQUIRED',
                Session=response['Session'],
                ChallengeResponses={
                    'USERNAME': username,
                    'NEW_PASSWORD': new_password,
                    'email_verified': 'true'
                }
            )
            return {
                'statusCode': 200,
                "headers": headers,
                'body': json.dumps({"message": "Password changed successfully."})
            }
        else:
            return {
                'statusCode': 400,
                "headers": headers,
                'body': json.dumps({"error_message": "Unexpected challenge."})
            }

    except ClientError as e:
        return {
            'statusCode': 400,
            "headers": headers,
            'body': json.dumps({"error_message": e.response['Error']['Message']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            "headers": headers,
            'body': json.dumps({"error_message": str(e)})
        }
import json
import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, __):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token"
    }

    client = boto3.client('cognito-idp', region_name='us-east-2')
    client_id = "13a00gp0ti81p4m6prtdl34jpm"
    try:
        body_parameters = json.loads(event["body"])
        username = body_parameters.get('username')
        password = body_parameters.get('password')

        response = client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )

        id_token = response['AuthenticationResult']['IdToken']
        access_token = response['AuthenticationResult']['AccessToken']
        refresh_token = response['AuthenticationResult']['RefreshToken']

        print(id_token)

        # Obtén los grupos del usuario
        user_groups = client.admin_list_groups_for_user(
            Username=username,
            UserPoolId='us-east-2_WxG0qudnH'  # Reemplaza con tu User Pool ID
        )

        # Determina el rol basado en el grupo
        role = None
        if user_groups['Groups']:
            role = user_groups['Groups'][0]['GroupName']  # Asumiendo un usuario pertenece a un solo grupo

        return {
            'statusCode': 200,
            "headers": headers,
            'body': json.dumps({
                'id_token': id_token,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'role': role
            })
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
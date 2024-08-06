import json
import pymysql
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

def get_secret():
    secret_name = "prod/Balu/RDS"
    region_name = "us-east-2"

    # Crear un cliente de Secrets Manager
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # Para obtener una lista de excepciones lanzadas, vea
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

# Obtener las credenciales desde Secrets Manager
secrets = get_secret()
rds_host = secrets["host"]
rds_user = secrets["username"]
rds_password = secrets["password"]
rds_db = secrets["dbname"]


def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, __):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token"
    }

    try:
        # Validar presencia del campo 'pathParameters' en el evento
        status = 0
        if 'pathParameters' in event:
            status = event['pathParameters'].get('status')
        else:
            status = None

        # Validar que el 'status' sea un entero si está presente
        if status is not None:
            try:
                status = int(status)
            except ValueError:
                return {
                    "statusCode": 400,
                    "headers": headers,
                    "body": json.dumps({
                        "message": "INVALID_STATUS"
                    }),
                }

        result = get_all_categories(status)

        body = {
            "message": "CATEGORIES_FETCHED",
            "categories": result
        }

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps(body, default=decimal_to_float)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                "message": "INTERNAL_SERVER_ERROR",
                "error": str(e)
            }),
        }

def get_all_categories(status):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()

        if status == 0:
            cursor.execute("SELECT * FROM categories")
        else:
            cursor.execute("SELECT * FROM categories WHERE status = %s", (status,))

        result = cursor.fetchall()

        result = [dict(zip([column[0] for column in cursor.description], row)) for row in result]

        return result
    except Exception as e:
        raise
    finally:
        connection.close()

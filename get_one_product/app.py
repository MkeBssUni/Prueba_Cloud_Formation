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

def lambda_handler(event, __):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token"
    }
    try:
        if 'pathParameters' not in event or 'id' not in event['pathParameters']:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "MISSING_PRODUCT_ID"
                }),
            }

        product_id = event['pathParameters']['id']

        try:
            product_id = int(product_id)
        except ValueError:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_PRODUCT_ID"
                }),
            }

        if product_id <= 0:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_PRODUCT_ID"
                }),
            }

        try:
            product = get_product(product_id)
        except Exception as e:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({
                    "message": "PRODUCT_NOT_FOUND",
                    "error": str(e)
                }),
            }

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "message": "PRODUCT_FETCHED",
                "product": product
            }, default=decimal_to_float)
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

def connect_to_database():
    try:
        connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
        return connection
    except pymysql.MySQLError as e:
        raise Exception("ERROR CONNECTING TO DATABASE: " + str(e))

def get_product(product_id):
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("SELECT p.*, c.name as category_name FROM products p INNER JOIN categories c ON p.category_id = c.id WHERE p.id = %s", (product_id,))
    result = cursor.fetchone()

    connection.close()

    if result is None:
        raise Exception("PRODUCT_NOT_FOUND")
    else:
        columns = [column[0] for column in cursor.description]
        product = dict(zip(columns, result))
        return product

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError
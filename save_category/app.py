import json
import pymysql
import logging
import re
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

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, __):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token"
    }
    try:
        claims = event['requestContext']['authorizer']['claims']
        role = claims['cognito:groups']

        if 'admin' not in role:
            return {
                "statusCode": 403,
                "headers": headers,
                "body": json.dumps({
                    "message": "FORBIDDEN"
                }),
            }

        body = json.loads(event.get('body', '{}'))
        name = body.get('name')

        if not name:
            logger.warning("Missing fields: name")
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "MISSING_FIELDS"
                }),
            }

        # Verificar caracteres no permitidos
        if re.search(r'[<>/``\\{}]', name):
            logger.warning("Invalid characters in name")
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_CHARACTERS"
                }),
            }

        # Verificar nombre duplicado
        if is_name_duplicate(name):
            logger.warning("Duplicate category name: %s", name)
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "DUPLICATE_NAME"
                }),
            }

        save_category(name, headers)
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "message": "CATEGORY_SAVED",
            }),
        }
    except json.JSONDecodeError:
        logger.error("Invalid JSON format")
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({
                "message": "INVALID_JSON_FORMAT"
            }),
        }
    except KeyError as e:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({
                "message": "MISSING_KEY",
                "error": str(e)
            }),
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

def is_name_duplicate(name):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM categories WHERE name = %s", (name,))
        result = cursor.fetchone()
        return result[0] > 0
    except Exception as e:
        logger.error("Database query error: %s", str(e))
        return False
    finally:
        connection.close()

def save_category(name, headers):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO categories (name, status) VALUES (%s, true)", (name,))
        connection.commit()
        logger.info("Database create successfully for name=%s", name)
    except Exception as e:
        logger.error("Database update error: %s", str(e))
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                "message": "DATABASE_ERROR"
            }),
        }
    finally:
        connection.close()

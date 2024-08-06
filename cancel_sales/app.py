import json
import pymysql
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


def lambda_handler(event, __):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "PATCH, OPTIONS",
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


        # Validar que 'id' esté presente en pathParameters
        id_str = event['pathParameters'].get('id')
        if id_str is None:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "MISSING_FIELDS"
                }),
            }

            # Verificar que el ID no contiene caracteres especiales
        if re.search(r'[<>?#``]', id_str):
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_CHARACTERS"
                }),
            }

        # Validar que 'id' sea un número entero
        try:
            id = int(id_str)
        except ValueError:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_ID"
                }),
            }

        # Validar que 'id' sea un entero positivo
        if id <= 0:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_ID"
                }),
            }

        # Verificar que el ID existe en la base de datos
        if not id_exists_in_db(id):
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({
                    "message": "ID_NOT_FOUND"
                }),
            }

        cancel_sale(id)
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "message": "SUCCESSFUL_CANCELLATION",
            }),
        }
    except pymysql.MySQLError as e:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                "message": "DATABASE_ERROR",
                "error": str(e)
            }),
        }
    except KeyError as e:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({
                "message": "MISSING_FIELDS",
                "error": str(e)
            }),
        }
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({
                "message": "INVALID_JSON_FORMAT"
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


def id_exists_in_db(id):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM sales WHERE id = %s", (id,))
        result = cursor.fetchone()
        return result[0] > 0
    except Exception as e:
        return False
    finally:
        connection.close()


def cancel_sale(id):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()
        cursor.execute("UPDATE sales SET status = 0 WHERE id=%s", (id,))
        connection.commit()
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token"
            },
            "body": json.dumps({
                "message": "DATABASE_ERROR"
            }),
        }
    finally:
        connection.close()

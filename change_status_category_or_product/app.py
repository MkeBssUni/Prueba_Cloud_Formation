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


        if 'body' not in event:
            raise KeyError('body')
        body = json.loads(event['body'])
        status = body.get('status')
        id = body.get('id')
        type = body.get('type')

        if status is None or id is None or type is None:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "MISSING_FIELDS"
                }),
            }

        if status != 0 and status != 1:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_STATUS"
                }),
            }

        if type != 'PRODUCT' and type != 'CATEGORY':
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_TYPE_"+type
                }),
            }

        if type_exists(type, id) == False:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({
                    "message": type + "_NOT_FOUND"
                }),
            }

        change_status(id, type, status)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "STATUS_CHANGED"
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "INTERNAL_SERVER_ERROR_",
            }),
        }

def change_status(id, type, status):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()
        query = ""

        if(type == 'PRODUCT'):
            query = "update products set status = %s where id = %s"

        if(type == 'CATEGORY'):
            query = "update categories set status = %s where id = %s"

        cursor.execute(query, (status,id))
        connection.commit()
    except Exception as e:
        raise e
    finally:
        connection.close()
def type_exists(type, id):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()
        query = ""

        if(type == 'PRODUCT'):
            query = "select count(*) from products where id = %s"

        if(type == 'CATEGORY'):
            query = "select count(*) from categories where id = %s"

        cursor.execute(query, (id))
        result = cursor.fetchone()
        return result[0] > 0

    except Exception as e:
        return False
    finally:
        connection.close()
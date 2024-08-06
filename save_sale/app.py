import json
import pymysql
import logging
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

        if 'admin' not in role and 'sales' not in role:
            return {
                "statusCode": 403,
                "headers": headers,
                "body": json.dumps({
                    "message": "FORBIDDEN"
                }),
            }

        if 'body' not in event:
            logger.error("Request body not found in the event")
            raise KeyError('body')

        body = json.loads(event['body'])
        products = body.get('products')
        total = body.get('total')

        if not products or total is None:
            logger.error("Products or total not found in the body")
            raise KeyError('products or total')

        products_info = get_products_info(products)

        response = save_sale(products_info, total, headers)

        return response

    except KeyError as e:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({
                "message": "BAD_REQUEST",
                "error": str(e)
            })
        }
    except ValueError as e:
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({
                "message": str(e)
            })
        }
    except Exception as e:
        logger.error("Unexpected error: %s", str(e), exc_info=True)
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                "message": "INTERNAL_SERVER_ERROR",
                "error": str(e)
            })
        }

def get_products_info(products):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()
        products_info = []

        for product in products:
            if product['quantity'] <= 0:
                raise ValueError(f"Product with id {product['id']} has invalid quantity")

            cursor.execute("SELECT id, price, stock FROM products WHERE id = %s", (product['id'],))
            product_info = cursor.fetchone()

            if product_info is None:
                raise ValueError(f"Product with id {product['id']} not found")

            if product_info[2] < product['quantity']:
                raise ValueError(f"Product with id {product['id']} does not have enough stock")

            products_info.append({
                "id": product_info[0],
                "price": product_info[1],
                "quantity": product['quantity']
            })

        return products_info
    except Exception as e:
        logger.error("Database query error: %s", str(e), exc_info=True)
        raise
    finally:
        connection.close()

def save_sale(products_info, total, headers):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()
        cursor.execute("INSERT INTO sales (total, status) VALUES (%s, 1)", (total,))
        sale_id = cursor.lastrowid

        for product in products_info:
            cursor.execute("INSERT INTO sales_products (sale_id, product_id, quantity) VALUES (%s, %s, %s)",
                           (sale_id, product['id'], product['quantity']))
            cursor.execute("UPDATE products SET stock = stock - %s WHERE id = %s",
                           (product['quantity'], product['id']))

        connection.commit()

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "message": "SALE_SAVED",
                "sale_id": sale_id
            })
        }
    except Exception as e:
        logger.error("Database transaction error: %s", str(e), exc_info=True)
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                "message": "DATABASE_ERROR",
                "error": str(e)
            })
        }
    finally:
        connection.close()

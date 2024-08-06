import json
import pymysql
import re
import boto3
import uuid
import base64
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

bucket_name = "cafe-balu-images"
s3 = boto3.client('s3')

def upload_image_to_s3(base64_data):
    # Remover el prefijo de la cadena base64
    base64_data = base64_data.split(",")[1]
    binary_data = base64.b64decode(base64_data)
    file_name = f"images/{uuid.uuid4()}.jpg"
    s3.put_object(Bucket=bucket_name, Key=file_name, Body=binary_data, ContentType='image/jpeg')
    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
    return s3_url

def lambda_handler(event, __):
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "PUT, OPTIONS",
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

        try:
            body = json.loads(event['body'])
        except json.JSONDecodeError as e:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_JSON_FORMAT"
                }),
            }

        product_id = body.get('id')
        name = body.get('name')
        stock = body.get('stock')
        price = body.get('price')
        status = body.get('status')
        image = body.get('image')
        category_id = body.get('category_id')
        description = "Sin descripción"

        if 'description' in body:
            description = body.get('description')

        if len(description) > 255:
            return {
                "statusCode": 413,
                "headers": headers,
                "body": json.dumps({
                    "message": "DESCRIPTION_TOO_LONG"
                }),
            }

        if description is None:
            description = "Sin descripción"

        # Validar campos faltantes: 'product_id', 'name', 'stock', 'price', 'status', 'image', 'category_id'
        missing_fields = [field for field in ['id', 'name', 'stock', 'price', 'status', 'image', 'category_id'] if body.get(field) is None]

        if missing_fields:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "MISSING_FIELDS",
                    "missing_fields": missing_fields
                }),
            }

        # Validar 'name': debe ser una cadena no vacía y sin caracteres inválidos
        if not isinstance(name, str) or not name.strip() or not re.match(r'^[\w\s.-]+$', name):
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_NAME"
                }),
            }

        # Validar 'stock': debe ser un entero mayor o igual a cero
        if not isinstance(stock, int) or stock < 0:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_STOCK"
                }),
            }

        # Validar 'price': debe ser un número mayor a cero
        if not isinstance(price, (int, float)) or price <= 0:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_PRICE"
                }),
            }

        # Validar 'category_id': debe ser un entero positivo
        if not isinstance(category_id, int) or category_id <= 0:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_CATEGORY_ID"
                }),
            }
        if not category_exists(category_id):
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "CATEGORY_NOT_FOUND"
                }),
            }

        if product_exists_in_category(category_id, name, product_id):
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "PRODUCT_EXISTS"
                }),
            }

        if is_invalid_image(image):
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_IMAGE"
                }),
            }

        # Subir imagen a S3 y obtener la URL
        image_url = upload_image_to_s3(image)

        update_product(product_id, name, stock, price, status, image_url, category_id, description)
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "message": "PRODUCT_UPDATED",
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
    except pymysql.MySQLError as e:
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                "message": "DATABASE_ERROR",
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

def update_product(product_id, name, stock, price, status, image_url, category_id, description):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE products 
            SET name=%s, stock=%s, price=%s, status=%s, image=%s, category_id=%s, description=%s 
            WHERE id=%s
        """, (name, stock, price, status, image_url, category_id, description, product_id))
        connection.commit()
    except Exception as e:
        raise e
    finally:
        connection.close()

def category_exists(category_id):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM categories WHERE id = %s", (category_id,))
        connection.commit()
        result = cursor.fetchone()
        if result is None:
            return False
        return result[0] > 0
    except Exception as e:
        raise e
    finally:
        connection.close()

def product_exists_in_category(category_id, name, product_id):
    connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM products WHERE category_id = %s AND lower(name) = %s AND id != %s", (category_id, name.lower(), product_id))
        connection.commit()
        result = cursor.fetchone()
        if result is None:
            return False
        return result[0] > 0
    except Exception as e:
        raise e
    finally:
        connection.close()

def is_invalid_image(image):
    pattern = r"^data:image/(png|jpg|jpeg);base64,([a-zA-Z0-9+/=]+)$"
    return not re.match(pattern, image)

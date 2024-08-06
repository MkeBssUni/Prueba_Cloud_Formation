import json
import pymysql
from datetime import datetime
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
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Amz-Security-Token"
    }
    try:
        if 'date' in json.loads(event['body']):
            date = json.loads(event['body']).get('date')
        else:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "MISSING_FIELDS"
                }),
            }

        if not validate_date(date):
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({
                    "message": "INVALID_DATE_FORMAT_OR_FUTURE_DATE"
                }),
            }

        balance = get_end_of_day_balance(date)

        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "message": "END_OF_DAY_BALANCE_FETCHED",
                "balance": balance
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

def validate_date(date_string):
    try:
        date_obj = datetime.strptime(date_string, '%Y-%m-%d')
        if date_obj > datetime.now():
            return False
        return True
    except ValueError:
        return False

def connect_to_database():
    try:
        connection = pymysql.connect(host=rds_host, user=rds_user, password=rds_password, db=rds_db)
        return connection
    except pymysql.MySQLError as e:
        raise Exception("ERROR CONNECTING TO DATABASE: " + str(e))

def get_end_of_day_balance(date):
    connection = connect_to_database()
    cursor = connection.cursor()
    cursor.execute("""
        WITH daily_sales AS (
            SELECT
                sp.product_id,
                p.name AS product_name,
                SUM(sp.quantity) AS total_quantity,
                COUNT(DISTINCT s.id) AS transaction_count
            FROM
                sales_products sp
            JOIN
                products p ON sp.product_id = p.id
            JOIN
                sales s ON sp.sale_id = s.id
            WHERE
                DATE(s.createdAt) = %s
                AND s.status = 1
            GROUP BY
                sp.product_id, p.name
        ),
        total_transactions AS (
            SELECT
                COUNT(DISTINCT s.id) AS total_transactions,
                SUM(s.total) AS total_sales
            FROM
                sales s
            WHERE
                DATE(s.createdAt) = %s
                AND s.status = 1
        ),
        cancelled_transactions AS (
            SELECT
                COUNT(DISTINCT s.id) AS cancelled_transactions
            FROM
                sales s
            WHERE
                DATE(s.createdAt) = %s
                AND s.status = 0
        )
        SELECT
            COALESCE((SELECT product_name FROM daily_sales ORDER BY total_quantity DESC LIMIT 1), 'No data') AS most_sold_product,
            COALESCE((SELECT AVG(total_sales / total_transactions) FROM total_transactions), 0) AS average_sale,
            COALESCE((SELECT total_sales FROM total_transactions), 0) AS total_sales_today,
            COALESCE((SELECT total_transactions FROM total_transactions), 0) AS total_transactions_today,
            COALESCE((SELECT cancelled_transactions FROM cancelled_transactions), 0) AS total_cancelled_transactions;
    """, (date, date, date))
    result = cursor.fetchone()
    connection.close()
    balance = {
        "most_sold_product": result[0],
        "average_sale": result[1],
        "total_sales_today": result[2],
        "total_transactions_today": result[3],
        "total_cancelled_transactions": result[4]
    }
    return balance

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj
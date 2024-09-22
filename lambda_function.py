import json
import boto3
import hmac
import hashlib
import base64
import os
from botocore.exceptions import ClientError

cognito = boto3.client('cognito-idp')

def calculate_secret_hash(client_id, client_secret, username):
    message = username + client_id
    dig = hmac.new(
        str(client_secret).encode('utf-8'),
        msg=str(message).encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(dig).decode()

def lambda_handler(event, context):
    
    if isinstance(event['body'], str):
        body = json.loads(event['body'])
    else:
        body = event['body']
    
    username = body['username']
    password = body['password']
    email = body['email']

    client_id = os.environ['client_id']
    user_pool_id = os.environ['user_pool_id']
    client_secret = os.environ['client_secret']
    
    # Check if email is already confirmed
    try:
        response = cognito.list_users(
            UserPoolId=user_pool_id,
            AttributesToGet=['email_verified'],
            Filter=f'email = "{email}"'
        )
        
        for user in response['Users']:
            for attribute in user['Attributes']:
                if attribute['Name'] == 'email_verified' and attribute['Value'] == 'true':
                    return {
                        'statusCode': 400,
                        'body': json.dumps({'error': 'Email is already confirmed and in use.'})
                    }
    except ClientError as error:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': error.response['Error']['Message']})
        }

    secret_hash = calculate_secret_hash(client_id, client_secret, username)

    params = {
        'ClientId': client_id,
        'Username': username,
        'Password': password,
        'UserAttributes': [
            {
                'Name': 'email',
                'Value': email
            }
        ],
        'SecretHash': secret_hash
    }

    try:
        # Use Cognito to sign up the user
        sign_up_response = cognito.sign_up(**params)
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'User registration successful', 'userSub': sign_up_response['UserSub']})
        }
    except ClientError as error:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': error.response['Error']['Message']})
        }

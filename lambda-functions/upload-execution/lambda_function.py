import base64
import json
import boto3
import uuid
import os
from datetime import datetime, timedelta, timezone

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        username = event['requestContext']['authorizer']['claims']['email']
        
        reference_key = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc)
        expiration_time = current_time + timedelta(weeks=0.5)
        
        # Handle both PDF upload and text input
        if 'fileContent' in body:
            # PDF Upload
            file_name = body['fileName']
            language = body['language']
            start_page = body['startPage']
            end_page = body['endPage']
            file_content_base64 = body['fileContent']
            
            file_content = base64.b64decode(file_content_base64)
            s3_path = f"upload/{reference_key}/{file_name}"
            
            s3_client.put_object(
                Bucket=os.environ['S3_BUCKET'],
                Key=s3_path,
                Body=file_content
            )
            
            item = {
                'reference_key': reference_key,
                'FileName': file_name,
                'Language': language,
                'StartPage': str(start_page),
                'EndPage': str(end_page),
                'S3Path': f"s3://{os.environ['S3_BUCKET']}/{s3_path}",
                'UploadDateTime': current_time.isoformat(),
                'TaskStatus': 'Upload-Completed',
                'Username': username,
                'ExpiresAt': int(expiration_time.timestamp()),
                'InputType': 'PDF'
            }
            
        else:
            # Text Input
            text = body['text']
            language = body.get('language', 'english')
            voice_id = body.get('voice_id', 'Joanna')
            
            s3_path = f"upload/{reference_key}/input.txt"
            s3_client.put_object(
                Bucket=os.environ['S3_BUCKET'],
                Key=s3_path,
                Body=text.encode('utf-8'),
                ContentType='text/plain'
            )
            
            item = {
                'reference_key': reference_key,
                'text': text,
                'Language': language,
                'voice_id': voice_id,
                'S3Path': f"s3://{os.environ['S3_BUCKET']}/{s3_path}",
                'UploadDateTime': current_time.isoformat(),
                'TaskStatus': 'Upload-Completed',
                'Username': username,
                'ExpiresAt': int(expiration_time.timestamp()),
                'InputType': 'TEXT'
            }
        
        table.put_item(Item=item)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'POST,OPTIONS'
            },
            'body': json.dumps({
                'message': 'Request submitted successfully',
                'reference_key': reference_key
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
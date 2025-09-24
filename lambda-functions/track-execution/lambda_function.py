import json
import os
import boto3
from boto3.dynamodb.conditions import Attr

dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

def lambda_handler(event, context):
    try:
        username = event['requestContext']['authorizer']['claims']['email']
        
        if 'action' in event and event['action'] == 'generate_url':
            # Generate presigned URL
            reference_key = event['reference_key']
            
            response = table.get_item(Key={'reference_key': reference_key})
            if 'Item' not in response or response['Item']['Username'] != username:
                return {
                    'statusCode': 403,
                    'headers': {'Access-Control-Allow-Origin': '*'},
                    'body': json.dumps({'error': 'Access denied'})
                }
            
            audio_key = f'download/{reference_key}/Audio.mp3'
            presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': os.environ['S3_BUCKET'], 'Key': audio_key},
                ExpiresIn=3600
            )
            
            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'presigned_url': presigned_url})
            }
        
        else:
            # List user requests
            response = table.scan(
                FilterExpression=Attr('Username').eq(username)
            )
            
            requests = []
            for item in response['Items']:
                request_data = {
                    'reference_key': item['reference_key'],
                    'TaskStatus': item['TaskStatus'],
                    'UploadDateTime': item.get('UploadDateTime', ''),
                    'InputType': item.get('InputType', 'PDF')
                }
                
                if item.get('InputType') == 'PDF':
                    request_data['fileName'] = item.get('FileName', 'Unknown')
                    request_data['Language'] = item.get('Language', 'english')
                else:
                    request_data['text'] = item.get('text', '')[:100] + '...' if len(item.get('text', '')) > 100 else item.get('text', '')
                    request_data['Language'] = item.get('Language', 'english')
                
                requests.append(request_data)
            
            return {
                'statusCode': 200,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'requests': requests})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
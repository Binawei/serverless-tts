import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('UserProfiles')

def lambda_handler(event, context):
    try:
        user_id = event['requestContext']['authorizer']['claims']['sub']
        email = event['requestContext']['authorizer']['claims']['email']
        username = event['requestContext']['authorizer']['claims'].get('preferred_username', '')
        
        if event['httpMethod'] == 'POST':
            body = json.loads(event['body'])
            
            table.put_item(
                Item={
                    'user_id': user_id,
                    'email': email,
                    'username': username,
                    'phone_number': body.get('phone_number', ''),
                    'preferences': body.get('preferences', {}),
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                }
            )
            
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Profile created'})
            }
            
        elif event['httpMethod'] == 'GET':
            response = table.get_item(Key={'user_id': user_id})
            
            if 'Item' in response:
                return {
                    'statusCode': 200,
                    'body': json.dumps(response['Item'])
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'message': 'Profile not found'})
                }
                
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
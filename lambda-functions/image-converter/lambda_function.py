import base64
import json
import os
import boto3

s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')

def get_model_endpoint():
    region = os.environ['AWS_REGION']
    if region.startswith('eu-'):
        return 'eu.anthropic.claude-3-5-sonnet-20240620-v1:0'
    elif region.startswith('us-'):
        return 'us.anthropic.claude-3-5-sonnet-20240620-v1:0'
    elif region.startswith('ap-'):
        return 'apac.anthropic.claude-3-5-sonnet-20240620-v1:0'
    else:
        return 'us.anthropic.claude-3-5-sonnet-20240620-v1:0'

def update_dynamodb(reference_key, status):
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    table.update_item(
        Key={'reference_key': reference_key},
        UpdateExpression='SET TaskStatus = :status',
        ExpressionAttributeValues={':status': status}
    )

def process_image_claude(image_base64):
    model_endpoint = get_model_endpoint()
    response = bedrock.invoke_model(
        modelId=model_endpoint,
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 1000,
            'temperature': 0.0,
            'top_p': 1.0,
            'top_k': 0,
            'messages': [{
                'role': 'user',
                'content': [
                    {
                        'type': 'image',
                        'source': {
                            'type': 'base64',
                            'media_type': 'image/png',
                            'data': image_base64
                        }
                    },
                    {
                        'type': 'text',
                        'text': 'Read the text in this image in sequence, DO NOT add any word that is not included, ignore footers and headers. Give me the text directly without any extra word from your side.'
                    }
                ]
            }]
        })
    )
    
    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']

def lambda_handler(event, context):
    try:
        message = json.loads(event['Records'][0]['Sns']['Message'])
        reference_key = message['reference_key']
        bucket = message['bucket']
        
        # List all images
        all_objects = []
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket, Prefix=f'images/{reference_key}/')
        
        for page in page_iterator:
            if 'Contents' in page:
                all_objects.extend(page['Contents'])
        
        if not all_objects:
            update_dynamodb(reference_key, 'images-to-text conversion is failed')
            return {'statusCode': 200}
        
        # Process each image with Bedrock
        all_text = ''
        for obj in sorted(all_objects, key=lambda x: x['Key']):
            image_key = obj['Key']
            
            image_object = s3.get_object(Bucket=bucket, Key=image_key)
            image_content = image_object['Body'].read()
            image_base64 = base64.b64encode(image_content).decode('utf-8')
            
            all_text += process_image_claude(image_base64) + '\n\n'
        
        # Save extracted text to S3
        text_output_key = f'download/{reference_key}/formatted_output.txt'
        s3.put_object(Bucket=bucket, Key=text_output_key, Body=all_text)
        
        update_dynamodb(reference_key, 'images-to-text conversion is completed')
        
        return {'statusCode': 200}
        
    except Exception as e:
        update_dynamodb(reference_key, 'images-to-text conversion is failed')
        raise e
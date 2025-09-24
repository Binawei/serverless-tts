import io
import json
import os
import tempfile
from typing import List
from urllib.parse import urlparse
import boto3
from pdf2image import convert_from_path

s3 = boto3.client('s3')
sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

def parse_s3_path(s3_path):
    parsed = urlparse(s3_path)
    return parsed.netloc, parsed.path.lstrip('/')

def update_dynamodb_status(reference_key, status):
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    table.update_item(
        Key={'reference_key': reference_key},
        UpdateExpression='SET TaskStatus = :status',
        ExpressionAttributeValues={':status': status}
    )

def lambda_handler(event, context):
    try:
        record = event['Records'][0]['dynamodb']['NewImage']
        reference_key = record['reference_key']['S']
        input_type = record.get('InputType', {}).get('S', 'PDF')
        
        if input_type == 'TEXT':
            # Skip PDF processing for text input, go directly to text processing
            s3_path = record['S3Path']['S']
            bucket, key = parse_s3_path(s3_path)
            
            # Get text content
            response = s3.get_object(Bucket=bucket, Key=key)
            text_content = response['Body'].read().decode('utf-8')
            
            # Save directly to download folder
            text_key = f'download/{reference_key}/formatted_output.txt'
            s3.put_object(
                Bucket=bucket,
                Key=text_key,
                Body=text_content.encode('utf-8'),
                ContentType='text/plain'
            )
            
            update_dynamodb_status(reference_key, 'images-to-text conversion is completed')
            return {'statusCode': 200}
        
        # PDF Processing
        s3_path = record['S3Path']['S']
        start_page = int(record['StartPage']['S'])
        end_page = int(record['EndPage']['S'])
        
        bucket, key = parse_s3_path(s3_path)
        
        # Download PDF
        tmp_file = tempfile.NamedTemporaryFile(delete=False)
        s3.download_fileobj(bucket, key, tmp_file)
        tmp_file.close()
        
        # Convert to images
        images = convert_from_path(tmp_file.name, first_page=start_page, last_page=end_page)
        
        # Upload images
        uploaded_images = []
        for i, image in enumerate(images):
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            image_key = f'images/{reference_key}/page_{i+start_page}.png'
            s3.put_object(
                Bucket=bucket,
                Key=image_key,
                Body=img_byte_arr,
                ContentType='image/png'
            )
            uploaded_images.append(image_key)
        
        update_dynamodb_status(reference_key, 'pdf-to-images conversion is completed')
        
        # Send SNS notification
        account_id = context.invoked_function_arn.split(':')[4]
        topic_arn = f"arn:aws:sns:{os.environ['AWS_REGION']}:{account_id}:{os.environ['SNS_TOPIC_NAME']}"
        
        sns.publish(
            TopicArn=topic_arn,
            Message=json.dumps({
                'reference_key': reference_key,
                'bucket': bucket,
                'images': uploaded_images
            })
        )
        
        os.unlink(tmp_file.name)
        return {'statusCode': 200}
        
    except Exception as e:
        update_dynamodb_status(reference_key, 'pdf-to-images conversion is failed')
        raise e
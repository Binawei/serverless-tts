import json
import os
import boto3

s3 = boto3.client('s3')
polly = boto3.client('polly')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

def get_language_from_dynamodb(reference_key):
    response = table.get_item(Key={'reference_key': reference_key})
    language = str(response['Item']['Language']).lower()
    return language

def get_voice_id(language):
    if language == 'english':
        return 'Joanna'
    elif language == 'arabic':
        return 'Zeina'
    else:
        return 'Joanna'

def get_language_code(language):
    if language == 'english':
        return 'en-US'
    elif language == 'arabic':
        return 'arb'
    else:
        return 'en-US'

def split_text(text):
    MAX_CHARS = 190000
    words = text.split()
    chunks = []
    current_chunk = []
    
    for word in words:
        if len(' '.join(current_chunk + [word])) <= MAX_CHARS:
            current_chunk.append(word)
        else:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def update_dynamodb_status(reference_key, status):
    table.update_item(
        Key={'reference_key': reference_key},
        UpdateExpression='SET TaskStatus = :status',
        ExpressionAttributeValues={':status': status}
    )

def lambda_handler(event, context):
    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        reference_key = key.split('/')[1]
        
        # Get text content
        response = s3.get_object(Bucket=bucket, Key=key)
        text_content = response['Body'].read().decode('utf-8')
        
        # Get language from DynamoDB
        language = get_language_from_dynamodb(reference_key)
        voice_id = get_voice_id(language)
        language_code = get_language_code(language)
        
        # Split text into chunks
        text_chunks = split_text(text_content)
        
        # Convert each chunk to audio
        audio_files = []
        for i, chunk in enumerate(text_chunks):
            polly_response = polly.synthesize_speech(
                Text=chunk,
                OutputFormat='mp3',
                VoiceId=voice_id,
                LanguageCode=language_code
            )
            
            audio_key = f'download/{reference_key}/chunk_{i}.mp3'
            s3.put_object(
                Bucket=bucket,
                Key=audio_key,
                Body=polly_response['AudioStream'].read(),
                ContentType='audio/mpeg'
            )
            audio_files.append(audio_key)
        
        # Rename first chunk to Audio.mp3 (VocalDocs pattern)
        final_audio_key = f'download/{reference_key}/Audio.mp3'
        s3.copy_object(
            Bucket=bucket,
            CopySource={'Bucket': bucket, 'Key': audio_files[0]},
            Key=final_audio_key
        )
        
        # Clean up chunk files
        for audio_file in audio_files:
            s3.delete_object(Bucket=bucket, Key=audio_file)
        
        update_dynamodb_status(reference_key, 'Voice-is-Ready')
        
        return {'statusCode': 200}
        
    except Exception as e:
        update_dynamodb_status(reference_key, 'failed')
        raise e
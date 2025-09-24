#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import json
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid
import jwt
import base64
from werkzeug.utils import secure_filename
import PyPDF2
import io
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

# AWS clients
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

polly = boto3.client(
    'polly',
    region_name='us-east-1',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

s3 = boto3.client(
    's3',
    region_name='us-east-1',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

table = dynamodb.Table('tts-requests')

def extract_user_info(auth_header):
    try:
        if not auth_header or not auth_header.startswith('Bearer '):
            return None, 'Missing authorization token'
        
        token = auth_header.replace('Bearer ', '')
        
        # Decode JWT without verification (for local testing)
        decoded = jwt.decode(token, options={"verify_signature": False})
        print(f"Decoded token: {decoded}")  # Debug log
        
        user_email = decoded.get('email')
        user_id = decoded.get('sub')
        
        if not user_email:
            return None, 'Invalid token: missing email'
            
        # Handle both regular Cognito and OAuth tokens
        username = decoded.get('name') or decoded.get('given_name') or decoded.get('cognito:username') or user_email
            
        return {
            'email': user_email,
            'user_id': user_id,
            'username': username
        }, None
        
    except Exception as e:
        print(f"Token validation error: {e}")  # Debug log
        return None, f'Token validation failed: {str(e)}'

def extract_user_email(auth_header):
    user_info, error = extract_user_info(auth_header)
    return user_info['email'] if user_info else 'anonymous@example.com'

@app.route('/upload', methods=['POST'])
def upload_text():
    try:
        # Validate authentication
        auth_header = request.headers.get('Authorization', '')
        user_info, error = extract_user_info(auth_header)
        
        if error:
            return jsonify({'error': error}), 401
            
        user_email = user_info['email']
        
        data = request.json
        print(f"User {user_email} processing text: {data['text'][:50]}...")
        
        reference_key = str(uuid.uuid4())
        
        # Create DynamoDB record
        item = {
            'reference_key': reference_key,
            'user_email': user_email,
            'text': data['text'],
            'voice': data.get('voice_id', 'Joanna'),
            'language': data.get('language', 'en-US'),
            'TaskStatus': 'Upload-Completed',
            'UploadDateTime': datetime.now().isoformat(),
            'InputType': 'TEXT'
        }
        
        table.put_item(Item=item)
        
        print(f"Generating audio for: {reference_key}")
        
        # Generate audio with Polly
        response = polly.synthesize_speech(
            Text=data['text'],
            OutputFormat='mp3',
            VoiceId=data.get('voice_id', 'Joanna')
        )
        
        # Upload to S3
        s3_key = f'audio/{reference_key}.mp3'
        s3.put_object(
            Bucket='tts-bucket-1758733916',
            Key=s3_key,
            Body=response['AudioStream'].read(),
            ContentType='audio/mpeg'
        )
        
        print(f"Audio uploaded to S3: {s3_key}")
        
        # Update status
        table.update_item(
            Key={'reference_key': reference_key},
            UpdateExpression='SET TaskStatus = :status',
            ExpressionAttributeValues={':status': 'Voice-is-Ready'}
        )
        
        print(f"Conversion complete: {reference_key}")
        
        return jsonify({
            'reference_key': reference_key,
            'status': 'success'
        })
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/track', methods=['GET', 'POST'])
def track_requests():
    try:
        if request.method == 'GET':
            # Validate authentication
            auth_header = request.headers.get('Authorization', '')
            user_info, error = extract_user_info(auth_header)
            
            if error:
                return jsonify({'error': error}), 401
                
            user_email = user_info['email']
            
            # Get all requests for authenticated user
            response = table.scan(
                FilterExpression='user_email = :email',
                ExpressionAttributeValues={':email': user_email}
            )
            
            return jsonify({
                'requests': response['Items']
            })
            
        elif request.method == 'POST':
            # Generate presigned URL
            data = request.json
            reference_key = data['reference_key']
            
            url = s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': 'tts-bucket-1758733916',
                    'Key': f'audio/{reference_key}.mp3'
                },
                ExpiresIn=3600
            )
            
            return jsonify({
                'presigned_url': url
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    try:
        auth_header = request.headers.get('Authorization', '')
        user_email = extract_user_email(auth_header)
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
            
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files allowed'}), 400
        
        # Get form data
        language = request.form.get('language', 'english')
        start_page = int(request.form.get('start_page', 1))
        end_page = int(request.form.get('end_page', 1))
        voice_id = request.form.get('voice_id', 'Joanna')
        
        reference_key = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        
        print(f"Processing PDF: {filename} (pages {start_page}-{end_page})")
        
        # Upload PDF to S3
        s3_key = f'pdfs/{reference_key}/{filename}'
        s3.put_object(
            Bucket='tts-bucket-1758733916',
            Key=s3_key,
            Body=file.read(),
            ContentType='application/pdf'
        )
        
        # Create DynamoDB record
        item = {
            'reference_key': reference_key,
            'user_email': user_email,
            'fileName': filename,
            'Language': language,
            'StartPage': start_page,
            'EndPage': end_page,
            'voice': voice_id,
            'TaskStatus': 'Upload-Completed',
            'UploadDateTime': datetime.now().isoformat(),
            'InputType': 'PDF'
        }
        
        table.put_item(Item=item)
        
        # Extract text from PDF
        file.seek(0)  # Reset file pointer
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        
        extracted_text = ""
        total_pages = len(pdf_reader.pages)
        
        # Adjust end_page if it exceeds total pages
        actual_end_page = min(end_page, total_pages)
        
        for page_num in range(start_page - 1, actual_end_page):
            if page_num < total_pages:
                page = pdf_reader.pages[page_num]
                extracted_text += page.extract_text() + " "
        
        # Clean up text
        extracted_text = extracted_text.strip()
        if not extracted_text:
            extracted_text = f"No readable text found in {filename} pages {start_page}-{actual_end_page}. The PDF might contain images or scanned content."
        
        print(f"Extracted {len(extracted_text)} characters from PDF")
        print(f"Text preview: {extracted_text[:100]}...")
        
        # Store extracted text in DynamoDB
        table.update_item(
            Key={'reference_key': reference_key},
            UpdateExpression='SET extracted_text = :text',
            ExpressionAttributeValues={':text': extracted_text}
        )
        
        print(f"Generating audio for PDF: {reference_key}")
        
        # Generate audio with Polly (limit text length)
        text_for_audio = extracted_text[:3000] if len(extracted_text) > 3000 else extracted_text
        
        response = polly.synthesize_speech(
            Text=text_for_audio,
            OutputFormat='mp3',
            VoiceId=voice_id
        )
        
        # Upload audio to S3
        audio_key = f'audio/{reference_key}.mp3'
        s3.put_object(
            Bucket='tts-bucket-1758733916',
            Key=audio_key,
            Body=response['AudioStream'].read(),
            ContentType='audio/mpeg'
        )
        
        print(f"PDF audio uploaded to S3: {audio_key}")
        
        # Update status
        table.update_item(
            Key={'reference_key': reference_key},
            UpdateExpression='SET TaskStatus = :status',
            ExpressionAttributeValues={':status': 'Voice-is-Ready'}
        )
        
        print(f"PDF conversion complete: {reference_key}")
        
        return jsonify({
            'reference_key': reference_key,
            'status': 'success',
            'message': 'PDF uploaded and converted successfully'
        })
        
    except Exception as e:
        print(f"PDF upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/auth/oauth-callback', methods=['POST'])
def oauth_callback():
    try:
        data = request.json
        code = data.get('code')
        redirect_uri = data.get('redirect_uri')
        
        if not code:
            return jsonify({'error': 'Missing authorization code'}), 400
        
        # Exchange code for tokens
        token_url = 'https://tts-app-wry4owok.auth.us-east-1.amazoncognito.com/oauth2/token'
        
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': '1piov92n8lm83rjufak0rih9qp',
            'code': code,
            'redirect_uri': redirect_uri
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(token_url, data=token_data, headers=headers)
        
        if response.status_code == 200:
            tokens = response.json()
            return jsonify({
                'success': True,
                'tokens': tokens
            })
        else:
            print(f"Token exchange failed: {response.status_code} - {response.text}")
            return jsonify({
                'success': False,
                'error': 'Token exchange failed'
            }), 400
            
    except Exception as e:
        print(f"OAuth callback error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting mock API server on http://localhost:5000")
    print("Update frontend config: API_GATEWAY_URL: 'http://localhost:5000'")
    app.run(debug=True, port=5000)
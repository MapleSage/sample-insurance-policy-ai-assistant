#!/usr/bin/env python3
"""
File Upload API for Insurance Documents
Handles customer document uploads and policy certificate uploads
"""

import boto3
import json
import os
from typing import Dict, Optional
import uuid
from datetime import datetime

class DocumentUploadHandler:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.customer_bucket = os.getenv('CUSTOMER_POLICY_BUCKET')
        self.uploads_bucket = os.getenv('UPLOADS_BUCKET', self.customer_bucket)
    
    def upload_customer_policy(self, file_content: bytes, username: str, filename: str) -> str:
        """Upload customer-specific policy document"""
        try:
            s3_key = f'customer_policy/{username}.txt'
            
            # If it's a text file, store as-is; if PDF, we'd need to extract text
            if filename.endswith('.txt'):
                content = file_content.decode('utf-8')
            else:
                # For demo purposes, treat as text. In production, use PDF extraction
                content = file_content.decode('utf-8', errors='ignore')
            
            self.s3_client.put_object(
                Bucket=self.customer_bucket,
                Key=s3_key,
                Body=content.encode('utf-8'),
                ContentType='text/plain',
                Metadata={
                    'customer': username,
                    'original_filename': filename,
                    'uploaded_at': datetime.now().isoformat(),
                    'document_type': 'customer_policy'
                }
            )
            
            return s3_key
            
        except Exception as e:
            raise Exception(f"Failed to upload customer policy: {e}")
    
    def upload_general_document(self, file_content: bytes, filename: str, category: str = 'general') -> str:
        """Upload general insurance documents"""
        try:
            file_id = str(uuid.uuid4())
            s3_key = f'uploads/{category}/{file_id}_{filename}'
            
            self.s3_client.put_object(
                Bucket=self.uploads_bucket,
                Key=s3_key,
                Body=file_content,
                Metadata={
                    'original_filename': filename,
                    'category': category,
                    'uploaded_at': datetime.now().isoformat(),
                    'file_id': file_id
                }
            )
            
            return s3_key
            
        except Exception as e:
            raise Exception(f"Failed to upload document: {e}")
    
    def get_upload_url(self, filename: str, username: Optional[str] = None) -> str:
        """Generate presigned URL for direct S3 upload"""
        try:
            if username:
                s3_key = f'customer_policy/{username}_{filename}'
                bucket = self.customer_bucket
            else:
                s3_key = f'uploads/general/{str(uuid.uuid4())}_{filename}'
                bucket = self.uploads_bucket
            
            url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': bucket,
                    'Key': s3_key,
                    'ContentType': 'application/octet-stream'
                },
                ExpiresIn=3600  # 1 hour
            )
            
            return url
            
        except Exception as e:
            raise Exception(f"Failed to generate upload URL: {e}")

def handle_upload(request_data: Dict) -> Dict:
    """Main handler for document uploads"""
    action = request_data.get('action', 'upload')
    
    handler = DocumentUploadHandler()
    
    if action == 'upload':
        file_content = request_data.get('file_content')  # bytes
        filename = request_data.get('filename', '')
        username = request_data.get('username')
        category = request_data.get('category', 'general')
        
        if not file_content or not filename:
            return {'error': 'file_content and filename are required', 'status': 400}
        
        try:
            if username and category == 'customer_policy':
                s3_key = handler.upload_customer_policy(file_content, username, filename)
                message = f'Customer policy uploaded for {username}'
            else:
                s3_key = handler.upload_general_document(file_content, filename, category)
                message = f'Document uploaded to {category} category'
            
            return {
                'success': True,
                'message': message,
                's3_key': s3_key,
                'filename': filename,
                'category': category,
                'size': len(file_content)
            }
            
        except Exception as e:
            return {'error': str(e), 'status': 500}
    
    elif action == 'get_upload_url':
        filename = request_data.get('filename', '')
        username = request_data.get('username')
        
        if not filename:
            return {'error': 'filename is required', 'status': 400}
        
        try:
            upload_url = handler.get_upload_url(filename, username)
            return {
                'success': True,
                'upload_url': upload_url,
                'expires_in': 3600
            }
            
        except Exception as e:
            return {'error': str(e), 'status': 500}
    
    else:
        return {'error': 'Invalid action. Use "upload" or "get_upload_url"', 'status': 400}

# Example usage
if __name__ == "__main__":
    # Test upload
    test_content = b"Test customer policy content for John Doe..."
    result = handle_upload({
        'action': 'upload',
        'file_content': test_content,
        'filename': 'john_doe_policy.txt',
        'username': 'john_doe',
        'category': 'customer_policy'
    })
    print(json.dumps(result, indent=2))
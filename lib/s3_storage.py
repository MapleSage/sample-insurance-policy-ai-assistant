#!/usr/bin/env python3
"""
S3 Storage utilities for insurance documents
"""

import boto3
import os
from typing import Optional

class S3Storage:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket = os.getenv('CUSTOMER_POLICY_BUCKET')
    
    def upload_file(self, file_content: bytes, key: str, content_type: str = 'text/plain') -> bool:
        """Upload file to S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_content,
                ContentType=content_type
            )
            return True
        except Exception as e:
            print(f"Upload error: {e}")
            return False
    
    def get_file(self, key: str) -> Optional[str]:
        """Get file content from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
            return response['Body'].read().decode('utf-8')
        except Exception as e:
            print(f"Get file error: {e}")
            return None
#!/usr/bin/env python3
"""
Policy Documents Ingestion API
Ingests PDF policy documents into Bedrock Knowledge Base
"""

import boto3
import json
import os
from pathlib import Path
from typing import Dict, List

class PolicyIngestionHandler:
    def __init__(self):
        self.bedrock_agent = boto3.client(
            'bedrock-agent',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.s3_client = boto3.client(
            's3',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.kb_id = os.getenv('KNOWLEDGE_BASE_ID')
        self.data_source_id = os.getenv('DATA_SOURCE_ID')
        self.policy_bucket = os.getenv('POLICY_BUCKET')
    
    def upload_policies_to_s3(self, policy_docs_path: str = './policy_docs') -> List[str]:
        """Upload policy documents to S3"""
        uploaded_files = []
        policy_path = Path(policy_docs_path)
        
        if not policy_path.exists():
            return uploaded_files
        
        for pdf_file in policy_path.glob('*.pdf'):
            try:
                s3_key = f'policy_docs/{pdf_file.name}'
                
                with open(pdf_file, 'rb') as f:
                    self.s3_client.put_object(
                        Bucket=self.policy_bucket,
                        Key=s3_key,
                        Body=f.read(),
                        ContentType='application/pdf',
                        Metadata={
                            'source': 'policy_documents',
                            'type': 'insurance_policy',
                            'uploaded_at': str(pdf_file.stat().st_mtime)
                        }
                    )
                
                uploaded_files.append(s3_key)
                print(f"Uploaded: {pdf_file.name}")
                
            except Exception as e:
                print(f"Failed to upload {pdf_file.name}: {e}")
        
        return uploaded_files
    
    def start_ingestion_job(self) -> str:
        """Start Knowledge Base ingestion job"""
        try:
            response = self.bedrock_agent.start_ingestion_job(
                knowledgeBaseId=self.kb_id,
                dataSourceId=self.data_source_id,
                description="Ingesting insurance policy documents"
            )
            return response['ingestionJob']['ingestionJobId']
        except Exception as e:
            print(f"Failed to start ingestion job: {e}")
            return ""
    
    def check_ingestion_status(self, job_id: str) -> Dict:
        """Check ingestion job status"""
        try:
            response = self.bedrock_agent.get_ingestion_job(
                knowledgeBaseId=self.kb_id,
                dataSourceId=self.data_source_id,
                ingestionJobId=job_id
            )
            
            job = response['ingestionJob']
            return {
                'status': job['status'],
                'started_at': job.get('startedAt', ''),
                'updated_at': job.get('updatedAt', ''),
                'statistics': job.get('statistics', {})
            }
        except Exception as e:
            print(f"Failed to check ingestion status: {e}")
            return {'status': 'ERROR', 'error': str(e)}

def handle_policy_ingestion(request_data: Dict) -> Dict:
    """Main handler for policy document ingestion"""
    action = request_data.get('action', 'ingest')
    
    handler = PolicyIngestionHandler()
    
    if action == 'ingest':
        # Upload PDFs to S3
        uploaded_files = handler.upload_policies_to_s3()
        
        if not uploaded_files:
            return {
                'error': 'No policy documents found to upload',
                'status': 400
            }
        
        # Start ingestion job
        job_id = handler.start_ingestion_job()
        
        if not job_id:
            return {
                'error': 'Failed to start ingestion job',
                'status': 500
            }
        
        return {
            'success': True,
            'message': f'Started ingestion of {len(uploaded_files)} policy documents',
            'job_id': job_id,
            'uploaded_files': uploaded_files
        }
    
    elif action == 'status':
        job_id = request_data.get('job_id')
        if not job_id:
            return {'error': 'job_id required for status check', 'status': 400}
        
        status = handler.check_ingestion_status(job_id)
        return {
            'success': True,
            'job_status': status
        }
    
    else:
        return {'error': 'Invalid action. Use "ingest" or "status"', 'status': 400}

# Example usage
if __name__ == "__main__":
    # Test ingestion
    result = handle_policy_ingestion({'action': 'ingest'})
    print(json.dumps(result, indent=2))
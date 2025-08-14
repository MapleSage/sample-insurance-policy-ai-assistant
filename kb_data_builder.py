#!/usr/bin/env python3
"""
Knowledge Base Data Builder for Insurance Policy AI Assistant
Processes PDF documents and creates embeddings for Bedrock Knowledge Base
"""

import boto3
import json
import os
from pathlib import Path
import time
from typing import List, Dict

class KnowledgeBaseBuilder:
    def __init__(self, region='us-east-1'):
        self.bedrock = boto3.client('bedrock-agent', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)
        self.region = region
        
    def create_knowledge_base(self, kb_name: str, s3_bucket: str, role_arn: str) -> str:
        """Create Bedrock Knowledge Base"""
        try:
            response = self.bedrock.create_knowledge_base(
                name=kb_name,
                description="Insurance Policy Knowledge Base",
                roleArn=role_arn,
                knowledgeBaseConfiguration={
                    'type': 'VECTOR',
                    'vectorKnowledgeBaseConfiguration': {
                        'embeddingModelArn': f'arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v1'
                    }
                },
                storageConfiguration={
                    'type': 'OPENSEARCH_SERVERLESS',
                    'opensearchServerlessConfiguration': {
                        'collectionArn': f'arn:aws:aoss:{self.region}:123456789012:collection/insurance-kb',
                        'vectorIndexName': 'insurance-index',
                        'fieldMapping': {
                            'vectorField': 'vector',
                            'textField': 'text',
                            'metadataField': 'metadata'
                        }
                    }
                }
            )
            return response['knowledgeBase']['knowledgeBaseId']
        except Exception as e:
            print(f"Error creating knowledge base: {e}")
            return None
    
    def create_data_source(self, kb_id: str, s3_bucket: str, s3_prefix: str = 'policy_docs/') -> str:
        """Create data source for Knowledge Base"""
        try:
            response = self.bedrock.create_data_source(
                knowledgeBaseId=kb_id,
                name="insurance-policy-docs",
                description="Insurance policy documents data source",
                dataSourceConfiguration={
                    'type': 'S3',
                    's3Configuration': {
                        'bucketArn': f'arn:aws:s3:::{s3_bucket}',
                        'inclusionPrefixes': [s3_prefix]
                    }
                }
            )
            return response['dataSource']['dataSourceId']
        except Exception as e:
            print(f"Error creating data source: {e}")
            return None
    
    def start_ingestion_job(self, kb_id: str, data_source_id: str) -> str:
        """Start ingestion job for the data source"""
        try:
            response = self.bedrock.start_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id,
                description="Initial ingestion of insurance policy documents"
            )
            return response['ingestionJob']['ingestionJobId']
        except Exception as e:
            print(f"Error starting ingestion job: {e}")
            return None
    
    def check_ingestion_status(self, kb_id: str, data_source_id: str, job_id: str) -> str:
        """Check the status of ingestion job"""
        try:
            response = self.bedrock.get_ingestion_job(
                knowledgeBaseId=kb_id,
                dataSourceId=data_source_id,
                ingestionJobId=job_id
            )
            return response['ingestionJob']['status']
        except Exception as e:
            print(f"Error checking ingestion status: {e}")
            return "ERROR"

class KnowledgeBaseRetriever:
    def __init__(self, kb_id: str, region='us-east-1'):
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
        self.kb_id = kb_id
        
    def retrieve(self, query: str, max_results: int = 5) -> List[Dict]:
        """Retrieve relevant documents from Knowledge Base"""
        try:
            response = self.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            return response['retrievalResults']
        except Exception as e:
            print(f"Error retrieving from knowledge base: {e}")
            return []
    
    def retrieve_and_generate(self, query: str, model_id: str = 'us.anthropic.claude-3-5-haiku-20241022-v1:0') -> str:
        """Retrieve and generate response using RAG"""
        try:
            response = self.bedrock_agent_runtime.retrieve_and_generate(
                input={'text': query},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.kb_id,
                        'modelArn': f'arn:aws:bedrock:us-east-1::foundation-model/{model_id}'
                    }
                }
            )
            return response['output']['text']
        except Exception as e:
            print(f"Error in retrieve and generate: {e}")
            return "Error generating response"

if __name__ == "__main__":
    # Example usage
    builder = KnowledgeBaseBuilder()
    
    # Replace with your actual values
    KB_NAME = "insurance-policy-kb"
    S3_BUCKET = "your-s3-bucket-name"
    ROLE_ARN = "arn:aws:iam::123456789012:role/BedrockKnowledgeBaseRole"
    
    print("Creating Knowledge Base...")
    kb_id = builder.create_knowledge_base(KB_NAME, S3_BUCKET, ROLE_ARN)
    
    if kb_id:
        print(f"Knowledge Base created: {kb_id}")
        
        print("Creating data source...")
        ds_id = builder.create_data_source(kb_id, S3_BUCKET)
        
        if ds_id:
            print(f"Data source created: {ds_id}")
            
            print("Starting ingestion job...")
            job_id = builder.start_ingestion_job(kb_id, ds_id)
            
            if job_id:
                print(f"Ingestion job started: {job_id}")
                
                # Monitor ingestion status
                while True:
                    status = builder.check_ingestion_status(kb_id, ds_id, job_id)
                    print(f"Ingestion status: {status}")
                    
                    if status in ['COMPLETE', 'FAILED']:
                        break
                    
                    time.sleep(30)
                
                if status == 'COMPLETE':
                    print("Knowledge Base is ready!")
                    
                    # Test retrieval
                    retriever = KnowledgeBaseRetriever(kb_id)
                    test_query = "What is covered under motor insurance?"
                    results = retriever.retrieve(test_query)
                    
                    print(f"Test query: {test_query}")
                    print(f"Retrieved {len(results)} results")
                    
                    # Test RAG
                    response = retriever.retrieve_and_generate(test_query)
                    print(f"Generated response: {response}")
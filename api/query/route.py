#!/usr/bin/env python3
"""
Insurance Policy Query API
Handles customer queries using Bedrock Knowledge Base and customer-specific policies
"""

import json
import boto3
import os
from typing import Dict, List, Optional

class InsurancePolicyQueryHandler:
    def __init__(self):
        self.bedrock_agent_runtime = boto3.client(
            'bedrock-agent-runtime',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.s3_client = boto3.client(
            's3',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.kb_id = os.getenv('KNOWLEDGE_BASE_ID')
        self.customer_bucket = os.getenv('CUSTOMER_POLICY_BUCKET')
        
    def get_customer_policy(self, username: str) -> str:
        """Retrieve customer-specific policy from S3"""
        try:
            response = self.s3_client.get_object(
                Bucket=self.customer_bucket,
                Key=f'customer_policy/{username}.txt'
            )
            return response['Body'].read().decode('utf-8')
        except Exception as e:
            print(f"Error retrieving customer policy: {e}")
            return ""
    
    def retrieve_from_kb(self, query: str, max_results: int = 3) -> List[Dict]:
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
            print(f"Error retrieving from KB: {e}")
            return []
    
    def generate_response(self, query: str, username: str) -> Dict:
        """Generate response using RAG with customer context"""
        try:
            # Get customer policy
            customer_policy = self.get_customer_policy(username)
            
            # Retrieve from knowledge base
            kb_results = self.retrieve_from_kb(query)
            
            # Prepare context
            context = "\\n\\n".join([
                result['content']['text'] for result in kb_results
            ])
            
            # Enhanced prompt for insurance assistant
            prompt = f"""You are an expert insurance policy assistant. Use the following information to provide accurate, helpful responses:

CUSTOMER'S SPECIFIC POLICY:
{customer_policy}

GENERAL INSURANCE POLICY INFORMATION:
{context}

CUSTOMER QUESTION: {query}

Please provide a comprehensive response that:
1. Addresses the customer's specific policy details
2. References relevant general policy information
3. Includes clear explanations and next steps if applicable
4. Cites sources when possible

Response:"""

            # Use retrieve_and_generate for better integration
            response = self.bedrock_agent_runtime.retrieve_and_generate(
                input={'text': prompt},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': self.kb_id,
                        'modelArn': f'arn:aws:bedrock:us-east-1::foundation-model/{os.getenv("MODEL_ID", "us.anthropic.claude-3-5-haiku-20241022-v1:0")}'
                    }
                }
            )
            
            return {
                'response': response['output']['text'],
                'sources': [
                    {
                        'title': r.get('metadata', {}).get('source', 'Policy Document'),
                        'content': r['content']['text'][:200] + '...'
                    } for r in kb_results
                ],
                'customer_policy_used': bool(customer_policy),
                'timestamp': response['responseMetadata']['HTTPHeaders'].get('date', '')
            }
            
        except Exception as e:
            print(f"Error generating response: {e}")
            return {
                'response': 'I apologize, but I encountered an error processing your request. Please try again or contact customer service.',
                'sources': [],
                'error': str(e)
            }

def handle_query(request_data: Dict) -> Dict:
    """Main handler for insurance policy queries"""
    query = request_data.get('query', '')
    username = request_data.get('username', 'john_doe')
    
    if not query:
        return {'error': 'Query is required', 'status': 400}
    
    handler = InsurancePolicyQueryHandler()
    result = handler.generate_response(query, username)
    
    return {
        'success': True,
        'data': result,
        'timestamp': json.dumps({"timestamp": "now"}),
        'model': 'Insurance Policy Assistant with Bedrock KB'
    }

# Example usage for testing
if __name__ == "__main__":
    test_request = {
        'query': 'What is my deductible for collision coverage?',
        'username': 'john_doe'
    }
    
    result = handle_query(test_request)
    print(json.dumps(result, indent=2))
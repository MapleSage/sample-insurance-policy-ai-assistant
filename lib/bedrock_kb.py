#!/usr/bin/env python3
"""
Bedrock Knowledge Base Integration Library
"""

import boto3
import json
import os
from typing import Dict, List, Optional

class BedrockKnowledgeBase:
    def __init__(self, region: str = 'us-east-1'):
        self.bedrock_agent = boto3.client('bedrock-agent', region_name=region)
        self.bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=region)
        self.region = region
        
    def retrieve_and_generate(self, kb_id: str, query: str, model_id: str = 'us.anthropic.claude-3-5-haiku-20241022-v1:0') -> Dict:
        """Retrieve and generate response using RAG"""
        try:
            response = self.bedrock_agent_runtime.retrieve_and_generate(
                input={'text': query},
                retrieveAndGenerateConfiguration={
                    'type': 'KNOWLEDGE_BASE',
                    'knowledgeBaseConfiguration': {
                        'knowledgeBaseId': kb_id,
                        'modelArn': f'arn:aws:bedrock:{self.region}::foundation-model/{model_id}'
                    }
                }
            )
            
            return {
                'response': response['output']['text'],
                'citations': response.get('citations', []),
                'session_id': response.get('sessionId', '')
            }
        except Exception as e:
            return {
                'response': 'Error processing request.',
                'error': str(e)
            }

class InsuranceKBManager:
    def __init__(self):
        self.kb = BedrockKnowledgeBase()
        self.kb_id = os.getenv('KNOWLEDGE_BASE_ID')
    
    def query_insurance_policy(self, question: str, customer_context: str = "") -> Dict:
        """Query insurance policy with customer context"""
        if not self.kb_id:
            return {'error': 'Knowledge Base ID not configured'}
        
        enhanced_query = f"{question}\n\nCustomer Context: {customer_context}" if customer_context else question
        return self.kb.retrieve_and_generate(self.kb_id, enhanced_query)
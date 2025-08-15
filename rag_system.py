#!/usr/bin/env python3
"""
Enhanced RAG System for Insurance Policy AI Assistant
Handles document processing, knowledge base integration, and retrieval
"""

import os
import boto3
import json
import streamlit as st
from typing import Dict, List, Optional
from pathlib import Path
import tempfile
import PyPDF2
import docx
from datetime import datetime

class DocumentProcessor:
    """Handles document processing and text extraction"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.txt', '.docx']
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from various document formats"""
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.pdf':
                return self._extract_pdf_text(file_path)
            elif file_ext == '.txt':
                return self._extract_txt_text(file_path)
            elif file_ext == '.docx':
                return self._extract_docx_text(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
        except Exception as e:
            st.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def _extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF files"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            st.error(f"PDF extraction error: {e}")
        return text
    
    def _extract_txt_text(self, file_path: str) -> str:
        """Extract text from TXT files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            st.error(f"TXT extraction error: {e}")
            return ""
    
    def _extract_docx_text(self, file_path: str) -> str:
        """Extract text from DOCX files"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            st.error(f"DOCX extraction error: {e}")
            return ""

class EnhancedKnowledgeBaseManager:
    """Enhanced Knowledge Base Manager with document upload capabilities"""
    
    def __init__(self, knowledge_base_id: str, region: str = 'us-east-1'):
        self.knowledge_base_id = knowledge_base_id
        self.region = region
        self.document_processor = DocumentProcessor()
        
        # Initialize AWS clients
        try:
            self.bedrock_agent = boto3.client('bedrock-agent-runtime', region_name=region)
            self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
            self.s3_client = boto3.client('s3', region_name=region)
            self.connected = True
        except Exception as e:
            st.warning(f"AWS connection failed: {e}. Running in demo mode.")
            self.connected = False
    
    def upload_document(self, file_path: str, file_name: str, bucket_name: str) -> bool:
        """Upload document to S3 and trigger knowledge base sync"""
        try:
            if not self.connected:
                # Demo mode - just simulate upload
                st.info(f"Demo mode: Would upload {file_name} to knowledge base")
                return True
            
            # Extract text from document
            text_content = self.document_processor.extract_text(file_path)
            if not text_content:
                return False
            
            # Upload to S3
            s3_key = f"documents/{datetime.now().strftime('%Y/%m/%d')}/{file_name}"
            
            self.s3_client.upload_file(file_path, bucket_name, s3_key)
            
            # Trigger knowledge base sync (if available)
            # Note: This would require additional setup in production
            st.success(f"Document uploaded to S3: {s3_key}")
            
            return True
            
        except Exception as e:
            st.error(f"Upload failed: {e}")
            return False
    
    def retrieve_documents(self, query: str, max_results: int = 5) -> List[Dict]:
        """Retrieve relevant documents from knowledge base"""
        try:
            if not self.connected:
                # Demo mode - return mock results
                return self._get_demo_results(query)
            
            response = self.bedrock_agent.retrieve(
                knowledgeBaseId=self.knowledge_base_id,
                retrievalQuery={'text': query},
                retrievalConfiguration={
                    'vectorSearchConfiguration': {
                        'numberOfResults': max_results
                    }
                }
            )
            
            return response.get('retrievalResults', [])
            
        except Exception as e:
            st.error(f"Retrieval error: {e}")
            return []
    
    def _get_demo_results(self, query: str) -> List[Dict]:
        """Return demo results when not connected to AWS"""
        demo_results = [
            {
                'content': {'text': f'Demo result for query: {query}. This would contain relevant insurance policy information.'},
                'metadata': {'source': 'Demo Policy Document', 'type': 'policy'},
                'score': 0.95
            },
            {
                'content': {'text': 'Coverage includes comprehensive and collision protection with a $500 deductible.'},
                'metadata': {'source': 'Coverage Details', 'type': 'coverage'},
                'score': 0.87
            }
        ]
        return demo_results
    
    def generate_response(self, query: str, context: str, customer_policy: str = "") -> Dict:
        """Generate AI response using retrieved context"""
        try:
            if not self.connected:
                return self._generate_demo_response(query, context)
            
            # Prepare enhanced prompt
            prompt = f"""You are an expert insurance assistant. Use the following information to provide a comprehensive answer:

CUSTOMER POLICY:
{customer_policy}

RELEVANT CONTEXT:
{context}

CUSTOMER QUESTION: {query}

Please provide a detailed, accurate response based on the available information. Include specific policy details when relevant and cite sources when possible."""

            # Call Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=os.getenv('MODEL_ID', 'us.anthropic.claude-3-5-haiku-20241022-v1:0'),
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            return {
                'response': result['content'][0]['text'],
                'model_used': 'Claude 3.5 Haiku',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            st.error(f"Response generation error: {e}")
            return {'response': 'Sorry, I encountered an error generating a response.'}
    
    def _generate_demo_response(self, query: str, context: str) -> Dict:
        """Generate demo response when not connected to AWS"""
        demo_responses = {
            'deductible': "Based on your policy, your deductible is $500 for comprehensive and collision coverage. This means you'll pay the first $500 of any covered claim.",
            'rental': "Yes, your policy includes rental car coverage up to $30 per day for a maximum of 30 days while your vehicle is being repaired due to a covered loss.",
            'accident': "If you have an accident, first ensure everyone's safety, then contact the police if needed. You should report the claim to us within 24 hours by calling our claims hotline.",
            'claim': "To file a claim, you can call our 24/7 claims hotline, use our mobile app, or file online through your customer portal. Have your policy number and incident details ready.",
            'coverage': "Your policy excludes normal wear and tear, mechanical breakdowns, intentional damage, and damage from racing or commercial use."
        }
        
        # Simple keyword matching for demo
        response_key = 'deductible'
        for key in demo_responses.keys():
            if key in query.lower():
                response_key = key
                break
        
        return {
            'response': demo_responses.get(response_key, "I'd be happy to help with your insurance question. Could you please provide more specific details?"),
            'model_used': 'Demo Mode',
            'timestamp': datetime.now().isoformat()
        }

class RAGInsuranceAssistant:
    """Main RAG-powered Insurance Assistant"""
    
    def __init__(self, knowledge_base_id: str, region: str = 'us-east-1'):
        self.kb_manager = EnhancedKnowledgeBaseManager(knowledge_base_id, region)
        self.conversation_history = []
    
    def process_uploaded_files(self, uploaded_files, bucket_name: str = None) -> Dict:
        """Process multiple uploaded files"""
        results = {
            'successful': [],
            'failed': [],
            'total_processed': 0
        }
        
        for uploaded_file in uploaded_files:
            try:
                # Save file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getbuffer())
                    tmp_file_path = tmp_file.name
                
                # Process the file
                if bucket_name and self.kb_manager.connected:
                    success = self.kb_manager.upload_document(tmp_file_path, uploaded_file.name, bucket_name)
                else:
                    # Demo mode - just extract text to show it works
                    text = self.kb_manager.document_processor.extract_text(tmp_file_path)
                    success = len(text) > 0
                
                if success:
                    results['successful'].append(uploaded_file.name)
                else:
                    results['failed'].append(uploaded_file.name)
                
                results['total_processed'] += 1
                
                # Clean up temp file
                os.unlink(tmp_file_path)
                
            except Exception as e:
                results['failed'].append(f"{uploaded_file.name}: {str(e)}")
        
        return results
    
    def chat(self, query: str, username: str = "demo_user") -> Dict:
        """Main chat interface with RAG"""
        try:
            # Retrieve relevant documents
            retrieved_docs = self.kb_manager.retrieve_documents(query, max_results=3)
            
            # Prepare context
            context = "\n\n".join([
                doc['content']['text'] for doc in retrieved_docs
            ])
            
            # Get customer policy (mock for demo)
            customer_policy = self._get_customer_policy(username)
            
            # Generate response
            response_data = self.kb_manager.generate_response(query, context, customer_policy)
            
            # Store in conversation history
            self.conversation_history.append({
                'query': query,
                'response': response_data['response'],
                'timestamp': datetime.now().isoformat(),
                'sources': [{'title': doc.get('metadata', {}).get('source', 'Unknown'),
                           'content': doc['content']['text'][:200] + '...',
                           'score': doc.get('score', 0)} for doc in retrieved_docs]
            })
            
            return {
                'response': response_data['response'],
                'sources': self.conversation_history[-1]['sources'],
                'model_used': response_data.get('model_used', 'Unknown'),
                'retrieved_docs_count': len(retrieved_docs)
            }
            
        except Exception as e:
            st.error(f"Chat error: {e}")
            return {
                'response': 'I apologize, but I encountered an error processing your request. Please try again.',
                'sources': [],
                'model_used': 'Error',
                'retrieved_docs_count': 0
            }
    
    def _get_customer_policy(self, username: str) -> str:
        """Get customer policy information (mock implementation)"""
        policies = {
            'john_doe': """
            Policy Number: POL-123456
            Coverage: Comprehensive Auto Insurance
            Deductible: $500
            Premium: $1,200/year
            Vehicle: 2020 Honda Civic
            Coverage Limits: $100,000/$300,000/$50,000
            """,
            'jane_smith': """
            Policy Number: POL-789012
            Coverage: Full Coverage Auto Insurance
            Deductible: $250
            Premium: $1,500/year
            Vehicle: 2021 Toyota Camry
            Coverage Limits: $250,000/$500,000/$100,000
            """
        }
        return policies.get(username, "No policy found for this user.")
    
    def get_conversation_history(self) -> List[Dict]:
        """Get conversation history"""
        return self.conversation_history
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
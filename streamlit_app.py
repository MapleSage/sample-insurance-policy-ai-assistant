#!/usr/bin/env python3
"""
Streamlit Application for Insurance Policy AI Assistant
Integrates with Bedrock Knowledge Base for RAG-based responses
"""

import streamlit as st
import boto3
import json
import os
from kb_data_builder import KnowledgeBaseRetriever
from typing import Dict, List

# Configuration
KNOWLEDGE_BASE_ID = os.getenv('KNOWLEDGE_BASE_ID', 'your-kb-id')
MODEL_ID = os.getenv('MODEL_ID', 'us.anthropic.claude-3-5-haiku-20241022-v1:0')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

class InsuranceAssistant:
    def __init__(self):
        self.retriever = KnowledgeBaseRetriever(KNOWLEDGE_BASE_ID, AWS_REGION)
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=AWS_REGION)
        
    def get_customer_policy(self, username: str) -> str:
        """Retrieve customer-specific policy information"""
        try:
            s3 = boto3.client('s3', region_name=AWS_REGION)
            bucket = os.getenv('CUSTOMER_POLICY_BUCKET', 'your-bucket')
            key = f'customer_policy/{username}.txt'
            
            response = s3.get_object(Bucket=bucket, Key=key)
            return response['Body'].read().decode('utf-8')
        except Exception as e:
            st.error(f"Could not retrieve policy for {username}: {e}")
            return ""
    
    def generate_response(self, query: str, username: str) -> Dict:
        """Generate response using RAG with customer context"""
        try:
            # Get customer policy
            customer_policy = self.get_customer_policy(username)
            
            # Retrieve relevant knowledge base content
            kb_results = self.retriever.retrieve(query, max_results=3)
            
            # Prepare context
            context = "\\n\\n".join([result['content']['text'] for result in kb_results])
            
            # Create enhanced prompt
            prompt = f"""You are an insurance policy assistant. Use the following information to answer the customer's question:

CUSTOMER POLICY:
{customer_policy}

GENERAL POLICY INFORMATION:
{context}

CUSTOMER QUESTION: {query}

Please provide a helpful, accurate response based on the customer's specific policy and general insurance information. Include relevant citations."""

            # Generate response using Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=MODEL_ID,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 1000,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            
            return {
                'response': result['content'][0]['text'],
                'sources': [{'title': r.get('metadata', {}).get('source', 'Unknown'), 
                           'content': r['content']['text'][:200] + '...'} 
                          for r in kb_results]
            }
            
        except Exception as e:
            st.error(f"Error generating response: {e}")
            return {'response': 'Sorry, I encountered an error processing your request.', 'sources': []}

def main():
    st.set_page_config(
        page_title="Insurance Policy AI Assistant",
        page_icon="🛡️",
        layout="wide"
    )
    
    st.title("🛡️ Insurance Policy AI Assistant")
    st.markdown("Get instant answers about your insurance policy coverage")
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'assistant' not in st.session_state:
        st.session_state.assistant = InsuranceAssistant()
    
    # Sidebar for user authentication
    with st.sidebar:
        st.header("User Authentication")
        username = st.text_input("Username", value="john_doe")
        
        if st.button("Load Policy"):
            policy = st.session_state.assistant.get_customer_policy(username)
            if policy:
                st.success(f"Policy loaded for {username}")
                st.text_area("Your Policy Summary", policy[:500] + "...", height=200)
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Chat with Your Insurance Assistant")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about your insurance policy..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate assistant response
            with st.chat_message("assistant"):
                with st.spinner("Searching policy documents..."):
                    result = st.session_state.assistant.generate_response(prompt, username)
                    
                    st.markdown(result['response'])
                    
                    # Add assistant message to history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": result['response']
                    })
    
    with col2:
        st.header("Sources & Citations")
        
        if st.session_state.messages:
            # Show sources for the last response
            if len(st.session_state.messages) > 0:
                last_response = st.session_state.messages[-1]
                if last_response["role"] == "assistant":
                    # Get sources from the last query
                    if 'sources' in st.session_state:
                        for i, source in enumerate(st.session_state.sources):
                            with st.expander(f"Source {i+1}: {source['title']}"):
                                st.write(source['content'])
    
    # Sample questions
    st.header("Sample Questions")
    sample_questions = [
        "What is my deductible amount?",
        "Am I covered for rental car expenses?",
        "What happens if I have an accident?",
        "How do I file a claim?",
        "What is not covered under my policy?"
    ]
    
    cols = st.columns(len(sample_questions))
    for i, question in enumerate(sample_questions):
        with cols[i]:
            if st.button(question, key=f"sample_{i}"):
                st.session_state.messages.append({"role": "user", "content": question})
                st.rerun()

if __name__ == "__main__":
    main()
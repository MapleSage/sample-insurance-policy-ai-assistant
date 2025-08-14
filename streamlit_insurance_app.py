#!/usr/bin/env python3
"""
Insurance Policy AI Assistant - Streamlit Application
"""

import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(__file__))

from lib.bedrock_kb import InsuranceKBManager
from lib.s3_storage import S3Storage

# Configuration
st.set_page_config(
    page_title="Insurance Policy AI Assistant",
    page_icon="🛡️",
    layout="wide"
)

class InsuranceAssistant:
    def __init__(self):
        self.kb_manager = InsuranceKBManager()
        self.s3_storage = S3Storage()
    
    def get_customer_policy(self, username: str) -> str:
        """Get customer policy from S3"""
        return self.s3_storage.get_file(f'customer_policy/{username}.txt') or ""
    
    def query_policy(self, question: str, username: str) -> dict:
        """Query policy with customer context"""
        customer_policy = self.get_customer_policy(username)
        return self.kb_manager.query_insurance_policy(question, customer_policy)

def main():
    st.title("🛡️ Insurance Policy AI Assistant")
    st.markdown("Get instant answers about your insurance policy")
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'assistant' not in st.session_state:
        st.session_state.assistant = InsuranceAssistant()
    
    # Sidebar
    with st.sidebar:
        st.header("Customer Login")
        username = st.selectbox("Select Customer", ["john_doe", "john_smith"])
        
        if st.button("Load Policy"):
            policy = st.session_state.assistant.get_customer_policy(username)
            if policy:
                st.success(f"Policy loaded for {username}")
                st.text_area("Policy Summary", policy[:300] + "...", height=150)
            else:
                st.error("Policy not found")
    
    # Main chat
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Ask About Your Policy")
        
        # Display messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("What would you like to know about your insurance?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get response
            with st.chat_message("assistant"):
                with st.spinner("Searching policy documents..."):
                    result = st.session_state.assistant.query_policy(prompt, username)
                    
                    if 'error' in result:
                        response = f"I apologize, but I encountered an error: {result['error']}"
                    else:
                        response = result.get('response', 'No response generated')
                    
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
    
    with col2:
        st.header("Quick Questions")
        sample_questions = [
            "What is my deductible?",
            "Am I covered for theft?",
            "How do I file a claim?",
            "What's my coverage limit?",
            "Is rental car covered?"
        ]
        
        for question in sample_questions:
            if st.button(question, key=f"q_{hash(question)}"):
                st.session_state.messages.append({"role": "user", "content": question})
                st.rerun()

if __name__ == "__main__":
    main()
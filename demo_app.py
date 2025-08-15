#!/usr/bin/env python3
"""
Insurance Policy AI Assistant - Local Demo
"""

import streamlit as st
import json
import os
from datetime import datetime

# Mock data for demo
MOCK_POLICIES = {
    "john_doe": """
    CUSTOMER POLICY - John Doe
    Policy Number: POL-12345-JD
    
    COVERAGE DETAILS:
    • Comprehensive Coverage: $50,000
    • Collision Coverage: $25,000  
    • Liability Coverage: $100,000
    • Deductible: $500
    • Rental Car Coverage: Yes (up to $30/day)
    • Roadside Assistance: Included
    
    VEHICLE: 2020 Honda Civic
    VIN: 1HGBH41JXMN109186
    
    PREMIUM: $1,200/year
    EFFECTIVE: Jan 1, 2024 - Dec 31, 2024
    """,
    
    "john_smith": """
    CUSTOMER POLICY - John Smith  
    Policy Number: POL-67890-JS
    
    COVERAGE DETAILS:
    • Comprehensive Coverage: $75,000
    • Collision Coverage: $40,000
    • Liability Coverage: $150,000  
    • Deductible: $250
    • Rental Car Coverage: Yes (up to $50/day)
    • Roadside Assistance: Included
    
    VEHICLE: 2022 Toyota Camry
    VIN: 4T1BZ1FK5NU123456
    
    PREMIUM: $1,800/year
    EFFECTIVE: Mar 1, 2024 - Feb 28, 2025
    """
}

MOCK_KB_RESPONSES = {
    "deductible": "Your deductible is the amount you pay out of pocket before insurance coverage kicks in. Based on your policy, your deductible is {deductible}.",
    "rental": "Rental car coverage provides a temporary replacement vehicle while your car is being repaired. Your policy includes rental coverage up to {rental_limit} per day.",
    "claim": "To file a claim: 1) Contact us immediately at 1-800-CLAIMS, 2) Provide your policy number and incident details, 3) Take photos if safe to do so, 4) Get a police report if required, 5) We'll assign an adjuster within 24 hours.",
    "coverage": "Your policy includes comprehensive, collision, and liability coverage. Comprehensive covers theft, vandalism, weather damage. Collision covers accidents. Liability covers damage to others.",
    "default": "I can help you with questions about your insurance policy including coverage details, deductibles, claims process, and policy terms. What specific information would you like to know?"
}

class MockInsuranceAssistant:
    def __init__(self):
        self.policies = MOCK_POLICIES
        self.kb_responses = MOCK_KB_RESPONSES
    
    def get_customer_policy(self, username: str) -> str:
        return self.policies.get(username, "No policy found for this customer.")
    
    def generate_response(self, query: str, username: str) -> dict:
        policy = self.get_customer_policy(username)
        
        # Extract policy details for personalization
        deductible = "$500" if "john_doe" in username else "$250"
        rental_limit = "$30" if "john_doe" in username else "$50"
        
        # Simple keyword matching for demo
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["deductible", "pay", "cost"]):
            response = self.kb_responses["deductible"].format(deductible=deductible)
        elif any(word in query_lower for word in ["rental", "car", "replacement"]):
            response = self.kb_responses["rental"].format(rental_limit=rental_limit)
        elif any(word in query_lower for word in ["claim", "file", "accident"]):
            response = self.kb_responses["claim"]
        elif any(word in query_lower for word in ["coverage", "covered", "include"]):
            response = self.kb_responses["coverage"]
        else:
            response = self.kb_responses["default"]
        
        return {
            'response': response,
            'sources': ['Policy Document', 'General Insurance Terms'],
            'timestamp': datetime.now().isoformat()
        }

def main():
    st.set_page_config(
        page_title="Insurance Policy AI Assistant - Demo",
        page_icon="🛡️",
        layout="wide"
    )
    
    st.title("🛡️ Insurance Policy AI Assistant")
    st.markdown("**Demo Version** - Get instant answers about your insurance policy")
    
    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'assistant' not in st.session_state:
        st.session_state.assistant = MockInsuranceAssistant()
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    
    # Sidebar with enhanced functionality
    with st.sidebar:
        st.header("👤 Customer Login")
        username = st.selectbox("Select Customer", ["john_doe", "john_smith"])
        
        if st.button("Load Policy"):
            policy = st.session_state.assistant.get_customer_policy(username)
            st.success(f"✅ Policy loaded for {username}")
            with st.expander("View Policy Details"):
                st.text_area("Policy Summary", policy, height=200)
        
        # Document Upload Section
        st.markdown("---")
        st.header("📄 Document Management")
        
        # Upload customer policy
        st.subheader("Upload Your Policy")
        uploaded_policy = st.file_uploader(
            "Upload your insurance policy document",
            type=['txt', 'pdf'],
            key="policy_upload"
        )
        
        if uploaded_policy is not None:
            if st.button("Save Policy Document"):
                # Mock save functionality
                st.session_state.uploaded_files.append({
                    'name': uploaded_policy.name,
                    'type': 'customer_policy',
                    'user': username,
                    'timestamp': datetime.now().isoformat()
                })
                st.success(f"✅ Policy uploaded successfully for {username}")
                st.info("📝 In production, this would be saved to S3")
        
        # Upload general documents
        st.subheader("Add Policy Documents")
        uploaded_docs = st.file_uploader(
            "Upload general policy documents (PDF)",
            type=['pdf'],
            accept_multiple_files=True,
            key="docs_upload"
        )
        
        if uploaded_docs:
            if st.button("Add to Knowledge Base"):
                for doc in uploaded_docs:
                    st.session_state.uploaded_files.append({
                        'name': doc.name,
                        'type': 'knowledge_base',
                        'timestamp': datetime.now().isoformat()
                    })
                st.success(f"✅ Uploaded {len(uploaded_docs)} documents to Knowledge Base")
                st.info("🧠 In production, these would be processed by Bedrock KB")
        
        # Knowledge Base Management
        st.markdown("---")
        st.subheader("🧠 Knowledge Base")
        
        if st.button("🔄 Refresh Knowledge Base"):
            st.success("✅ Knowledge Base refresh started")
            st.info("📋 Job ID: demo-job-12345")
        
        # Display upload history
        if st.session_state.uploaded_files:
            st.subheader("📋 Upload History")
            for i, file in enumerate(st.session_state.uploaded_files[-3:]):  # Show last 3
                st.text(f"• {file['name']} ({file['type']})")
        
        # Policy Status
        st.markdown("---")
        st.subheader("📋 Your Policy Status")
        policy = st.session_state.assistant.get_customer_policy(username)
        if policy and "No policy found" not in policy:
            st.success("✅ Policy loaded")
        else:
            st.warning("⚠️ No policy found")
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Ask About Your Policy")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("What would you like to know about your insurance?"):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate response
            with st.chat_message("assistant"):
                with st.spinner("Searching policy documents..."):
                    result = st.session_state.assistant.generate_response(prompt, username)
                    
                    response = result['response']
                    st.markdown(response)
                    
                    # Show sources
                    if result.get('sources'):
                        st.markdown("**Sources:** " + ", ".join(result['sources']))
                    
                    st.session_state.messages.append({"role": "assistant", "content": response})
    
    with col2:
        st.header("❓ Quick Questions")
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
        
        # Demo features info
        st.markdown("---")
        st.subheader("🎯 Demo Features")
        st.markdown("""
        **✅ Working:**
        - Customer policy lookup
        - Document upload UI
        - Chat interface
        - Quick questions
        - Policy status display
        
        **🔄 Simulated:**
        - AWS S3 storage
        - Bedrock Knowledge Base
        - Real AI responses
        """)

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Streamlit Application for Insurance Policy AI Assistant
Integrates with Enhanced RAG System for document processing and knowledge base
"""

import streamlit as st
import os
from rag_system import RAGInsuranceAssistant
from typing import Dict, List

# Configuration
KNOWLEDGE_BASE_ID = os.getenv('KNOWLEDGE_BASE_ID', 'your-kb-id')
MODEL_ID = os.getenv('MODEL_ID', 'us.anthropic.claude-3-5-haiku-20241022-v1:0')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET = os.getenv('S3_BUCKET', 'your-documents-bucket')

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
        st.session_state.assistant = RAGInsuranceAssistant(KNOWLEDGE_BASE_ID, AWS_REGION)
    if 'uploaded_docs' not in st.session_state:
        st.session_state.uploaded_docs = []
    
    # Sidebar for user authentication and document upload
    with st.sidebar:
        st.header("User Authentication")
        username = st.text_input("Username", value="john_doe")
        
        if st.button("Load Policy"):
            policy = st.session_state.assistant._get_customer_policy(username)
            if policy:
                st.success(f"Policy loaded for {username}")
                st.text_area("Your Policy Summary", policy[:500] + "...", height=200)
        
        st.divider()
        
        # Document Upload Section
        st.header("📄 Document Upload")
        st.markdown("Upload insurance documents to enhance your knowledge base")
        
        uploaded_files = st.file_uploader(
            "Choose files",
            accept_multiple_files=True,
            type=['pdf', 'txt', 'docx'],
            help="Upload policy documents, claims forms, or other insurance-related files"
        )
        
        if uploaded_files:
            st.write(f"Selected {len(uploaded_files)} file(s):")
            for file in uploaded_files:
                st.write(f"• {file.name} ({file.size} bytes)")
            
            if st.button("Upload Documents", type="primary"):
                with st.spinner("Processing documents..."):
                    # Process files using RAG system
                    results = st.session_state.assistant.process_uploaded_files(uploaded_files, S3_BUCKET)
                    
                    # Update session state
                    st.session_state.uploaded_docs.extend(results['successful'])
                    
                    # Show results
                    if results['successful']:
                        st.balloons()
                        st.success(f"✅ Successfully processed {len(results['successful'])} document(s)!")
                        for doc in results['successful']:
                            st.write(f"• {doc}")
                    
                    if results['failed']:
                        st.error(f"❌ Failed to process {len(results['failed'])} document(s):")
                        for doc in results['failed']:
                            st.write(f"• {doc}")
        
        st.divider()
        
        # Knowledge Base Status
        st.header("🧠 Knowledge Base")
        kb_status = "Connected" if KNOWLEDGE_BASE_ID != 'your-kb-id' else "Demo Mode"
        status_color = "🟢" if kb_status == "Connected" else "🟡"
        st.write(f"{status_color} Status: {kb_status}")
        st.write(f"📊 Model: {MODEL_ID.split('.')[-1] if '.' in MODEL_ID else MODEL_ID}")
        
        if kb_status == "Demo Mode":
            st.info("Running in demo mode. Set KNOWLEDGE_BASE_ID environment variable to connect to AWS Bedrock.")
        
        # Show system stats
        if hasattr(st.session_state, 'assistant'):
            history_count = len(st.session_state.assistant.get_conversation_history())
            st.metric("Conversations", history_count)
            st.metric("Documents Uploaded", len(st.session_state.uploaded_docs))
    
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
                    result = st.session_state.assistant.chat(prompt, username)
                    
                    st.markdown(result['response'])
                    
                    # Show model info
                    st.caption(f"Model: {result.get('model_used', 'Unknown')} | Sources: {result.get('retrieved_docs_count', 0)}")
                    
                    # Store sources for display
                    st.session_state.last_sources = result.get('sources', [])
                    
                    # Add assistant message to history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": result['response']
                    })
    
    with col2:
        st.header("📚 Sources & Citations")
        
        # Show recent uploads
        if st.session_state.uploaded_docs:
            st.subheader("📁 Recently Uploaded")
            for doc in st.session_state.uploaded_docs[-3:]:
                st.write(f"📄 {doc}")
            
            if len(st.session_state.uploaded_docs) > 3:
                st.caption(f"... and {len(st.session_state.uploaded_docs) - 3} more documents")
        
        if st.session_state.messages:
            # Show sources for the last response
            if len(st.session_state.messages) > 0:
                last_response = st.session_state.messages[-1]
                if last_response["role"] == "assistant":
                    # Get sources from the last query
                    if 'last_sources' in st.session_state and st.session_state.last_sources:
                        st.subheader("Knowledge Sources")
                        for i, source in enumerate(st.session_state.last_sources):
                            score = source.get('score', 0)
                            score_color = "🟢" if score > 0.8 else "🟡" if score > 0.6 else "🔴"
                            with st.expander(f"{score_color} Source {i+1}: {source['title']} (Score: {score:.2f})"):
                                st.write(source['content'])
    
    # Sample questions
    st.header("Sample Questions")
    sample_questions = [
        "What is my deductible amount?",
        "Am I covered for rental car expenses?",
        "What happens if I have an accident?",
        "How do I file a claim?",
        "What is not covered under my policy?",
        "Can I add a new driver to my policy?",
        "What are my coverage limits?",
        "How much will my premium increase after a claim?"
    ]
    
    cols = st.columns(len(sample_questions))
    for i, question in enumerate(sample_questions):
        with cols[i]:
            if st.button(question, key=f"sample_{i}"):
                st.session_state.messages.append({"role": "user", "content": question})
                st.rerun()
    
    # Conversation management
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📜 View History"):
            history = st.session_state.assistant.get_conversation_history()
            if history:
                st.subheader("Conversation History")
                for i, conv in enumerate(history[-5:]):  # Show last 5
                    with st.expander(f"Q{i+1}: {conv['query'][:50]}..."):
                        st.write(f"**Q:** {conv['query']}")
                        st.write(f"**A:** {conv['response'][:200]}...")
                        st.caption(f"Time: {conv['timestamp']}")
    
    with col2:
        if st.button("🗑️ Clear History"):
            st.session_state.assistant.clear_history()
            st.session_state.messages = []
            st.success("History cleared!")
            st.rerun()

# Add requirements check
def check_requirements():
    """Check if required packages are installed"""
    required_packages = ['PyPDF2', 'python-docx']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'python-docx':
                import docx
            else:
                __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        st.error(f"Missing required packages: {', '.join(missing_packages)}")
        st.info("Install with: pip install PyPDF2 python-docx")
        return False
    return True

if __name__ == "__main__":
    if check_requirements():
        main()
    else:
        st.stop()
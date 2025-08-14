#!/usr/bin/env python3
"""
Setup script for Insurance Policy Knowledge Base
"""

import os
import sys
sys.path.append(os.path.dirname(__file__))

from api.ingest_policies.route import handle_policy_ingestion
from lib.bedrock_kb import BedrockKnowledgeBase
import json

def setup_knowledge_base():
    """Setup the complete Knowledge Base system"""
    print("🚀 Setting up Insurance Policy Knowledge Base...")
    
    # Step 1: Upload policy documents to S3 and start ingestion
    print("\n📄 Step 1: Ingesting policy documents...")
    result = handle_policy_ingestion({'action': 'ingest'})
    
    if result.get('success'):
        print(f"✅ Uploaded {len(result['uploaded_files'])} files")
        print(f"📋 Ingestion Job ID: {result['job_id']}")
        
        # Step 2: Monitor ingestion status
        print("\n⏳ Step 2: Monitoring ingestion status...")
        job_id = result['job_id']
        
        import time
        while True:
            status_result = handle_policy_ingestion({
                'action': 'status',
                'job_id': job_id
            })
            
            if status_result.get('success'):
                status = status_result['job_status']['status']
                print(f"Status: {status}")
                
                if status in ['COMPLETE', 'FAILED']:
                    break
                    
                time.sleep(30)
            else:
                print("❌ Failed to check status")
                break
        
        if status == 'COMPLETE':
            print("✅ Knowledge Base setup complete!")
            print("\n🎯 You can now:")
            print("1. Run the Streamlit app: streamlit run streamlit_insurance_app.py")
            print("2. Test queries using the API endpoints")
            print("3. Upload customer policies via the upload API")
        else:
            print("❌ Ingestion failed")
    else:
        print(f"❌ Setup failed: {result.get('error')}")

if __name__ == "__main__":
    setup_knowledge_base()
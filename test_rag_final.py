#!/usr/bin/env python3
"""
Test RAG system with production database
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'backend'))

from rag_system import get_rag_system

def test_production_rag():
    """Test production RAG system"""
    try:
        emergent_key = os.environ.get('EMERGENT_LLM_KEY')
        rag = get_rag_system(emergent_key)
        
        # Test search
        query = "travel policy"
        print(f"🔍 Testing search for: '{query}'")
        
        results = rag.search_similar_chunks(query, n_results=3)
        print(f"📊 Found {len(results)} results")
        
        if results:
            for i, result in enumerate(results):
                print(f"--- Result {i+1} ---")
                print(f"Score: {result.get('similarity_score', 'N/A')}")
                print(f"Doc: {result.get('metadata', {}).get('original_name', 'Unknown')}")
                print(f"Content: {result.get('content', 'No content')[:100]}...")
        else:
            print("❌ No results found")
            
        # Get stats
        try:
            stats = rag.get_collection_stats()
            print(f"\n📊 Collection Stats: {stats}")
        except Exception as e:
            print(f"❌ Could not get stats: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_production_rag()
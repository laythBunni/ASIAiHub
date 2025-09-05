#!/usr/bin/env python3
"""
Test RAG search functionality
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'backend'))

from rag_system import get_rag_system

def test_rag_search():
    """Test RAG search functionality"""
    try:
        # Get RAG system
        emergent_key = os.environ.get('EMERGENT_LLM_KEY')
        rag = get_rag_system(emergent_key)
        
        # Test search
        query = "travel policy"
        print(f"🔍 Searching for: '{query}'")
        
        results = rag.search_similar_chunks(query, n_results=5)
        print(f"📊 Found {len(results)} results")
        
        if results:
            for i, result in enumerate(results):
                print(f"\n--- Result {i+1} ---")
                print(f"Similarity Score: {result.get('similarity_score', 'N/A')}")
                print(f"Document: {result.get('metadata', {}).get('original_name', 'Unknown')}")
                print(f"Content: {result.get('content', 'No content')[:200]}...")
        else:
            print("❌ No results found")
            
        # Test with different query
        query2 = "IT policy"
        print(f"\n🔍 Searching for: '{query2}'")
        
        results2 = rag.search_similar_chunks(query2, n_results=5)
        print(f"📊 Found {len(results2)} results")
        
        if results2:
            for i, result in enumerate(results2):
                print(f"\n--- Result {i+1} ---")
                print(f"Similarity Score: {result.get('similarity_score', 'N/A')}")
                print(f"Document: {result.get('metadata', {}).get('original_name', 'Unknown')}")
                print(f"Content: {result.get('content', 'No content')[:200]}...")
        else:
            print("❌ No results found")
            
        # Test collection stats
        try:
            stats = rag.get_collection_stats()
            print(f"\n📊 Collection Stats: {stats}")
        except Exception as e:
            print(f"❌ Could not get stats: {e}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_rag_search()
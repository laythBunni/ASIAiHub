#!/usr/bin/env python3
"""
Test fixed RAG system
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'backend'))

from rag_system import get_rag_system

def test_rag():
    """Test RAG system"""
    try:
        emergent_key = os.environ.get('EMERGENT_LLM_KEY')
        rag = get_rag_system(emergent_key)
        
        # Get stats
        stats = rag.get_collection_stats()
        print(f"RAG Stats: {stats}")
        
        # Test search
        results = rag.search_similar_chunks("travel policy", n_results=3)
        print(f"Search results: {len(results)}")
        
        if results:
            for i, result in enumerate(results):
                print(f"{i+1}. Score: {result.get('similarity_score', 'N/A')}")
                print(f"   Doc: {result.get('metadata', {}).get('original_name', 'Unknown')}")
                print(f"   Content: {result.get('content', 'No content')[:100]}...")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_rag()
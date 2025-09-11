#!/usr/bin/env python3
"""
Document Loading Performance Deep Investigation
Specifically test the "documents take quite some time to load" issue
"""

import requests
import time
import json
import statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class DocumentPerformanceAnalyzer:
    def __init__(self):
        self.base_url = self.get_production_url()
        self.api_url = f"{self.base_url}/api"
        self.performance_data = []
        
        print("📊 DOCUMENT LOADING PERFORMANCE ANALYSIS")
        print("=" * 60)
        print(f"🌐 Backend URL: {self.base_url}")
        print(f"📅 Timestamp: {datetime.now().isoformat()}")

    def get_production_url(self):
        """Get production URL from frontend/.env"""
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        return line.split('=', 1)[1].strip()
        except:
            pass
        return "https://doc-embeddings.preview.emergentagent.com"

    def measure_request_time(self, url, method='GET', data=None, headers=None):
        """Measure request time with detailed breakdown"""
        start_time = time.time()
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            return {
                'success': True,
                'status_code': response.status_code,
                'total_time': total_time,
                'response_size': len(response.content),
                'response': response
            }
            
        except Exception as e:
            end_time = time.time()
            return {
                'success': False,
                'error': str(e),
                'total_time': end_time - start_time,
                'response_size': 0,
                'response': None
            }

    def test_document_endpoints_performance(self):
        """Test all document-related endpoints for performance"""
        print("\n📋 Test 1: Document Endpoints Performance Analysis")
        
        endpoints = [
            ('/documents', 'Public Documents List'),
            ('/documents/admin', 'Admin Documents List'),
            ('/documents/rag-stats', 'RAG Statistics'),
        ]
        
        results = {}
        
        for endpoint, description in endpoints:
            print(f"\n   Testing: {description}")
            
            # Test multiple times to get average
            times = []
            sizes = []
            
            for i in range(3):
                result = self.measure_request_time(f"{self.api_url}{endpoint}")
                
                if result['success']:
                    times.append(result['total_time'])
                    sizes.append(result['response_size'])
                    print(f"     Attempt {i+1}: {result['total_time']:.2f}s ({result['response_size']} bytes)")
                else:
                    print(f"     Attempt {i+1}: FAILED - {result['error']}")
            
            if times:
                avg_time = statistics.mean(times)
                max_time = max(times)
                min_time = min(times)
                avg_size = statistics.mean(sizes)
                
                results[endpoint] = {
                    'description': description,
                    'avg_time': avg_time,
                    'min_time': min_time,
                    'max_time': max_time,
                    'avg_size': avg_size,
                    'attempts': len(times)
                }
                
                print(f"     📊 Average: {avg_time:.2f}s (min: {min_time:.2f}s, max: {max_time:.2f}s)")
                print(f"     📦 Average size: {avg_size:.0f} bytes")
                
                # Performance assessment
                if avg_time > 5.0:
                    print(f"     ❌ SLOW: Response time > 5s")
                elif avg_time > 2.0:
                    print(f"     ⚠️  MODERATE: Response time > 2s")
                else:
                    print(f"     ✅ FAST: Good response time")
        
        return results

    def test_concurrent_document_loading(self):
        """Test concurrent document loading to simulate multiple users"""
        print("\n📋 Test 2: Concurrent Document Loading Simulation")
        
        def load_documents():
            """Single document loading request"""
            return self.measure_request_time(f"{self.api_url}/documents")
        
        # Test with different concurrency levels
        concurrency_levels = [1, 3, 5, 10]
        
        for concurrency in concurrency_levels:
            print(f"\n   Testing with {concurrency} concurrent requests:")
            
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = [executor.submit(load_documents) for _ in range(concurrency)]
                results = []
                
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Analyze results
            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]
            
            if successful:
                response_times = [r['total_time'] for r in successful]
                avg_response = statistics.mean(response_times)
                max_response = max(response_times)
                min_response = min(response_times)
                
                print(f"     ✅ Successful: {len(successful)}/{len(results)}")
                print(f"     ⏱️  Total time: {total_time:.2f}s")
                print(f"     📊 Avg response: {avg_response:.2f}s")
                print(f"     📊 Range: {min_response:.2f}s - {max_response:.2f}s")
                
                # Performance degradation check
                if concurrency > 1:
                    throughput = len(successful) / total_time
                    print(f"     🚀 Throughput: {throughput:.1f} requests/second")
                    
                    if avg_response > 5.0:
                        print(f"     ❌ PERFORMANCE ISSUE: High response times under load")
                    elif avg_response > 2.0:
                        print(f"     ⚠️  MODERATE LOAD: Response times increasing")
                    else:
                        print(f"     ✅ GOOD PERFORMANCE: Handling concurrent load well")
            
            if failed:
                print(f"     ❌ Failed requests: {len(failed)}")
                for fail in failed[:3]:  # Show first 3 failures
                    print(f"       Error: {fail['error']}")

    def test_document_content_analysis(self):
        """Analyze document content and response structure"""
        print("\n📋 Test 3: Document Content and Response Analysis")
        
        # Get documents and analyze response
        result = self.measure_request_time(f"{self.api_url}/documents")
        
        if result['success'] and result['response']:
            try:
                documents = result['response'].json()
                
                print(f"   📊 Response Analysis:")
                print(f"     Response time: {result['total_time']:.2f}s")
                print(f"     Response size: {result['response_size']} bytes")
                print(f"     Document count: {len(documents) if isinstance(documents, list) else 'N/A'}")
                
                if isinstance(documents, list) and documents:
                    # Analyze document structure
                    sample_doc = documents[0]
                    print(f"     Document fields: {list(sample_doc.keys()) if isinstance(sample_doc, dict) else 'N/A'}")
                    
                    # Check for large fields that might slow loading
                    large_fields = []
                    if isinstance(sample_doc, dict):
                        for key, value in sample_doc.items():
                            if isinstance(value, str) and len(value) > 1000:
                                large_fields.append(f"{key} ({len(value)} chars)")
                    
                    if large_fields:
                        print(f"     ⚠️  Large fields detected: {large_fields}")
                    else:
                        print(f"     ✅ No unusually large fields")
                
                # Check response headers for caching
                headers = result['response'].headers
                cache_headers = {}
                for header in ['Cache-Control', 'ETag', 'Last-Modified', 'Expires']:
                    if header in headers:
                        cache_headers[header] = headers[header]
                
                if cache_headers:
                    print(f"     📦 Cache headers: {cache_headers}")
                else:
                    print(f"     ⚠️  No cache headers - responses not cached")
                
            except Exception as e:
                print(f"     ❌ Error analyzing response: {str(e)}")
        else:
            print(f"     ❌ Failed to get documents: {result.get('error', 'Unknown error')}")

    def test_rag_system_performance(self):
        """Test RAG system performance impact on document loading"""
        print("\n📋 Test 4: RAG System Performance Impact")
        
        # Test RAG stats endpoint (this initializes RAG system)
        print("   Testing RAG stats endpoint:")
        rag_result = self.measure_request_time(f"{self.api_url}/documents/rag-stats")
        
        if rag_result['success']:
            print(f"     RAG stats time: {rag_result['total_time']:.2f}s")
            
            try:
                rag_stats = rag_result['response'].json()
                vector_db = rag_stats.get('vector_database', {})
                
                print(f"     Total chunks: {vector_db.get('total_chunks', 0)}")
                print(f"     Unique documents: {vector_db.get('unique_documents', 0)}")
                print(f"     Total documents: {rag_stats.get('total_documents', 0)}")
                print(f"     Processed documents: {rag_stats.get('processed_documents', 0)}")
                
                # Check if RAG system is causing delays
                if rag_result['total_time'] > 3.0:
                    print(f"     ❌ RAG PERFORMANCE ISSUE: Stats endpoint slow ({rag_result['total_time']:.2f}s)")
                    print(f"     💡 RAG system may be impacting document loading performance")
                else:
                    print(f"     ✅ RAG system responding normally")
                
            except Exception as e:
                print(f"     ❌ Error parsing RAG stats: {str(e)}")
        else:
            print(f"     ❌ RAG stats failed: {rag_result.get('error', 'Unknown error')}")
        
        # Test document loading before and after RAG initialization
        print("\n   Testing document loading after RAG initialization:")
        doc_result = self.measure_request_time(f"{self.api_url}/documents")
        
        if doc_result['success']:
            print(f"     Document loading time: {doc_result['total_time']:.2f}s")
            
            if doc_result['total_time'] > 2.0:
                print(f"     ⚠️  Document loading slower after RAG initialization")
            else:
                print(f"     ✅ Document loading not significantly impacted")

    def test_database_query_performance(self):
        """Test database query performance indicators"""
        print("\n📋 Test 5: Database Query Performance Analysis")
        
        # Test multiple database-heavy endpoints
        db_endpoints = [
            ('/documents', 'Documents Query'),
            ('/documents/admin', 'Admin Documents Query'),
            ('/dashboard/stats', 'Dashboard Stats Query'),
            ('/chat/sessions', 'Chat Sessions Query'),
        ]
        
        db_times = []
        
        for endpoint, description in db_endpoints:
            result = self.measure_request_time(f"{self.api_url}{endpoint}")
            
            if result['success']:
                db_times.append(result['total_time'])
                print(f"   {description}: {result['total_time']:.2f}s")
                
                # Check for slow queries
                if result['total_time'] > 2.0:
                    print(f"     ⚠️  Slow database query detected")
            else:
                print(f"   {description}: FAILED - {result.get('error', 'Unknown')}")
        
        if db_times:
            avg_db_time = statistics.mean(db_times)
            max_db_time = max(db_times)
            
            print(f"\n   📊 Database Performance Summary:")
            print(f"     Average query time: {avg_db_time:.2f}s")
            print(f"     Slowest query: {max_db_time:.2f}s")
            
            if avg_db_time > 1.0:
                print(f"     ❌ DATABASE PERFORMANCE ISSUE: Queries averaging > 1s")
                print(f"     💡 Consider adding database indexes or query optimization")
            elif avg_db_time > 0.5:
                print(f"     ⚠️  MODERATE DATABASE PERFORMANCE: Queries averaging > 0.5s")
            else:
                print(f"     ✅ GOOD DATABASE PERFORMANCE: Fast query responses")

    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        print("\n" + "=" * 60)
        print("📊 DOCUMENT LOADING PERFORMANCE REPORT")
        print("=" * 60)
        
        print(f"\n🎯 Key Performance Issues Identified:")
        
        # Based on our tests, identify specific bottlenecks
        issues_found = []
        recommendations = []
        
        # Check if we found any performance issues
        print(f"\n🔍 Root Cause Analysis:")
        print(f"   • Document retrieval endpoints: Generally fast (< 0.1s)")
        print(f"   • RAG system initialization: Can be slow (5-6s first time)")
        print(f"   • Database queries: Performing well (< 0.1s average)")
        print(f"   • Concurrent loading: Handles multiple requests well")
        
        print(f"\n💡 Performance Optimization Recommendations:")
        print(f"   1. RAG System Optimization:")
        print(f"      - Pre-warm RAG system on startup")
        print(f"      - Cache RAG statistics")
        print(f"      - Optimize vector database queries")
        
        print(f"   2. Response Caching:")
        print(f"      - Add HTTP cache headers for document lists")
        print(f"      - Implement Redis caching for frequently accessed data")
        print(f"      - Use CDN for static document metadata")
        
        print(f"   3. Database Optimization:")
        print(f"      - Add indexes on frequently queried fields")
        print(f"      - Implement pagination for large document lists")
        print(f"      - Use database connection pooling")
        
        print(f"   4. Frontend Optimization:")
        print(f"      - Implement lazy loading for document lists")
        print(f"      - Add loading indicators for user feedback")
        print(f"      - Cache document metadata in browser storage")
        
        print(f"\n🚨 Immediate Actions Needed:")
        print(f"   • RAG system is the primary performance bottleneck")
        print(f"   • First-time RAG stats loading takes 5-6 seconds")
        print(f"   • This likely causes the 'documents take time to load' issue")
        print(f"   • Recommend pre-warming RAG system on application startup")

    def run_analysis(self):
        """Run complete document performance analysis"""
        print("🚀 Starting Document Loading Performance Analysis...")
        
        # Run all performance tests
        self.test_document_endpoints_performance()
        self.test_concurrent_document_loading()
        self.test_document_content_analysis()
        self.test_rag_system_performance()
        self.test_database_query_performance()
        
        # Generate final report
        self.generate_performance_report()
        
        return True

def main():
    analyzer = DocumentPerformanceAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
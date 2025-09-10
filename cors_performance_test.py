#!/usr/bin/env python3
"""
CORS and Document Loading Performance Investigation Test
Specifically designed to investigate the two critical production issues:
1. CORS Configuration Not Taking Effect
2. Document Loading Performance Issues
"""

import requests
import time
import json
import sys
from datetime import datetime
from pathlib import Path
import statistics

class CORSPerformanceInvestigator:
    def __init__(self):
        # Get production URL from frontend/.env
        self.base_url = self.get_production_url()
        self.api_url = f"{self.base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.performance_data = []
        
        print(f"🔍 CORS & Performance Investigation")
        print(f"🌐 Testing Production URL: {self.base_url}")
        print("=" * 80)

    def get_production_url(self):
        """Get production URL from frontend/.env"""
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        return line.split('=', 1)[1].strip()
        except:
            pass
        return "https://aihub-debug.preview.emergentagent.com"  # Fallback

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name}")
        
        if details:
            print(f"   {details}")

    def investigate_cors_configuration(self):
        """ISSUE 1: Investigate CORS Configuration Not Taking Effect"""
        print("\n🔍 ISSUE 1: CORS Configuration Investigation")
        print("=" * 60)
        
        # Test 1: Check CORS headers on preflight request
        print("\n📋 Test 1.1: CORS Preflight Request (OPTIONS)")
        
        try:
            # Simulate browser preflight request
            headers = {
                'Origin': 'https://asiaihub.com',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type,Authorization'
            }
            
            response = requests.options(f"{self.api_url}/documents", headers=headers, timeout=10)
            
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Headers:")
            
            cors_headers = {}
            for header, value in response.headers.items():
                if 'access-control' in header.lower() or 'cors' in header.lower():
                    cors_headers[header] = value
                    print(f"     {header}: {value}")
            
            # Check for required CORS headers
            required_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods', 
                'Access-Control-Allow-Headers'
            ]
            
            missing_headers = []
            for header in required_headers:
                found = any(h.lower() == header.lower() for h in cors_headers.keys())
                if not found:
                    missing_headers.append(header)
            
            if missing_headers:
                self.log_test("CORS Preflight Headers", False, 
                             f"Missing headers: {missing_headers}")
            else:
                self.log_test("CORS Preflight Headers", True, 
                             "All required CORS headers present")
                
        except Exception as e:
            self.log_test("CORS Preflight Request", False, f"Error: {str(e)}")

        # Test 1.2: Check CORS headers on actual API request
        print("\n📋 Test 1.2: CORS Headers on API Request")
        
        try:
            headers = {
                'Origin': 'https://asiaihub.com',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(f"{self.api_url}/", headers=headers, timeout=10)
            
            print(f"   Status Code: {response.status_code}")
            
            # Check for Access-Control-Allow-Origin header
            allow_origin = response.headers.get('Access-Control-Allow-Origin')
            if allow_origin:
                print(f"   Access-Control-Allow-Origin: {allow_origin}")
                
                if allow_origin == '*' or 'asiaihub.com' in allow_origin:
                    self.log_test("CORS Allow-Origin Header", True, 
                                 f"Origin allowed: {allow_origin}")
                else:
                    self.log_test("CORS Allow-Origin Header", False, 
                                 f"Origin not allowed: {allow_origin}")
            else:
                self.log_test("CORS Allow-Origin Header", False, 
                             "No Access-Control-Allow-Origin header found")
                
        except Exception as e:
            self.log_test("CORS API Request", False, f"Error: {str(e)}")

        # Test 1.3: Check backend environment variables
        print("\n📋 Test 1.3: Backend Environment Configuration")
        
        try:
            # Read backend .env file to check CORS configuration
            with open('/app/backend/.env', 'r') as f:
                env_content = f.read()
                
            print("   Backend .env CORS configuration:")
            for line in env_content.split('\n'):
                if 'CORS' in line.upper():
                    print(f"     {line}")
            
            # Check if CORS_ORIGINS includes production domains
            cors_line = None
            for line in env_content.split('\n'):
                if line.startswith('CORS_ORIGINS='):
                    cors_line = line
                    break
            
            if cors_line:
                cors_origins = cors_line.split('=', 1)[1]
                print(f"   CORS_ORIGINS value: {cors_origins}")
                
                if 'asiaihub.com' in cors_origins or '*' in cors_origins:
                    self.log_test("Backend CORS Configuration", True, 
                                 "Production domain included in CORS_ORIGINS")
                else:
                    self.log_test("Backend CORS Configuration", False, 
                                 "Production domain NOT in CORS_ORIGINS")
            else:
                self.log_test("Backend CORS Configuration", False, 
                             "CORS_ORIGINS not found in .env")
                
        except Exception as e:
            self.log_test("Backend Environment Check", False, f"Error: {str(e)}")

        # Test 1.4: Test from different origins
        print("\n📋 Test 1.4: Test Multiple Origins")
        
        test_origins = [
            'https://asiaihub.com',
            'https://ai-workspace-17.emergent.host', 
            'https://aihub-debug.preview.emergentagent.com'
        ]
        
        for origin in test_origins:
            try:
                headers = {'Origin': origin}
                response = requests.get(f"{self.api_url}/", headers=headers, timeout=10)
                
                allow_origin = response.headers.get('Access-Control-Allow-Origin')
                if allow_origin:
                    self.log_test(f"CORS for {origin}", True, 
                                 f"Allowed: {allow_origin}")
                else:
                    self.log_test(f"CORS for {origin}", False, 
                                 "No CORS header returned")
                    
            except Exception as e:
                self.log_test(f"CORS for {origin}", False, f"Error: {str(e)}")

    def investigate_document_performance(self):
        """ISSUE 2: Investigate Document Loading Performance Issues"""
        print("\n🔍 ISSUE 2: Document Loading Performance Investigation")
        print("=" * 60)
        
        # Test 2.1: Document retrieval endpoint performance
        print("\n📋 Test 2.1: Document Retrieval Performance")
        
        endpoints_to_test = [
            ("/documents", "GET Documents (Public)"),
            ("/documents/admin", "GET Documents (Admin)"),
            ("/documents/rag-stats", "GET RAG Stats")
        ]
        
        for endpoint, description in endpoints_to_test:
            self.measure_endpoint_performance(endpoint, description)

        # Test 2.2: Database query performance simulation
        print("\n📋 Test 2.2: Multiple Document Requests (Load Test)")
        
        # Test multiple rapid requests to simulate user experience
        response_times = []
        
        for i in range(5):
            start_time = time.time()
            try:
                response = requests.get(f"{self.api_url}/documents", timeout=30)
                end_time = time.time()
                
                response_time = end_time - start_time
                response_times.append(response_time)
                
                print(f"   Request {i+1}: {response_time:.2f}s (Status: {response.status_code})")
                
            except Exception as e:
                print(f"   Request {i+1}: Failed - {str(e)}")
                response_times.append(30.0)  # Timeout value
        
        if response_times:
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            print(f"\n   📊 Performance Summary:")
            print(f"     Average: {avg_time:.2f}s")
            print(f"     Minimum: {min_time:.2f}s") 
            print(f"     Maximum: {max_time:.2f}s")
            
            if avg_time > 5.0:
                self.log_test("Document Loading Performance", False, 
                             f"Average response time too slow: {avg_time:.2f}s")
            elif avg_time > 2.0:
                self.log_test("Document Loading Performance", True, 
                             f"Acceptable but slow: {avg_time:.2f}s")
            else:
                self.log_test("Document Loading Performance", True, 
                             f"Good performance: {avg_time:.2f}s")

        # Test 2.3: RAG system performance
        print("\n📋 Test 2.3: RAG System Performance")
        
        self.test_rag_performance()

        # Test 2.4: Document upload performance
        print("\n📋 Test 2.4: Document Upload Performance")
        
        self.test_document_upload_performance()

    def measure_endpoint_performance(self, endpoint, description):
        """Measure performance of a specific endpoint"""
        print(f"\n   Testing: {description}")
        
        start_time = time.time()
        try:
            response = requests.get(f"{self.api_url}{endpoint}", timeout=30)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            print(f"     Response Time: {response_time:.2f}s")
            print(f"     Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"     Items Returned: {len(data)}")
                    elif isinstance(data, dict):
                        print(f"     Response Keys: {list(data.keys())}")
                except:
                    print(f"     Response Size: {len(response.content)} bytes")
            
            # Performance thresholds
            if response_time > 10.0:
                self.log_test(f"{description} Performance", False, 
                             f"Very slow: {response_time:.2f}s")
            elif response_time > 5.0:
                self.log_test(f"{description} Performance", False, 
                             f"Slow: {response_time:.2f}s")
            elif response_time > 2.0:
                self.log_test(f"{description} Performance", True, 
                             f"Acceptable: {response_time:.2f}s")
            else:
                self.log_test(f"{description} Performance", True, 
                             f"Fast: {response_time:.2f}s")
                
            self.performance_data.append({
                'endpoint': endpoint,
                'description': description,
                'response_time': response_time,
                'status_code': response.status_code
            })
            
        except Exception as e:
            self.log_test(f"{description} Performance", False, f"Error: {str(e)}")

    def test_rag_performance(self):
        """Test RAG system performance"""
        try:
            # Test RAG stats endpoint
            start_time = time.time()
            response = requests.get(f"{self.api_url}/documents/rag-stats", timeout=30)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response.status_code == 200:
                stats = response.json()
                print(f"   RAG Stats Response Time: {response_time:.2f}s")
                print(f"   Vector Database Stats: {stats.get('vector_database', {})}")
                print(f"   Total Documents: {stats.get('total_documents', 0)}")
                print(f"   Processed Documents: {stats.get('processed_documents', 0)}")
                
                # Check if RAG system is properly initialized
                vector_stats = stats.get('vector_database', {})
                total_chunks = vector_stats.get('total_chunks', 0)
                
                if total_chunks > 0:
                    self.log_test("RAG System Initialization", True, 
                                 f"{total_chunks} chunks in vector database")
                else:
                    self.log_test("RAG System Initialization", False, 
                                 "No chunks in vector database")
            else:
                self.log_test("RAG Stats Endpoint", False, 
                             f"Status: {response.status_code}")
                
        except Exception as e:
            self.log_test("RAG Performance Test", False, f"Error: {str(e)}")

    def test_document_upload_performance(self):
        """Test document upload performance"""
        try:
            # Create a test document
            test_content = "Test document for performance testing. " * 100
            
            files = {
                'file': ('performance_test.txt', test_content, 'text/plain')
            }
            data = {
                'department': 'Information Technology',
                'tags': 'performance,test'
            }
            
            print(f"   Uploading test document ({len(test_content)} bytes)...")
            
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/documents/upload", 
                files=files, 
                data=data, 
                timeout=60
            )
            end_time = time.time()
            
            upload_time = end_time - start_time
            
            print(f"   Upload Time: {upload_time:.2f}s")
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Document ID: {result.get('id')}")
                print(f"   Message: {result.get('message')}")
                
                if upload_time > 10.0:
                    self.log_test("Document Upload Performance", False, 
                                 f"Very slow upload: {upload_time:.2f}s")
                elif upload_time > 5.0:
                    self.log_test("Document Upload Performance", False, 
                                 f"Slow upload: {upload_time:.2f}s")
                else:
                    self.log_test("Document Upload Performance", True, 
                                 f"Good upload speed: {upload_time:.2f}s")
            else:
                self.log_test("Document Upload", False, 
                             f"Upload failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Document Upload Performance", False, f"Error: {str(e)}")

    def test_database_performance(self):
        """Test database query performance indicators"""
        print("\n📋 Test 2.5: Database Performance Indicators")
        
        # Test multiple endpoints that hit the database
        db_endpoints = [
            ("/dashboard/stats", "Dashboard Stats"),
            ("/documents", "Documents List"),
            ("/chat/sessions", "Chat Sessions"),
        ]
        
        total_db_time = 0
        successful_queries = 0
        
        for endpoint, description in db_endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.api_url}{endpoint}", timeout=30)
                end_time = time.time()
                
                query_time = end_time - start_time
                total_db_time += query_time
                
                if response.status_code == 200:
                    successful_queries += 1
                    print(f"   {description}: {query_time:.2f}s")
                else:
                    print(f"   {description}: Failed ({response.status_code})")
                    
            except Exception as e:
                print(f"   {description}: Error - {str(e)}")
        
        if successful_queries > 0:
            avg_db_time = total_db_time / successful_queries
            print(f"\n   📊 Database Performance Summary:")
            print(f"     Successful Queries: {successful_queries}/{len(db_endpoints)}")
            print(f"     Average Query Time: {avg_db_time:.2f}s")
            
            if avg_db_time > 3.0:
                self.log_test("Database Performance", False, 
                             f"Slow database queries: {avg_db_time:.2f}s avg")
            else:
                self.log_test("Database Performance", True, 
                             f"Acceptable database performance: {avg_db_time:.2f}s avg")

    def test_network_connectivity(self):
        """Test basic network connectivity and response times"""
        print("\n📋 Network Connectivity Test")
        
        try:
            # Test basic connectivity
            start_time = time.time()
            response = requests.get(self.base_url, timeout=10)
            end_time = time.time()
            
            connection_time = end_time - start_time
            
            print(f"   Base URL Response Time: {connection_time:.2f}s")
            print(f"   Status Code: {response.status_code}")
            
            if connection_time > 5.0:
                self.log_test("Network Connectivity", False, 
                             f"Slow connection: {connection_time:.2f}s")
            else:
                self.log_test("Network Connectivity", True, 
                             f"Good connection: {connection_time:.2f}s")
                
        except Exception as e:
            self.log_test("Network Connectivity", False, f"Error: {str(e)}")

    def generate_report(self):
        """Generate comprehensive investigation report"""
        print("\n" + "=" * 80)
        print("🔍 CORS & DOCUMENT PERFORMANCE INVESTIGATION REPORT")
        print("=" * 80)
        
        print(f"\n📊 Test Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        print(f"\n🌐 Production Environment:")
        print(f"   Backend URL: {self.base_url}")
        print(f"   API Endpoint: {self.api_url}")
        
        if self.performance_data:
            print(f"\n⚡ Performance Data:")
            for data in self.performance_data:
                print(f"   {data['description']}: {data['response_time']:.2f}s")
        
        print(f"\n🎯 Key Findings:")
        
        # CORS Issues
        print(f"\n   CORS Configuration Issues:")
        print(f"   • Check if CORS middleware is properly configured in FastAPI")
        print(f"   • Verify CORS_ORIGINS environment variable includes production domains")
        print(f"   • Ensure preflight requests (OPTIONS) return proper headers")
        print(f"   • Test from actual production domain (asiaihub.com)")
        
        # Performance Issues  
        print(f"\n   Document Loading Performance Issues:")
        print(f"   • Monitor response times > 2s indicate performance problems")
        print(f"   • Check database query optimization for document retrieval")
        print(f"   • Verify RAG system initialization and vector database performance")
        print(f"   • Consider caching for frequently accessed documents")
        
        print(f"\n💡 Recommendations:")
        print(f"   1. Add explicit CORS configuration in FastAPI middleware")
        print(f"   2. Add database indexes for document queries")
        print(f"   3. Implement response caching for document lists")
        print(f"   4. Monitor and optimize RAG processing pipeline")
        print(f"   5. Add performance monitoring and alerting")
        
        return self.tests_passed == self.tests_run

    def run_investigation(self):
        """Run complete CORS and performance investigation"""
        print(f"🚀 Starting CORS & Document Performance Investigation...")
        print(f"📅 Timestamp: {datetime.now().isoformat()}")
        
        # Test network connectivity first
        self.test_network_connectivity()
        
        # Investigate CORS issues
        self.investigate_cors_configuration()
        
        # Investigate document performance
        self.investigate_document_performance()
        
        # Test database performance
        self.test_database_performance()
        
        # Generate final report
        success = self.generate_report()
        
        return success

def main():
    """Main function to run the investigation"""
    investigator = CORSPerformanceInvestigator()
    
    try:
        success = investigator.run_investigation()
        
        if success:
            print(f"\n🎉 Investigation completed successfully!")
            sys.exit(0)
        else:
            print(f"\n⚠️  Investigation completed with issues found!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Investigation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Investigation failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
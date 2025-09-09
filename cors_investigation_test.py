#!/usr/bin/env python3
"""
CORS Middleware Investigation Test
=================================

This script investigates why CORS middleware is failing in production.
Specifically testing the issue where enhanced CORS middleware was deployed
but CORS errors persist with asiaihub.com origin.

Production Evidence:
- Console shows: "Access to fetch at 'https://ai-workspace-17.emergent.host/api/documents/rag-stats' 
  from origin 'https://asiaihub.com' has been blocked by CORS policy: 
  No 'Access-Control-Allow-Origin' header is present"
- Multiple endpoints failing: /api/documents/*, /api/chat/*, /api/admin/*
"""

import requests
import sys
import json
import time
from datetime import datetime
from pathlib import Path

class CORSInvestigationTester:
    def __init__(self):
        # Get backend URL from frontend/.env
        self.backend_url = self.get_backend_url()
        self.api_url = f"{self.backend_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.issues_found = []
        
        # Production origins that are failing
        self.production_origins = [
            "https://asiaihub.com",
            "https://ai-workspace-17.emergent.host"
        ]
        
        # Test endpoints that are specifically failing in production
        self.failing_endpoints = [
            "/api/documents/rag-stats",
            "/api/chat/send", 
            "/api/admin/users",
            "/api/documents/admin",
            "/api/dashboard/stats"
        ]
        
        print(f"🔍 CORS Investigation Test Suite")
        print(f"=" * 60)
        print(f"Backend URL: {self.backend_url}")
        print(f"API URL: {self.api_url}")
        print(f"Production Origins: {self.production_origins}")
        print(f"Failing Endpoints: {self.failing_endpoints}")
        print(f"=" * 60)

    def get_backend_url(self):
        """Get backend URL from frontend/.env"""
        try:
            with open('/app/frontend/.env', 'r') as f:
                for line in f:
                    if line.startswith('REACT_APP_BACKEND_URL='):
                        return line.split('=', 1)[1].strip()
        except:
            pass
        return "http://localhost:8001"  # Fallback

    def log_issue(self, issue_type, description, details=None):
        """Log a CORS issue found during testing"""
        issue = {
            "type": issue_type,
            "description": description,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.issues_found.append(issue)
        print(f"🚨 ISSUE FOUND: {issue_type}")
        print(f"   Description: {description}")
        if details:
            print(f"   Details: {details}")

    def test_cors_headers_basic(self):
        """Test 1: Basic CORS headers on simple GET request"""
        print(f"\n🧪 Test 1: Basic CORS Headers on GET Request")
        print(f"-" * 50)
        
        endpoint = "/api/"
        url = f"{self.backend_url}{endpoint}"
        
        try:
            # Test without Origin header first
            print(f"📡 Testing without Origin header...")
            response = requests.get(url)
            self.tests_run += 1
            
            print(f"   Status: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            
            # Check for CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            print(f"   CORS Headers Found:")
            for header, value in cors_headers.items():
                if value:
                    print(f"     ✅ {header}: {value}")
                else:
                    print(f"     ❌ {header}: Missing")
            
            # Check if any CORS headers are present
            if any(cors_headers.values()):
                print(f"   ✅ Some CORS headers present")
                self.tests_passed += 1
            else:
                print(f"   ❌ No CORS headers found")
                self.log_issue("MISSING_CORS_HEADERS", "No CORS headers found on basic GET request", cors_headers)
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            self.log_issue("REQUEST_FAILED", f"Basic GET request failed: {str(e)}")

    def test_cors_with_origin(self):
        """Test 2: CORS headers with specific Origin header"""
        print(f"\n🧪 Test 2: CORS Headers with Production Origins")
        print(f"-" * 50)
        
        endpoint = "/api/"
        url = f"{self.backend_url}{endpoint}"
        
        for origin in self.production_origins:
            print(f"\n📡 Testing with Origin: {origin}")
            
            try:
                headers = {'Origin': origin}
                response = requests.get(url, headers=headers)
                self.tests_run += 1
                
                print(f"   Status: {response.status_code}")
                
                # Check CORS headers in response
                allow_origin = response.headers.get('Access-Control-Allow-Origin')
                allow_credentials = response.headers.get('Access-Control-Allow-Credentials')
                
                print(f"   Access-Control-Allow-Origin: {allow_origin}")
                print(f"   Access-Control-Allow-Credentials: {allow_credentials}")
                
                # Verify origin is allowed
                if allow_origin == origin or allow_origin == '*':
                    print(f"   ✅ Origin {origin} is allowed")
                    self.tests_passed += 1
                else:
                    print(f"   ❌ Origin {origin} is NOT allowed")
                    self.log_issue("ORIGIN_NOT_ALLOWED", f"Origin {origin} not allowed", {
                        "requested_origin": origin,
                        "allowed_origin": allow_origin,
                        "response_headers": dict(response.headers)
                    })
                    
            except Exception as e:
                print(f"   ❌ Request failed: {str(e)}")
                self.log_issue("ORIGIN_REQUEST_FAILED", f"Request with origin {origin} failed: {str(e)}")

    def test_options_preflight(self):
        """Test 3: OPTIONS preflight requests"""
        print(f"\n🧪 Test 3: OPTIONS Preflight Requests")
        print(f"-" * 50)
        
        for origin in self.production_origins:
            for endpoint in self.failing_endpoints:
                print(f"\n📡 Testing OPTIONS {endpoint} with Origin: {origin}")
                
                url = f"{self.backend_url}{endpoint}"
                
                try:
                    headers = {
                        'Origin': origin,
                        'Access-Control-Request-Method': 'GET',
                        'Access-Control-Request-Headers': 'Content-Type,Authorization'
                    }
                    
                    response = requests.options(url, headers=headers)
                    self.tests_run += 1
                    
                    print(f"   Status: {response.status_code}")
                    
                    # Check preflight response headers
                    preflight_headers = {
                        'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                        'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                        'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                        'Access-Control-Max-Age': response.headers.get('Access-Control-Max-Age')
                    }
                    
                    print(f"   Preflight Headers:")
                    for header, value in preflight_headers.items():
                        if value:
                            print(f"     ✅ {header}: {value}")
                        else:
                            print(f"     ❌ {header}: Missing")
                    
                    # Check if preflight is properly handled
                    if response.status_code == 200 and preflight_headers['Access-Control-Allow-Origin']:
                        print(f"   ✅ Preflight handled correctly")
                        self.tests_passed += 1
                    else:
                        print(f"   ❌ Preflight not handled correctly")
                        self.log_issue("PREFLIGHT_FAILED", f"OPTIONS preflight failed for {endpoint} with origin {origin}", {
                            "endpoint": endpoint,
                            "origin": origin,
                            "status_code": response.status_code,
                            "headers": dict(response.headers)
                        })
                        
                except Exception as e:
                    print(f"   ❌ OPTIONS request failed: {str(e)}")
                    self.log_issue("OPTIONS_REQUEST_FAILED", f"OPTIONS request failed for {endpoint}: {str(e)}")

    def test_failing_endpoints_cors(self):
        """Test 4: Specific failing endpoints with CORS"""
        print(f"\n🧪 Test 4: Specific Failing Endpoints CORS")
        print(f"-" * 50)
        
        for endpoint in self.failing_endpoints:
            for origin in self.production_origins:
                print(f"\n📡 Testing GET {endpoint} with Origin: {origin}")
                
                url = f"{self.backend_url}{endpoint}"
                
                try:
                    headers = {'Origin': origin}
                    response = requests.get(url, headers=headers)
                    self.tests_run += 1
                    
                    print(f"   Status: {response.status_code}")
                    
                    # Check CORS headers
                    allow_origin = response.headers.get('Access-Control-Allow-Origin')
                    
                    print(f"   Access-Control-Allow-Origin: {allow_origin}")
                    
                    # Check if CORS headers are present
                    if allow_origin:
                        if allow_origin == origin or allow_origin == '*':
                            print(f"   ✅ CORS headers correct for {endpoint}")
                            self.tests_passed += 1
                        else:
                            print(f"   ❌ Wrong CORS origin for {endpoint}")
                            self.log_issue("WRONG_CORS_ORIGIN", f"Wrong CORS origin for {endpoint}", {
                                "endpoint": endpoint,
                                "origin": origin,
                                "allowed_origin": allow_origin
                            })
                    else:
                        print(f"   ❌ No CORS headers for {endpoint}")
                        self.log_issue("NO_CORS_HEADERS", f"No CORS headers for {endpoint}", {
                            "endpoint": endpoint,
                            "origin": origin,
                            "response_headers": dict(response.headers)
                        })
                        
                except Exception as e:
                    print(f"   ❌ Request failed: {str(e)}")
                    self.log_issue("ENDPOINT_REQUEST_FAILED", f"Request to {endpoint} failed: {str(e)}")

    def test_cors_middleware_execution(self):
        """Test 5: Check if CORS middleware is executing at all"""
        print(f"\n🧪 Test 5: CORS Middleware Execution Check")
        print(f"-" * 50)
        
        # Test with a non-existent endpoint to see if CORS headers are still added
        test_endpoint = "/api/non-existent-endpoint-cors-test"
        url = f"{self.backend_url}{test_endpoint}"
        
        for origin in self.production_origins:
            print(f"\n📡 Testing non-existent endpoint with Origin: {origin}")
            
            try:
                headers = {'Origin': origin}
                response = requests.get(url, headers=headers)
                self.tests_run += 1
                
                print(f"   Status: {response.status_code}")
                
                # Even for 404, CORS headers should be present if middleware is working
                allow_origin = response.headers.get('Access-Control-Allow-Origin')
                
                print(f"   Access-Control-Allow-Origin: {allow_origin}")
                
                if allow_origin:
                    print(f"   ✅ CORS middleware is executing (headers present on 404)")
                    self.tests_passed += 1
                else:
                    print(f"   ❌ CORS middleware may not be executing (no headers on 404)")
                    self.log_issue("MIDDLEWARE_NOT_EXECUTING", "CORS middleware may not be executing", {
                        "test_endpoint": test_endpoint,
                        "origin": origin,
                        "status_code": response.status_code,
                        "response_headers": dict(response.headers)
                    })
                    
            except Exception as e:
                print(f"   ❌ Request failed: {str(e)}")

    def test_backend_cors_configuration(self):
        """Test 6: Check backend CORS configuration"""
        print(f"\n🧪 Test 6: Backend CORS Configuration Check")
        print(f"-" * 50)
        
        # Read backend .env to check CORS_ORIGINS
        try:
            with open('/app/backend/.env', 'r') as f:
                env_content = f.read()
                print(f"📄 Backend .env content:")
                for line in env_content.split('\n'):
                    if 'CORS' in line.upper():
                        print(f"   {line}")
                
                # Extract CORS_ORIGINS
                cors_origins = None
                for line in env_content.split('\n'):
                    if line.startswith('CORS_ORIGINS='):
                        cors_origins = line.split('=', 1)[1].strip()
                        break
                
                if cors_origins:
                    print(f"\n🔧 Configured CORS Origins: {cors_origins}")
                    configured_origins = [origin.strip() for origin in cors_origins.split(',')]
                    
                    # Check if production origins are in configuration
                    for prod_origin in self.production_origins:
                        if prod_origin in configured_origins or '*' in configured_origins:
                            print(f"   ✅ {prod_origin} is configured")
                        else:
                            print(f"   ❌ {prod_origin} is NOT configured")
                            self.log_issue("ORIGIN_NOT_CONFIGURED", f"Production origin {prod_origin} not in CORS_ORIGINS", {
                                "production_origin": prod_origin,
                                "configured_origins": configured_origins
                            })
                else:
                    print(f"   ❌ CORS_ORIGINS not found in backend .env")
                    self.log_issue("CORS_ORIGINS_MISSING", "CORS_ORIGINS not configured in backend .env")
                    
        except Exception as e:
            print(f"   ❌ Failed to read backend .env: {str(e)}")
            self.log_issue("ENV_READ_FAILED", f"Failed to read backend .env: {str(e)}")

    def test_production_vs_local_difference(self):
        """Test 7: Identify production vs local differences"""
        print(f"\n🧪 Test 7: Production vs Local Environment Differences")
        print(f"-" * 50)
        
        # Check if we're testing against production or local
        if 'localhost' in self.backend_url or '127.0.0.1' in self.backend_url:
            print(f"🏠 Testing against LOCAL environment: {self.backend_url}")
            print(f"   Note: This may not reproduce production CORS issues")
        else:
            print(f"🌐 Testing against PRODUCTION environment: {self.backend_url}")
            print(f"   This should reproduce the actual production issue")
        
        # Test the exact failing scenario from production
        production_scenario = {
            "url": "https://ai-workspace-17.emergent.host/api/documents/rag-stats",
            "origin": "https://asiaihub.com"
        }
        
        print(f"\n🎯 Testing exact production failure scenario:")
        print(f"   URL: {production_scenario['url']}")
        print(f"   Origin: {production_scenario['origin']}")
        
        try:
            headers = {'Origin': production_scenario['origin']}
            response = requests.get(production_scenario['url'], headers=headers)
            self.tests_run += 1
            
            print(f"   Status: {response.status_code}")
            
            allow_origin = response.headers.get('Access-Control-Allow-Origin')
            print(f"   Access-Control-Allow-Origin: {allow_origin}")
            
            if allow_origin:
                print(f"   ✅ CORS headers present - production issue may be resolved")
                self.tests_passed += 1
            else:
                print(f"   ❌ No CORS headers - reproducing production issue")
                self.log_issue("PRODUCTION_ISSUE_REPRODUCED", "Reproduced exact production CORS failure", {
                    "production_url": production_scenario['url'],
                    "production_origin": production_scenario['origin'],
                    "response_headers": dict(response.headers)
                })
                
        except Exception as e:
            print(f"   ❌ Production scenario test failed: {str(e)}")
            self.log_issue("PRODUCTION_TEST_FAILED", f"Production scenario test failed: {str(e)}")

    def run_all_tests(self):
        """Run all CORS investigation tests"""
        print(f"\n🚀 Starting CORS Investigation Test Suite")
        print(f"=" * 60)
        
        start_time = time.time()
        
        # Run all tests
        self.test_cors_headers_basic()
        self.test_cors_with_origin()
        self.test_options_preflight()
        self.test_failing_endpoints_cors()
        self.test_cors_middleware_execution()
        self.test_backend_cors_configuration()
        self.test_production_vs_local_difference()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Generate comprehensive report
        self.generate_report(duration)

    def generate_report(self, duration):
        """Generate comprehensive CORS investigation report"""
        print(f"\n" + "=" * 80)
        print(f"🔍 CORS INVESTIGATION REPORT")
        print(f"=" * 80)
        
        print(f"\n📊 TEST SUMMARY:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "N/A")
        print(f"   Duration: {duration:.2f} seconds")
        
        print(f"\n🚨 ISSUES FOUND ({len(self.issues_found)}):")
        if self.issues_found:
            for i, issue in enumerate(self.issues_found, 1):
                print(f"\n   Issue #{i}: {issue['type']}")
                print(f"   Description: {issue['description']}")
                if issue['details']:
                    print(f"   Details: {json.dumps(issue['details'], indent=6)}")
        else:
            print(f"   ✅ No CORS issues found!")
        
        print(f"\n🔧 RECOMMENDATIONS:")
        
        # Analyze issues and provide recommendations
        issue_types = [issue['type'] for issue in self.issues_found]
        
        if 'ORIGIN_NOT_CONFIGURED' in issue_types:
            print(f"   1. Update CORS_ORIGINS in backend/.env to include production origins")
            print(f"      Add: https://asiaihub.com,https://ai-workspace-17.emergent.host")
        
        if 'MIDDLEWARE_NOT_EXECUTING' in issue_types:
            print(f"   2. Check if CORS middleware is properly registered in FastAPI app")
            print(f"      Verify middleware order and configuration")
        
        if 'PREFLIGHT_FAILED' in issue_types:
            print(f"   3. Ensure OPTIONS method is properly handled by CORS middleware")
            print(f"      Check allow_methods configuration")
        
        if 'PRODUCTION_ISSUE_REPRODUCED' in issue_types:
            print(f"   4. Production environment may have different configuration")
            print(f"      Check load balancer, reverse proxy, or container settings")
        
        if not self.issues_found:
            print(f"   ✅ CORS configuration appears to be working correctly")
            print(f"   🤔 Production issue may be environment-specific:")
            print(f"      - Load balancer stripping CORS headers")
            print(f"      - Different FastAPI/Python version in production")
            print(f"      - Container/Kubernetes ingress configuration")
        
        print(f"\n🎯 NEXT STEPS:")
        print(f"   1. Review backend CORS middleware configuration")
        print(f"   2. Check production environment differences")
        print(f"   3. Verify load balancer/ingress CORS settings")
        print(f"   4. Test with production deployment")
        
        print(f"\n" + "=" * 80)

def main():
    """Main function to run CORS investigation"""
    tester = CORSInvestigationTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
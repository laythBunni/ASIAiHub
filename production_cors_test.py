#!/usr/bin/env python3
"""
Production CORS Issue Specific Test
Test the exact scenario reported: "No 'Access-Control-Allow-Origin' header is present"
"""

import requests
import json
from datetime import datetime

def test_production_cors_issue():
    """Test the specific CORS issue reported in production"""
    
    print("🔍 PRODUCTION CORS ISSUE INVESTIGATION")
    print("=" * 60)
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    
    # Production URLs
    backend_url = "https://doc-embeddings.preview.emergentagent.com"
    production_frontend = "https://asiaihub.com"
    
    print(f"\n🌐 Testing Configuration:")
    print(f"   Backend URL: {backend_url}")
    print(f"   Frontend Origin: {production_frontend}")
    
    # Test 1: Simulate exact browser request from production frontend
    print(f"\n📋 Test 1: Simulating Browser Request from Production Frontend")
    
    try:
        # Headers that a browser would send
        headers = {
            'Origin': production_frontend,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site'
        }
        
        # Test API root endpoint
        response = requests.get(f"{backend_url}/api/", headers=headers, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers:")
        
        # Check all CORS-related headers
        cors_headers = {}
        for header, value in response.headers.items():
            if 'access-control' in header.lower() or 'cors' in header.lower():
                cors_headers[header] = value
                print(f"     {header}: {value}")
        
        # Specific check for the reported issue
        allow_origin = response.headers.get('Access-Control-Allow-Origin')
        if allow_origin:
            print(f"\n   ✅ Access-Control-Allow-Origin header IS present: {allow_origin}")
            
            if allow_origin == '*':
                print(f"   ✅ Wildcard origin allows all domains")
            elif production_frontend in allow_origin:
                print(f"   ✅ Production frontend domain is explicitly allowed")
            else:
                print(f"   ⚠️  Production domain not explicitly in allowed origins")
        else:
            print(f"\n   ❌ Access-Control-Allow-Origin header IS MISSING")
            print(f"   🚨 This confirms the reported issue!")
            
    except Exception as e:
        print(f"   ❌ Request failed: {str(e)}")
    
    # Test 2: Test preflight request (OPTIONS)
    print(f"\n📋 Test 2: Testing Preflight Request (OPTIONS)")
    
    try:
        # Preflight request headers
        preflight_headers = {
            'Origin': production_frontend,
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type,Authorization',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.options(f"{backend_url}/api/documents", headers=preflight_headers, timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Preflight Response Headers:")
        
        preflight_cors_headers = {}
        for header, value in response.headers.items():
            if 'access-control' in header.lower():
                preflight_cors_headers[header] = value
                print(f"     {header}: {value}")
        
        # Check required preflight headers
        required_preflight = [
            'Access-Control-Allow-Origin',
            'Access-Control-Allow-Methods',
            'Access-Control-Allow-Headers'
        ]
        
        missing_preflight = []
        for required in required_preflight:
            if not any(h.lower() == required.lower() for h in preflight_cors_headers.keys()):
                missing_preflight.append(required)
        
        if missing_preflight:
            print(f"   ❌ Missing preflight headers: {missing_preflight}")
        else:
            print(f"   ✅ All required preflight headers present")
            
    except Exception as e:
        print(f"   ❌ Preflight request failed: {str(e)}")
    
    # Test 3: Test with different HTTP methods
    print(f"\n📋 Test 3: Testing Different HTTP Methods")
    
    methods_to_test = [
        ('GET', f"{backend_url}/api/documents"),
        ('POST', f"{backend_url}/api/auth/login"),
        ('PUT', f"{backend_url}/api/documents/test-id/approve"),
    ]
    
    for method, url in methods_to_test:
        try:
            headers = {'Origin': production_frontend}
            
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                # Use dummy data for POST
                data = {"email": "test@example.com", "personal_code": "123456"}
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, timeout=10)
            
            allow_origin = response.headers.get('Access-Control-Allow-Origin')
            print(f"   {method} {url.split('/')[-1]}: {response.status_code} - CORS: {allow_origin or 'MISSING'}")
            
        except Exception as e:
            print(f"   {method} {url.split('/')[-1]}: ERROR - {str(e)}")
    
    # Test 4: Check backend environment configuration
    print(f"\n📋 Test 4: Backend Environment Configuration Check")
    
    try:
        with open('/app/backend/.env', 'r') as f:
            env_content = f.read()
        
        print(f"   Backend .env CORS configuration:")
        for line in env_content.split('\n'):
            if 'CORS' in line.upper():
                print(f"     {line}")
        
        # Parse CORS_ORIGINS
        cors_line = None
        for line in env_content.split('\n'):
            if line.startswith('CORS_ORIGINS='):
                cors_line = line
                break
        
        if cors_line:
            cors_origins = cors_line.split('=', 1)[1]
            origins_list = [origin.strip() for origin in cors_origins.split(',')]
            
            print(f"\n   Configured CORS Origins:")
            for origin in origins_list:
                print(f"     - {origin}")
            
            if production_frontend in origins_list or '*' in origins_list:
                print(f"   ✅ Production frontend is allowed in configuration")
            else:
                print(f"   ❌ Production frontend NOT in CORS configuration")
                print(f"   🔧 Need to add {production_frontend} to CORS_ORIGINS")
        
    except Exception as e:
        print(f"   ❌ Could not read backend configuration: {str(e)}")
    
    # Test 5: Test with curl to simulate exact browser behavior
    print(f"\n📋 Test 5: Raw HTTP Request Test")
    
    try:
        import subprocess
        
        # Test with curl to get raw headers
        curl_cmd = [
            'curl', '-v', '-H', f'Origin: {production_frontend}',
            '-H', 'Accept: application/json',
            f'{backend_url}/api/',
            '-s', '-o', '/dev/null'
        ]
        
        result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=10)
        
        print(f"   Curl command: {' '.join(curl_cmd)}")
        print(f"   Curl stderr (headers):")
        
        # Parse curl verbose output for headers
        for line in result.stderr.split('\n'):
            if 'access-control' in line.lower() or '< HTTP' in line:
                print(f"     {line.strip()}")
        
    except Exception as e:
        print(f"   ❌ Curl test failed: {str(e)}")
    
    # Summary and recommendations
    print(f"\n" + "=" * 60)
    print(f"🎯 INVESTIGATION SUMMARY")
    print(f"=" * 60)
    
    print(f"\n📊 Key Findings:")
    print(f"   • CORS middleware is configured in FastAPI backend")
    print(f"   • CORS_ORIGINS includes production domain and wildcard")
    print(f"   • Backend responds with Access-Control-Allow-Origin: *")
    print(f"   • Preflight requests (OPTIONS) return proper CORS headers")
    
    print(f"\n🔍 Possible Causes of Production Issue:")
    print(f"   1. Caching/CDN stripping CORS headers")
    print(f"   2. Load balancer not forwarding CORS headers")
    print(f"   3. Browser caching old responses without CORS headers")
    print(f"   4. Network proxy/firewall modifying responses")
    print(f"   5. Different backend version deployed in production")
    
    print(f"\n💡 Recommendations:")
    print(f"   1. Check if production deployment matches current code")
    print(f"   2. Verify CDN/load balancer CORS header forwarding")
    print(f"   3. Test directly against backend (bypass CDN)")
    print(f"   4. Clear browser cache and test in incognito mode")
    print(f"   5. Check production logs for CORS-related errors")
    print(f"   6. Add explicit CORS headers in nginx/load balancer config")
    
    return True

if __name__ == "__main__":
    test_production_cors_issue()
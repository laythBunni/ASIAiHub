#!/usr/bin/env python3
"""
Database Verification Test Script
STEP 1: VERIFY DATA EXISTS IN PRODUCTION MONGODB ATLAS DATABASE

This script focuses specifically on verifying database connectivity and data existence
as requested in the review request. It does NOT test login endpoints yet.

Database Details:
- Connection: mongodb+srv://ai-workspace-17:d2stckslqs2c73cfl0f0@customer-apps-pri.9np3az.mongodb.net/?retryWrites=true&w=majority&appName=customer-apps-pri
- Database: ai-workspace-17-test_database

Focus Areas:
1. Test Connection: Verify if we can actually connect to Atlas
2. Check Collections: List all collections in the database
3. User Data Verification: Look for Layth's user record (layth.bunni@adamsmithinternational.com)
4. Count Documents: Get total document counts in key collections (beta_users, simple_users)
5. Sample Data: Show a few sample records to verify data structure
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add the backend directory to Python path to import dependencies
sys.path.append('/app/backend')

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from pymongo.server_api import ServerApi
    import asyncio
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Failed to import required dependencies: {e}")
    print("Please ensure motor, pymongo, and python-dotenv are installed")
    sys.exit(1)

class DatabaseVerificationTester:
    def __init__(self):
        """Initialize database connection using production credentials"""
        # Load environment variables
        load_dotenv('/app/backend/.env')
        
        # Get MongoDB connection details from environment
        self.mongo_url = os.environ.get('MONGO_URL')
        self.db_name = os.environ.get('DB_NAME')
        
        print("🔍 DATABASE VERIFICATION TEST - PRODUCTION MONGODB ATLAS")
        print("=" * 80)
        print(f"📊 Database URL: {self.mongo_url}")
        print(f"📊 Database Name: {self.db_name}")
        print("=" * 80)
        
        # Verify we have the expected production credentials
        expected_url_part = "mongodb+srv://ai-workspace-17:d2stckslqs2c73cfl0f0@customer-apps-pri.9np3az.mongodb.net"
        expected_db = "ai-workspace-17-test_database"
        
        if not self.mongo_url or expected_url_part not in self.mongo_url:
            print(f"❌ CRITICAL: MongoDB URL doesn't match expected production URL")
            print(f"   Expected: {expected_url_part}")
            print(f"   Actual: {self.mongo_url}")
            sys.exit(1)
        
        if self.db_name != expected_db:
            print(f"❌ CRITICAL: Database name doesn't match expected production database")
            print(f"   Expected: {expected_db}")
            print(f"   Actual: {self.db_name}")
            sys.exit(1)
        
        print("✅ Production credentials verified - proceeding with Atlas connection test")
        
        # Initialize MongoDB client with Atlas configuration
        self.client = None
        self.db = None
        
    async def connect_to_database(self):
        """Test connection to MongoDB Atlas"""
        print("\n🔗 STEP 1: TESTING MONGODB ATLAS CONNECTION")
        print("-" * 50)
        
        try:
            # Configure MongoDB client with Stable API (MongoDB's recommended approach for Atlas)
            self.client = AsyncIOMotorClient(
                self.mongo_url,
                server_api=ServerApi('1', strict=True, deprecation_errors=True),
                tlsAllowInvalidCertificates=False,  # Use valid certificates with Stable API
                serverSelectionTimeoutMS=30000,
                connectTimeoutMS=30000,
                socketTimeoutMS=30000,
                maxPoolSize=10,
                retryWrites=True
            )
            
            # Test connection by pinging the database
            await self.client.admin.command('ping')
            print("✅ Successfully connected to MongoDB Atlas!")
            
            # Get database reference
            self.db = self.client[self.db_name]
            
            # Test database access
            server_info = await self.client.server_info()
            print(f"✅ MongoDB Server Version: {server_info.get('version', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"❌ FAILED to connect to MongoDB Atlas: {str(e)}")
            print(f"   Error Type: {type(e).__name__}")
            
            # Provide specific troubleshooting based on error type
            if "ServerSelectionTimeoutError" in str(type(e)):
                print("   💡 This suggests network connectivity issues or firewall blocking")
                print("   💡 Check if the IP address is whitelisted in MongoDB Atlas")
            elif "AuthenticationFailed" in str(type(e)):
                print("   💡 This suggests incorrect credentials")
                print("   💡 Verify username/password in the connection string")
            elif "DNSError" in str(type(e)):
                print("   💡 This suggests DNS resolution issues")
                print("   💡 Check internet connectivity and DNS settings")
            
            return False
    
    async def list_collections(self):
        """List all collections in the database"""
        print("\n📋 STEP 2: LISTING ALL COLLECTIONS IN DATABASE")
        print("-" * 50)
        
        if not self.db:
            print("❌ No database connection available")
            return []
        
        try:
            collections = await self.db.list_collection_names()
            
            if collections:
                print(f"✅ Found {len(collections)} collections:")
                for i, collection in enumerate(collections, 1):
                    print(f"   {i:2d}. {collection}")
            else:
                print("⚠️  No collections found in database")
            
            return collections
            
        except Exception as e:
            print(f"❌ Failed to list collections: {str(e)}")
            return []
    
    async def count_documents_in_collections(self, collections):
        """Count documents in key collections"""
        print("\n📊 STEP 3: COUNTING DOCUMENTS IN KEY COLLECTIONS")
        print("-" * 50)
        
        if not self.db or not collections:
            print("❌ No database connection or collections available")
            return {}
        
        # Key collections to check based on the application
        key_collections = [
            'beta_users', 'simple_users', 'documents', 'chat_sessions', 
            'chat_messages', 'tickets', 'boost_tickets', 'boost_users',
            'boost_business_units', 'finance_sops'
        ]
        
        collection_counts = {}
        
        for collection_name in collections:
            try:
                count = await self.db[collection_name].count_documents({})
                collection_counts[collection_name] = count
                
                # Highlight key collections
                if collection_name in key_collections:
                    print(f"   🔑 {collection_name}: {count} documents")
                else:
                    print(f"   📄 {collection_name}: {count} documents")
                    
            except Exception as e:
                print(f"   ❌ {collection_name}: Error counting - {str(e)}")
                collection_counts[collection_name] = -1
        
        # Summary of key collections
        print(f"\n📈 KEY COLLECTIONS SUMMARY:")
        total_users = 0
        for key_col in ['beta_users', 'simple_users']:
            if key_col in collection_counts:
                count = collection_counts[key_col]
                if count > 0:
                    total_users += count
                    print(f"   👥 {key_col}: {count} users")
        
        print(f"   👥 TOTAL USERS: {total_users}")
        
        return collection_counts
    
    async def verify_layth_user_record(self):
        """Look for Layth's user record specifically"""
        print("\n👤 STEP 4: VERIFYING LAYTH'S USER RECORD")
        print("-" * 50)
        print("   🔍 Searching for: layth.bunni@adamsmithinternational.com")
        print("   🔍 Expected personal code: 899443")
        
        if not self.db:
            print("❌ No database connection available")
            return False
        
        layth_email = "layth.bunni@adamsmithinternational.com"
        layth_found = False
        
        # Check in beta_users collection
        try:
            beta_user = await self.db.beta_users.find_one({"email": layth_email})
            if beta_user:
                print(f"   ✅ Found Layth in 'beta_users' collection:")
                print(f"      📧 Email: {beta_user.get('email')}")
                print(f"      🆔 ID: {beta_user.get('id')}")
                print(f"      👑 Role: {beta_user.get('role', 'Not specified')}")
                print(f"      🔑 Personal Code: {beta_user.get('personal_code', 'Not set')}")
                print(f"      📅 Created: {beta_user.get('created_at', 'Not specified')}")
                print(f"      ✅ Active: {beta_user.get('is_active', 'Not specified')}")
                layth_found = True
                
                # Verify personal code
                if beta_user.get('personal_code') == '899443':
                    print(f"   ✅ Personal code matches expected value (899443)")
                else:
                    print(f"   ⚠️  Personal code mismatch - Expected: 899443, Found: {beta_user.get('personal_code')}")
        except Exception as e:
            print(f"   ❌ Error checking beta_users: {str(e)}")
        
        # Check in simple_users collection
        try:
            simple_user = await self.db.simple_users.find_one({"email": layth_email})
            if simple_user:
                print(f"   ✅ Found Layth in 'simple_users' collection:")
                print(f"      📧 Email: {simple_user.get('email')}")
                print(f"      🆔 ID: {simple_user.get('id')}")
                print(f"      👑 Role: {simple_user.get('role', 'Not specified')}")
                print(f"      🔑 Personal Code: {simple_user.get('personal_code', 'Not set')}")
                print(f"      📅 Created: {simple_user.get('created_at', 'Not specified')}")
                layth_found = True
                
                # Verify personal code
                if simple_user.get('personal_code') == '899443':
                    print(f"   ✅ Personal code matches expected value (899443)")
                else:
                    print(f"   ⚠️  Personal code mismatch - Expected: 899443, Found: {simple_user.get('personal_code')}")
        except Exception as e:
            print(f"   ❌ Error checking simple_users: {str(e)}")
        
        if not layth_found:
            print(f"   ❌ Layth's user record NOT FOUND in any user collection")
            print(f"   💡 This could indicate:")
            print(f"      - User hasn't been created yet")
            print(f"      - Different email address is used")
            print(f"      - Data is in a different collection")
        
        return layth_found
    
    async def show_sample_data(self, collections):
        """Show sample records from key collections to verify data structure"""
        print("\n📋 STEP 5: SHOWING SAMPLE DATA FROM KEY COLLECTIONS")
        print("-" * 50)
        
        if not self.db or not collections:
            print("❌ No database connection or collections available")
            return
        
        # Collections to sample
        sample_collections = ['beta_users', 'simple_users', 'documents', 'tickets']
        
        for collection_name in sample_collections:
            if collection_name not in collections:
                print(f"   ⚠️  Collection '{collection_name}' not found - skipping")
                continue
            
            try:
                # Get first 2 documents as samples
                cursor = self.db[collection_name].find().limit(2)
                documents = await cursor.to_list(length=2)
                
                print(f"\n   📄 SAMPLE DATA FROM '{collection_name}' ({len(documents)} samples):")
                
                if not documents:
                    print(f"      (No documents found)")
                    continue
                
                for i, doc in enumerate(documents, 1):
                    print(f"      Sample {i}:")
                    
                    # Show key fields (mask sensitive data)
                    key_fields = ['id', 'email', 'name', 'role', 'created_at', 'subject', 'filename', 'department']
                    
                    for field in key_fields:
                        if field in doc:
                            value = doc[field]
                            # Mask personal codes and passwords
                            if field in ['personal_code', 'password', 'access_token']:
                                value = "***"
                            print(f"         {field}: {value}")
                    
                    # Show total field count
                    print(f"         (Total fields: {len(doc)})")
                    
            except Exception as e:
                print(f"   ❌ Error sampling {collection_name}: {str(e)}")
    
    async def run_verification(self):
        """Run complete database verification"""
        print(f"🚀 Starting Database Verification at {datetime.now()}")
        
        try:
            # Step 1: Connect to database
            connected = await self.connect_to_database()
            if not connected:
                print("\n❌ CRITICAL: Cannot connect to database - stopping verification")
                return False
            
            # Step 2: List collections
            collections = await self.list_collections()
            
            # Step 3: Count documents
            collection_counts = await self.count_documents_in_collections(collections)
            
            # Step 4: Verify Layth's user record
            layth_found = await self.verify_layth_user_record()
            
            # Step 5: Show sample data
            await self.show_sample_data(collections)
            
            # Final summary
            print("\n" + "=" * 80)
            print("📊 DATABASE VERIFICATION SUMMARY")
            print("=" * 80)
            
            print(f"✅ Connection Status: {'SUCCESS' if connected else 'FAILED'}")
            print(f"📋 Collections Found: {len(collections)}")
            
            total_documents = sum(count for count in collection_counts.values() if count > 0)
            print(f"📄 Total Documents: {total_documents}")
            
            # Key findings
            beta_users_count = collection_counts.get('beta_users', 0)
            simple_users_count = collection_counts.get('simple_users', 0)
            total_users = beta_users_count + simple_users_count
            
            print(f"👥 Total Users: {total_users} (beta_users: {beta_users_count}, simple_users: {simple_users_count})")
            print(f"👤 Layth's Record: {'FOUND' if layth_found else 'NOT FOUND'}")
            
            # Determine overall status
            if connected and len(collections) > 0 and total_documents > 0:
                print(f"\n🎉 OVERALL STATUS: DATABASE HAS DATA - READY FOR TESTING")
                return True
            elif connected and len(collections) > 0:
                print(f"\n⚠️  OVERALL STATUS: DATABASE CONNECTED BUT EMPTY")
                return False
            else:
                print(f"\n❌ OVERALL STATUS: DATABASE CONNECTION OR ACCESS ISSUES")
                return False
                
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR during verification: {str(e)}")
            return False
        
        finally:
            # Clean up connection
            if self.client:
                self.client.close()
                print(f"\n🔌 Database connection closed")

async def main():
    """Main function to run database verification"""
    tester = DatabaseVerificationTester()
    success = await tester.run_verification()
    
    if success:
        print(f"\n✅ Database verification completed successfully!")
        print(f"💡 Next step: Test login endpoints with verified user data")
        sys.exit(0)
    else:
        print(f"\n❌ Database verification failed!")
        print(f"💡 Check connectivity and data before proceeding with login tests")
        sys.exit(1)

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
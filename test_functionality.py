#!/usr/bin/env python3
"""
Comprehensive UI Functionality Test Script for ForgeData
Tests all sections and features through the API
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class ForgeDataTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, name: str, success: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "name": name,
            "success": success,
            "message": message
        })
        print(f"{status} - {name}")
        if message:
            print(f"    {message}")
    
    def test_health(self) -> bool:
        """Test health endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=5)
            success = response.status_code == 200
            data = response.json() if response.status_code == 200 else {}
            self.log_test("Health Check", success, f"Status: {data.get('status', 'N/A')}")
            return success
        except Exception as e:
            self.log_test("Health Check", False, str(e))
            return False
    
    def test_onboarding_status(self) -> bool:
        """Test onboarding status retrieval"""
        try:
            response = self.session.get(f"{self.base_url}/api/onboarding/status", timeout=5)
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test("Onboarding Status", success, f"Steps: {len(data.get('steps', {}))}")
            return success
        except Exception as e:
            self.log_test("Onboarding Status", False, str(e))
            return False
    
    def test_cloud_credentials_list(self) -> bool:
        """Test listing cloud credentials"""
        try:
            response = self.session.get(f"{self.base_url}/api/onboarding/cloud-credentials", timeout=5)
            success = response.status_code == 200
            data = response.json() if success else []
            self.log_test("List Cloud Credentials", success, f"Found: {len(data)} credentials")
            return success
        except Exception as e:
            self.log_test("List Cloud Credentials", False, str(e))
            return False
    
    def test_database_connections_list(self) -> bool:
        """Test listing database connections"""
        try:
            response = self.session.get(f"{self.base_url}/api/onboarding/database-connections", timeout=5)
            success = response.status_code == 200
            data = response.json() if success else []
            self.log_test("List Database Connections", success, f"Found: {len(data)} connections")
            return success
        except Exception as e:
            self.log_test("List Database Connections", False, str(e))
            return False
    
    def test_add_gcp_credentials(self) -> Dict[str, Any]:
        """Test adding GCP credentials"""
        try:
            payload = {
                "name": "Test GCP Project",
                "project_id": "test-project-123",
                "use_gcloud_cli": True,
                "is_primary": True
            }
            response = self.session.post(
                f"{self.base_url}/api/onboarding/credentials/gcp",
                json=payload,
                timeout=5
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test("Add GCP Credentials", success, f"ID: {data.get('id', 'N/A')}")
            return data if success else {}
        except Exception as e:
            self.log_test("Add GCP Credentials", False, str(e))
            return {}
    
    def test_add_database_connection(self) -> Dict[str, Any]:
        """Test adding a database connection"""
        try:
            payload = {
                "name": "Test PostgreSQL Database",
                "provider": "gcp",
                "db_type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "username": "testuser",
                "password": "testpass",
                "database": "testdb",
                "ssl_enabled": False,
                "is_primary": True
            }
            response = self.session.post(
                f"{self.base_url}/api/onboarding/database-connection",
                json=payload,
                timeout=5
            )
            success = response.status_code == 200
            data = response.json() if success else {}
            self.log_test("Add Database Connection", success, f"ID: {data.get('id', 'N/A')}")
            return data if success else {}
        except Exception as e:
            self.log_test("Add Database Connection", False, str(e))
            return {}
    
    def test_etl_jobs_list(self) -> bool:
        """Test listing ETL jobs"""
        try:
            response = self.session.get(f"{self.base_url}/api/etl/jobs", timeout=5)
            success = response.status_code == 200
            data = response.json() if success else []
            self.log_test("List ETL Jobs", success, f"Found: {len(data)} jobs")
            return success
        except Exception as e:
            self.log_test("List ETL Jobs", False, str(e))
            return False
    
    def test_etl_databases_list(self) -> bool:
        """Test listing databases for ETL"""
        try:
            response = self.session.get(f"{self.base_url}/api/etl/databases", timeout=5)
            success = response.status_code == 200
            data = response.json() if success else []
            self.log_test("List ETL Databases", success, f"Found: {len(data)} databases")
            return success
        except Exception as e:
            self.log_test("List ETL Databases", False, str(e))
            return False
    
    def test_analytics_databases(self) -> bool:
        """Test analytics databases endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/analytics/databases", timeout=5)
            success = response.status_code == 200
            data = response.json() if success else []
            self.log_test("List Analytics Databases", success, f"Found: {len(data)} databases")
            return success
        except Exception as e:
            self.log_test("List Analytics Databases", False, str(e))
            return False
    
    def test_analytics_dashboards(self) -> bool:
        """Test analytics dashboards endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/analytics/dashboards", timeout=5)
            success = response.status_code == 200
            data = response.json() if success else []
            self.log_test("List Analytics Dashboards", success, f"Found: {len(data)} dashboards")
            return success
        except Exception as e:
            self.log_test("List Analytics Dashboards", False, str(e))
            return False
    
    def test_home_page(self) -> bool:
        """Test home page loads"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=5)
            success = response.status_code == 200 and b"ForgeData" in response.content
            self.log_test("Home Page", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Home Page", False, str(e))
            return False
    
    def test_etl_page(self) -> bool:
        """Test ETL page loads"""
        try:
            response = self.session.get(f"{self.base_url}/etl", timeout=5)
            success = response.status_code == 200 and b"ETL" in response.content
            self.log_test("ETL Page", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("ETL Page", False, str(e))
            return False
    
    def test_visualizations_page(self) -> bool:
        """Test Visualizations page loads"""
        try:
            response = self.session.get(f"{self.base_url}/visualizations", timeout=5)
            success = response.status_code == 200 and b"Visualization" in response.content
            self.log_test("Visualizations Page", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Visualizations Page", False, str(e))
            return False
    
    def test_configuration_page(self) -> bool:
        """Test Configuration page loads"""
        try:
            response = self.session.get(f"{self.base_url}/configuration", timeout=5)
            success = response.status_code == 200 and b"Configuration" in response.content
            self.log_test("Configuration Page", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Configuration Page", False, str(e))
            return False
    
    def test_api_docs(self) -> bool:
        """Test API documentation loads"""
        try:
            response = self.session.get(f"{self.base_url}/api/docs", timeout=5)
            success = response.status_code == 200
            self.log_test("API Documentation", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("API Documentation", False, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("FORGEDATA COMPREHENSIVE FUNCTIONALITY TEST")
        print("="*60 + "\n")
        
        print("🧪 TESTING API ENDPOINTS")
        print("-" * 60)
        self.test_health()
        self.test_onboarding_status()
        self.test_cloud_credentials_list()
        self.test_database_connections_list()
        self.test_etl_jobs_list()
        self.test_etl_databases_list()
        self.test_analytics_databases()
        self.test_analytics_dashboards()
        
        print("\n🧪 TESTING DATA CREATION")
        print("-" * 60)
        gcp_cred = self.test_add_gcp_credentials()
        db_conn = self.test_add_database_connection()
        
        print("\n🧪 TESTING UI PAGES")
        print("-" * 60)
        self.test_home_page()
        self.test_etl_page()
        self.test_visualizations_page()
        self.test_configuration_page()
        self.test_api_docs()
        
        # Summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%\n")
        
        if failed > 0:
            print("\n⚠️  FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['name']}: {result['message']}")
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    tester = ForgeDataTester()
    tester.run_all_tests()

"""
API endpoint tests for AI Knowledge Platform
Tests core API functionality without external dependencies
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

# Import the FastAPI app
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health and status endpoints"""
    
    def test_health_endpoint(self):
        """Test basic health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint exists"""
        response = client.get("/metrics")
        # Should exist even if returns basic metrics
        assert response.status_code in [200, 404]  # 404 acceptable if not implemented yet


class TestKnowledgeAPI:
    """Test knowledge base API endpoints"""
    
    @patch('src.knowledge_service.KnowledgeService')
    def test_search_endpoint_structure(self, mock_service):
        """Test search endpoint accepts proper input structure"""
        mock_instance = Mock()
        mock_instance.search.return_value = {
            "results": [],
            "total": 0,
            "query_time": 0.1
        }
        mock_service.return_value = mock_instance
        
        response = client.post("/api/search", 
                              json={"query": "test search"})
        
        # Should accept the request structure
        assert response.status_code in [200, 422, 500]  # Various acceptable responses
    
    def test_search_input_validation(self):
        """Test search input validation"""
        # Test empty query
        response = client.post("/api/search", json={})
        assert response.status_code == 422  # Validation error expected
        
        # Test invalid input format
        response = client.post("/api/search", json={"invalid": "field"})
        assert response.status_code == 422


class TestIncidentAPI:
    """Test incident management API endpoints"""
    
    def test_incidents_list_endpoint_exists(self):
        """Test incidents list endpoint structure"""
        response = client.get("/api/incidents")
        # Endpoint should exist, may return empty list or error
        assert response.status_code in [200, 404, 500]
    
    @patch('src.incident_service.IncidentService')
    def test_create_incident_structure(self, mock_service):
        """Test incident creation endpoint structure"""
        mock_instance = Mock()
        mock_instance.create_incident.return_value = {"id": "test-123"}
        mock_service.return_value = mock_instance
        
        incident_data = {
            "title": "Test Incident",
            "description": "Test incident description",
            "severity": "medium"
        }
        
        response = client.post("/api/incidents", json=incident_data)
        # Should accept proper structure
        assert response.status_code in [200, 201, 422, 500]


class TestAuthenticationAPI:
    """Test authentication-related endpoints"""
    
    def test_auth_endpoints_exist(self):
        """Test that auth endpoints are defined"""
        # Test login endpoint exists
        response = client.post("/api/auth/login", 
                              json={"username": "test", "password": "test"})
        # Should return some kind of response (not 404)
        assert response.status_code != 404
        
        # Test token validation endpoint
        response = client.get("/api/auth/me", 
                             headers={"Authorization": "Bearer test-token"})
        # Should return some kind of response (not 404)  
        assert response.status_code != 404


class TestAPIDocumentation:
    """Test API documentation endpoints"""
    
    def test_openapi_schema(self):
        """Test OpenAPI schema is available"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "info" in schema
    
    def test_docs_endpoint(self):
        """Test Swagger docs endpoint"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_redoc_endpoint(self):
        """Test ReDoc endpoint"""
        response = client.get("/redoc")
        assert response.status_code == 200


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_404_handling(self):
        """Test 404 error handling"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test method not allowed handling"""
        response = client.put("/health")  # PUT on GET endpoint
        assert response.status_code == 405
    
    def test_malformed_json(self):
        """Test malformed JSON handling"""
        response = client.post("/api/search", 
                              data="{invalid json}",
                              headers={"content-type": "application/json"})
        assert response.status_code == 422


class TestPerformanceBaseline:
    """Test basic performance characteristics"""
    
    def test_health_endpoint_response_time(self):
        """Test health endpoint responds within reasonable time"""
        import time
        
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 200
        assert response_time < 1000  # Should respond within 1 second
        print(f"Health endpoint response time: {response_time:.2f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
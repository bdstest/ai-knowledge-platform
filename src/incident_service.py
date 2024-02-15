"""
Incident Service - AI-powered incident classification and management
"""

import os
import json
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random

import httpx

logger = logging.getLogger(__name__)

class IncidentService:
    def __init__(self):
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.sample_incidents = []
        
    async def load_sample_incidents(self):
        """Load sample historical incidents for similarity matching"""
        self.sample_incidents = [
            {
                "id": "INC-2024-001",
                "title": "Email server outage",
                "description": "Users unable to send or receive emails",
                "category": "Email Infrastructure",
                "severity": "high",
                "resolution_time": 45,
                "procedures": ["Check email server status", "Verify DNS MX records", "Restart email services"],
                "resolved_at": "2024-02-15T14:30:00Z"
            },
            {
                "id": "INC-2024-002", 
                "title": "Database connection timeout",
                "description": "Application showing database connection timeout errors",
                "category": "Database",
                "severity": "medium",
                "resolution_time": 22,
                "procedures": ["Check database connection pool", "Analyze slow queries", "Restart database connections"],
                "resolved_at": "2024-02-18T09:15:00Z"
            },
            {
                "id": "INC-2024-003",
                "title": "Website loading slowly",
                "description": "Website pages taking more than 10 seconds to load",
                "category": "Performance",
                "severity": "medium", 
                "resolution_time": 67,
                "procedures": ["Check server CPU/memory", "Analyze database queries", "Clear application cache"],
                "resolved_at": "2024-02-20T16:45:00Z"
            },
            {
                "id": "INC-2024-004",
                "title": "Network connectivity issues",
                "description": "Intermittent network connectivity problems affecting multiple users",
                "category": "Network",
                "severity": "high",
                "resolution_time": 89,
                "procedures": ["Check network switches", "Verify internet connectivity", "Restart network equipment"],
                "resolved_at": "2024-02-25T11:20:00Z"
            },
            {
                "id": "INC-2024-005",
                "title": "Login authentication failure",
                "description": "Users cannot log in with correct credentials",
                "category": "Authentication",
                "severity": "critical",
                "resolution_time": 34,
                "procedures": ["Check authentication service", "Verify LDAP connectivity", "Review security logs"],
                "resolved_at": "2024-03-01T08:30:00Z"
            }
        ]
        
        logger.info(f"Loaded {len(self.sample_incidents)} sample incidents")
    
    async def classify_incident(self, description: str, severity: str = "medium", priority: str = "normal") -> Dict[str, Any]:
        """Classify incident using AI and suggest resolution procedures"""
        
        # Generate unique incident ID
        incident_id = f"INC-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Use AI to classify the incident
        classification = await self._ai_classify_incident(description)
        
        # Find similar historical incidents
        similar_incidents = self._find_similar_incidents(description, classification["category"])
        
        # Estimate resolution time based on similar incidents
        estimated_time = self._estimate_resolution_time(classification["category"], severity)
        
        # Auto-assign based on category
        assigned_to = self._auto_assign_incident(classification["category"])
        
        return {
            "incident_id": incident_id,
            "category": classification["category"],
            "confidence": classification["confidence"],
            "procedures": classification["procedures"],
            "eta": estimated_time,
            "similar": similar_incidents,
            "assigned_to": assigned_to,
            "severity": severity,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def _ai_classify_incident(self, description: str) -> Dict[str, Any]:
        """Use AI to classify incident category and suggest procedures"""
        
        # Define categories and their typical procedures
        categories = {
            "Email Infrastructure": ["Check email server status", "Verify DNS MX records", "Restart email services"],
            "Database": ["Check database connection pool", "Analyze slow queries", "Restart database connections"],
            "Network": ["Check network switches", "Verify internet connectivity", "Restart network equipment"], 
            "Performance": ["Check server CPU/memory", "Analyze database queries", "Clear application cache"],
            "Authentication": ["Check authentication service", "Verify LDAP connectivity", "Review security logs"],
            "Security": ["Isolate affected systems", "Review security logs", "Check for malware"],
            "Application": ["Check application logs", "Restart application services", "Verify configuration"],
            "Infrastructure": ["Check hardware status", "Verify power and cooling", "Review system logs"]
        }
        
        try:
            # Try to use Ollama for classification
            prompt = f"""Classify this IT incident and suggest 3 resolution procedures.

Incident Description: {description}

Available Categories: {', '.join(categories.keys())}

Respond with JSON format:
{{
    "category": "category_name",
    "confidence": 0.95,
    "reasoning": "brief explanation",
    "procedures": ["procedure1", "procedure2", "procedure3"]
}}"""

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": "llama2:7b-chat",
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9,
                            "max_tokens": 300
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result.get("response", "").strip()
                    
                    # Try to parse JSON response
                    try:
                        # Extract JSON from response (AI might include extra text)
                        json_start = ai_response.find("{")
                        json_end = ai_response.rfind("}") + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = ai_response[json_start:json_end]
                            parsed = json.loads(json_str)
                            
                            # Validate category
                            if parsed["category"] in categories:
                                return parsed
                    except (json.JSONDecodeError, KeyError):
                        pass
                        
        except Exception as e:
            logger.warning(f"AI classification failed, using fallback: {e}")
        
        # Fallback: Rule-based classification
        description_lower = description.lower()
        
        if any(word in description_lower for word in ["email", "mail", "smtp", "imap"]):
            category = "Email Infrastructure"
        elif any(word in description_lower for word in ["database", "db", "sql", "connection", "timeout"]):
            category = "Database"
        elif any(word in description_lower for word in ["network", "connectivity", "internet", "ping"]):
            category = "Network"
        elif any(word in description_lower for word in ["slow", "performance", "loading", "timeout"]):
            category = "Performance"
        elif any(word in description_lower for word in ["login", "authentication", "password", "access"]):
            category = "Authentication"
        elif any(word in description_lower for word in ["security", "virus", "malware", "breach"]):
            category = "Security"
        elif any(word in description_lower for word in ["application", "app", "service", "server"]):
            category = "Application"
        else:
            category = "Infrastructure"
        
        return {
            "category": category,
            "confidence": 0.75,
            "reasoning": "Rule-based classification",
            "procedures": categories[category]
        }
    
    def _find_similar_incidents(self, description: str, category: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Find similar historical incidents"""
        similar = []
        
        for incident in self.sample_incidents:
            # Simple similarity based on category and keyword matching
            similarity_score = 0.0
            
            # Category match
            if incident["category"] == category:
                similarity_score += 0.5
            
            # Keyword matching
            desc_words = set(description.lower().split())
            incident_words = set(incident["description"].lower().split())
            common_words = desc_words.intersection(incident_words)
            
            if common_words:
                similarity_score += (len(common_words) / max(len(desc_words), len(incident_words))) * 0.5
            
            if similarity_score > 0.3:  # Threshold for similarity
                similar.append({
                    "id": incident["id"],
                    "title": incident["title"],
                    "similarity": round(similarity_score, 2),
                    "resolution_time": incident["resolution_time"],
                    "procedures": incident["procedures"]
                })
        
        # Sort by similarity and return top results
        similar.sort(key=lambda x: x["similarity"], reverse=True)
        return similar[:max_results]
    
    def _estimate_resolution_time(self, category: str, severity: str) -> str:
        """Estimate resolution time based on category and severity"""
        
        # Base times by category (in minutes)
        base_times = {
            "Email Infrastructure": 45,
            "Database": 30,
            "Network": 60,
            "Performance": 75,
            "Authentication": 25,
            "Security": 120,
            "Application": 40,
            "Infrastructure": 90
        }
        
        base_time = base_times.get(category, 60)
        
        # Adjust for severity
        severity_multipliers = {
            "critical": 0.7,  # Faster response for critical
            "high": 0.8,
            "medium": 1.0,
            "low": 1.3
        }
        
        multiplier = severity_multipliers.get(severity, 1.0)
        estimated_minutes = int(base_time * multiplier)
        
        # Add some randomness for realism
        estimated_minutes += random.randint(-10, 15)
        estimated_minutes = max(5, estimated_minutes)  # Minimum 5 minutes
        
        if estimated_minutes < 60:
            return f"{estimated_minutes} minutes"
        else:
            hours = estimated_minutes // 60
            minutes = estimated_minutes % 60
            if minutes == 0:
                return f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                return f"{hours}h {minutes}m"
    
    def _auto_assign_incident(self, category: str) -> Optional[str]:
        """Auto-assign incident based on category"""
        
        assignments = {
            "Email Infrastructure": "email-team@demo.local",
            "Database": "dba-team@demo.local", 
            "Network": "network-ops@demo.local",
            "Performance": "platform-team@demo.local",
            "Authentication": "security-team@demo.local",
            "Security": "security-team@demo.local",
            "Application": "dev-team@demo.local",
            "Infrastructure": "infrastructure-team@demo.local"
        }
        
        return assignments.get(category, "support-team@demo.local")
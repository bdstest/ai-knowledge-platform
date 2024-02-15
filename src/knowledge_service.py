"""
Knowledge Service - AI-powered knowledge retrieval
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class KnowledgeService:
    def __init__(self):
        self.chroma_client = None
        self.embedding_model = None
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.chroma_host = os.getenv("CHROMA_HOST", "http://localhost:8000")
        self.collection_name = "knowledge_base"
        
    async def initialize(self):
        """Initialize the knowledge service"""
        try:
            # Initialize ChromaDB client
            self.chroma_client = chromadb.HttpClient(host=self.chroma_host.replace("http://", "").replace(":8000", ""))
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            # Create or get collection
            try:
                self.collection = self.chroma_client.get_collection(self.collection_name)
                logger.info(f"Using existing collection: {self.collection_name}")
            except Exception:
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Enterprise knowledge base"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize knowledge service: {e}")
            # Fallback to in-memory mode for demo
            self.chroma_client = chromadb.Client()
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            self.collection = self.chroma_client.create_collection(self.collection_name)
    
    async def health_check(self) -> bool:
        """Check if knowledge service is healthy"""
        try:
            if self.chroma_client is None:
                await self.initialize()
            
            # Test collection access
            count = self.collection.count()
            logger.info(f"Knowledge base contains {count} documents")
            return True
        except Exception as e:
            logger.error(f"Knowledge service health check failed: {e}")
            return False
    
    async def check_ollama(self) -> bool:
        """Check Ollama service connectivity"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_host}/api/tags", timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def check_chromadb(self) -> bool:
        """Check ChromaDB connectivity"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.chroma_host}/api/v1/heartbeat", timeout=5.0)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"ChromaDB health check failed: {e}")
            return False
    
    async def load_sample_data(self):
        """Load sample knowledge base data"""
        if self.chroma_client is None:
            await self.initialize()
        
        # Check if data already loaded
        try:
            count = self.collection.count()
            if count > 0:
                logger.info(f"Knowledge base already contains {count} documents")
                return
        except Exception:
            pass
        
        # Sample knowledge base documents
        sample_documents = [
            {
                "id": "kb_001",
                "title": "Network Troubleshooting Guide",
                "content": "Network connectivity issues can be resolved by checking physical connections, verifying IP configuration, testing DNS resolution, and examining firewall rules. Common tools include ping, traceroute, nslookup, and netstat.",
                "category": "Network",
                "document_type": "procedure",
                "tags": ["network", "troubleshooting", "connectivity"]
            },
            {
                "id": "kb_002", 
                "title": "Database Connection Timeout Resolution",
                "content": "Database connection timeouts typically occur due to connection pool exhaustion, long-running queries, or network latency. Increase connection timeout values, optimize queries, and monitor connection pool usage.",
                "category": "Database",
                "document_type": "troubleshooting",
                "tags": ["database", "timeout", "performance"]
            },
            {
                "id": "kb_003",
                "title": "Email Server Configuration",
                "content": "Email server setup requires configuring SMTP, IMAP/POP3 settings, setting up DNS MX records, implementing security protocols like SPF, DKIM, and DMARC, and configuring anti-spam measures.",
                "category": "Email",
                "document_type": "configuration",
                "tags": ["email", "smtp", "configuration"]
            },
            {
                "id": "kb_004",
                "title": "Security Incident Response Playbook",
                "content": "Security incident response involves immediate containment, evidence preservation, threat analysis, communication to stakeholders, remediation steps, and post-incident review. Follow the incident severity matrix for escalation.",
                "category": "Security",
                "document_type": "playbook",
                "tags": ["security", "incident", "response"]
            },
            {
                "id": "kb_005",
                "title": "Backup and Recovery Procedures",
                "content": "Implement 3-2-1 backup strategy: 3 copies of data, 2 different media types, 1 offsite backup. Test backup integrity regularly, document recovery procedures, and maintain recovery time objectives (RTO) and recovery point objectives (RPO).",
                "category": "Backup",
                "document_type": "procedure",
                "tags": ["backup", "recovery", "disaster"]
            },
            {
                "id": "kb_006",
                "title": "Load Balancer Configuration",
                "content": "Configure load balancer health checks, set up backend server pools, implement SSL termination, configure session persistence, and monitor traffic distribution. Use weighted routing for gradual traffic shifts.",
                "category": "Infrastructure",
                "document_type": "configuration", 
                "tags": ["load-balancer", "infrastructure", "scaling"]
            },
            {
                "id": "kb_007",
                "title": "API Rate Limiting Implementation",
                "content": "Implement rate limiting using token bucket or sliding window algorithms. Configure limits per user, IP, or API key. Return HTTP 429 status codes when limits exceeded. Monitor rate limit metrics.",
                "category": "API",
                "document_type": "implementation",
                "tags": ["api", "rate-limiting", "performance"]
            },
            {
                "id": "kb_008",
                "title": "Container Orchestration Best Practices",
                "content": "Use resource limits and requests, implement health checks, configure rolling updates, use secrets management, implement proper logging, and monitor container metrics. Follow the principle of least privilege.",
                "category": "Containers",
                "document_type": "best-practices",
                "tags": ["containers", "kubernetes", "orchestration"]
            }
        ]
        
        try:
            # Prepare data for ChromaDB
            documents = [doc["content"] for doc in sample_documents]
            metadatas = [{
                "title": doc["title"],
                "category": doc["category"],
                "document_type": doc["document_type"],
                "tags": ",".join(doc["tags"]),
                "timestamp": datetime.utcnow().isoformat()
            } for doc in sample_documents]
            ids = [doc["id"] for doc in sample_documents]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(documents).tolist()
            
            # Add to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings
            )
            
            logger.info(f"Loaded {len(sample_documents)} documents into knowledge base")
            
        except Exception as e:
            logger.error(f"Failed to load sample data: {e}")
    
    async def search(self, query: str, max_results: int = 10, include_incidents: bool = True) -> List[Dict[str, Any]]:
        """Search knowledge base with semantic similarity"""
        if self.chroma_client is None:
            await self.initialize()
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode([query]).tolist()[0]
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and len(results['documents']) > 0:
                for i, (doc, metadata, distance) in enumerate(zip(
                    results['documents'][0],
                    results['metadatas'][0], 
                    results['distances'][0]
                )):
                    # Convert distance to relevance score (0-1)
                    relevance = max(0, 1 - distance)
                    
                    formatted_results.append({
                        "title": metadata.get("title", f"Document {i+1}"),
                        "content": doc[:300] + "..." if len(doc) > 300 else doc,
                        "relevance": round(relevance, 3),
                        "source": "knowledge_base",
                        "document_type": metadata.get("document_type", "unknown"),
                        "category": metadata.get("category", "general"),
                        "tags": metadata.get("tags", "").split(",") if metadata.get("tags") else [],
                        "timestamp": metadata.get("timestamp")
                    })
            
            # Add AI-generated response using Ollama
            try:
                ai_response = await self._get_ai_response(query, formatted_results[:3])
                if ai_response:
                    formatted_results.insert(0, {
                        "title": "AI Assistant Response",
                        "content": ai_response,
                        "relevance": 1.0,
                        "source": "ai_assistant",
                        "document_type": "ai_response",
                        "category": "ai_generated",
                        "tags": ["ai", "assistant"],
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except Exception as e:
                logger.warning(f"AI response generation failed: {e}")
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            # Return fallback results for demo
            return [
                {
                    "title": "Fallback: Network Troubleshooting",
                    "content": "Check network connectivity, DNS resolution, and firewall rules.",
                    "relevance": 0.85,
                    "source": "fallback",
                    "document_type": "procedure",
                    "category": "network",
                    "tags": ["network", "troubleshooting"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
    
    async def _get_ai_response(self, query: str, context_docs: List[Dict]) -> Optional[str]:
        """Generate AI response using Ollama"""
        try:
            # Prepare context from top documents
            context = "\n".join([doc["content"] for doc in context_docs[:3]])
            
            prompt = f"""Based on the following knowledge base content, provide a helpful response to the user's query.

Context:
{context}

User Query: {query}

Response (be concise and helpful):"""
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": "llama2:7b-chat",
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "max_tokens": 200
                        }
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("response", "").strip()
                    
        except Exception as e:
            logger.warning(f"AI response generation failed: {e}")
            
        return None
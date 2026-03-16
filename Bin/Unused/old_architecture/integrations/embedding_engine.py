"""
Embedding Engine for Semantic Matching
"""

import os
import logging
from typing import List, Optional, Dict, Any
from openai import OpenAI
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """Generate and manage embeddings for semantic search"""
    
    MODEL = "text-embedding-3-small"  # Fast and efficient
    BATCH_SIZE = 100
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize embedding engine"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY")
        
        self.client = OpenAI(api_key=self.api_key)
        logger.info("Embedding engine initialized")
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """Generate embedding for single text"""
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return None
            
            # Clean and truncate text
            text = text.strip()[:8000]  # Limit to 8000 chars
            
            response = self.client.embeddings.create(
                input=text,
                model=self.MODEL
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for text (len={len(text)})")
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def embed_texts(self, texts: List[str]) -> Dict[str, Optional[List[float]]]:
        """Generate embeddings for multiple texts"""
        embeddings = {}
        
        try:
            # Process in batches
            for i in range(0, len(texts), self.BATCH_SIZE):
                batch = texts[i:i + self.BATCH_SIZE]
                
                # Clean texts
                batch = [t.strip()[:8000] for t in batch if t.strip()]
                
                if not batch:
                    continue
                
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.MODEL
                )
                
                for j, item in enumerate(response.data):
                    embeddings[str(i + j)] = item.embedding
            
            logger.info(f"Generated embeddings for {len(embeddings)} texts")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            return embeddings
    
    @staticmethod
    def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    @staticmethod
    def find_similar_embeddings(
        query_embedding: List[float],
        embedding_list: List[Dict[str, Any]],
        top_k: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find top-k similar embeddings above threshold"""
        try:
            similarities = []
            
            for item in embedding_list:
                embedding = item.get("embedding")
                if embedding:
                    similarity = EmbeddingEngine.cosine_similarity(query_embedding, embedding)
                    if similarity >= threshold:
                        similarities.append({
                            **item,
                            "similarity_score": similarity
                        })
            
            # Sort by similarity descending
            similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            logger.info(f"Found {len(similarities)} similar embeddings")
            return similarities[:top_k]
        except Exception as e:
            logger.error(f"Error finding similar embeddings: {str(e)}")
            return []

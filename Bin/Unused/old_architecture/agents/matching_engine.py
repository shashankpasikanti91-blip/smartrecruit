"""
Matching Engine for Semantic Candidate-JD Matching
"""

import logging
from typing import List, Dict, Any, Optional
from ..integrations.embedding_engine import EmbeddingEngine

logger = logging.getLogger(__name__)


class MatchingEngine:
    """Semantic matching engine for candidates and job descriptions"""
    
    def __init__(self, embedding_engine: Optional[EmbeddingEngine] = None):
        """Initialize matching engine"""
        self.embedding_engine = embedding_engine or EmbeddingEngine()
        logger.info("Matching engine initialized")
    
    def extract_key_terms(self, text: str) -> List[str]:
        """Extract key terms from text"""
        # Simple keyword extraction (can be enhanced with NLP)
        stop_words = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "is", "be"}
        
        words = text.lower().split()
        terms = [w for w in words if len(w) > 3 and w not in stop_words]
        
        return list(set(terms))[:20]  # Top 20 unique terms
    
    def calculate_term_overlap(
        self,
        candidate_terms: List[str],
        jd_terms: List[str]
    ) -> float:
        """Calculate overlap between candidate and JD terms"""
        if not jd_terms:
            return 0.0
        
        candidate_set = set(candidate_terms)
        jd_set = set(jd_terms)
        
        overlap = len(candidate_set & jd_set)
        total = len(jd_set)
        
        return overlap / total if total > 0 else 0.0
    
    def calculate_semantic_similarity(
        self,
        resume_text: str,
        jd_text: str
    ) -> float:
        """Calculate semantic similarity between resume and JD"""
        try:
            # Generate embeddings
            resume_embedding = self.embedding_engine.embed_text(resume_text)
            jd_embedding = self.embedding_engine.embed_text(jd_text)
            
            if not resume_embedding or not jd_embedding:
                logger.warning("Could not generate embeddings")
                return 0.0
            
            # Calculate cosine similarity
            similarity = EmbeddingEngine.cosine_similarity(resume_embedding, jd_embedding)
            
            logger.info(f"Semantic similarity score: {similarity}")
            return similarity
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {str(e)}")
            return 0.0
    
    def calculate_skill_match_score(
        self,
        candidate_skills: List[str],
        required_skills: List[str],
        preferred_skills: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Calculate skill matching score"""
        
        candidate_skills_lower = [s.lower() for s in candidate_skills]
        required_skills_lower = [s.lower() for s in required_skills]
        preferred_skills_lower = [s.lower() for s in (preferred_skills or [])]
        
        # Required skills match
        required_matches = sum(
            1 for skill in required_skills_lower
            if any(skill in cand for cand in candidate_skills_lower)
        )
        required_score = required_matches / len(required_skills_lower) if required_skills_lower else 0
        
        # Preferred skills match
        preferred_matches = sum(
            1 for skill in preferred_skills_lower
            if any(skill in cand for cand in candidate_skills_lower)
        )
        preferred_score = preferred_matches / len(preferred_skills_lower) if preferred_skills_lower else 0
        
        # Overall skill match (weighted)
        overall_skill_score = (required_score * 0.7) + (preferred_score * 0.3)
        
        return {
            "required_skills_match": required_score,
            "preferred_skills_match": preferred_score,
            "overall_skill_score": overall_skill_score,
            "required_matches": required_matches,
            "preferred_matches": preferred_matches
        }
    
    def calculate_experience_match_score(
        self,
        candidate_experience: float,
        required_experience: float,
        preferred_experience: Optional[float] = None
    ) -> Dict[str, Any]:
        """Calculate experience matching score"""
        
        if candidate_experience >= required_experience:
            experience_match = 1.0
            meets_requirement = True
        else:
            # Partial credit for close matches
            experience_match = candidate_experience / required_experience if required_experience > 0 else 0
            meets_requirement = False
        
        # Check if has preferred experience
        has_preferred = False
        if preferred_experience and candidate_experience >= preferred_experience:
            has_preferred = True
        
        return {
            "experience_match_score": min(experience_match, 1.0),
            "meets_requirement": meets_requirement,
            "has_preferred": has_preferred,
            "gap_years": max(0, required_experience - candidate_experience),
            "candidate_years": candidate_experience,
            "required_years": required_experience
        }
    
    def calculate_composite_match_score(
        self,
        resume_text: str,
        jd_text: str,
        candidate_skills: List[str],
        required_skills: List[str],
        candidate_experience: float,
        required_experience: float,
        preferred_skills: Optional[List[str]] = None,
        preferred_experience: Optional[float] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Calculate comprehensive match score"""
        
        # Default weights
        weights = weights or {
            "semantic": 0.2,
            "skills": 0.4,
            "experience": 0.3,
            "term_overlap": 0.1
        }
        
        try:
            # Calculate component scores
            semantic_score = self.calculate_semantic_similarity(resume_text, jd_text)
            
            skill_scores = self.calculate_skill_match_score(
                candidate_skills, required_skills, preferred_skills
            )
            skill_score = skill_scores["overall_skill_score"]
            
            experience_scores = self.calculate_experience_match_score(
                candidate_experience, required_experience, preferred_experience
            )
            experience_score = experience_scores["experience_match_score"]
            
            # Term overlap
            candidate_terms = self.extract_key_terms(resume_text)
            jd_terms = self.extract_key_terms(jd_text)
            term_overlap_score = self.calculate_term_overlap(candidate_terms, jd_terms)
            
            # Composite score
            composite_score = (
                (semantic_score * weights["semantic"]) +
                (skill_score * weights["skills"]) +
                (experience_score * weights["experience"]) +
                (term_overlap_score * weights["term_overlap"])
            )
            
            return {
                "composite_match_score": composite_score,
                "semantic_score": semantic_score,
                "skill_scores": skill_scores,
                "experience_scores": experience_scores,
                "term_overlap_score": term_overlap_score,
                "weights": weights,
                "recommendation": self._get_recommendation(composite_score)
            }
        except Exception as e:
            logger.error(f"Error calculating composite score: {str(e)}")
            return {
                "composite_match_score": 0.0,
                "error": str(e),
                "recommendation": "error"
            }
    
    @staticmethod
    def _get_recommendation(score: float) -> str:
        """Get recommendation based on score"""
        if score >= 0.8:
            return "strong_match"
        elif score >= 0.6:
            return "good_match"
        elif score >= 0.4:
            return "fair_match"
        else:
            return "poor_match"

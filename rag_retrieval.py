"""RAG (Retrieval-Augmented Generation) module for personalized practice"""

from typing import List, Dict, Optional
import os
from sqlalchemy.orm import Session
from database import MathProblem, Answer
from config import CHROMA_PERSIST_DIRECTORY, EMBEDDING_MODEL

class RAGRetrieval:
    """RAG system for retrieving relevant problems based on student performance"""
    
    def __init__(self, db: Session):
        """
        Initialize RAG retrieval system
        
        Args:
            db: Database session
        """
        self.db = db
        self.collection = None
        self._initialized = False
        self.persist_directory = CHROMA_PERSIST_DIRECTORY
        self.embedding_model = EMBEDDING_MODEL
    
    def initialize(self):
        """Initialize ChromaDB for vector storage"""
        if self._initialized:
            return
        
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Initialize ChromaDB client
            self.client = chromadb.Client(Settings(
                persist_directory=self.persist_directory,
                anonymized_telemetry=False
            ))
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="math_problems",
                metadata={"description": "Math problems for adaptive learning"}
            )
            
            self._initialized = True
            print("RAG system initialized successfully")
        except Exception as e:
            print(f"Warning: Could not initialize RAG system: {e}")
            print("The system will work without vector-based retrieval.")
    
    def index_problem(self, problem: MathProblem):
        """
        Index a problem in the vector database
        
        Args:
            problem: MathProblem object to index
        """
        if not self._initialized:
            return
        
        try:
            # Create document text
            doc_text = f"{problem.problem_type}: {problem.problem_text}"
            
            # Add to collection
            self.collection.add(
                documents=[doc_text],
                metadatas=[{
                    "problem_id": problem.id,
                    "problem_type": problem.problem_type,
                    "difficulty": problem.difficulty
                }],
                ids=[f"problem_{problem.id}"]
            )
        except Exception as e:
            print(f"Error indexing problem: {e}")
    
    def find_similar_problems(self, problem_text: str, n_results: int = 5) -> List[Dict]:
        """
        Find similar problems using vector similarity
        
        Args:
            problem_text: Text to search for
            n_results: Number of results to return
        
        Returns:
            List of similar problems
        """
        if not self._initialized:
            return []
        
        try:
            results = self.collection.query(
                query_texts=[problem_text],
                n_results=n_results
            )
            
            similar_problems = []
            for i, problem_id in enumerate(results['ids'][0]):
                pid = int(problem_id.split('_')[1])
                problem = self.db.query(MathProblem).filter(MathProblem.id == pid).first()
                if problem:
                    similar_problems.append({
                        "problem_id": problem.id,
                        "problem_text": problem.problem_text,
                        "problem_type": problem.problem_type,
                        "difficulty": problem.difficulty,
                        "similarity_score": 1.0 - results['distances'][0][i] if 'distances' in results else 1.0
                    })
            
            return similar_problems
        except Exception as e:
            print(f"Error finding similar problems: {e}")
            return []
    
    def get_adaptive_problems(self, limit: int = 10) -> List[Dict]:
        """
        Get adaptive problems based on student's performance
        
        Args:
            limit: Maximum number of problems to return
        
        Returns:
            List of recommended problems
        """
        # Get student's answer history
        answers = self.db.query(Answer).order_by(Answer.timestamp.desc()).limit(50).all()
        
        if not answers:
            # No history, return random problems
            return self._get_random_problems(limit)
        
        # Analyze performance by problem type
        type_performance = {}
        for answer in answers:
            problem = self.db.query(MathProblem).filter(MathProblem.id == answer.problem_id).first()
            if problem:
                if problem.problem_type not in type_performance:
                    type_performance[problem.problem_type] = {"correct": 0, "total": 0}
                type_performance[problem.problem_type]["total"] += 1
                if answer.is_correct:
                    type_performance[problem.problem_type]["correct"] += 1
        
        # Find weak areas (accuracy < 70%)
        weak_types = []
        for ptype, stats in type_performance.items():
            accuracy = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
            if accuracy < 0.7:
                weak_types.append(ptype)
        
        # Get problems from weak areas
        recommended_problems = []
        
        if weak_types:
            # Focus on weak areas
            for ptype in weak_types:
                problems = self.db.query(MathProblem).filter(
                    MathProblem.problem_type == ptype
                ).limit(limit // len(weak_types) + 1).all()
                
                for problem in problems:
                    recommended_problems.append({
                        "problem_id": problem.id,
                        "problem_text": problem.problem_text,
                        "problem_type": problem.problem_type,
                        "difficulty": problem.difficulty,
                        "reason": f"Practice needed in {ptype}"
                    })
        else:
            # Good performance, increase difficulty
            last_problems = [self.db.query(MathProblem).filter(
                MathProblem.id == a.problem_id
            ).first() for a in answers[:5]]
            
            avg_difficulty = sum(p.difficulty for p in last_problems if p) / len(last_problems) if last_problems else 1
            next_difficulty = min(5, int(avg_difficulty) + 1)
            
            problems = self.db.query(MathProblem).filter(
                MathProblem.difficulty >= next_difficulty
            ).limit(limit).all()
            
            for problem in problems:
                recommended_problems.append({
                    "problem_id": problem.id,
                    "problem_text": problem.problem_text,
                    "problem_type": problem.problem_type,
                    "difficulty": problem.difficulty,
                    "reason": "Challenge problem"
                })
        
        return recommended_problems[:limit]
    
    def _get_random_problems(self, limit: int) -> List[Dict]:
        """Get random problems when no history exists"""
        problems = self.db.query(MathProblem).limit(limit).all()
        
        return [{
            "problem_id": p.id,
            "problem_text": p.problem_text,
            "problem_type": p.problem_type,
            "difficulty": p.difficulty,
            "reason": "Getting started"
        } for p in problems]

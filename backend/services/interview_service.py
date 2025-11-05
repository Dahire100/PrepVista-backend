import sys
import os
import json
import time
import gc
from typing import Tuple, Optional, Any, List, Dict

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from interview import (
    InterviewPlan,
    Question,
    Evaluation,
    InterviewResult
)
from resume import extract_text_from_pdf
from config import Config
import google.generativeai as genai


# --------------------------
# Stub functions (temporary implementations)
# --------------------------

def parse_resume(pdf_path: str) -> str:
    """Parse resume using extract_text_from_pdf from resume module"""
    try:
        return extract_text_from_pdf(pdf_path)
    except Exception as e:
        raise Exception(f"Failed to parse resume: {str(e)}") from e


def generate_interview_plan(resume_text: str) -> InterviewPlan:
    """Generate interview plan - stub implementation"""
    # TODO: Implement proper interview plan generation
    try:
        return InterviewPlan(
            branch="Software Engineering",
            skills_summary="Python, Backend Development",
            projects_summary="To be analyzed from resume",
            question_bank=[]
        )
    except Exception as e:
        raise Exception(f"Failed to generate interview plan: {str(e)}") from e


def evaluate_answer(question: Question, answer: str, plan: InterviewPlan) -> Evaluation:
    """Evaluate answer - stub implementation"""
    # TODO: Implement proper answer evaluation
    try:
        return Evaluation(
            score=75,
            feedback="Good answer",
            key_points_covered=[],
            improvement_suggestions=[]
        )
    except Exception as e:
        raise Exception(f"Failed to evaluate answer: {str(e)}") from e


def generate_word_report(results: InterviewResult, output_path: str) -> None:
    """Generate Word report - stub implementation"""
    # TODO: Implement proper report generation
    try:
        # Placeholder implementation
        print(f"Generating report at: {output_path}")
        pass
    except Exception as e:
        raise Exception(f"Failed to generate report: {str(e)}") from e


# --------------------------
# InterviewService Class
# --------------------------

class InterviewService:
    """Service for handling AI interview functionality"""
    
    def __init__(self):
        # Configure Gemini API
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY_1)
        except Exception as e:
            raise Exception(f"Failed to configure Gemini API: {str(e)}") from e
    
    @staticmethod
    def parse_resume_file(pdf_path: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse resume PDF and extract text
        Returns: (resume_text, error)
        """
        try:
            if not os.path.exists(pdf_path):
                return None, f"Resume file not found: {pdf_path}"
            
            resume_text = parse_resume(pdf_path)
            if not resume_text or not resume_text.strip():
                return None, "No text could be extracted from the resume"
                
            return resume_text, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def generate_interview_questions(resume_text: str) -> Tuple[Optional[InterviewPlan], Optional[str]]:
        """
        Generate interview questions based on resume
        Returns: (interview_plan, error)
        """
        try:
            if not resume_text or not resume_text.strip():
                return None, "Resume text is empty or invalid"
                
            plan = generate_interview_plan(resume_text)
            return plan, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def create_interview_plan(resume_text: str) -> Tuple[Optional[InterviewPlan], Optional[str]]:
        """
        Alias for generate_interview_questions method
        Returns: (interview_plan, error)
        """
        return InterviewService.generate_interview_questions(resume_text)
    
    @staticmethod
    def evaluate_candidate_answer(question: Question, answer: str, plan: InterviewPlan) -> Tuple[Optional[Evaluation], Optional[str]]:
        """
        Evaluate candidate's answer
        Returns: (evaluation, error)
        """
        try:
            if not question:
                return None, "Question is required"
            if not answer or not answer.strip():
                return None, "Answer cannot be empty"
            if not plan:
                return None, "Interview plan is required"
                
            evaluation = evaluate_answer(question, answer, plan)
            return evaluation, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def create_interview_result(plan: InterviewPlan, evaluations: List[Evaluation], 
                              candidate_name: str = "Candidate") -> InterviewResult:
        """
        Create InterviewResult object with proper parameters
        """
        try:
            # Check what parameters InterviewResult actually accepts
            # This is a safer way to create the object
            result_data = {
                'interview_plan': plan,
                'evaluations': evaluations,
                # Only include parameters that InterviewResult actually accepts
            }
            
            # Try creating the object with minimal parameters first
            return InterviewResult(
                interview_plan=plan,
                evaluations=evaluations
            )
        except TypeError as e:
            # If the above fails, try with even fewer parameters
            try:
                return InterviewResult(
                    plan=plan,
                    evaluations=evaluations
                )
            except TypeError:
                # Last resort - create with only essential parameters
                return InterviewResult(plan, evaluations)
    
    @staticmethod
    def generate_report(interview_plan: InterviewPlan, evaluations: List[Evaluation], 
                       output_path: str, candidate_name: str = "Candidate") -> Optional[str]:
        """
        Generate interview report - updated to accept individual components
        Returns: error (if any)
        """
        try:
            if not interview_plan:
                return "Interview plan is required"
            if not evaluations:
                return "Evaluations are required"
            
            # Create InterviewResult without candidate_name if it's not accepted
            results = InterviewService.create_interview_result(interview_plan, evaluations, candidate_name)
            
            # Create directory if it doesn't exist
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
                
            generate_word_report(results, output_path)
            return None
        except Exception as e:
            return str(e)
    
    @staticmethod
    def cleanup() -> None:
        """Clean up resources and perform garbage collection"""
        try:
            gc.collect()
        except Exception:
            pass  # Ignore cleanup errors


# Alternative approach if you need to store candidate information
class InterviewResultWrapper:
    """Wrapper class to handle InterviewResult with additional metadata"""
    
    def __init__(self, interview_result: InterviewResult, candidate_name: str = "Candidate"):
        self.interview_result = interview_result
        self.candidate_name = candidate_name
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'candidate_name': self.candidate_name,
            'timestamp': self.timestamp,
            'interview_result': self._result_to_dict(self.interview_result)
        }
    
    def _result_to_dict(self, result: InterviewResult) -> Dict[str, Any]:
        """Convert InterviewResult to dictionary"""
        # This will depend on what attributes InterviewResult has
        return {
            'evaluations': [
                {
                    'score': eval.score if hasattr(eval, 'score') else None,
                    'feedback': eval.feedback if hasattr(eval, 'feedback') else None
                }
                for eval in (result.evaluations if hasattr(result, 'evaluations') else [])
            ]
        }

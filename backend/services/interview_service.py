import sys
import os
import json
import time
import gc

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

# Stub functions until they're implemented
def parse_resume(pdf_path):
    """Parse resume using extract_text_from_pdf from resume module"""
    return extract_text_from_pdf(pdf_path)

def generate_interview_plan(resume_text):
    """Generate interview plan - stub implementation"""
    # TODO: Implement proper interview plan generation
    return InterviewPlan(
        candidate_name="Candidate",
        position="Software Engineer",
        key_skills=["Python", "Backend Development"],
        experience_level="Intermediate",
        questions=[]
    )

def evaluate_answer(question, answer, plan):
    """Evaluate answer - stub implementation"""
    # TODO: Implement proper answer evaluation
    return Evaluation(
        score=75,
        feedback="Good answer",
        key_points_covered=[],
        improvement_suggestions=[]
    )

def generate_word_report(results, output_path):
    """Generate Word report - stub implementation"""
    # TODO: Implement proper report generation
    pass

class InterviewService:
    """Service for handling AI interview functionality"""
    
    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=Config.GEMINI_API_KEY_1)
    
    @staticmethod
    def parse_resume_file(pdf_path):
        """
        Parse resume PDF and extract text
        Returns: (resume_text, error)
        """
        try:
            resume_text = parse_resume(pdf_path)
            return resume_text, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def generate_interview_questions(resume_text):
        """
        Generate interview questions based on resume
        Returns: (interview_plan, error)
        """
        try:
            plan = generate_interview_plan(resume_text)
            return plan, None
        except Exception as e:
            return None, str(e)


    @staticmethod
            create_interview_plan(resume_text):
                        """
                                Alias for generate_interview_questions method
                                        Returns: (interview_plan, error)
                                                """
                        return InterviewService.generate_interview_questions(resume_text)
    
    @staticmethod
    def evaluate_candidate_answer(question, answer, plan):
        """
        Evaluate candidate's answer
        Returns: (evaluation, error)
        """
        try:
            evaluation = evaluate_answer(question, answer, plan)
            return evaluation, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def generate_report(results, output_path):
        """
        Generate interview report
        Returns: error (if any)
        """
        try:
            generate_word_report(results, output_path)
            return None
        except Exception as e:
            return str(e)

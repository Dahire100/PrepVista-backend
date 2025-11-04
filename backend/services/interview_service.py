import sys
import os
import json
import time
import gc

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from interview import (
    parse_resume, 
    generate_interview_plan, 
    evaluate_answer,
    generate_word_report,
    InterviewPlan,
    Question,
    Evaluation,
    InterviewResult
)
from config import Config
import google.generativeai as genai

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
            if not resume_text or len(resume_text.strip()) < 50:
                return None, "Could not extract sufficient text from resume"
            return resume_text, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def create_interview_plan(resume_text):
        """
        Generate interview plan based on resume
        Returns: (plan_dict, error)
        """
        try:
            plan = generate_interview_plan(resume_text)
            if not plan:
                return None, "Failed to generate interview plan"
            
            # Convert to dict for JSON serialization
            plan_dict = {
                'branch': plan.branch,
                'skills_summary': plan.skills_summary,
                'projects_summary': plan.projects_summary,
                'questions': [
                    {
                        'type': q.type,
                        'question': q.question,
                        'category': getattr(q, 'category', 'general')
                    }
                    for q in plan.question_bank
                ],
                'resume_keywords': plan.resume_keywords or []
            }
            
            return plan_dict, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def evaluate_interview_answer(question_data, answer, resume_keywords=None):
        """
        Evaluate a single interview answer
        Returns: (evaluation_dict, error)
        """
        try:
            # Create Question object
            question = Question(
                type=question_data.get('type', 'general'),
                question=question_data.get('question', ''),
                category=question_data.get('category', 'general')
            )
            
            # Evaluate answer
            evaluation = evaluate_answer(question, answer, resume_keywords)
            
            # Convert to dict
            evaluation_dict = {
                'score': evaluation.score,
                'feedback': evaluation.feedback,
                'suggestions': evaluation.suggestions,
                'corrected_answer': evaluation.corrected_answer,
                'keywords_matched': evaluation.keywords_matched or []
            }
            
            return evaluation_dict, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def generate_interview_report(interview_data, output_dir):
        """
        Generate comprehensive interview report
        interview_data should contain:
        - interview_plan: dict with plan details
        - results: list of {question, answer, evaluation, face_detected}
        - camera_verified: bool
        
        Returns: (report_path, average_score, error)
        """
        report_file = None
        try:
            # Reconstruct interview plan
            plan_data = interview_data['interview_plan']
            plan = InterviewPlan(
                branch=plan_data['branch'],
                skills_summary=plan_data['skills_summary'],
                projects_summary=plan_data['projects_summary'],
                question_bank=[
                    Question(type=q['type'], question=q['question'])
                    for q in plan_data['questions']
                ],
                resume_keywords=plan_data.get('resume_keywords', [])
            )
            
            # Reconstruct interview results
            results = []
            for r in interview_data['results']:
                question = Question(
                    type=r['question']['type'],
                    question=r['question']['question']
                )
                
                evaluation = Evaluation(
                    score=r['evaluation']['score'],
                    feedback=r['evaluation']['feedback'],
                    suggestions=r['evaluation']['suggestions'],
                    corrected_answer=r['evaluation']['corrected_answer'],
                    keywords_matched=r['evaluation'].get('keywords_matched', [])
                )
                
                result = InterviewResult(
                    question=question,
                    user_answer=r['answer'],
                    evaluation=evaluation,
                    face_detected=r.get('face_detected', True)
                )
                results.append(result)
            
            # Generate report
            camera_verified = interview_data.get('camera_verified', True)
            report_filename = f"Interview_Report_{os.urandom(8).hex()}.docx"
            report_path = os.path.join(output_dir, report_filename)
            
            # Generate the report
            report_file, avg_score = generate_word_report(plan, results, camera_verified)
            
            # Force cleanup of any resources
            gc.collect()
            time.sleep(0.3)  # Give time for file handles to release
            
            # Move report to correct location
            if report_file and os.path.exists(report_file):
                if report_file != report_path:
                    # Retry logic for moving file
                    for attempt in range(5):
                        try:
                            time.sleep(0.1)
                            os.rename(report_file, report_path)
                            break
                        except PermissionError:
                            if attempt == 4:
                                # If rename fails, try copy and delete
                                import shutil
                                shutil.copy2(report_file, report_path)
                                time.sleep(0.3)
                                # Try to delete original with retry
                                for del_attempt in range(3):
                                    try:
                                        gc.collect()
                                        time.sleep(0.2)
                                        os.remove(report_file)
                                        break
                                    except:
                                        if del_attempt == 2:
                                            print(f"Warning: Could not delete temp report file: {report_file}")
                                break
                            gc.collect()
                            time.sleep(0.2 * (attempt + 1))
                            continue
                
                return report_path, avg_score, None
            
            return None, 0, "Report generation failed"
            
        except Exception as e:
            # Cleanup on error
            if report_file and os.path.exists(report_file):
                gc.collect()
                time.sleep(0.2)
                for attempt in range(3):
                    try:
                        os.remove(report_file)
                        break
                    except:
                        if attempt < 2:
                            time.sleep(0.2)
            return None, 0, str(e)
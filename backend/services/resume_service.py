import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from resume import (
    extract_text_from_pdf,
    analyze_resume_with_gemini,
    generate_report
)
from config import Config
import google.generativeai as genai

class ResumeService:
    """Service for handling resume analysis functionality"""
    
    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=Config.GEMINI_API_KEY_2)
    
    @staticmethod
    def extract_resume_text(pdf_path):
        """
        Extract text from resume PDF
        Returns: (text, error)
        """
        try:
            text = extract_text_from_pdf(pdf_path)
            if not text or len(text.strip()) < 50:
                return None, "Could not extract sufficient text from PDF"
            return text, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def analyze_resume(resume_text, job_description):
        """
        Analyze resume against job description
        Returns: (analysis_results, error)
        """
        try:
            if len(job_description.strip()) < 50:
                return None, "Job description is too short"
            
            results = analyze_resume_with_gemini(resume_text, job_description)
            
            if not results:
                return None, "Analysis failed - AI service error"
            
            return results, None
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def generate_analysis_report(analysis_results, output_dir):
        """
        Generate comprehensive resume analysis report
        Returns: (report_path, error)
        """
        try:
            # Generate unique filename
            candidate_name = analysis_results.get('candidate_info', {}).get('name', 'Unknown')
            safe_name = "".join(c for c in candidate_name if c.isalnum() or c in (' ', '_')).replace(' ', '_')
            
            # CHANGED: Use .docx extension instead of .pdf
            report_filename = f"Resume_Analysis_{safe_name}_{os.urandom(8).hex()}.docx"
            report_path = os.path.join(output_dir, report_filename)
            
            # Generate report - this creates a DOCX file
            from resume import generate_report
            
            # CHANGED: Pass report_path as is (it's already .docx)
            # The generate_report function will create DOCX
            doc = generate_report(analysis_results, report_path)
            
            if doc and os.path.exists(report_path):
                return report_path, None
            
            return None, "Report generation failed"
            
        except Exception as e:
            return None, str(e)
    
    @staticmethod
    def get_analysis_summary(analysis_results):
        """Generate text summary of analysis results"""
        summary = []
        
        # Candidate info
        info = analysis_results.get('candidate_info', {})
        summary.append(f"Candidate: {info.get('name', 'N/A')}")
        
        # Scores
        ats_score = analysis_results.get('ats_score', 0)
        match_score = analysis_results.get('match_score', 0)
        summary.append(f"\nATS Compliance: {ats_score}%")
        summary.append(f"Job Match Score: {match_score}%")
        
        # Recommendation
        recommendation = analysis_results.get('recommendation', 'N/A')
        summary.append(f"\nRecommendation: {recommendation}")
        
        # Key strengths
        strengths = analysis_results.get('strengths', [])
        if strengths:
            summary.append("\nKey Strengths:")
            for strength in strengths[:3]:
                summary.append(f"- {strength}")
        
        # Areas for improvement
        weaknesses = analysis_results.get('weaknesses', [])
        if weaknesses:
            summary.append("\nAreas for Improvement:")
            for weakness in weaknesses[:3]:
                summary.append(f"- {weakness}")
        
        return '\n'.join(summary)
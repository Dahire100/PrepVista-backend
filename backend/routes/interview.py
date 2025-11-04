from flask import Blueprint, request, jsonify, send_file
from models import User, Analysis
from services import InterviewService
from utils import token_required, save_file, delete_file
import os

interview_bp = Blueprint('interview', __name__, url_prefix='/api/interview')

def init_interview_routes(db):
    user_model = User(db)
    analysis_model = Analysis(db)
    interview_service = InterviewService()
    
    @interview_bp.route('/plan', methods=['POST'])  # FIXED: Removed typo 'POSTa'
    @token_required
    def create_interview_plan(current_user_id):
        """Generate interview plan from resume"""
        try:
            # Check usage limit - DISABLED for testing
            # if not user_model.check_analysis_limit(current_user_id):
            #     return jsonify({'error': 'Analysis limit reached. Please upgrade your plan.'}), 403
            
            # Check if file is present
            if 'resume' not in request.files:
                return jsonify({'error': 'No resume file provided'}), 400
            
            resume_file = request.files['resume']
            
            if resume_file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Save resume file
            resume_path, error = save_file(resume_file, 'resumes')
            if error:
                return jsonify({'error': error}), 400
            
            try:
                # Parse resume
                resume_text, error = interview_service.parse_resume_file(resume_path)
                if error:
                    return jsonify({'error': error}), 400
                
                # Generate interview plan
                plan, error = interview_service.create_interview_plan(resume_text)
                if error:
                    return jsonify({'error': error}), 500
                
                return jsonify({
                    'message': 'Interview plan generated successfully',
                    'plan': plan
                }), 200
                
            finally:
                # Clean up resume file
                if resume_path and os.path.exists(resume_path):
                    import gc
                    import time
                    gc.collect()
                    time.sleep(0.1)
                    try:
                        delete_file(resume_path)
                    except Exception as e:
                        print(f"Cleanup warning: {str(e)}")
                    
        except Exception as e:
            return jsonify({'error': f'Plan generation failed: {str(e)}'}), 500
    
    @interview_bp.route('/evaluate', methods=['POST'])
    @token_required
    def evaluate_answer(current_user_id):
        """Evaluate a single interview answer"""
        try:
            data = request.get_json()
            
            # Validate input
            if 'question' not in data or 'answer' not in data:
                return jsonify({'error': 'Question and answer required'}), 400
            
            question = data['question']
            answer = data['answer']
            resume_keywords = data.get('resume_keywords', None)
            
            # Evaluate answer
            evaluation, error = interview_service.evaluate_interview_answer(
                question, answer, resume_keywords
            )
            
            if error:
                return jsonify({'error': error}), 500
            
            return jsonify({
                'message': 'Answer evaluated successfully',
                'evaluation': evaluation
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Evaluation failed: {str(e)}'}), 500
    
    @interview_bp.route('/complete', methods=['POST'])
    @token_required
    def complete_interview(current_user_id):
        """Complete interview and generate report"""
        try:
            data = request.get_json()
            
            # Validate input
            required_fields = ['interview_plan', 'results']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
            
            # Generate report
            from config import Config
            report_path, avg_score, error = interview_service.generate_interview_report(
                data, Config.UPLOAD_FOLDER
            )
            
            if error:
                return jsonify({'error': error}), 500
            
            # Save to database
            analysis_record = analysis_model.create_analysis(
                user_id=current_user_id,
                analysis_type='interview',
                data={
                    'average_score': avg_score,
                    'branch': data['interview_plan']['branch'],
                    'questions_count': len(data['results']),
                    'camera_verified': data.get('camera_verified', False)
                },
                report_path=report_path
            )
            
            # Increment usage count - DISABLED for testing
            # user_model.increment_analyses_count(current_user_id)
            
            return jsonify({
                'message': 'Interview completed successfully',
                'analysis_id': analysis_record['_id'],
                'average_score': avg_score,
                'report_available': True
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Interview completion failed: {str(e)}'}), 500
    
    @interview_bp.route('/report/<analysis_id>', methods=['GET'])
    @token_required
    def download_interview_report(current_user_id, analysis_id):
        """Download interview report"""
        try:
            # Get analysis record
            analysis = analysis_model.get_analysis_by_id(analysis_id)
            
            if not analysis:
                return jsonify({'error': 'Analysis not found'}), 404
            
            # Check ownership
            if analysis['user_id'] != current_user_id:
                return jsonify({'error': 'Unauthorized access'}), 403
            
            # Check if it's an interview analysis
            if analysis['analysis_type'] != 'interview':
                return jsonify({'error': 'Not an interview analysis'}), 400
            
            # Get report path
            report_path = analysis.get('report_path')
            
            if not report_path or not os.path.exists(report_path):
                return jsonify({'error': 'Report not found'}), 404
            
            # Determine file type and set correct mimetype
            file_extension = os.path.splitext(report_path)[1].lower()
            if file_extension == '.pdf':
                mimetype = 'application/pdf'
            elif file_extension in ['.docx', '.doc']:
                mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:
                mimetype = 'application/octet-stream'
            
            # Send file
            return send_file(
                report_path,
                as_attachment=True,
                download_name=os.path.basename(report_path),
                mimetype=mimetype
            )
            
        except Exception as e:
            return jsonify({'error': f'Download failed: {str(e)}'}), 500
    
    return interview_bp
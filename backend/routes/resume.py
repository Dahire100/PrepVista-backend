from flask import Blueprint, request, jsonify, send_file
from models import User, Analysis
from services import ResumeService
from utils import token_required, save_file, delete_file
import os

resume_bp = Blueprint('resume', __name__, url_prefix='/api/resume')

def init_resume_routes(db):
    user_model = User(db)
    analysis_model = Analysis(db)
    resume_service = ResumeService()
    
    @resume_bp.route('/analyze', methods=['POST'])
    @token_required
    def analyze_resume(current_user_id):
        """Analyze resume against job description"""
        try:
            # Check usage limit (commented out for now)
            # if not user_model.check_analysis_limit(current_user_id):
            #     return jsonify({'error': 'Analysis limit reached. Please upgrade your plan.'}), 403
            
            # Check if file is present
            if 'resume' not in request.files:
                return jsonify({'error': 'No resume file provided'}), 400
            
            resume_file = request.files['resume']
            
            if resume_file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Get job description from form data
            job_description = request.form.get('job_description', '')
            
            if len(job_description.strip()) < 50:
                return jsonify({'error': 'Job description is too short (minimum 50 characters)'}), 400
            
            # Save resume file
            resume_path, error = save_file(resume_file, 'resumes')
            if error:
                return jsonify({'error': error}), 400
            
            try:
                # Extract resume text
                resume_text, error = resume_service.extract_resume_text(resume_path)
                if error:
                    return jsonify({'error': error}), 400
                
                # Analyze resume
                analysis_results, error = resume_service.analyze_resume(resume_text, job_description)
                if error:
                    return jsonify({'error': error}), 500
                
                # Generate report
                from config import Config
                report_path, error = resume_service.generate_analysis_report(
                    analysis_results, Config.UPLOAD_FOLDER
                )
                
                if error:
                    return jsonify({'error': error}), 500
                
                # Save to database
                analysis_record = analysis_model.create_analysis(
                    user_id=current_user_id,
                    analysis_type='resume',
                    data={
                        'ats_score': analysis_results.get('ats_score', 0),
                        'match_score': analysis_results.get('match_score', 0),
                        'candidate_name': analysis_results.get('candidate_info', {}).get('name', 'Unknown'),
                        'recommendation': analysis_results.get('recommendation', 'N/A'),
                        'improvement_tips': analysis_results.get('improvement_tips', [])
                    },
                    report_path=report_path
                )
                
                # Increment usage count (commented out for now)
                # user_model.increment_analyses_count(current_user_id)
                
                # Generate summary
                summary = resume_service.get_analysis_summary(analysis_results)
                
                return jsonify({
                    'message': 'Resume analysis completed successfully',
                    'analysis_id': analysis_record['_id'],
                    'results': {
                        'ats_score': analysis_results.get('ats_score', 0),
                        'match_score': analysis_results.get('match_score', 0),
                        'candidate_info': analysis_results.get('candidate_info', {}),
                        'strengths': analysis_results.get('strengths', []),
                        'weaknesses': analysis_results.get('weaknesses', []),
                        'improvement_tips': analysis_results.get('improvement_tips', []),
                        'keywords_found': analysis_results.get('keywords_found', []),
                        'keywords_missing': analysis_results.get('keywords_missing', []),
                        'recommendation': analysis_results.get('recommendation', 'N/A')
                    },
                    'summary': summary,
                    'report_available': True
                }), 200
                
            finally:
                # Clean up resume file
                if os.path.exists(resume_path):
                    delete_file(resume_path)
                    
        except Exception as e:
            return jsonify({'error': f'Analysis failed: {str(e)}'}), 500
    
    @resume_bp.route('/report/<analysis_id>', methods=['GET'])
    @token_required
    def download_resume_report(current_user_id, analysis_id):
        """Download resume analysis report"""
        try:
            # Get analysis record
            analysis = analysis_model.get_analysis_by_id(analysis_id)
            
            if not analysis:
                return jsonify({'error': 'Analysis not found'}), 404
            
            # Check ownership
            if analysis['user_id'] != current_user_id:
                return jsonify({'error': 'Unauthorized access'}), 403
            
            # Check if it's a resume analysis
            if analysis['analysis_type'] != 'resume':
                return jsonify({'error': 'Not a resume analysis'}), 400
            
            # Get report path
            report_path = analysis.get('report_path')
            
            if not report_path or not os.path.exists(report_path):
                return jsonify({'error': 'Report not found'}), 404
            
            # Determine the actual file type
            file_extension = os.path.splitext(report_path)[1].lower()
            
            # Set appropriate mimetype based on file extension
            if file_extension == '.pdf':
                mimetype = 'application/pdf'
            elif file_extension == '.docx':
                mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            elif file_extension == '.doc':
                mimetype = 'application/msword'
            else:
                mimetype = 'application/octet-stream'
            
            # Send file with correct mimetype
            return send_file(
                report_path,
                as_attachment=True,
                download_name=os.path.basename(report_path),
                mimetype=mimetype
            )
            
        except Exception as e:
            return jsonify({'error': f'Download failed: {str(e)}'}), 500
    
    return resume_bp
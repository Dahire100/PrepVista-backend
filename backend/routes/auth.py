from flask import Blueprint, request, jsonify, send_file
from models import User
from utils import token_required, generate_token
import base64
import os
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import uuid
import zipfile
from io import BytesIO
from datetime import datetime
import shutil

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads/profile_photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_photo(file_data):
    """Save profile photo and return the file path or URL"""
    try:
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Check if file_data is base64 encoded
        if isinstance(file_data, str) and file_data.startswith('data:image'):
            # Extract base64 data
            header, encoded = file_data.split(',', 1)
            file_type = header.split('/')[1].split(';')[0]
            
            # Generate unique filename
            filename = f"{uuid.uuid4()}.{file_type}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            
            # Decode and save
            with open(filepath, 'wb') as f:
                f.write(base64.b64decode(encoded))
            
            # Return relative path
            return f"/uploads/profile_photos/{filename}"
        else:
            # If it's already a URL, return as is
            return file_data
            
    except Exception as e:
        print(f"Error saving profile photo: {str(e)}")
        return None

def init_auth_routes(db):
    user_model = User(db)
    
    @auth_bp.route('/register', methods=['POST'])
    def register():
        """Register a new user"""
        try:
            data = request.get_json()
            
            # Validate input
            required_fields = ['email', 'password', 'full_name']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400
            
            email = data['email'].strip()
            password = data['password']
            full_name = data['full_name'].strip()
            
            # Basic validation
            if len(password) < 6:
                return jsonify({'error': 'Password must be at least 6 characters'}), 400
            
            if '@' not in email:
                return jsonify({'error': 'Invalid email format'}), 400
            
            # Create user
            user, error = user_model.create_user(email, password, full_name)
            
            if error:
                return jsonify({'error': error}), 400
            
            # Generate token
            token = generate_token(user['_id'])
            
            return jsonify({
                'message': 'User registered successfully',
                'token': token,
                'user': user
            }), 201
            
        except Exception as e:
            return jsonify({'error': f'Registration failed: {str(e)}'}), 500
    
    @auth_bp.route('/login', methods=['POST'])
    def login():
        """Login user"""
        try:
            data = request.get_json()
            
            # Validate input
            if 'email' not in data or 'password' not in data:
                return jsonify({'error': 'Email and password required'}), 400
            
            email = data['email'].strip()
            password = data['password']
            
            # Authenticate user
            user, error = user_model.authenticate(email, password)
            
            if error:
                return jsonify({'error': error}), 401
            
            # Generate token
            token = generate_token(user['_id'])
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': user
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Login failed: {str(e)}'}), 500
    
    @auth_bp.route('/me', methods=['GET'])
    @token_required
    def get_current_user(current_user_id):
        """Get current user profile"""
        try:
            user = user_model.get_user_by_id(current_user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify({'user': user}), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to fetch user: {str(e)}'}), 500
    
    @auth_bp.route('/update', methods=['PUT'])
    @token_required
    def update_profile(current_user_id):
        """Update user profile"""
        try:
            data = request.get_json()
            
            # Fields that can be updated
            allowed_fields = ['full_name', 'profile']
            update_data = {k: v for k, v in data.items() if k in allowed_fields}
            
            if not update_data:
                return jsonify({'error': 'No valid fields to update'}), 400
            
            # Handle profile photo if present
            if 'profile' in update_data and update_data['profile'] and 'profile_photo' in update_data['profile']:
                photo_data = update_data['profile']['profile_photo']
                if photo_data and isinstance(photo_data, str) and photo_data.startswith('data:image'):
                    # Save the photo and get the path
                    photo_path = save_profile_photo(photo_data)
                    if photo_path:
                        update_data['profile']['profile_photo'] = photo_path
                    else:
                        # If saving fails, remove it from update
                        del update_data['profile']['profile_photo']
            
            user = user_model.update_user(current_user_id, update_data)
            
            if not user:
                return jsonify({'error': 'Update failed'}), 400
            
            return jsonify({
                'message': 'Profile updated successfully',
                'user': user
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Update failed: {str(e)}'}), 500
    
    @auth_bp.route('/upload-photo', methods=['POST'])
    @token_required
    def upload_profile_photo(current_user_id):
        """Upload profile photo as multipart/form-data"""
        try:
            # Check if file is in request
            if 'photo' not in request.files:
                return jsonify({'error': 'No photo file provided'}), 400
            
            file = request.files['photo']
            
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Validate file
            if not allowed_file(file.filename):
                return jsonify({'error': 'Invalid file type. Allowed: png, jpg, jpeg, gif, webp'}), 400
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                return jsonify({'error': 'File too large. Maximum size is 5MB'}), 400
            
            # Generate secure filename
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            # Create upload directory
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            # Save file
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(filepath)
            
            # Update user profile with photo path
            photo_url = f"/uploads/profile_photos/{unique_filename}"
            
            # Get current user profile to merge with existing data
            user = user_model.get_user_by_id(current_user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
                
            current_profile = user.get('profile', {})
            
            # Delete old photo if exists
            old_photo = current_profile.get('profile_photo')
            if old_photo and old_photo.startswith('/uploads/'):
                old_path = old_photo[1:]  # Remove leading slash
                if os.path.exists(old_path):
                    try:
                        os.remove(old_path)
                    except Exception as e:
                        print(f"Error deleting old photo: {e}")
            
            current_profile['profile_photo'] = photo_url
            
            update_data = {
                'profile': current_profile
            }
            
            updated_user = user_model.update_user(current_user_id, update_data)
            
            if not updated_user:
                return jsonify({'error': 'Failed to update profile'}), 400
            
            return jsonify({
                'message': 'Photo uploaded successfully',
                'photo_url': photo_url,
                'user': updated_user
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Upload failed: {str(e)}'}), 500
    
    @auth_bp.route('/change-password', methods=['POST'])
    @token_required
    def change_password(current_user_id):
        """Change user password"""
        try:
            data = request.get_json()
            
            # Validate input
            if 'current_password' not in data or 'new_password' not in data:
                return jsonify({'error': 'Current password and new password required'}), 400
            
            current_password = data['current_password']
            new_password = data['new_password']
            
            # Validate new password
            if len(new_password) < 6:
                return jsonify({'error': 'New password must be at least 6 characters'}), 400
            
            # Get user
            user = user_model.get_user_by_id(current_user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Verify current password
            if not check_password_hash(user.get('password_hash', ''), current_password):
                return jsonify({'error': 'Current password is incorrect'}), 401
            
            # Hash new password
            new_password_hash = generate_password_hash(new_password)
            
            # Update password in database
            db.users.update_one(
                {'_id': user['_id']},
                {'$set': {'password_hash': new_password_hash}}
            )
            
            return jsonify({
                'message': 'Password changed successfully'
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Password change failed: {str(e)}'}), 500
    
    @auth_bp.route('/export-data', methods=['GET'])
    @token_required
    def export_data(current_user_id):
        """Export all user data as a ZIP file"""
        try:
            # Get user data
            user = user_model.get_user_by_id(current_user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Get analysis history
            analyses = list(db.analyses.find({'user_id': current_user_id}))
            
            # Create a BytesIO object to store the ZIP
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add user profile data
                import json
                
                # Remove sensitive data
                user_export = {k: v for k, v in user.items() if k != 'password_hash'}
                user_export['_id'] = str(user_export['_id'])
                
                user_json = json.dumps(user_export, indent=2, default=str)
                zip_file.writestr('profile.json', user_json)
                
                # Add analysis history
                analyses_export = []
                for analysis in analyses:
                    analysis_data = {k: v for k, v in analysis.items()}
                    analysis_data['_id'] = str(analysis_data['_id'])
                    analysis_data['user_id'] = str(analysis_data['user_id'])
                    analyses_export.append(analysis_data)
                
                if analyses_export:
                    analyses_json = json.dumps(analyses_export, indent=2, default=str)
                    zip_file.writestr('analysis_history.json', analyses_json)
                
                # Add README
                readme_content = f"""
Data Export for {user.get('full_name', 'User')}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This ZIP file contains:
1. profile.json - Your account and profile information
2. analysis_history.json - Your interview analysis history (if any)

You can import this data or keep it as a backup.
"""
                zip_file.writestr('README.txt', readme_content.strip())
            
            # Prepare the file for sending
            zip_buffer.seek(0)
            
            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f'user_data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
            )
            
        except Exception as e:
            return jsonify({'error': f'Data export failed: {str(e)}'}), 500
    
    @auth_bp.route('/delete-account', methods=['DELETE'])
    @token_required
    def delete_account(current_user_id):
        """Permanently delete user account and all associated data"""
        try:
            data = request.get_json() or {}
            
            # Require password confirmation for security
            if 'password' not in data:
                return jsonify({'error': 'Password confirmation required'}), 400
            
            password = data['password']
            
            # Get user
            user = user_model.get_user_by_id(current_user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            # Verify password
            if not check_password_hash(user.get('password_hash', ''), password):
                return jsonify({'error': 'Incorrect password'}), 401
            
            # Delete user's profile photo if exists
            if user.get('profile', {}).get('profile_photo'):
                photo_path = user['profile']['profile_photo']
                if photo_path.startswith('/uploads/'):
                    full_path = photo_path[1:]  # Remove leading slash
                    if os.path.exists(full_path):
                        try:
                            os.remove(full_path)
                        except Exception as e:
                            print(f"Error deleting profile photo: {e}")
            
            # Delete all analyses
            db.analyses.delete_many({'user_id': current_user_id})
            
            # Delete user account
            result = db.users.delete_one({'_id': user['_id']})
            
            if result.deleted_count == 0:
                return jsonify({'error': 'Failed to delete account'}), 500
            
            return jsonify({
                'message': 'Account deleted successfully'
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Account deletion failed: {str(e)}'}), 500
    
    @auth_bp.route('/clear-data', methods=['DELETE'])
    @token_required
    def clear_user_data(current_user_id):
        """Clear all user practice data but keep the account"""
        try:
            # Delete all analyses
            result = db.analyses.delete_many({'user_id': current_user_id})
            
            # Reset subscription usage if the field exists
            user = user_model.get_user_by_id(current_user_id)
            if user and 'subscription' in user:
                db.users.update_one(
                    {'_id': current_user_id},
                    {'$set': {'subscription.analyses_used': 0}}
                )
            
            return jsonify({
                'message': f'Successfully cleared {result.deleted_count} analysis records',
                'deleted_count': result.deleted_count
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'Failed to clear data: {str(e)}'}), 500
    
    return auth_bp
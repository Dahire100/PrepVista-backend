from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from config import Config
import os

# Import route initializers
from routes import (
    init_auth_routes,
    init_analysis_routes,
    init_interview_routes,
    init_resume_routes
)

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    Config.init_app(app)
    
    # Enable CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                Config.FRONTEND_URL,      # your deployed frontend
                "http://localhost:3000",  # React dev (older default)
                "http://localhost:5173"   # Vite dev server
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": ["Content-Type", "Authorization", "Content-Disposition"],
            "supports_credentials": True
        },
        r"/uploads/*": {
            "origins": [
                Config.FRONTEND_URL,
                "http://localhost:3000",
                "http://localhost:5173"
            ],
            "methods": ["GET"],
            "allow_headers": ["Content-Type"],
            "supports_credentials": False
        }
    })
    
    # Connect to MongoDB
    try:
        client = MongoClient(Config.MONGO_URI)
        db = client[Config.DB_NAME]
        
        # Test connection
        client.server_info()
        print(f"✅ Connected to MongoDB: {Config.DB_NAME}")
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("Please ensure MongoDB is running on your system.")
        raise
    
    # Create upload directories
    upload_dirs = [
        'uploads/profile_photos',
        'uploads/videos',
        'uploads/resumes'
    ]
    for directory in upload_dirs:
        os.makedirs(directory, exist_ok=True)
    print(f"✅ Upload directories created/verified")
    
    # Register blueprints
    app.register_blueprint(init_auth_routes(db))
    app.register_blueprint(init_analysis_routes(db))
    app.register_blueprint(init_interview_routes(db))
    app.register_blueprint(init_resume_routes(db))
    
    # Serve uploaded files (profile photos, etc.)
    @app.route('/uploads/<path:filename>', methods=['GET'])
    def serve_upload(filename):
        """
        Serve uploaded files from the uploads directory.
        This endpoint handles profile photos, videos, and other uploaded content.
        """
        try:
            return send_from_directory('uploads', filename)
        except FileNotFoundError:
            return jsonify({'error': 'File not found'}), 404
        except Exception as e:
            return jsonify({'error': f'Error serving file: {str(e)}'}), 500
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'Server is running',
            'database': 'connected',
            'upload_dirs': {
                'profile_photos': os.path.exists('uploads/profile_photos'),
                'videos': os.path.exists('uploads/videos'),
                'resumes': os.path.exists('uploads/resumes')
            }
        }), 200
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'message': 'Career Preparation Platform API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'analysis': '/api/analysis',
                'interview': '/api/interview',
                'resume': '/api/resume',
                'uploads': '/uploads/<filename>'
            }
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'error': 'File too large. Maximum size is 100MB'}), 413
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    print("\n" + "="*50)
    print("🚀 Starting Career Preparation Platform API")
    print("="*50)
    print(f"🌐 Server: http://localhost:{Config.FLASK_PORT}")
    print(f"🗄️  Database: {Config.DB_NAME}")
    print(f"🌍 CORS: {Config.FRONTEND_URL}")
    print(f"📁 Upload Directory: uploads/")
    print(f"🔧 Debug Mode: {Config.FLASK_DEBUG}")
    print("="*50)
    print("\n📋 Available Endpoints:")
    print(f"  • Health Check: http://localhost:{Config.FLASK_PORT}/api/health")
    print(f"  • Auth: http://localhost:{Config.FLASK_PORT}/api/auth")
    print(f"  • Uploads: http://localhost:{Config.FLASK_PORT}/uploads/<filename>")
    print("="*50 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )
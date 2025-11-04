from .auth import init_auth_routes
from .analysis import init_analysis_routes
from .interview import init_interview_routes
from .resume import init_resume_routes

__all__ = [
    'init_auth_routes',
    'init_analysis_routes', 
    'init_interview_routes',
    'init_resume_routes'
]
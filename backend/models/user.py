from datetime import datetime
from bson import ObjectId
import bcrypt

class User:
    def __init__(self, db):
        self.collection = db['users']
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        self.collection.create_index('email', unique=True)
        self.collection.create_index('created_at')
    
    def create_user(self, email, password, full_name):
        """Create a new user"""
        # Check if user already exists
        if self.collection.find_one({'email': email.lower()}):
            return None, "User already exists"
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_data = {
            'email': email.lower(),
            'password': hashed_password,
            'full_name': full_name,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'profile': {
                'phone': '',
                'linkedin': '',
                'location': ''
            },
            'subscription': {
                'plan': 'free',
                'analyses_used': 0,
                'analyses_limit': 5
            }
        }
        
        result = self.collection.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        
        return self._serialize_user(user_data), None
    
    def authenticate(self, email, password):
        """Authenticate user credentials"""
        user = self.collection.find_one({'email': email.lower()})
        
        if not user:
            return None, "Invalid credentials"
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return None, "Invalid credentials"
        
        return self._serialize_user(user), None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        try:
            user = self.collection.find_one({'_id': ObjectId(user_id)})
            if user:
                return self._serialize_user(user)
            return None
        except:
            return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        user = self.collection.find_one({'email': email.lower()})
        if user:
            return self._serialize_user(user)
        return None
    
    def update_user(self, user_id, update_data):
        """Update user information"""
        try:
            update_data['updated_at'] = datetime.utcnow()
            
            self.collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
            
            return self.get_user_by_id(user_id)
        except:
            return None
    
    def increment_analyses_count(self, user_id):
        """Increment the number of analyses used"""
        try:
            self.collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$inc': {'subscription.analyses_used': 1}}
            )
            return True
        except:
            return False
    
    def check_analysis_limit(self, user_id):
        """Check if user has reached analysis limit"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        subscription = user.get('subscription', {})
        used = subscription.get('analyses_used', 0)
        limit = subscription.get('analyses_limit', 5)
        
        return used < limit
    
    def _serialize_user(self, user):
        """Convert user document to JSON-serializable format"""
        if not user:
            return None
        
        user['_id'] = str(user['_id'])
        user.pop('password', None)  # Remove password from response
        
        return user
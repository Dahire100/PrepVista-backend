from datetime import datetime
from bson import ObjectId

class Analysis:
    def __init__(self, db):
        self.collection = db['analyses']
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes"""
        self.collection.create_index('user_id')
        self.collection.create_index('analysis_type')
        self.collection.create_index('created_at')
    
    def create_analysis(self, user_id, analysis_type, data, report_path=None):
        """Create a new analysis record"""
        analysis_data = {
            'user_id': str(user_id),
            'analysis_type': analysis_type,  # 'video', 'interview', 'resume'
            'data': data,
            'report_path': report_path,
            'created_at': datetime.utcnow(),
            'status': 'completed'
        }
        
        result = self.collection.insert_one(analysis_data)
        analysis_data['_id'] = result.inserted_id
        
        return self._serialize_analysis(analysis_data)
    
    def get_user_analyses(self, user_id, analysis_type=None, limit=10):
        """Get all analyses for a user"""
        query = {'user_id': str(user_id)}
        
        if analysis_type:
            query['analysis_type'] = analysis_type
        
        analyses = self.collection.find(query).sort('created_at', -1).limit(limit)
        
        return [self._serialize_analysis(a) for a in analyses]
    
    def get_analysis_by_id(self, analysis_id):
        """Get specific analysis by ID"""
        try:
            analysis = self.collection.find_one({'_id': ObjectId(analysis_id)})
            if analysis:
                return self._serialize_analysis(analysis)
            return None
        except:
            return None
    
    def delete_analysis(self, analysis_id, user_id):
        """Delete an analysis (only by owner)"""
        try:
            result = self.collection.delete_one({
                '_id': ObjectId(analysis_id),
                'user_id': str(user_id)
            })
            return result.deleted_count > 0
        except:
            return False
    
    def get_user_stats(self, user_id):
        """Get statistics for user's analyses"""
        pipeline = [
            {'$match': {'user_id': str(user_id)}},
            {'$group': {
                '_id': '$analysis_type',
                'count': {'$sum': 1}
            }}
        ]
        
        results = list(self.collection.aggregate(pipeline))
        
        stats = {
            'total': 0,
            'video': 0,
            'interview': 0,
            'resume': 0
        }
        
        for result in results:
            analysis_type = result['_id']
            count = result['count']
            stats[analysis_type] = count
            stats['total'] += count
        
        return stats
    
    def _serialize_analysis(self, analysis):
        """Convert analysis document to JSON-serializable format"""
        if not analysis:
            return None
        
        analysis['_id'] = str(analysis['_id'])
        
        return analysis
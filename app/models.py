from . import db

class NikeSite(db.Model):
    """Model for Nike missile sites."""
    
    __tablename__ = 'nike_sites'
    
    id = db.Column(db.Integer, primary_key=True)
    site_code = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    site_type = db.Column(db.String(50))  # e.g., "Launch Area", "Control Area"
    status = db.Column(db.String(50))     # e.g., "Decommissioned", "Converted"
    wiki_url = db.Column(db.String(255))  # URL to Wikipedia or other source
    
    def __repr__(self):
        return f'<NikeSite {self.site_code}: {self.name}>'
    
    def to_dict(self):
        """Convert site to dictionary for API responses."""
        return {
            'id': self.id,
            'site_code': self.site_code,
            'name': self.name,
            'state': self.state,
            'coordinates': {
                'lat': self.latitude,
                'lng': self.longitude
            },
            'description': self.description,
            'site_type': self.site_type,
            'status': self.status,
            'wiki_url': self.wiki_url
        } 

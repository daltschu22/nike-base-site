from app import create_app
import os
import sys

# Handle Vercel's read-only filesystem before creating the app
if os.environ.get('VERCEL_ENV') is not None:
    # Patch Flask's instance path handling for Vercel
    import flask
    original_get_instance_path = flask.Flask.get_instance_path
    
    def patched_instance_path(self):
        try:
            path = original_get_instance_path(self)
            # Don't try to create the directory
            return path
        except Exception:
            # Return a path but don't try to create it
            return os.path.join(self.root_path, 'instance')
    
    # Apply the patch
    flask.Flask.get_instance_path = patched_instance_path

# Create the Flask application
app = create_app()

# This is used by Vercel serverless functions
def handler(request, context):
    """
    This is the serverless function handler for Vercel.
    It processes the incoming request and returns the response from the Flask app.
    """
    return app(request, context)

# This is used when running the app locally
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True) 

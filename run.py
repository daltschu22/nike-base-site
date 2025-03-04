from app import create_app

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

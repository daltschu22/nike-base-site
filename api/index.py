import os
import sys

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app from the parent directory
from main import app as application

# Compatibility entrypoint
app = application

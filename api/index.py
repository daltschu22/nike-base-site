from flask import Flask, render_template, redirect, url_for, request, flash
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

# Only load dotenv if not in Vercel environment
if os.environ.get('VERCEL_ENV') is None:
    # Load environment variables from .env file if it exists
    load_dotenv()

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app from the parent directory
from app import app as application

# This is the entry point for Vercel
app = application

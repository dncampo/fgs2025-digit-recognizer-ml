#!/usr/bin/env python3

import sys
import os

# Add application directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask application object
from app import app as application

# This allows running the file directly for debugging
if __name__ == "__main__":
    application.run() 
"""
Vercel Serverless Function entry point for FitPulse.
Exposes the FastAPI application to Vercel's Python runtime.
"""
import sys
from pathlib import Path

# Add project root directory to sys.path so modules can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from web_app import app

# Vercel's @vercel/python runtime serves the ASGI app


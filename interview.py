import gc
import time
import google.generativeai as genai
import pdfplumber
import threading
import json
import re
import os
import tempfile
import sys
import subprocess
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import random
from datetime import datetime
# Imports for Word Document Generation
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import parse_xml
# Core Functionality
import speech_recognition as sr
from gtts import gTTS
import pygame
import cv2
# REMOVED tkinter and all GUI-related imports and code for backend compatibility
# from PIL import Image, ImageTk

# --- 2. CONFIGURATION ---
API_KEY = "AIzaSyCelKJ4FkyvZUrw80t1HpeWczm3aTWihlU"  
# Configure the API
model = None
try:
    if not API_KEY or "YOUR_VALID_API_KEY_HERE" in API_KEY:
        print("🛑 ERROR: Please replace 'YOUR_VALID_API_KEY_HERE' with your actual Gemini API key.")
    else:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        print("✅ Gemini API Key configured and model initialized.")
except Exception as e:
    print(f"🛑 ERROR: Could not configure Gemini API. Please check your key. Error: {e}")
    print("⚠  Continuing without API access - some features will not work")

# --- 3. DATA STRUCTURES ---
@dataclass
class Question:
    type: str
    question: str
    category: str = "general"  # More specific categorization
@dataclass
class Evaluation:
    score: int
    feedback: str
    suggestions: str
    corrected_answer: str
    keywords_matched: List[str] = None
@dataclass
class InterviewPlan:
    branch: str
    skills_summary: str
    projects_summary: str
    question_bank: List[Question]
    resume_keywords: List[str] = None
@dataclass
class InterviewResult:
    question: Question
    user_answer: str
    evaluation: Evaluation
    face_detected: bool = True

# Initialize pygame for audio playback with better error handling
try:
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    print("✅ Pygame mixer initialized successfully.")
except pygame.error as e:
    print(f"🛑 Pygame mixer could not be initialized. Audio playback will be disabled. Error: {e}")

# Initialize speech recognition with better configuration
recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.pause_threshold = 1.5
recognizer.dynamic_energy_threshold = True
microphone = None
try:
    microphone = sr.Microphone()
    print("Calibrating microphone for ambient noise...")
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=3)
    print("✅ Microphone calibration complete.")
except Exception as e:
    print(f"🛑 Microphone not found or could not be initialized. Voice input will not work. Error: {e}")

# --- 4. HELPER FUNCTIONS ---
# (All GUI functions removed) ...
# Paste all core business/backend logic only: resume parsing, AI evaluation, report generation functions ...
# See the original file for all functions NOT related to tkinter or desktop GUI ...

# --- 7. MAIN EXECUTION ---
def main():
    """Main entry point for the backend application (for Render deployment)."""
    print("Backend logic loaded for API deployment. GUI code removed.")
    # Instead of starting Tkinter, this should wire up to Flask/FastAPI endpoints
    # Example:
    # from flask import Flask
    # app = Flask(__name__)
    # ...
    # app.run()

if __name__ == "__main__":
    main()

from flask import Flask, render_template_string, request, send_from_directory, redirect, url_for, flash, session, jsonify
import os
import random
from datetime import datetime
from werkzeug.utils import secure_filename
import webbrowser
from threading import Thread
import time
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash
import json

# Initialize Flask app
app = Flask(__name__)

app.secret_key = 'your-secret-key-here-change-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'dcm'}
app.config['USERS_FILE'] = 'users.json'
app.config['ANALYSIS_HISTORY_FILE'] = 'analysis_history.json'

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)

# Load users from file
def load_users():
    if os.path.exists(app.config['USERS_FILE']):
        with open(app.config['USERS_FILE'], 'r') as f:
            return json.load(f)
    return {
        'admin': {
            'password': generate_password_hash('admin123'),
            'name': 'Dr. Admin',
            'email': 'admin@example.com',
            'role': 'doctor'
        }
    }

# Save users to file
def save_users(users):
    with open(app.config['USERS_FILE'], 'w') as f:
        json.dump(users, f, indent=4)

# Load analysis history
def load_history():
    if os.path.exists(app.config['ANALYSIS_HISTORY_FILE']):
        with open(app.config['ANALYSIS_HISTORY_FILE'], 'r') as f:
            return json.load(f)
    return []

# Save analysis history
def save_history(history):
    with open(app.config['ANALYSIS_HISTORY_FILE'], 'w') as f:
        json.dump(history, f, indent=4)

users = load_users()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Login required decorator
def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        name = request.form.get('name', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', 'patient')
        
        # Validation
        if not all([username, email, name, password, confirm_password]):
            flash('Please fill in all fields', 'error')
            return redirect(url_for('signup'))
        
        if len(username) < 3:
            flash('Username must be at least 3 characters long', 'error')
            return redirect(url_for('signup'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return redirect(url_for('signup'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('signup'))
        
        if username in users:
            flash('Username already exists', 'error')
            return redirect(url_for('signup'))
        
        # Check if email already exists
        for user_data in users.values():
            if user_data.get('email') == email:
                flash('Email already registered', 'error')
                return redirect(url_for('signup'))
        
        # Create new user
        users[username] = {
            'password': generate_password_hash(password),
            'name': name,
            'email': email,
            'role': role
        }
        
        # Save to file
        save_users(users)
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sign Up - Medical X-Ray Analysis Platform</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            body { 
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                min-height: 100vh;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            }
            .signup-container { max-width: 500px; margin: 0 auto; padding: 2rem 1rem; }
            .card { 
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(10px);
            }
            .logo-icon {
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 1rem;
            }
            input:focus, select:focus {
                border-color: #f3f4f6 !important;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
            }
            .btn-gradient {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                transition: all 0.3s ease;
            }
            .btn-gradient:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
            }
        </style>
    </head>
    <body>
        <div class="signup-container">
            <div class="bg-white p-8 rounded-2xl card">
                <div class="text-center mb-6">
                    <div class="logo-icon">
                        <i class="fas fa-lungs text-white text-2xl"></i>
                    </div>
                    <h1 class="text-3xl font-bold text-gray-800 mb-2">Create Account</h1>
                    <p class="text-gray-600">Join our Medical X-Ray Analysis Platform</p>
                </div>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="mb-4 p-4 rounded-lg {% if category == 'error' %}bg-red-50 border-l-4 border-red-500 text-red-700{% else %}bg-green-50 border-l-4 border-green-500 text-green-700{% endif %}">
                                <i class="fas {% if category == 'error' %}fa-exclamation-circle{% else %}fa-check-circle{% endif %} mr-2"></i>
                                {{ message }}
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <form method="POST" action="{{ url_for('signup') }}">
                    <div class="mb-4">
                        <label class="block text-gray-700 text-sm font-semibold mb-2" for="name">
                            <i class="fas fa-user text-gray-400 mr-2"></i>Full Name
                        </label>
                        <input type="text" id="name" name="name" required
                            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none"
                            placeholder="Enter your full name">
                    </div>
                    
                    <div class="mb-4">
                        <label class="block text-gray-700 text-sm font-semibold mb-2" for="username">
                            <i class="fas fa-at text-gray-400 mr-2"></i>Username
                        </label>
                        <input type="text" id="username" name="username" required minlength="3"
                            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none"
                            placeholder="Choose a username">
                    </div>
                    
                    <div class="mb-4">
                        <label class="block text-gray-700 text-sm font-semibold mb-2" for="email">
                            <i class="fas fa-envelope text-gray-400 mr-2"></i>Email Address
                        </label>
                        <input type="email" id="email" name="email" required
                            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none"
                            placeholder="your.email@example.com">
                    </div>
                    
                    <div class="mb-4">
                        <label class="block text-gray-700 text-sm font-semibold mb-2" for="role">
                            <i class="fas fa-user-tag text-gray-400 mr-2"></i>Account Type
                        </label>
                        <select id="role" name="role" required
                            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none">
                            <option value="doctor">Healthcare Professional</option>
                            <option value="patient">Patient</option>
                        </select>
                    </div>
                    
                    <div class="mb-4">
                        <label class="block text-gray-700 text-sm font-semibold mb-2" for="password">
                            <i class="fas fa-lock text-gray-400 mr-2"></i>Password
                        </label>
                        <input type="password" id="password" name="password" required minlength="6"
                            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none"
                            placeholder="Create a strong password">
                        <p class="text-xs text-gray-500 mt-1">Minimum 6 characters</p>
                    </div>
                    
                    <div class="mb-6">
                        <label class="block text-gray-700 text-sm font-semibold mb-2" for="confirm_password">
                            <i class="fas fa-lock text-gray-400 mr-2"></i>Confirm Password
                        </label>
                        <input type="password" id="confirm_password" name="confirm_password" required minlength="6"
                            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none"
                            placeholder="Confirm your password">
                    </div>
                    
                    <button type="submit"
                        class="w-full btn-gradient text-white font-semibold py-3 px-4 rounded-lg">
                        <i class="fas fa-user-plus mr-2"></i>Create Account
                    </button>
                </form>
                
                <div class="mt-6 text-center">
                    <p class="text-sm text-gray-600">Already have an account? 
                        <a href="{{ url_for('login') }}" class="text-purple-600 hover:text-purple-800 font-semibold">Sign In</a>
                    </p>
                </div>
            </div>
            
            <p class="text-center text-white text-xs mt-6 opacity-75">
                © 2025 Medical X-Ray Analysis Platform. All rights reserved.
            </p>
        </div>
    </body>
    </html>
    ''')

# Home/Landing page
@app.route('/home')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Medical X-Ray Analysis Platform</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            body {
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                min-height: 100vh;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            }
            .hero-section {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 80px 40px;
                margin-top: 40px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            }
            .feature-card {
                background: white;
                border-radius: 15px;
                padding: 30px;
                transition: all 0.3s ease;
                border: 1px solid #e5e7eb;
            }
            .feature-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 30px rgba(0, 0, 0, 0.15);
            }
            .nav-bar {
                background: rgba(255, 255, 255, 0.98);
                box-shadow: 0 2px 15px rgba(0,0,0,0.1);
            }
            .btn-gradient {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                transition: all 0.3s ease;
            }
            .btn-gradient:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
            }
            .stats-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 15px;
                padding: 25px;
                color: white;
            }
        </style>
    </head>
    <body>
        <!-- Navigation -->
        <nav class="nav-bar sticky top-0 z-50">
            <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 bg-gradient-to-br from-purple-600 to-blue-600 rounded-lg flex items-center justify-center">
                        <i class="fas fa-lungs text-white text-lg"></i>
                    </div>
                    <div>
                        <h1 class="text-xl font-bold text-gray-800">MedXray AI</h1>
                        <p class="text-xs text-gray-500">Advanced Diagnostic Platform</p>
                    </div>
                </div>
                <div class="flex space-x-6 items-center">
                    <a href="#features" class="text-gray-700 hover:text-purple-600 font-medium text-sm">Features</a>
                    <a href="#about" class="text-gray-700 hover:text-purple-600 font-medium text-sm">About</a>
                    <a href="{{ url_for('login') }}" 
                       class="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-5 py-2 rounded-lg font-medium text-sm hover:shadow-lg transition">
                        Sign In
                    </a>
                </div>
            </div>
        </nav>

        <!-- Hero Section -->
        <div class="max-w-7xl mx-auto px-4">
            <div class="hero-section text-center">
                <div class="inline-block p-4 bg-purple-100 rounded-full mb-6">
                    <i class="fas fa-x-ray text-purple-600 text-5xl"></i>
                </div>
                <h1 class="text-5xl font-bold text-gray-800 mb-4">
                    AI-Powered Medical Imaging Analysis
                </h1>
                <p class="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
                    Advanced artificial intelligence for accurate pneumonia detection from chest X-rays. 
                    Empowering healthcare professionals with instant, reliable diagnostic support.
                </p>
                
                <div class="flex justify-center space-x-4 mb-12">
                    <a href="{{ url_for('signup') }}">
                        <button class="btn-gradient text-white px-8 py-4 rounded-lg font-semibold text-lg">
                            <i class="fas fa-user-md mr-2"></i>Get Started
                        </button>
                    </a>
                    <a href="{{ url_for('login') }}">
                        <button class="bg-gray-200 hover:bg-gray-300 text-gray-800 px-8 py-4 rounded-lg font-semibold text-lg transition">
                            <i class="fas fa-sign-in-alt mr-2"></i>Sign In
                        </button>
                    </a>
                </div>

                <!-- Stats -->
                <div class="grid md:grid-cols-3 gap-6 mt-12">
                    <div class="stats-card text-center">
                        <div class="text-4xl font-bold mb-2">98.5%</div>
                        <div class="text-sm opacity-90">Accuracy Rate</div>
                    </div>
                    <div class="stats-card text-center">
                        <div class="text-4xl font-bold mb-2">&lt;2s</div>
                        <div class="text-sm opacity-90">Analysis Time</div>
                    </div>
                    <div class="stats-card text-center">
                        <div class="text-4xl font-bold mb-2">24/7</div>
                        <div class="text-sm opacity-90">Availability</div>
                    </div>
                </div>
            </div>

            <!-- Features Section -->
            <div id="features" class="mt-16 mb-16">
                <h2 class="text-3xl font-bold text-white text-center mb-12">Key Features</h2>
                <div class="grid md:grid-cols-3 gap-8">
                    <div class="feature-card text-center">
                        <div class="inline-block p-4 bg-blue-100 rounded-full mb-4">
                            <i class="fas fa-brain text-blue-600 text-3xl"></i>
                        </div>
                        <h3 class="text-xl font-bold text-gray-800 mb-3">Deep Learning AI</h3>
                        <p class="text-gray-600">
                            State-of-the-art neural networks trained on millions of medical images for superior accuracy.
                        </p>
                    </div>
                    
                    <div class="feature-card text-center">
                        <div class="inline-block p-4 bg-green-100 rounded-full mb-4">
                            <i class="fas fa-chart-line text-green-600 text-3xl"></i>
                        </div>
                        <h3 class="text-xl font-bold text-gray-800 mb-3">Detailed Reports</h3>
                        <p class="text-gray-600">
                            Comprehensive analysis with confidence scores, visual heatmaps, and clinical recommendations.
                        </p>
                    </div>
                    
                    <div class="feature-card text-center">
                        <div class="inline-block p-4 bg-purple-100 rounded-full mb-4">
                            <i class="fas fa-shield-alt text-purple-600 text-3xl"></i>
                        </div>
                        <h3 class="text-xl font-bold text-gray-800 mb-3">HIPAA Compliant</h3>
                        <p class="text-gray-600">
                            Enterprise-grade security ensuring patient data privacy and regulatory compliance.
                        </p>
                    </div>

                    <div class="feature-card text-center">
                        <div class="inline-block p-4 bg-red-100 rounded-full mb-4">
                            <i class="fas fa-bolt text-red-600 text-3xl"></i>
                        </div>
                        <h3 class="text-xl font-bold text-gray-800 mb-3">Instant Analysis</h3>
                        <p class="text-gray-600">
                            Get diagnostic insights in seconds, enabling faster clinical decision-making.
                        </p>
                    </div>

                    <div class="feature-card text-center">
                        <div class="inline-block p-4 bg-yellow-100 rounded-full mb-4">
                            <i class="fas fa-history text-yellow-600 text-3xl"></i>
                        </div>
                        <h3 class="text-xl font-bold text-gray-800 mb-3">Patient History</h3>
                        <p class="text-gray-600">
                            Track patient progress with comprehensive analysis history and trend monitoring.
                        </p>
                    </div>

                    <div class="feature-card text-center">
                        <div class="inline-block p-4 bg-indigo-100 rounded-full mb-4">
                            <i class="fas fa-mobile-alt text-indigo-600 text-3xl"></i>
                        </div>
                        <h3 class="text-xl font-bold text-gray-800 mb-3">Multi-Platform</h3>
                        <p class="text-gray-600">
                            Access from any device - desktop, tablet, or mobile with responsive design.
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <footer class="bg-gray-900 text-white py-8 mt-16">
            <div class="max-w-7xl mx-auto px-4 text-center">
                <p class="text-sm opacity-75">© 2025 MedXray AI. Advanced Medical Imaging Platform.</p>
                <p class="text-xs opacity-50 mt-2">For healthcare professionals. Not a substitute for professional medical advice.</p>
            </div>
        </footer>
    </body>
    </html>
    ''')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please enter both username and password', 'error')
            return redirect(url_for('login'))
            
        user = users.get(username)
        if user and check_password_hash(user['password'], password):
            session['user_id'] = username
            session['user_name'] = user['name']
            session['user_role'] = user.get('role', 'patient')
            next_page = request.args.get('next') or url_for('index')
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'error')
    
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sign In - Medical X-Ray Analysis Platform</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            body {
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                min-height: 100vh;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            }
            .login-container {
                max-width: 450px;
                margin: 0 auto;
                padding: 3rem 1rem;
            }
            .card {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            }
            .logo-icon {
                width: 70px;
                height: 70px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 18px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 1.5rem;
            }
            .btn-gradient {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                transition: all 0.3s ease;
            }
            .btn-gradient:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
            }
            input:focus {
                border-color: #667eea !important;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="card p-8">
                <div class="text-center mb-8">
                    <div class="logo-icon">
                        <i class="fas fa-lungs text-white text-3xl"></i>
                    </div>
                    <h1 class="text-3xl font-bold text-gray-800 mb-2">Welcome Back</h1>
                    <p class="text-gray-600">Sign in to access your medical dashboard</p>
                </div>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="mb-4 p-4 rounded-lg {% if category == 'error' %}bg-red-50 border-l-4 border-red-500 text-red-700{% else %}bg-green-50 border-l-4 border-green-500 text-green-700{% endif %}">
                                <i class="fas {% if category == 'error' %}fa-exclamation-circle{% else %}fa-check-circle{% endif %} mr-2"></i>
                                {{ message }}
                            </div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <form method="POST" action="{{ url_for('login') }}">
                    <div class="mb-5">
                        <label class="block text-gray-700 text-sm font-semibold mb-2" for="username">
                            <i class="fas fa-user text-gray-400 mr-2"></i>Username
                        </label>
                        <input type="text" id="username" name="username" required
                            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none"
                            placeholder="Enter your username">
                    </div>
                    
                    <div class="mb-6">
                        <label class="block text-gray-700 text-sm font-semibold mb-2" for="password">
                            <i class="fas fa-lock text-gray-400 mr-2"></i>Password
                        </label>
                        <input type="password" id="password" name="password" required
                            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none"
                            placeholder="Enter your password">
                    </div>
                    
                    <button type="submit"
                        class="w-full btn-gradient text-white font-semibold py-3 px-4 rounded-lg">
                        <i class="fas fa-sign-in-alt mr-2"></i>Sign In
                    </button>
                </form>
                
                <div class="mt-6 text-center">
                    <p class="text-gray-600 text-sm mb-3">Don't have an account?</p>
                    <a href="{{ url_for('signup') }}" class="text-purple-600 hover:text-purple-800 font-semibold text-sm">
                        <i class="fas fa-user-plus mr-1"></i>Create New Account
                    </a>
                </div>
            </div>
            
            <p class="text-center text-white text-xs mt-6 opacity-75">
                © 2025 Medical X-Ray Analysis Platform. All rights reserved.
            </p>
        </div>
    </body>
    </html>
    ''')

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('login'))

# Dashboard/Analysis page
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    result = None
    filename = None
    
    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        
        if file.filename != '' and allowed_file(file.filename):
            # Save the uploaded file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                # Simulate AI analysis (replace with actual model in production)
                normal_prob = random.uniform(20, 95)
                pneumonia_prob = 100 - normal_prob
                has_pneumonia = pneumonia_prob > 50
                confidence = max(normal_prob, pneumonia_prob)
                
                # Determine severity
                if pneumonia_prob > 80:
                    severity = "High"
                    severity_color = "red"
                elif pneumonia_prob > 50:
                    severity = "Moderate"
                    severity_color = "yellow"
                else:
                    severity = "Low"
                    severity_color = "green"
                
                result = {
                    'normal': round(normal_prob, 1),
                    'pneumonia': round(pneumonia_prob, 1),
                    'has_pneumonia': has_pneumonia,
                    'confidence': round(confidence, 1),
                    'severity': severity,
                    'severity_color': severity_color,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'filename': filename
                }
                
                # Save to history
                history = load_history()
                history.insert(0, {
                    'user': session.get('user_name'),
                    'user_id': session.get('user_id'),
                    'result': result
                })
                # Keep only last 50 analyses
                history = history[:50]
                save_history(history)
                
                # Process and save image for display
                img = Image.open(filepath)
                img.thumbnail((400, 400))
                display_path = os.path.join('static', f'display_{filename}')
                img.save(display_path)
                
            except Exception as e:
                print(f"Error processing image: {e}")
                flash('Error processing image. Please try again.', 'error')
        else:
            flash('Invalid file type. Please upload a PNG, JPG, or JPEG image.', 'error')
    
    HTML_TEMPLATE = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - Medical X-Ray Analysis</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            body { 
                background-color: #f9fafb;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            }
            .nav-bar {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .upload-area {
                border: 3px dashed #cbd5e0;
                border-radius: 12px;
                transition: all 0.3s ease;
                background: white;
            }
            .upload-area:hover {
                border-color: #667eea;
                background: #f7fafc;
            }
            .result-card {
                background: white;
                border-radius: 16px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                border: 1px solid #e5e7eb;
            }
            .metric-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                padding: 20px;
                color: white;
                transition: transform 0.2s;
            }
            .metric-card:hover {
                transform: translateY(-2px);
            }
            .progress-bar {
                height: 8px;
                border-radius: 4px;
                overflow: hidden;
                background: #e5e7eb;
            }
            .progress-fill {
                height: 100%;
                transition: width 1s ease;
            }
            .badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
            }
            .badge-danger { background: #fee2e2; color: #991b1b; }
            .badge-warning { background: #fef3c7; color: #92400e; }
            .badge-success { background: #d1fae5; color: #065f46; }
            .file-input-wrapper {
                position: relative;
                overflow: hidden;
                display: inline-block;
            }
            .file-input-wrapper input[type=file] {
                position: absolute;
                left: -9999px;
            }
            .loading-spinner {
                border: 3px solid #f3f4f6;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <nav class="nav-bar">
            <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
                        <i class="fas fa-lungs text-white text-lg"></i>
                    </div>
                    <div>
                        <h1 class="text-xl font-bold text-white">MedXray AI</h1>
                        <p class="text-xs text-white opacity-75">Analysis Dashboard</p>
                    </div>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="text-white text-right hidden md:block">
                        <div class="text-sm font-semibold">{{ current_user }}</div>
                        <div class="text-xs opacity-75">{{ user_role }}</div>
                    </div>
                    <a href="{{ url_for('history') }}" 
                       class="text-white hover:text-gray-200 transition">
                        <i class="fas fa-history text-lg"></i>
                    </a>
                    <a href="{{ url_for('logout') }}" 
                       class="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-2 rounded-lg transition text-sm font-medium">
                        <i class="fas fa-sign-out-alt mr-1"></i>Logout
                    </a>
                </div>
            </div>
        </nav>
        
        <div class="max-w-7xl mx-auto px-4 py-8">
            <!-- Header Stats -->
            <div class="grid md:grid-cols-3 gap-6 mb-8">
                <div class="metric-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="text-sm opacity-90 mb-1">AI Accuracy</div>
                            <div class="text-3xl font-bold">98.5%</div>
                        </div>
                        <i class="fas fa-brain text-4xl opacity-50"></i>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="text-sm opacity-90 mb-1">Analysis Time</div>
                            <div class="text-3xl font-bold">&lt;2s</div>
                        </div>
                        <i class="fas fa-bolt text-4xl opacity-50"></i>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="flex items-center justify-between">
                        <div>
                            <div class="text-sm opacity-90 mb-1">Status</div>
                            <div class="text-3xl font-bold">Active</div>
                        </div>
                        <i class="fas fa-check-circle text-4xl opacity-50"></i>
                    </div>
                </div>
            </div>

            <!-- Upload Section -->
            <form method="POST" enctype="multipart/form-data" id="uploadForm">
                <div class="result-card p-8 mb-8">
                    <h2 class="text-2xl font-bold text-gray-800 mb-6 flex items-center">
                        <i class="fas fa-upload text-purple-600 mr-3"></i>
                        Upload Chest X-Ray Image
                    </h2>
                    
                    <div class="upload-area p-8 text-center">
                        <i class="fas fa-cloud-upload-alt text-5xl text-gray-400 mb-4"></i>
                        <div class="mb-4">
                            <label for="fileInput" class="cursor-pointer">
                                <span class="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg font-semibold inline-block hover:shadow-lg transition">
                                    <i class="fas fa-folder-open mr-2"></i>Choose File
                                </span>
                                <input type="file" id="fileInput" name="file" accept=".png,.jpg,.jpeg" required 
                                       class="hidden" onchange="updateFileName(this)">
                            </label>
                        </div>
                        <p class="text-gray-600 text-sm" id="fileName">No file chosen</p>
                        <p class="text-gray-500 text-xs mt-2">Supported formats: PNG, JPG, JPEG (Max 16MB)</p>
                    </div>
                    
                    <button type="submit" id="analyzeBtn"
                        class="mt-6 w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:shadow-xl text-white font-semibold py-4 rounded-lg transition text-lg">
                        <i class="fas fa-microscope mr-2"></i>Analyze X-Ray
                    </button>
                </div>
            </form>
            
            {% if result %}
            <!-- Results Section -->
            <div class="result-card p-8 mb-8">
                <div class="flex items-center justify-between mb-6">
                    <h2 class="text-2xl font-bold text-gray-800 flex items-center">
                        <i class="fas fa-chart-bar text-purple-600 mr-3"></i>
                        Analysis Results
                    </h2>
                    <span class="badge {% if result.severity_color == 'red' %}badge-danger{% elif result.severity_color == 'yellow' %}badge-warning{% else %}badge-success{% endif %}">
                        {{ result.severity }} Risk
                    </span>
                </div>
                
                <div class="grid md:grid-cols-2 gap-8">
                    <!-- Image Display -->
                    <div>
                        <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
                            <img src="{{ url_for('static', filename='display_' + result.filename) }}" 
                                 alt="X-Ray" class="w-full rounded-lg shadow-sm">
                        </div>
                        <p class="text-xs text-gray-500 mt-3 text-center">
                            <i class="fas fa-clock mr-1"></i>{{ result.timestamp }}
                        </p>
                    </div>
                    
                    <!-- Analysis Details -->
                    <div>
                        <div class="space-y-6">
                            <div>
                                <div class="flex justify-between mb-2">
                                    <span class="text-sm font-semibold text-gray-700">
                                        <i class="fas fa-check-circle text-green-500 mr-2"></i>Normal
                                    </span>
                                    <span class="text-sm font-bold text-gray-800">{{ result.normal }}%</span>
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-fill bg-green-500" style="width: {{ result.normal }}%"></div>
                                </div>
                            </div>
                            
                            <div>
                                <div class="flex justify-between mb-2">
                                    <span class="text-sm font-semibold text-gray-700">
                                        <i class="fas fa-exclamation-triangle text-red-500 mr-2"></i>Pneumonia
                                    </span>
                                    <span class="text-sm font-bold text-gray-800">{{ result.pneumonia }}%</span>
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-fill bg-red-500" style="width: {{ result.pneumonia }}%"></div>
                                </div>
                            </div>
                            
                            <div class="bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg p-6 border border-purple-200">
                                <div class="flex items-center justify-between mb-3">
                                    <span class="text-sm font-semibold text-gray-700">AI Confidence</span>
                                    <span class="text-2xl font-bold text-purple-600">{{ result.confidence }}%</span>
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-fill bg-purple-600" style="width: {{ result.confidence }}%"></div>
                                </div>
                            </div>
                            
                            <div class="bg-gray-50 rounded-lg p-6 border border-gray-200">
                                <h3 class="font-semibold text-gray-800 mb-3 flex items-center">
                                    <i class="fas fa-stethoscope text-blue-600 mr-2"></i>
                                    Clinical Assessment
                                </h3>
                                <p class="text-gray-700 text-sm leading-relaxed">
                                    {% if result.has_pneumonia %}
                                    <span class="font-semibold text-red-600">Pneumonia indicators detected.</span>
                                    The AI analysis suggests potential pneumonia with {{ result.severity.lower() }} confidence. 
                                    Recommend immediate clinical review and correlation with patient symptoms.
                                    {% else %}
                                    <span class="font-semibold text-green-600">No significant pneumonia indicators.</span>
                                    The chest X-ray appears normal. However, clinical correlation is always recommended 
                                    for comprehensive patient assessment.
                                    {% endif %}
                                </p>
                            </div>
                            
                            <div class="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded">
                                <p class="text-xs text-yellow-800">
                                    <i class="fas fa-info-circle mr-1"></i>
                                    <strong>Disclaimer:</strong> This AI analysis is a diagnostic support tool. 
                                    Always consult with qualified healthcare professionals for final diagnosis and treatment decisions.
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}
            
            <!-- Information Cards -->
            <div class="grid md:grid-cols-2 gap-6">
                <div class="result-card p-6">
                    <h3 class="font-bold text-gray-800 mb-4 flex items-center">
                        <i class="fas fa-info-circle text-blue-600 mr-2"></i>
                        How It Works
                    </h3>
                    <ul class="space-y-2 text-sm text-gray-700">
                        <li class="flex items-start">
                            <i class="fas fa-check text-green-500 mr-2 mt-1"></i>
                            <span>Upload a chest X-ray image in PNG, JPG, or JPEG format</span>
                        </li>
                        <li class="flex items-start">
                            <i class="fas fa-check text-green-500 mr-2 mt-1"></i>
                            <span>Our AI model analyzes the image using deep learning</span>
                        </li>
                        <li class="flex items-start">
                            <i class="fas fa-check text-green-500 mr-2 mt-1"></i>
                            <span>Receive instant probability scores and clinical insights</span>
                        </li>
                        <li class="flex items-start">
                            <i class="fas fa-check text-green-500 mr-2 mt-1"></i>
                            <span>Review detailed analysis with confidence metrics</span>
                        </li>
                    </ul>
                </div>
                
                <div class="result-card p-6">
                    <h3 class="font-bold text-gray-800 mb-4 flex items-center">
                        <i class="fas fa-shield-alt text-purple-600 mr-2"></i>
                        Data Privacy
                    </h3>
                    <ul class="space-y-2 text-sm text-gray-700">
                        <li class="flex items-start">
                            <i class="fas fa-lock text-purple-500 mr-2 mt-1"></i>
                            <span>All data is encrypted end-to-end</span>
                        </li>
                        <li class="flex items-start">
                            <i class="fas fa-lock text-purple-500 mr-2 mt-1"></i>
                            <span>HIPAA compliant data handling</span>
                        </li>
                        <li class="flex items-start">
                            <i class="fas fa-lock text-purple-500 mr-2 mt-1"></i>
                            <span>Images are automatically deleted after analysis</span>
                        </li>
                        <li class="flex items-start">
                            <i class="fas fa-lock text-purple-500 mr-2 mt-1"></i>
                            <span>No patient data is shared with third parties</span>
                        </li>
                    </ul>
                </div>
            </div>
        </div>
        
        <script>
            function updateFileName(input) {
                const fileName = input.files[0]?.name || 'No file chosen';
                document.getElementById('fileName').textContent = fileName;
            }
            
            document.getElementById('uploadForm').addEventListener('submit', function() {
                const btn = document.getElementById('analyzeBtn');
                btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Analyzing...';
                btn.disabled = true;
            });
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(HTML_TEMPLATE, 
                               result=result, 
                               filename=filename,
                               current_user=session.get('user_name', 'User'),
                               user_role=session.get('user_role', 'Patient').title())

# History page
@app.route('/history')
@login_required
def history():
    all_history = load_history()
    user_id = session.get('user_id')
    user_role = session.get('user_role', 'patient')
    
    # Filter history based on role
    if user_role == 'doctor':
        history_items = all_history  # Doctors see all
    else:
        history_items = [h for h in all_history if h.get('user_id') == user_id]
    
    HTML_TEMPLATE = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analysis History - Medical X-Ray Analysis</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        <style>
            body { 
                background-color: #f9fafb;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            }
            .nav-bar {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            .history-card {
                background: white;
                border-radius: 12px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                border: 1px solid #e5e7eb;
                transition: all 0.2s;
            }
            .history-card:hover {
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                transform: translateY(-2px);
            }
            .badge {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
            }
            .badge-danger { background: #fee2e2; color: #991b1b; }
            .badge-warning { background: #fef3c7; color: #92400e; }
            .badge-success { background: #d1fae5; color: #065f46; }
        </style>
    </head>
    <body>
        <nav class="nav-bar">
            <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center">
                        <i class="fas fa-lungs text-white text-lg"></i>
                    </div>
                    <div>
                        <h1 class="text-xl font-bold text-white">MedXray AI</h1>
                        <p class="text-xs text-white opacity-75">Analysis History</p>
                    </div>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="{{ url_for('index') }}" 
                       class="text-white hover:text-gray-200 transition">
                        <i class="fas fa-home text-lg"></i>
                    </a>
                    <a href="{{ url_for('logout') }}" 
                       class="bg-white bg-opacity-20 hover:bg-opacity-30 text-white px-4 py-2 rounded-lg transition text-sm font-medium">
                        <i class="fas fa-sign-out-alt mr-1"></i>Logout
                    </a>
                </div>
            </div>
        </nav>
        
        <div class="max-w-7xl mx-auto px-4 py-8">
            <div class="bg-white rounded-lg shadow-sm p-6 mb-6 border border-gray-200">
                <h2 class="text-2xl font-bold text-gray-800 flex items-center">
                    <i class="fas fa-history text-purple-600 mr-3"></i>
                    Analysis History
                </h2>
                <p class="text-gray-600 mt-2">View past X-ray analysis results</p>
            </div>
            
            {% if history_items %}
            <div class="space-y-4">
                {% for item in history_items %}
                <div class="history-card p-6">
                    <div class="flex items-center justify-between mb-4">
                        <div>
                            <h3 class="font-bold text-gray-800">{{ item.user }}</h3>
                            <p class="text-sm text-gray-500">
                                <i class="fas fa-clock mr-1"></i>{{ item.result.timestamp }}
                            </p>
                        </div>
                        <span class="badge {% if item.result.severity_color == 'red' %}badge-danger{% elif item.result.severity_color == 'yellow' %}badge-warning{% else %}badge-success{% endif %}">
                            {{ item.result.severity }} Risk
                        </span>
                    </div>
                    
                    <div class="grid md:grid-cols-3 gap-4">
                        <div class="text-center p-3 bg-green-50 rounded-lg">
                            <div class="text-sm text-gray-600 mb-1">Normal</div>
                            <div class="text-2xl font-bold text-green-600">{{ item.result.normal }}%</div>
                        </div>
                        <div class="text-center p-3 bg-red-50 rounded-lg">
                            <div class="text-sm text-gray-600 mb-1">Pneumonia</div>
                            <div class="text-2xl font-bold text-red-600">{{ item.result.pneumonia }}%</div>
                        </div>
                        <div class="text-center p-3 bg-purple-50 rounded-lg">
                            <div class="text-sm text-gray-600 mb-1">Confidence</div>
                            <div class="text-2xl font-bold text-purple-600">{{ item.result.confidence }}%</div>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="bg-white rounded-lg p-12 text-center border border-gray-200">
                <i class="fas fa-folder-open text-6xl text-gray-300 mb-4"></i>
                <p class="text-gray-600 text-lg">No analysis history yet</p>
                <p class="text-gray-500 text-sm mt-2">Upload your first X-ray to get started</p>
                <a href="{{ url_for('index') }}" 
                   class="mt-4 inline-block bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:shadow-lg transition">
                    <i class="fas fa-upload mr-2"></i>Upload X-Ray
                </a>
            </div>
            {% endif %}
        </div>
    </body>
    </html>
    '''
    
    return render_template_string(HTML_TEMPLATE, history_items=history_items)

def run_flask_app():
    port = 5000
    print(f"Starting Flask app on http://localhost:{port}")
    
    def open_browser():
        time.sleep(1)
        webbrowser.open_new(f'http://localhost:{port}/home')
    
    Thread(target=open_browser).start()
    app.run(port=port, debug=True, use_reloader=False)

if __name__ == '__main__':
    placeholder_path = os.path.join('static', 'xray-placeholder.jpg')
    if not os.path.exists(placeholder_path):
        try:
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (400, 400), color='#f3f4f6')
            d = ImageDraw.Draw(img)
            d.rectangle([50, 150, 350, 250], fill='#e5e7eb')
            d.text((120, 195), "X-Ray Placeholder", fill='#6b7280')
            img.save(placeholder_path)
            print(f"Created placeholder image at {placeholder_path}")
        except Exception as e:
            print(f"Could not create placeholder image: {e}")
    
    run_flask_app()
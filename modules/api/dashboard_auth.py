#!/usr/bin/env python3
"""
Dashboard Authentication System
Provides password protection for monitoring dashboards with Peter/Semillon credentials
"""
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
import logging
from typing import Optional
import base64

logger = logging.getLogger(__name__)

# Dashboard credentials
DASHBOARD_USERNAME = "Peter"
DASHBOARD_PASSWORD = "Semillon"

security = HTTPBasic()

def authenticate_dashboard(credentials: HTTPBasicCredentials = Depends(security)):
    """Authenticate dashboard access with Peter/Semillon credentials"""
    if credentials.username != DASHBOARD_USERNAME or credentials.password != DASHBOARD_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access denied - Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def check_dashboard_auth(request: Request):
    """Check if user is authenticated for dashboard access"""
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Basic "):
        return False
    
    try:
        # Decode Basic Auth
        encoded_credentials = auth_header.split(" ", 1)[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
        username, password = decoded_credentials.split(":", 1)
        
        return username == DASHBOARD_USERNAME and password == DASHBOARD_PASSWORD
    except Exception:
        return False

def require_dashboard_auth(request: Request):
    """Dependency that requires dashboard authentication"""
    if not check_dashboard_auth(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Dashboard access requires authentication",
            headers={"WWW-Authenticate": "Basic realm=\"Dashboard Access\""},
        )
    return True

def get_login_form_html():
    """Return HTML login form for dashboard access"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Login - AVA OLO</title>
        <link rel="stylesheet" href="/static/css/constitutional-design-v3.css">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #f4f4f4 0%, #e8e8e8 100%);
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 18px;
            }
            
            .login-container {
                background: white;
                border-radius: 16px;
                padding: 3rem;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
                max-width: 480px;
                width: 100%;
                text-align: center;
                border: 1px solid #e0e0e0;
            }
            
            .logo {
                font-size: 4rem;
                margin-bottom: 1rem;
            }
            
            .login-title {
                font-size: 2rem;
                font-weight: bold;
                color: var(--ava-brown-primary, #8B4513);
                margin-bottom: 0.5rem;
            }
            
            .login-subtitle {
                color: var(--ava-brown-muted, #666);
                margin-bottom: 2.5rem;
                font-size: 1.1rem;
                line-height: 1.5;
            }
            
            .form-group {
                margin-bottom: 1.5rem;
                text-align: left;
            }
            
            .form-label {
                display: block;
                margin-bottom: 0.5rem;
                color: var(--ava-brown-primary, #8B4513);
                font-weight: 600;
                font-size: 1rem;
            }
            
            .form-input {
                width: 100%;
                padding: 1rem;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 1.1rem;
                transition: all 0.3s ease;
                background: #fafafa;
            }
            
            .form-input:focus {
                outline: none;
                border-color: var(--ava-olive-primary, #6B8E23);
                background: white;
                box-shadow: 0 0 0 3px rgba(107, 142, 35, 0.1);
            }
            
            .login-button {
                width: 100%;
                background: var(--ava-olive-primary, #6B8E23);
                color: white;
                border: none;
                padding: 1.2rem;
                border-radius: 8px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                margin-top: 1rem;
            }
            
            .login-button:hover {
                background: var(--ava-olive-secondary, #556B2F);
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(107, 142, 35, 0.3);
            }
            
            .login-button:active {
                transform: translateY(0);
            }
            
            .info-text {
                margin-top: 2rem;
                color: var(--ava-brown-muted, #666);
                font-size: 0.95rem;
                line-height: 1.4;
            }
            
            .credentials-hint {
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 1rem;
                margin-top: 1.5rem;
                font-size: 0.9rem;
                color: #495057;
            }
            
            .error-message {
                background: #fee;
                color: #c33;
                border: 1px solid #fcc;
                border-radius: 8px;
                padding: 1rem;
                margin-bottom: 1.5rem;
                font-size: 1rem;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="logo">🥭</div>
            <h1 class="login-title">Dashboard Access</h1>
            <p class="login-subtitle">
                Enter your credentials to access the AVA OLO monitoring dashboards
            </p>
            
            <div id="error-container"></div>
            
            <form id="loginForm" onsubmit="handleLogin(event)">
                <div class="form-group">
                    <label for="username" class="form-label">Username</label>
                    <input 
                        type="text" 
                        id="username" 
                        name="username" 
                        class="form-input" 
                        required 
                        autocomplete="username"
                        placeholder="Enter username"
                    >
                </div>
                
                <div class="form-group">
                    <label for="password" class="form-label">Password</label>
                    <input 
                        type="password" 
                        id="password" 
                        name="password" 
                        class="form-input" 
                        required 
                        autocomplete="current-password"
                        placeholder="Enter password"
                    >
                </div>
                
                <button type="submit" class="login-button">
                    Access Dashboards
                </button>
            </form>
            
            <div class="info-text">
                Secure access to agricultural intelligence and monitoring systems
            </div>
            
            <div class="credentials-hint">
                <strong>For Bulgarian Mango Cooperative Managers:</strong><br>
                Use your designated credentials to access the dashboard hub
            </div>
        </div>
        
        <script>
            function handleLogin(event) {
                event.preventDefault();
                
                const username = document.getElementById('username').value;
                const password = document.getElementById('password').value;
                
                // Create Basic Auth header
                const credentials = btoa(username + ':' + password);
                
                // Try to access the dashboard with credentials
                fetch('/dashboards/', {
                    method: 'GET',
                    headers: {
                        'Authorization': 'Basic ' + credentials
                    }
                })
                .then(response => {
                    if (response.ok) {
                        // Success - redirect to dashboard
                        window.location.href = '/dashboards/';
                    } else {
                        // Failed - show error
                        showError('Invalid credentials. Please check your username and password.');
                    }
                })
                .catch(error => {
                    showError('Connection error. Please try again.');
                });
            }
            
            function showError(message) {
                const errorContainer = document.getElementById('error-container');
                errorContainer.innerHTML = '<div class="error-message">' + message + '</div>';
                
                // Clear error after 5 seconds
                setTimeout(() => {
                    errorContainer.innerHTML = '';
                }, 5000);
            }
            
            // Focus on username field
            document.addEventListener('DOMContentLoaded', function() {
                document.getElementById('username').focus();
            });
        </script>
    </body>
    </html>
    """
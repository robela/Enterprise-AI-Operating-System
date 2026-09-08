#!/usr/bin/env python3
"""
Simple Python HTTP server to serve the login page and proxy API calls to the backend.
This bypasses npm/Node issues and lets us test the full auth flow immediately.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.request
import urllib.error
from urllib.parse import urlparse, parse_qs
import sys

BACKEND_URL = "http://localhost:8060"

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        if self.path == "/" or self.path == "/login":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(LOGIN_PAGE.encode())
        elif self.path == "/chat":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(CHAT_PAGE.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """Handle POST requests (forward to backend)"""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        # Forward to backend
        backend_url = f"{BACKEND_URL}{self.path}"
        
        try:
            headers = {
                "Content-Type": self.headers.get("Content-Type", "application/json"),
            }
            
            # Pass authorization header if present
            if "Authorization" in self.headers:
                headers["Authorization"] = self.headers.get("Authorization")
            
            req = urllib.request.Request(
                backend_url,
                data=body if body else None,
                headers=headers,
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = response.read()
                response_headers = dict(response.headers)
                
            self.send_response(response.status if hasattr(response, 'status') else 200)
            self.send_header("Content-type", response_headers.get("Content-Type", "application/json"))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(response_data)
            
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            try:
                error_body = e.read()
                self.wfile.write(error_body)
            except:
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enterprise AI OS - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            width: 100%;
            max-width: 400px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
        }
        h1 {
            font-size: 28px;
            color: #333;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
            font-size: 14px;
        }
        input {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            font-family: inherit;
            transition: border-color 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            margin-top: 10px;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        button:active {
            transform: translateY(0);
        }
        button:disabled {
            opacity: 0.7;
            cursor: not-allowed;
        }
        .error {
            color: #dc3545;
            font-size: 14px;
            padding: 10px;
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 4px;
            margin-bottom: 20px;
            display: none;
        }
        .success {
            color: #155724;
            font-size: 14px;
            padding: 10px;
            background: #d4edda;
            border: 1px solid #c3e6cb;
            border-radius: 4px;
            margin-bottom: 20px;
            display: none;
        }
        .spinner {
            display: inline-block;
            width: 12px;
            height: 12px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 0.8s linear infinite;
            margin-right: 8px;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Enterprise AI OS</h1>
        <p class="subtitle">Multi-tenant AI Platform</p>
        
        <div class="error" id="errorMsg"></div>
        <div class="success" id="successMsg"></div>
        
        <form id="loginForm">
            <div class="form-group">
                <label for="username">Email</label>
                <input type="email" id="username" name="username" required value="admin@enterprise.ai">
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required value="Admin@1234">
            </div>
            
            <button type="submit" id="submitBtn">
                <span id="btnText">Sign in</span>
            </button>
        </form>
    </div>

    <script>
        const form = document.getElementById('loginForm');
        const submitBtn = document.getElementById('submitBtn');
        const btnText = document.getElementById('btnText');
        const errorMsg = document.getElementById('errorMsg');
        const successMsg = document.getElementById('successMsg');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Clear messages
            errorMsg.style.display = 'none';
            successMsg.style.display = 'none';
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            // Show loading state
            submitBtn.disabled = true;
            btnText.innerHTML = '<span class="spinner"></span>Signing in...';
            
            try {
                // Send to backend auth endpoint
                const response = await fetch('/api/v1/auth/token', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: new URLSearchParams({
                        username: username,
                        password: password,
                        tenant_id: 'default'
                    })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Login failed');
                }
                
                const data = await response.json();
                
                // Store token
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('refresh_token', data.refresh_token);
                
                // Show success
                successMsg.textContent = 'Login successful! Redirecting...';
                successMsg.style.display = 'block';
                
                // Redirect to chat
                setTimeout(() => {
                    window.location.href = '/chat';
                }, 1500);
                
            } catch (error) {
                console.error('Login error:', error);
                errorMsg.textContent = error.message || 'Login failed. Please check your credentials.';
                errorMsg.style.display = 'block';
                
                // Reset button
                submitBtn.disabled = false;
                btnText.textContent = 'Sign in';
            }
        });
    </script>
</body>
</html>
"""

CHAT_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat - Enterprise AI OS</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            height: 100vh;
            display: flex;
        }
        .container {
            display: flex;
            width: 100%;
            height: 100vh;
        }
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: white;
        }
        .header {
            padding: 20px;
            border-bottom: 1px solid #e0e0e0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .header h1 {
            font-size: 20px;
            margin: 0;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .message {
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
        }
        .message.user {
            flex-direction: row-reverse;
        }
        .message-bubble {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 8px;
            word-wrap: break-word;
            line-height: 1.4;
        }
        .message.assistant .message-bubble {
            background: #f0f0f0;
            color: #333;
        }
        .message.user .message-bubble {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .input-area {
            padding: 20px;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 12px;
        }
        textarea {
            flex: 1;
            padding: 12px;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            font-family: inherit;
            font-size: 14px;
            resize: none;
            max-height: 120px;
        }
        textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .send-btn {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            transition: transform 0.2s;
        }
        .send-btn:hover {
            transform: translateY(-2px);
        }
        .send-btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
        }
        .loading {
            color: #999;
            font-style: italic;
            padding: 12px 16px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="chat-area">
            <div class="header">
                <h1>💬 Chat with Enterprise AI</h1>
            </div>
            
            <div class="messages" id="messages">
                <div class="message assistant">
                    <div class="message-bubble">
                        👋 Hello! I'm your Enterprise AI Assistant. How can I help you today?
                    </div>
                </div>
            </div>
            
            <div class="input-area">
                <textarea id="input" placeholder="Type your message..." rows="1"></textarea>
                <button class="send-btn" onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>

    <script>
        const token = localStorage.getItem('access_token');
        if (!token) {
            window.location.href = '/login';
        }

        const messagesDiv = document.getElementById('messages');
        const input = document.getElementById('input');
        let isLoading = false;

        function addMessage(text, isUser) {
            const msg = document.createElement('div');
            msg.className = 'message ' + (isUser ? 'user' : 'assistant');
            
            const bubble = document.createElement('div');
            bubble.className = 'message-bubble';
            bubble.textContent = text;
            
            msg.appendChild(bubble);
            messagesDiv.appendChild(msg);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        async function sendMessage() {
            const text = input.value.trim();
            if (!text || isLoading) return;
            
            isLoading = true;
            input.value = '';
            input.disabled = true;
            
            addMessage(text, true);
            
            try {
                const response = await fetch('/api/v1/ai/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + token
                    },
                    body: JSON.stringify({
                        messages: [{ role: 'user', content: text }],
                        conversation_id: 'demo'
                    })
                });
                
                if (!response.ok) throw new Error('Failed to send message');
                
                const data = await response.json();
                const aiResponse = data.answer || data.response || data.message || 'No response';
                addMessage(aiResponse, false);
                
            } catch (error) {
                addMessage('❌ Error: ' + error.message, false);
            } finally {
                isLoading = false;
                input.disabled = false;
                input.focus();
            }
        }
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        input.focus();
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    port = 3001
    server_address = ("", port)
    httpd = HTTPServer(server_address, RequestHandler)
    
    print(f"✅ Frontend server starting on http://localhost:{port}")
    print(f"📡 Backend API: {BACKEND_URL}")
    print(f"🔐 Test credentials: admin@enterprise.ai / Admin@1234")
    print(f"⏹️  Press Ctrl+C to stop\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n✋ Server stopped")
        sys.exit(0)

"""
Universal Version Badge Middleware
Automatically injects version badge on ALL HTML pages
"""
from fastapi import Request
from fastapi.responses import Response
import json
from datetime import datetime

class VersionBadgeMiddleware:
    """Middleware to inject version badge on all HTML responses"""
    
    def __init__(self, app):
        self.app = app
        self.version = "v3.5.34"
        
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        # Capture the response
        send_wrapper = SendWrapper(send, self.version)
        await self.app(scope, receive, send_wrapper)


class SendWrapper:
    """Wrapper to intercept and modify response body"""
    
    def __init__(self, send, version):
        self.send = send
        self.version = version
        self.body_parts = []
        self.headers = {}
        
    async def __call__(self, message):
        if message["type"] == "http.response.start":
            # Capture headers
            self.headers = dict(message.get("headers", []))
            # Remove content-length header as we'll modify the body
            message["headers"] = [
                (name, value) for name, value in message.get("headers", [])
                if name.lower() != b"content-length"
            ]
            await self.send(message)
            
        elif message["type"] == "http.response.body":
            # Check if this is HTML content
            content_type = self.headers.get(b"content-type", b"").decode()
            
            if "text/html" in content_type:
                # Accumulate body parts
                body = message.get("body", b"")
                more_body = message.get("more_body", False)
                
                self.body_parts.append(body)
                
                if not more_body:
                    # This is the last chunk, inject badge
                    full_body = b"".join(self.body_parts)
                    modified_body = self.inject_version_badge(full_body)
                    
                    # Send modified body
                    await self.send({
                        "type": "http.response.body",
                        "body": modified_body,
                        "more_body": False
                    })
                # If more_body is True, wait for next chunk
            else:
                # Not HTML, pass through unchanged
                await self.send(message)
                
    def inject_version_badge(self, html_body):
        """Inject version badge into HTML body"""
        version_badge = f'''
        <!-- AVA OLO Version Badge -->
        <div id="ava-olo-version-badge" style="
            position: fixed;
            bottom: 10px;
            right: 10px;
            background: #333;
            color: white;
            padding: 8px 12px;
            border-radius: 5px;
            font-size: 12px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            z-index: 9999;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            cursor: pointer;
            transition: all 0.3s ease;
        " onclick="this.style.opacity = this.style.opacity == '0.3' ? '1' : '0.3';">
            <span id="version-text">{self.version}</span>
            <span id="deploy-status" style="
                display: inline-block;
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: #FFC107;
                animation: pulse 2s infinite;
            "></span>
            <style>
                @keyframes pulse {{
                    0% {{ opacity: 1; }}
                    50% {{ opacity: 0.6; }}
                    100% {{ opacity: 1; }}
                }}
                #ava-olo-version-badge:hover {{
                    transform: scale(1.05);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
                }}
            </style>
        </div>
        <script>
        (function() {{
            // Check deployment status
            fetch('/api/deployment/status')
                .then(r => r.json())
                .then(data => {{
                    const versionEl = document.getElementById('version-text');
                    const statusEl = document.getElementById('deploy-status');
                    
                    if (versionEl) versionEl.textContent = data.version || '{self.version}';
                    
                    if (statusEl) {{
                        if (data.fully_deployed) {{
                            statusEl.style.backgroundColor = '#4CAF50';
                            statusEl.style.animation = 'none';
                            statusEl.title = 'Fully Deployed';
                        }} else {{
                            statusEl.style.backgroundColor = '#FFC107';
                            statusEl.title = 'Partial Deployment';
                        }}
                    }}
                }})
                .catch(() => {{
                    const statusEl = document.getElementById('deploy-status');
                    if (statusEl) {{
                        statusEl.style.backgroundColor = '#F44336';
                        statusEl.style.animation = 'none';
                        statusEl.title = 'Deployment Error';
                    }}
                }});
        }})();
        </script>
        '''.encode()
        
        # Try to inject before </body>
        if b'</body>' in html_body:
            return html_body.replace(b'</body>', version_badge + b'</body>')
        # If no </body>, append at end
        else:
            return html_body + version_badge
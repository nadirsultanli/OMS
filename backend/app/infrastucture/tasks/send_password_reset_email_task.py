import secrets
from app.infrastucture.logs.logger import default_logger
from decouple import config
from celery import shared_task

logger = default_logger

@shared_task(
    name="app.infrastucture.tasks.send_password_reset_email_task.send_password_reset_email_task",
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, "countdown": 10},
    queue="email_queue"
)
def send_password_reset_email_task(email: str, user_name: str, user_id: str, role: str, frontend_url: str):
    try:
        logger.info(f"📧 Sending password reset email to: {email}")
        
        # Generate simple token with user_id
        token = f"{user_id}_{secrets.token_urlsafe(32)}"
        
        # Email content
        subject = "Password Reset Request - LPG-OMS"
        
        # Choose frontend URL based on role
        if role.lower() == "admin":
            reset_url = f"{frontend_url}/reset-password?token={token}"
        else:
            # For drivers, use a different frontend URL
            driver_frontend_url = config("DRIVER_FRONTEND_URL", default="http://localhost:3001")
            reset_url = f"{driver_frontend_url}/reset-password?token={token}"
        
        content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .email-container {{
                    background-color: #ffffff;
                    border-radius: 10px;
                    padding: 40px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .logo {{
                    font-size: 28px;
                    font-weight: bold;
                    color: #2c3e50;
                    margin-bottom: 10px;
                }}
                .subtitle {{
                    color: #7f8c8d;
                    font-size: 16px;
                }}
                .greeting {{
                    font-size: 18px;
                    color: #2c3e50;
                    margin-bottom: 20px;
                }}
                .content {{
                    margin-bottom: 30px;
                }}
                .reset-button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 25px;
                    font-weight: bold;
                    font-size: 16px;
                    margin: 20px 0;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(231, 76, 60, 0.4);
                    transition: all 0.3s ease;
                }}
                .reset-button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(231, 76, 60, 0.6);
                }}
                .link-text {{
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    border-left: 4px solid #e74c3c;
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    word-break: break-all;
                    margin: 20px 0;
                }}
                .important {{
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .important h4 {{
                    color: #721c24;
                    margin-top: 0;
                    margin-bottom: 15px;
                }}
                .important ul {{
                    margin: 0;
                    padding-left: 20px;
                }}
                .important li {{
                    margin-bottom: 8px;
                    color: #721c24;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e9ecef;
                    color: #6c757d;
                }}
                .team-name {{
                    font-weight: bold;
                    color: #2c3e50;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <div class="logo">LPG-OMS</div>
                    <div class="subtitle">Order Management System</div>
                </div>
                
                <div class="greeting">Hello {user_name},</div>
                
                <div class="content">
                    <p>We received a request to reset your password for your <strong>LPG-OMS</strong> account.</p>
                    
                    <p>To reset your password, please click the button below:</p>
                </div>
                
                <div style="text-align: center;">
                    <a href="{reset_url}" class="reset-button">Reset Password</a>
                </div>
                
                <p style="text-align: center; margin: 20px 0; color: #6c757d;">Or copy and paste this link in your browser:</p>
                
                <div class="link-text">{reset_url}</div>
                
                <div class="important">
                    <h4>🔒 Security Information:</h4>
                    <ul>
                        <li>This link will expire in <strong>1 hour</strong> for your security.</li>
                        <li>If you didn't request this password reset, please ignore this email.</li>
                        <li>Your password will remain unchanged until you click the link above.</li>
                        <li>For additional security, consider changing your password regularly.</li>
                    </ul>
                </div>
                
                <div class="footer">
                    <p>Best regards,<br><span class="team-name">CIRCL Team</span></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Import and call the general email task
        from .send_email_task import send_email_task
        result = send_email_task.delay(email, subject, content)
        
        logger.info(f"✅ Password reset email sent to {email} with token: {token}")
        return {"task_id": result.id, "token": token}
        
    except Exception as e:
        logger.error(f"❌ Failed to send password reset email to {email}: {e}")
        raise e 
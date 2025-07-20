import smtplib
from email.mime.text import MIMEText
from app.infrastucture.logs.logger import default_logger
from decouple import config
from celery import shared_task

logger = default_logger

@shared_task(
    name="app.infrastucture.tasks.send_email_task.send_email_task",
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, "countdown": 10},
    queue="email_queue"
)
def send_email_task(email: str, subject: str, content: str):
    try:
        logger.info("📧 Fetching SMTP config from .env")
        smtp_server = config("SMTP_SERVER", default="smtp.gmail.com")
        smtp_port = config("SMTP_PORT", cast=int, default=587)
        smtp_user = config("SMTP_USER")
        smtp_password = config("SMTP_PASSWORD")

        logger.info(f"📧 Preparing message for: {email}")
        msg = MIMEText(content, "html")  # Send as HTML content
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = email

        logger.info("📧 Connecting to SMTP server...")
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
        server.starttls()
        server.login(smtp_user, smtp_password)

        logger.info(f"📧 Sending email to {email}")
        server.sendmail(smtp_user, email, msg.as_string())
        server.quit()

        logger.info(f"✅ Email sent to {email} (subject: {subject})")

    except Exception as e:
        logger.error(f"❌ Failed to send email to {email} (subject: {subject}): {e}")
        raise e
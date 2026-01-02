"""Email service for sending magic links and notifications."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

from app.core.config import settings


class EmailService:
    """Service for sending emails."""

    def __init__(self):
        """Initialize email service."""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAIL_FROM

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (fallback)

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            # Add plain text part
            if text_content:
                part1 = MIMEText(text_content, "plain")
                msg.attach(part1)

            # Add HTML part
            part2 = MIMEText(html_content, "html")
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_user and self.smtp_password:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)

                server.sendmail(self.from_email, to_email, msg.as_string())

            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    async def send_magic_link(
        self,
        to_email: str,
        magic_link: str,
        expires_in_minutes: int,
    ) -> bool:
        """
        Send a magic link authentication email.

        Args:
            to_email: Recipient email address
            magic_link: Magic link URL
            expires_in_minutes: Link expiration time in minutes

        Returns:
            True if email sent successfully, False otherwise
        """
        subject = "🏀 Your Git League Login Link"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background-color: #f9fafb;
                    border-radius: 8px;
                    padding: 30px;
                }}
                .logo {{
                    text-align: center;
                    font-size: 48px;
                    margin-bottom: 20px;
                }}
                h1 {{
                    color: #004E89;
                    font-size: 24px;
                    margin-bottom: 20px;
                }}
                .button {{
                    display: inline-block;
                    background-color: #FF6B35;
                    color: white !important;
                    padding: 14px 28px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .expiry {{
                    color: #6b7280;
                    font-size: 14px;
                    margin-top: 20px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    font-size: 12px;
                    color: #9ca3af;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">🏀</div>
                <h1>Welcome to The Git League!</h1>
                <p>Click the button below to sign in to your account:</p>
                <a href="{magic_link}" class="button">Sign In to The Git League</a>
                <p class="expiry">
                    ⏰ This link will expire in {expires_in_minutes} minutes.
                </p>
                <p>
                    If you didn't request this login link, you can safely ignore this email.
                </p>
                <div class="footer">
                    <p>
                        This is an automated email from The Git League.
                        <br>
                        Not working? Copy and paste this link into your browser:
                        <br>
                        {magic_link}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to The Git League!

        Click the link below to sign in to your account:
        {magic_link}

        This link will expire in {expires_in_minutes} minutes.

        If you didn't request this login link, you can safely ignore this email.
        """

        return await self.send_email(to_email, subject, html_content, text_content)


# Singleton instance
email_service = EmailService()

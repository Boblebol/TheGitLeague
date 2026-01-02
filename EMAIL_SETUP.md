# 📧 Email Provider Setup Guide

This guide explains how to configure email delivery for **magic link authentication** in The Git League.

---

## 📋 Overview

The Git League uses **passwordless authentication** via magic links sent to user emails. To send these emails, you need to configure an SMTP email provider.

**Environment Variables Used:**
```bash
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-smtp-password
EMAIL_FROM=noreply@thegitleague.com
```

---

## 🧪 Development Setup (MailHog)

For **local development**, we use [MailHog](https://github.com/mailhog/MailHog) to test emails without actually sending them.

### Configuration

In your `.env` file:

```bash
# Email Configuration (Development)
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=noreply@thegitleague.local

# MailHog ports
MAILHOG_SMTP_PORT=1025
MAILHOG_WEB_PORT=8025
```

### Start MailHog

```bash
# With Docker Compose (recommended)
docker-compose up -d mailhog

# Access web interface
open http://localhost:8025
```

### Testing

1. Request a magic link (e.g., via frontend or API)
2. Open MailHog at http://localhost:8025
3. Find your email and click the magic link

**Note:** MailHog captures all emails, so they never leave your local machine.

---

## 🚀 Production Setup

Choose one of the following email providers for production:

### Option 1: Gmail (Simple, Small Teams)

**Pros:** Free (with limits), easy setup
**Cons:** 500 emails/day limit, requires App Password

#### Setup Steps

1. **Enable 2FA** on your Gmail account
2. **Generate App Password:**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Copy the 16-character password

3. **Configure `.env`:**

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
EMAIL_FROM=your-email@gmail.com
```

#### Limitations
- 500 emails per day
- Not recommended for production use (deliverability issues)
- Use only for small teams or testing

---

### Option 2: SendGrid (Recommended for Production)

**Pros:** Reliable, scalable, generous free tier (100 emails/day)
**Cons:** Requires account creation

#### Setup Steps

1. **Create SendGrid Account:**
   - Go to https://signup.sendgrid.com/
   - Free tier: 100 emails/day forever

2. **Create API Key:**
   - Settings → API Keys → Create API Key
   - Choose "Full Access" or "Mail Send" permission
   - Copy the API key (starts with `SG.`)

3. **Verify Sender Identity:**
   - Settings → Sender Authentication → Verify a Single Sender
   - Enter your "From" email (e.g., noreply@yourdomain.com)
   - Check your email and click verification link

4. **Configure `.env`:**

```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.your-actual-api-key-here
EMAIL_FROM=noreply@yourdomain.com
```

**Important:**
- `SMTP_USER` is literally the string `"apikey"` (not your email)
- `SMTP_PASSWORD` is your SendGrid API key

#### Free Tier Limits
- 100 emails/day
- Sufficient for small teams (10-20 users)

#### Paid Tier
- Starts at $20/month for 40k emails/month
- Better deliverability and support

---

### Option 3: AWS SES (Enterprise, Cost-Effective)

**Pros:** Very cheap ($0.10 per 1000 emails), highly scalable
**Cons:** More complex setup, requires AWS account

#### Setup Steps

1. **Create AWS Account** and enable SES

2. **Verify Domain or Email:**
   - AWS Console → SES → Verified Identities
   - Add and verify your domain or email

3. **Create SMTP Credentials:**
   - SES → SMTP Settings → Create SMTP Credentials
   - Download credentials (username + password)

4. **Request Production Access:**
   - By default, SES is in "sandbox mode" (can only send to verified emails)
   - Submit a request to move to production (usually approved in 24h)

5. **Configure `.env`:**

```bash
# US East (N. Virginia) region example
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-smtp-username
SMTP_PASSWORD=your-smtp-password
EMAIL_FROM=noreply@yourdomain.com
```

**Region-specific SMTP endpoints:**
- `us-east-1`: email-smtp.us-east-1.amazonaws.com
- `eu-west-1`: email-smtp.eu-west-1.amazonaws.com
- `ap-southeast-1`: email-smtp.ap-southeast-1.amazonaws.com
- [See full list](https://docs.aws.amazon.com/ses/latest/dg/smtp-connect.html)

#### Pricing
- First 62,000 emails/month: **FREE** (from EC2)
- Beyond that: $0.10 per 1,000 emails

---

### Option 4: Microsoft 365 / Outlook (Enterprise)

**Pros:** Integration with corporate email
**Cons:** Requires Microsoft 365 subscription

#### Setup Steps

1. **Create App Password** (if using MFA):
   - account.microsoft.com → Security → Additional security options
   - Create app password

2. **Configure `.env`:**

```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@yourdomain.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@yourdomain.com
```

#### Limitations
- 10,000 emails per day (per mailbox)
- Requires Microsoft 365 Business subscription

---

### Option 5: Custom SMTP Server

If you manage your own mail server:

```bash
SMTP_HOST=mail.yourdomain.com
SMTP_PORT=587  # or 465 for SSL, 25 for legacy
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=your-password
EMAIL_FROM=noreply@yourdomain.com
```

**Common ports:**
- **587** (STARTTLS) — Recommended, modern standard
- **465** (SSL/TLS) — Older but still supported
- **25** (Plain) — Usually blocked by ISPs, not recommended

---

## ✅ Testing Your Email Setup

### 1. Test via API

```bash
curl -X POST http://localhost:8000/api/v1/auth/magic-link \
  -H "Content-Type: application/json" \
  -d '{"email": "your-test-email@example.com"}'
```

**Expected Response:**
```json
{
  "message": "Magic link sent to your-test-email@example.com"
}
```

### 2. Check Email Delivery

- **Development (MailHog):** Open http://localhost:8025
- **Production:** Check your inbox (and spam folder!)

### 3. Verify Magic Link Works

Click the link in the email. You should be redirected to the app and automatically logged in.

---

## 🔧 Troubleshooting

### "Connection refused" or "SMTP connection failed"

**Possible causes:**
- Wrong SMTP host or port
- Firewall blocking outbound SMTP (port 587/465/25)
- SMTP server requires authentication but credentials missing

**Solution:**
```bash
# Test SMTP connection with telnet
telnet smtp.gmail.com 587

# Or with openssl (for SSL/TLS)
openssl s_client -connect smtp.gmail.com:587 -starttls smtp
```

---

### "Authentication failed" or "535 Error"

**Possible causes:**
- Wrong username or password
- Gmail: Not using App Password (regular password won't work)
- SendGrid: Using email instead of "apikey" as username

**Solution:**
- Double-check credentials
- For Gmail: Use App Password, not regular password
- For SendGrid: Username must be exactly `"apikey"`

---

### "Sender not verified" (SendGrid/SES)

**Cause:** You must verify your sender email/domain before sending.

**Solution:**
- **SendGrid:** Settings → Sender Authentication → Verify Single Sender
- **AWS SES:** SES Console → Verified Identities → Add email/domain

---

### Emails going to spam

**Possible causes:**
- No SPF/DKIM/DMARC records configured
- Sending from generic domain (e.g., @gmail.com)
- Low sender reputation

**Solutions:**
1. **Use a custom domain** (not @gmail.com)
2. **Configure SPF record** (DNS TXT record):
   ```
   v=spf1 include:_spf.google.com ~all  # For Gmail
   v=spf1 include:sendgrid.net ~all     # For SendGrid
   ```
3. **Enable DKIM** (SendGrid/SES provide this)
4. **Warm up your domain** (start with low volume, gradually increase)

---

### "Too many login attempts" (Gmail)

**Cause:** Google may temporarily block automated logins.

**Solutions:**
- Use App Password instead of regular password
- Enable "Less secure app access" (not recommended)
- Switch to SendGrid or SES for production

---

## 🔒 Security Best Practices

### 1. Never Commit Credentials

**Bad:**
```bash
# .env committed to Git
SMTP_PASSWORD=mypassword123
```

**Good:**
```bash
# .env in .gitignore
# Use environment variables or secret management
```

### 2. Use Environment Variables

```bash
# In production (e.g., Docker, Kubernetes)
docker run -e SMTP_PASSWORD=$SMTP_PASSWORD ...
```

### 3. Rotate Credentials Regularly

- Change SMTP passwords every 90 days
- Regenerate API keys if leaked

### 4. Use Least Privilege

- SendGrid: Use "Mail Send" permission only (not "Full Access")
- AWS SES: Create IAM user with `ses:SendEmail` only

### 5. Monitor Email Quota

- Set up alerts for email quota limits
- Track bounce rates and spam reports

---

## 📊 Provider Comparison

| Provider | Free Tier | Cost (Paid) | Setup Difficulty | Best For |
|----------|-----------|-------------|------------------|----------|
| **MailHog** | Unlimited (local) | N/A | ⭐ Easy | Development only |
| **Gmail** | 500/day | N/A | ⭐⭐ Easy | Small teams, testing |
| **SendGrid** | 100/day | $20/mo (40k/mo) | ⭐⭐ Easy | Small-Medium teams |
| **AWS SES** | 62k/mo | $0.10/1k | ⭐⭐⭐ Moderate | Enterprise, high volume |
| **Office 365** | 10k/day | Included | ⭐⭐ Easy | Corporate integration |
| **Custom SMTP** | Varies | Varies | ⭐⭐⭐⭐ Hard | Self-hosted |

---

## 🎯 Recommended Setup

### Development
```bash
# Use MailHog (included in docker-compose)
SMTP_HOST=localhost
SMTP_PORT=1025
```

### Small Teams (<100 users)
```bash
# Use SendGrid Free Tier
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=SG.your-api-key
```

### Enterprise / High Volume
```bash
# Use AWS SES
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-ses-username
SMTP_PASSWORD=your-ses-password
```

---

## 📚 Additional Resources

- **SendGrid Docs:** https://docs.sendgrid.com/for-developers/sending-email/integrating-with-the-smtp-api
- **AWS SES Docs:** https://docs.aws.amazon.com/ses/latest/dg/send-email-smtp.html
- **Gmail App Passwords:** https://support.google.com/accounts/answer/185833
- **MailHog:** https://github.com/mailhog/MailHog
- **Email Deliverability Best Practices:** https://sendgrid.com/blog/email-deliverability-best-practices/

---

## 🆘 Need Help?

If you encounter issues not covered here:

1. Check backend logs: `docker-compose logs backend`
2. Test SMTP connection manually (see Troubleshooting)
3. Open a GitHub issue with logs and configuration (redact passwords!)

---

**Ready to send magic links?** 🚀

[Back to Main README](./README.md) | [Development Guide](./DEVELOPMENT.md)

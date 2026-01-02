# 🔒 Security Audit & Recommendations

This document provides a comprehensive security audit of The Git League application, covering current security measures and recommendations for improvement.

**Last Updated:** 2024-12-27
**Status:** ✅ Good foundation, ⚠️ Some improvements recommended

---

## 📋 Executive Summary

### ✅ Current Security Strengths
- ✅ **SQL Injection Protection** - SQLAlchemy ORM with parameterized queries
- ✅ **Input Validation** - Pydantic schemas with type validation
- ✅ **Password Hashing** - Argon2 (industry standard)
- ✅ **JWT Authentication** - Secure token-based auth with expiration
- ✅ **Encryption** - Fernet encryption for repository credentials
- ✅ **CORS Configuration** - Properly configured for cross-origin requests
- ✅ **Magic Link Security** - One-time use tokens with expiration

### ⚠️ Security Gaps (Recommended Improvements)
- ⚠️ **No Cookie-Based Sessions** - Using Bearer tokens only (less secure for web apps)
- ⚠️ **No Rate Limiting** - Vulnerable to brute force and DoS attacks
- ⚠️ **No CSRF Protection** - Required if using cookies
- ⚠️ **No Security Headers** - Missing Helmet-style headers
- ⚠️ **No Content Security Policy (CSP)** - XSS vulnerability mitigation
- ⚠️ **CORS Too Permissive** - Allows all methods and headers

---

## 🔐 Detailed Security Analysis

### 1. Authentication System

**Current Implementation:**
```python
# Backend uses Bearer tokens (JWT)
Authorization: Bearer <token>
```

**✅ Strengths:**
- Magic link authentication (passwordless)
- JWT tokens with expiration (15 minutes for magic links, 1440 minutes for access tokens)
- One-time use magic links (marked as `used` in database)
- Token validation on every request
- User approval workflow (PENDING → APPROVED)

**⚠️ Weaknesses:**
1. **No HTTPOnly Cookies** - Bearer tokens stored in localStorage are vulnerable to XSS
2. **Long Access Token Expiry** - 1440 minutes (24 hours) is too long for sensitive operations
3. **No Refresh Tokens** - Forces re-authentication instead of smooth token refresh

**🔧 Recommendation: Add Cookie-Based Authentication**

Create a dual-token system with HTTPOnly cookies:

```python
# backend/app/api/v1/auth.py
from fastapi import Response

@router.get("/verify", response_model=TokenResponse)
async def verify_magic_link(
    token: str,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
):
    result = await auth_service.verify_magic_link(token=token, db=db)

    # Set HTTPOnly cookie for better security
    response.set_cookie(
        key="access_token",
        value=result["access_token"],
        httponly=True,  # Prevents JavaScript access (XSS protection)
        secure=True,     # HTTPS only
        samesite="lax",  # CSRF protection
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

    return result
```

Update `get_current_user` dependency to support both cookies and Bearer tokens:

```python
# backend/app/api/deps.py
from fastapi import Cookie, Header

def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    access_token: Optional[str] = Cookie(None),  # Check cookie first
    authorization: Optional[str] = Header(None),  # Fallback to Bearer token
) -> User:
    # Prefer cookie, fallback to header
    token = access_token
    if not token and authorization:
        scheme, _, param = authorization.partition(" ")
        if scheme.lower() == "bearer":
            token = param

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return auth_service.get_current_user(token, db)
```

---

### 2. SQL Injection Protection

**Current Implementation:**
```python
# SQLAlchemy ORM with parameterized queries
user = db.query(User).filter(User.email == email).first()
```

**✅ Status: PROTECTED**

- All database queries use SQLAlchemy ORM
- No raw SQL with string concatenation
- Parameterized queries prevent injection

**✅ No Action Required**

---

### 3. Cross-Site Scripting (XSS)

**Current Implementation:**
- Pydantic validates input types
- FastAPI automatically JSON-encodes responses

**⚠️ Weaknesses:**
1. **No Content Security Policy (CSP)** headers
2. **No input sanitization** for HTML content (if rendering user input)
3. **Bearer tokens in localStorage** vulnerable to XSS attacks

**🔧 Recommendation: Add Security Headers**

Create a security headers middleware:

```python
# backend/app/middleware/security.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Adjust for your needs
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'"
        )

        # Prevent MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # XSS Protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Force HTTPS (production only)
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response
```

Add to `main.py`:
```python
from app.middleware.security import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
```

---

### 4. Cross-Site Request Forgery (CSRF)

**Current Implementation:**
- ❌ **No CSRF protection**

**⚠️ Risk Level:**
- **Low** if using Bearer tokens only (CSRF doesn't affect Bearer tokens)
- **HIGH** if implementing cookie-based auth (recommended above)

**🔧 Recommendation: Add CSRF Protection (If Using Cookies)**

```python
# backend/app/middleware/csrf.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import secrets

# Store CSRF tokens (use Redis in production)
csrf_tokens = {}

class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF for safe methods
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)

        # Skip CSRF for magic link verification (one-time token)
        if request.url.path == "/api/v1/auth/verify":
            return await call_next(request)

        # Verify CSRF token
        csrf_token = request.headers.get("X-CSRF-Token")
        cookie_token = request.cookies.get("csrf_token")

        if not csrf_token or not cookie_token or csrf_token != cookie_token:
            raise HTTPException(status_code=403, detail="CSRF token missing or invalid")

        return await call_next(request)


@app.get("/api/v1/csrf-token")
async def get_csrf_token(response: Response):
    """Generate CSRF token."""
    token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=False,  # JavaScript needs to read this
        secure=True,
        samesite="lax",
    )
    return {"csrf_token": token}
```

---

### 5. Rate Limiting

**Current Implementation:**
- ❌ **No rate limiting**

**⚠️ Vulnerabilities:**
1. **Brute Force Attacks** - Unlimited magic link requests
2. **DoS Attacks** - API can be overwhelmed
3. **Email Bombing** - Unlimited magic link emails to same address

**🔧 Recommendation: Add Rate Limiting**

Install `slowapi`:
```bash
pip install slowapi
```

Implement rate limiting:
```python
# backend/app/core/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
)
```

Add to `main.py`:
```python
from app.core.rate_limit import limiter, RateLimitExceeded, _rate_limit_exceeded_handler

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

Apply to sensitive endpoints:
```python
# backend/app/api/v1/auth.py
from app.core.rate_limit import limiter

@router.post("/magic-link")
@limiter.limit("5/minute")  # Max 5 magic links per minute per IP
async def request_magic_link(...):
    ...
```

**Recommended Limits:**
```python
# Magic Link: 5 requests per minute per IP
# Login: 10 attempts per 15 minutes per IP
# API endpoints: 100 requests per minute per user
# Webhook sync: 1 request per 5 minutes per project
```

---

### 6. CORS Configuration

**Current Implementation:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],  # ⚠️ Too permissive
    allow_headers=["*"],  # ⚠️ Too permissive
)
```

**⚠️ Issues:**
1. **Wildcard methods** - Should restrict to needed methods only
2. **Wildcard headers** - Should restrict to needed headers only

**🔧 Recommendation: Restrict CORS**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-CSRF-Token",
        "X-Requested-With",
    ],
    expose_headers=["Content-Range", "X-Total-Count"],
)
```

---

### 7. Input Validation & Sanitization

**Current Implementation:**
```python
# Pydantic schemas with type validation
class MagicLinkRequest(BaseModel):
    email: EmailStr  # ✅ Email validation
```

**✅ Strengths:**
- Pydantic validates all input types
- EmailStr validates email format
- Field constraints (min/max length, ranges)

**⚠️ Gaps:**
1. **No HTML sanitization** (if rendering user input)
2. **No URL validation** for repository URLs
3. **No file upload validation** (if implemented)

**🔧 Recommendations:**

```python
# Add validators for URLs
from pydantic import HttpUrl, validator

class RepositoryCreate(BaseModel):
    url: HttpUrl  # Validates URL format

    @validator('url')
    def validate_git_url(cls, v):
        # Additional validation for Git URLs
        if not any(v.startswith(prefix) for prefix in ['git@', 'https://', 'http://']):
            raise ValueError('Invalid Git URL')
        return v

# Sanitize user-generated content
import bleach

def sanitize_html(html: str) -> str:
    """Sanitize HTML to prevent XSS."""
    allowed_tags = ['p', 'br', 'strong', 'em', 'a', 'ul', 'ol', 'li']
    allowed_attrs = {'a': ['href', 'title']}
    return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)
```

---

### 8. Secrets Management

**Current Implementation:**
```python
# .env file with secrets
SECRET_KEY=your-secret-key
FERNET_KEY=your-fernet-key
```

**✅ Strengths:**
- Secrets not committed to Git (.env in .gitignore)
- Fernet encryption for repository credentials
- Argon2 for password hashing (if used)

**⚠️ Recommendations:**
1. **Use environment variables** in production (not .env files)
2. **Use secret management** (AWS Secrets Manager, HashiCorp Vault)
3. **Rotate secrets regularly** (90-day rotation policy)

**🔧 Production Setup:**

```bash
# Use Docker secrets
docker secret create db_password /path/to/password.txt

# Or environment variables
export SECRET_KEY=$(openssl rand -hex 32)
export FERNET_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
```

---

### 9. Dependency Security

**Current Status:**
- ⚠️ **No automated dependency scanning**

**🔧 Recommendation: Add Dependency Scanning**

```yaml
# .github/workflows/security.yml
name: Security Scan
on: [push, pull_request]

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Safety check
        run: |
          pip install safety
          safety check -r backend/requirements.txt

      - name: Run Bandit (Python security linter)
        run: |
          pip install bandit
          bandit -r backend/app/
```

Add to `requirements-dev.txt`:
```
safety==2.3.5
bandit==1.7.5
```

Run locally:
```bash
# Check for known vulnerabilities
safety check -r backend/requirements.txt

# Security linting
bandit -r backend/app/
```

---

## 🎯 Priority Action Items

### 🔴 Critical (Do First)
1. **Add Rate Limiting** - Prevents brute force and DoS attacks
   - Magic link endpoint: 5/minute per IP
   - Login attempts: 10/15min per IP

2. **Shorten Access Token Expiry** - Reduce from 24h to 1-2 hours
   - Add refresh token mechanism

3. **Add Security Headers** - CSP, X-Frame-Options, etc.

### 🟡 High Priority (Do Soon)
4. **Implement Cookie-Based Auth** - HTTPOnly cookies for XSS protection
5. **Add CSRF Protection** - If using cookies
6. **Restrict CORS** - Remove wildcards, specify exact methods/headers

### 🟢 Medium Priority (Do Later)
7. **Dependency Scanning** - Automated vulnerability checks
8. **Input Sanitization** - HTML sanitization if rendering user content
9. **Audit Logging** - Log security events (failed logins, permission changes)

---

## 📊 Security Checklist

### Authentication & Authorization
- [x] Magic link authentication
- [x] JWT with expiration
- [x] One-time use tokens
- [x] Role-based access control (RBAC)
- [ ] HTTPOnly cookies
- [ ] Refresh tokens
- [ ] Rate limiting on auth endpoints

### Input Validation
- [x] Pydantic schema validation
- [x] Email validation
- [x] Type checking
- [ ] URL validation
- [ ] HTML sanitization
- [ ] File upload validation

### Data Protection
- [x] SQLAlchemy ORM (SQL injection protection)
- [x] Argon2 password hashing
- [x] Fernet encryption for credentials
- [x] HTTPS enforcement (production)
- [ ] Field-level encryption for sensitive data

### Network Security
- [x] CORS configured
- [ ] CORS restricted (no wildcards)
- [ ] Rate limiting
- [ ] CSRF protection
- [ ] Security headers (CSP, X-Frame-Options)

### Monitoring & Logging
- [ ] Failed login attempt logging
- [ ] Permission change audit trail
- [ ] Security event alerts
- [ ] Dependency vulnerability scanning

---

## 🔧 Implementation Guide

### Quick Wins (1-2 hours each)

**1. Add Security Headers**
```bash
# Create middleware file
touch backend/app/middleware/security.py

# Copy Security Headers implementation from section 3 above
```

**2. Add Rate Limiting**
```bash
# Install slowapi
pip install slowapi

# Add to requirements.txt
echo "slowapi==0.1.9" >> backend/requirements.txt

# Implement rate limiting (see section 5 above)
```

**3. Restrict CORS**
```python
# Edit backend/app/main.py
# Replace allow_methods=["*"] with explicit list
```

### Moderate Effort (4-8 hours each)

**4. Implement HTTPOnly Cookies**
- Modify auth endpoints to set cookies
- Update get_current_user to check cookies
- Add logout endpoint to clear cookies

**5. Add CSRF Protection**
- Create CSRF middleware
- Add CSRF token endpoint
- Update frontend to include CSRF tokens

### Larger Projects (1-2 days each)

**6. Refresh Token System**
- Create refresh token model
- Implement refresh endpoint
- Add automatic token refresh in frontend

**7. Comprehensive Audit Logging**
- Create audit log model
- Add audit middleware
- Create audit log viewer UI

---

## 📚 Additional Resources

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **JWT Best Practices**: https://tools.ietf.org/html/rfc8725
- **CORS Security**: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
- **CSP Guide**: https://content-security-policy.com/

---

## 🆘 Reporting Security Issues

If you discover a security vulnerability, please email: security@thegitleague.com

**Do not** open a public GitHub issue for security vulnerabilities.

---

**Last Reviewed:** 2024-12-27
**Next Review:** 2025-03-27 (Quarterly)

---

[Back to README](./README.md) | [Development Guide](./DEVELOPMENT.md)

# 🏀 The Git League

Transform your Git activity into an NBA-style league: stats, rankings, awards, "plays of the day", seasons, and fantasy league — all **self-hosted** and **open source**.

## 🎯 Features

- **Gamification**: Turn Git commits into NBA-style stats (PTS/REB/AST/BLK/STL/TOV)
- **Secure PAT Management**: Encrypted storage of Personal Access Tokens for private repositories
- **Multi-Repository Support**: Track contributions across multiple repos with a single PAT
- **Awards & Highlights**: Player of the Week/Month, MVP, Hall of Fame
- **Fantasy League**: Draft contributors and compete based on their stats
- **Self-Hosted**: Keep your code metadata private, no SaaS required

## 🔐 Security Features

- **Encryption at-rest**: All credentials encrypted with Fernet (AES-128 + HMAC-SHA256)
- **RBAC**: Role-based access control (Commissioner, Player, Spectator)
- **Audit Logging**: Track all credential access and configuration changes
- **Rate Limiting**: Protect sensitive endpoints from abuse
- **No Code Storage**: Only metadata (commits, stats, messages) - never source code

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Node.js 18+ (for frontend, coming soon)

### Backend Setup

1. **Clone the repository**

```bash
git clone https://github.com/Boblebol/TheGitLeague.git
cd TheGitLeague
```

2. **Create virtual environment**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Generate encryption master key**

```bash
python backend/scripts/generate_encryption_key.py
```

⚠️  **IMPORTANT**: Save the generated key securely! You'll need it in the next step.

5. **Configure environment**

```bash
cp .env.example .env
```

Edit `.env` and set:
- `ENCRYPTION_MASTER_KEY` (from step 4)
- `SECRET_KEY` (generate with: `openssl rand -hex 32`)
- `DATABASE_URL` (your PostgreSQL connection string)

**Example `.env`:**
```bash
ENCRYPTION_MASTER_KEY=your-44-character-base64-key-here
SECRET_KEY=your-jwt-secret-key-min-32-characters
DATABASE_URL=postgresql://thegitleague:password@localhost:5432/thegitleague
REDIS_URL=redis://localhost:6379/0
ENVIRONMENT=development
DEBUG=false
```

6. **Set file permissions** (critical for security)

```bash
chmod 600 .env
```

7. **Create database**

```bash
# PostgreSQL
createdb thegitleague

# Or via psql
psql -U postgres -c "CREATE DATABASE thegitleague;"
```

8. **Run database migrations** (coming soon)

```bash
alembic upgrade head
```

9. **Run the application**

```bash
uvicorn backend.main:app --reload
```

API docs available at: http://localhost:8000/docs

## 📁 Project Structure

```
TheGitLeague/
├── backend/
│   ├── core/
│   │   ├── config.py          # Configuration with Pydantic
│   │   └── encryption.py      # Fernet encryption module
│   ├── models/
│   │   ├── user.py            # User model (RBAC)
│   │   ├── project.py         # Project model
│   │   ├── repository.py      # Repository with encrypted_credentials
│   │   └── audit_log.py       # Audit logging
│   ├── services/
│   │   └── repository_service.py  # Secure PAT handling
│   ├── schemas/
│   │   └── repository.py      # Pydantic request/response schemas
│   ├── api/
│   │   └── routes/            # FastAPI endpoints (coming soon)
│   ├── scripts/
│   │   └── generate_encryption_key.py  # Key generation utility
│   ├── tests/
│   │   └── test_encryption.py # Encryption tests
│   └── requirements.txt       # Python dependencies
├── Base doc                   # Comprehensive PRD and documentation
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## 🔐 Security Best Practices

### DO ✅

- Store `ENCRYPTION_MASTER_KEY` in a secure password manager (1Password, Bitwarden, Vault)
- Use `.env` file with `600` permissions (owner read/write only)
- Backup your encryption key securely (if lost, credentials are irrecoverable)
- Rotate PAT tokens regularly
- Use a dedicated "bot" GitHub account for PATs (not personal tokens)
- Enable HTTPS in production (use reverse proxy like Traefik/Nginx)

### DON'T ❌

- ❌ Never commit `.env` to Git
- ❌ Never share encryption keys in plain text (email, Slack, etc.)
- ❌ Never log decrypted tokens
- ❌ Never embed credentials in Git URLs (use PAT field instead)
- ❌ Never use personal PAT tokens (create a bot account)

## 🧪 Running Tests

```bash
# Run all tests
pytest backend/tests/ -v

# Run encryption tests only
pytest backend/tests/test_encryption.py -v

# With coverage
pytest backend/tests/ --cov=backend --cov-report=html
```

## 📊 Database Schema

### Core Tables

- **users**: User accounts with RBAC (commissioner/player/spectator)
- **projects**: Collection of repositories
- **repos**: Git repositories with encrypted credentials
- **audit_logs**: Security and compliance tracking

### Key Fields

#### `repos.encrypted_credentials` (JSONB)
```json
{
  "type": "pat",
  "encrypted_data": "gAAAAABl...[encrypted]...",
  "algorithm": "fernet",
  "key_version": "v1"
}
```

**NEVER exposed in API responses** — only metadata like `has_credentials: true` is returned.

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ENCRYPTION_MASTER_KEY` | ✅ | Fernet key for encrypting credentials | `3x4mpl3K3yB4s364...` |
| `SECRET_KEY` | ✅ | JWT signing key (min 32 chars) | `your-secret-key` |
| `DATABASE_URL` | ✅ | PostgreSQL connection string | `postgresql://user:pass@localhost/db` |
| `REDIS_URL` | ❌ | Redis connection string | `redis://localhost:6379/0` |
| `ENVIRONMENT` | ❌ | `development` or `production` | `development` |
| `DEBUG` | ❌ | Enable debug mode (never in prod) | `false` |
| `CORS_ORIGINS` | ❌ | Allowed frontend URLs | `http://localhost:3000` |
| `RATE_LIMIT_ENABLED` | ❌ | Enable rate limiting | `true` |
| `LOG_LEVEL` | ❌ | Logging level | `INFO` |

## 📖 Documentation

Comprehensive documentation is available in the **Base doc** file:

1. **PRD.md** - Product Requirements Document
2. **SECURITY.md** - Security architecture and PAT encryption
3. **TECHNICAL_STACK.md** - Tech stack and libraries
4. **UX_GUIDELINES.md** - UI/UX patterns
5. **ROADMAP_AND_GTM.md** - Development timeline

### Security Documentation Highlights

- PAT encryption architecture (Fernet)
- Database schema for `encrypted_credentials`
- Master key management and rotation
- Audit logging and monitoring
- Docker deployment best practices
- Incident response procedures
- Deployment security checklist

## 🛠️ Technology Stack

### Backend
- **FastAPI**: Modern Python web framework with OpenAPI
- **SQLAlchemy**: ORM and database migrations (Alembic)
- **PostgreSQL**: Relational database with JSONB support
- **Redis**: Caching and job queue
- **Cryptography**: Fernet encryption for credentials
- **Celery**: Background job processing

### Frontend (Coming Soon)
- **Next.js**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS + shadcn/ui**: UI components
- **TanStack Query**: Data fetching and caching

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines (coming soon).

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest backend/tests/ -v`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 License

This project is open source and available under the MIT License (coming soon).

## 🔒 Security

### Reporting Vulnerabilities

Please report security issues to: [security@yourdomain.com]

**Response time**: < 48 hours

### Security Features

- ✅ Encryption at-rest (Fernet AES-128)
- ✅ RBAC (Commissioner/Player/Spectator)
- ✅ Audit logging
- ✅ Rate limiting
- ✅ HTTPS-only in production (recommended)

## 🙏 Acknowledgments

- Inspired by the NBA and fantasy sports
- Built for engineering teams who value transparency and fun
- Privacy-first: self-hosted, no SaaS dependencies

## 📞 Support

- GitHub Issues: [Report bugs or request features](https://github.com/Boblebol/TheGitLeague/issues)
- Documentation: See **Base doc** file
- Security: [security@yourdomain.com]

---

**Made with 🏀 for developers who love Git and basketball**

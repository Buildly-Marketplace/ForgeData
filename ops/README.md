# ops/ Directory - Operations & Deployment

This directory contains all deployment and operational scripts for ForgeMarketing.

## 🚀 Quick Start

```bash
# Initial setup - creates virtualenv, installs dependencies
./ops/startup.sh setup

# Initialize database and migrate credentials
python3 ops/init_database.py
python3 ops/migrate_credentials.py

# Start server
./ops/startup.sh start

# Stop server
./ops/startup.sh stop

# Restart server
./ops/startup.sh restart
```

## Main Scripts

### `startup.sh` (⭐ PRIMARY)
**Setup and deployment manager for ForgeMarketing**

Complete operational script that handles:
- Python 3 prerequisites check
- Virtual environment creation (.venv)
- Dependency installation from requirements.txt
- Configuration validation
- Smoke tests
- Server startup, stop, and restart management
- PID tracking and log management

**Usage:**
```bash
./ops/startup.sh setup                    # Initial setup
./ops/startup.sh start                    # Start server (default port 8002)
./ops/startup.sh start --port 9000        # Start on custom port
./ops/startup.sh stop                     # Stop server
./ops/startup.sh restart                  # Restart server
./ops/startup.sh setup --clean            # Fresh install (removes .venv)
./ops/startup.sh --help                   # Show all options
```

**Features:**
- Automatic .venv creation if missing
- Requirements installation with pip
- Ollama connectivity check (warning, not blocking)
- Smoke tests before startup
- PID file tracking (`ops/.server.pid`)
- Server logging to `ops/server.log`
- Graceful shutdown with force-kill fallback
- Prevents duplicate server instances
- Color-coded output for easy troubleshooting
- Both Flask dev server and Gunicorn support

### `init_database.py`
**Database initialization script**

Creates all database tables and loads default brands.

**Usage:**
```bash
python3 ops/init_database.py
```

### `migrate_credentials.py`
**Credential migration script**

Migrates hardcoded credentials and environment variables to database storage for enhanced security.

**Usage:**
```bash
python3 ops/migrate_credentials.py
```

**Migrates:**
- System-wide configuration (Ollama, Flask settings)
- Brand-specific API credentials (Twitter, Google Analytics, YouTube)
- Email provider configurations
- All sensitive tokens and keys

## Configuration Management

### Database-Backed Configuration (✅ RECOMMENDED)
All credentials and configuration stored securely in database:

1. **System Config Table** - Global settings
2. **Brand API Credentials** - Service-specific auth
3. **Brand Email Configs** - Email provider settings
4. **Audit Logs** - Track all credential access

**Benefits:**
- No hardcoded secrets in code
- Centralized management via admin UI
- Audit trail for compliance
- Easy credential rotation
- Environment-agnostic deployment

### Legacy Environment Variables (⚠️ DEPRECATED)
System falls back to environment variables if database values not set.
Run `migrate_credentials.py` to move to database storage.

## Docker Deployment

### `Dockerfile`
Production-ready Docker image with:
- Python 3.10 slim base
- System dependencies (PostgreSQL client, curl)
- Health checks
- Port 8002 exposure

**Build:**
```bash
docker build -t forgemark:latest -f ops/Dockerfile .
```

**Run:**
```bash
docker run -p 5000:5000 -e OLLAMA_HOST=ollama:11434 forgemark:latest
```

### `docker-compose.yml`
Multi-service stack with:
- ForgeMark application
- PostgreSQL database
- Ollama AI service

**Usage:**
```bash
docker-compose -f ops/docker-compose.yml up -d
docker-compose -f ops/docker-compose.yml logs -f
docker-compose -f ops/docker-compose.yml down
```

## Kubernetes Deployment

### `helm/forgemark/`
Helm chart for Kubernetes deployment

**Files:**
- `Chart.yaml` - Chart metadata
- `values-example.yaml` - Example configuration values

**Installation:**
```bash
helm install forgemark ops/helm/forgemark/ \
  -n forgemark \
  --create-namespace \
  -f ops/helm/forgemark/values-example.yaml
```

## Legacy Scripts

- `legacy_setup_buildly_outreach.sh` - Old setup script (archived for reference)

## Quick Start

**For local development:**
```bash
cd /path/to/marketing
./ops/startup.sh setup
./ops/startup.sh start
```

Setup will:
1. ✓ Verify Python 3 is installed
2. ✓ Create/use .venv
3. ✓ Install requirements
4. ✓ Copy .env.example to .env if missing
5. ✓ Check Ollama (non-blocking)
6. ✓ Run smoke tests

Start will:
1. ✓ Start server on http://localhost:8002
2. ✓ Save PID to `ops/.server.pid`
3. ✓ Log output to `ops/server.log`

**For production with Docker:**
```bash
docker-compose -f ops/docker-compose.yml up -d
```

**For Kubernetes:**
```bash
helm install forgemark ops/helm/forgemark/ -n forgemark --create-namespace
```

## Configuration

### Environment Variables
Used by `startup.sh`:
- `FLASK_ENV` - development or production (default: development)
- `OLLAMA_HOST` - Ollama server address (default: localhost:11434)
- `DATABASE_URL` - Database connection (optional, defaults to SQLite)

### Port Configuration
Default: **8002**
Set custom: `./ops/startup.sh start --port 9000`

### Server Management
- **PID File**: `ops/.server.pid` (tracks running process)
- **Log File**: `ops/server.log` (server output and errors)
- **View logs**: `tail -f ops/server.log`

## Troubleshooting

### Script won't execute
```bash
chmod +x ./ops/startup.sh
```

### Python not found
Install Python 3.8+: https://python.org

### Virtual environment issues
```bash
./ops/startup.sh setup --clean    # Fresh install
```

### Port already in use
```bash
./ops/startup.sh start --port 9000
```

### Server won't stop
```bash
./ops/startup.sh stop    # Graceful shutdown with force-kill fallback
```

### View server errors
```bash
tail -f ops/server.log
```

### Ollama not responding
```bash
# In another terminal:
ollama serve

# Optional: Pull a model
ollama pull mistral
```

## File Structure

```
ops/
├── startup.sh                 ⭐ Main setup/start/stop/restart script
├── Dockerfile                 Docker image definition
├── docker-compose.yml         Multi-service compose
├── helm/
│   └── forgemark/
│       ├── Chart.yaml         Helm chart metadata
│       └── values-example.yaml Example values
└── legacy_setup_buildly_outreach.sh  Old script (archived)
```

## Support

See `/SUPPORT.md` for getting help and `/devdocs/OPERATIONS.md` for detailed operations guide.

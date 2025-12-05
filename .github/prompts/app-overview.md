# ForgeData - App Overview

## Purpose
ForgeData is a universal data exploration, ETL, reporting, and visualization platform designed to consolidate multiple data management workflows into a single, cohesive application. It provides organizations with the tools to connect to multi-cloud databases, transform data securely, and generate actionable insights.

## Core Features

### 1. Data Explorer
- Real-time database browsing and schema inspection
- Table data preview with pagination
- Ad-hoc SQL query execution with safety guards
- Database statistics and metadata viewing

### 2. ETL Pipeline
- Extract, Transform, Load operations with job tracking
- Built-in data anonymization (hash, mask, redact, substitute, generalize)
- Configurable deduplication rules
- Append, reset, and update modes for data loading
- Background job processing with status monitoring

### 3. Reporting & Analytics
- Star schema query builder
- Saved report management
- Custom aggregations and filters
- Visualization configuration support
- Organization-level report isolation

### 4. Multi-Cloud Database Support
- Google Cloud SQL (PostgreSQL, MySQL)
- AWS RDS (PostgreSQL, MySQL)
- Digital Ocean Managed Databases (PostgreSQL, MySQL)
- Universal connection factory pattern for easy extension

### 5. Security & Multi-Tenancy
- Buildly Core authentication integration
- Organization-level data isolation
- Secure credential storage
- SQL injection protection
- Role-based access (via Buildly)

## Architecture

### Technology Stack
- **Backend**: FastAPI (Python)
- **Database**: SQLAlchemy ORM with async support
- **Frontend**: Jinja2 templates, htmx, Alpine.js, Tailwind CSS
- **Authentication**: Buildly Core OAuth2
- **Data Processing**: Pandas, NumPy

### Application Structure
```
src/
├── main.py                 # FastAPI application entry point
├── core/
│   ├── config.py          # Settings and configuration
│   └── database.py        # Database models and connection factory
├── routers/
│   ├── auth.py            # Authentication endpoints
│   ├── etl.py             # ETL job management
│   ├── reporting.py       # Report CRUD and execution
│   └── explorer.py        # Data exploration endpoints
├── services/
│   ├── etl_service.py     # ETL business logic
│   ├── reporting_service.py  # Reporting business logic
│   └── explorer_service.py   # Explorer business logic
└── templates/
    └── index.html         # Landing page
```

## Key Concepts

### Connection Management
- Connections are organization-scoped configurations
- Each connection stores provider type and credentials
- Connection factory creates appropriate connection strings
- Connections are validated before use

### ETL Jobs
- Jobs are background tasks that process data
- Configurable anonymization and deduplication
- Status tracking: pending → running → completed/failed
- Job history maintained for auditing

### Reports
- Saved query configurations with visualization metadata
- Parameterized execution with runtime filters
- Star schema support for complex analytical queries
- Results cached for performance

### Data Anonymization Methods
1. **Hash**: SHA-256 hash of original value (one-way)
2. **Mask**: Show first/last char, mask middle with asterisks
3. **Redact**: Replace with [REDACTED] placeholder
4. **Substitute**: Replace with random similar value
5. **Generalize**: Round numbers, categorize strings

## Integration Points

### Buildly Core
- OAuth2 authentication flow
- Organization and user management
- Multi-tenant data isolation
- API token validation

### Cloud Providers
- Standard database connection protocols
- SSL/TLS support for secure connections
- IAM integration capability (future)

## Deployment

### Development
```bash
./ops/startup.sh setup
./ops/startup.sh start
```

### Production
- Docker container deployment
- Kubernetes via Helm charts
- Environment-based configuration
- Health check endpoints

## Data Flow

1. **User Authentication**
   - User logs in via Buildly Core
   - Receives JWT token
   - Token validates organization membership

2. **Connection Setup**
   - Admin creates database connection
   - Credentials stored encrypted
   - Connection tested and validated

3. **ETL Process**
   - User creates ETL job with source/target
   - Job runs in background
   - Data anonymized per rules
   - Duplicates removed if enabled
   - Results written to target table

4. **Reporting**
   - User builds report query
   - Report saved with visualization config
   - Report executed with runtime filters
   - Results returned as JSON

## Development Standards
- Follow Buildly Forge conventions
- Use async/await for I/O operations
- Implement proper error handling
- Log important operations
- Write tests for critical paths
- Document API endpoints
- Use type hints throughout

## Future Enhancements
- Real-time data streaming
- ML model integration for data quality
- Advanced visualization library integration
- Data lineage tracking
- Workflow orchestration
- Custom transformation functions
- API rate limiting and caching
- Audit log export

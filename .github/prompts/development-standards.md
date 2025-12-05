# Buildly Forge Development Standards

## Project Structure

All Buildly Forge projects follow a consistent structure:

```
project-root/
├── .github/
│   └── prompts/           # AI assistant context and documentation
│       ├── app-overview.md
│       ├── architecture.md
│       ├── development-standards.md
│       └── todo.md
├── src/                   # Source code
├── ops/                   # Operations and deployment
│   ├── startup.sh        # Unified startup/build script
│   ├── Dockerfile
│   └── helm/             # Kubernetes configs
├── devdocs/              # Developer documentation
├── static/               # Static assets
│   └── forge-logo.png   # Official Forge logo
├── BUILDLY.yaml          # Forge metadata
├── requirements.txt      # Dependencies
└── README.md             # User-facing docs
```

## BUILDLY.yaml Standard

Every Forge project must include a `BUILDLY.yaml` file:

```yaml
name: ProjectName
slug: project-slug
version: 1.0.0
summary: One-line description
license: BSL-1.1->Apache-2.0
license_change_date: "YYYY-MM-DD"
categories:
  - category1
  - category2
targets:
  - docker
  - k8s
author: Buildly Labs
homepage: https://github.com/buildly-marketplace/project
repository: https://github.com/buildly-marketplace/project
description: |
  Detailed multi-line description
  
docker:
  image: buildly/project
  ports:
    - "PORT:PORT"
  environment:
    - KEY=value

k8s:
  helm_chart_path: ops/helm/project
  values_example: ops/helm/project/values-example.yaml
```

## Coding Standards

### Python (FastAPI)

**File Organization**
- One router per domain concept
- Services contain business logic
- Models/schemas in separate files
- Config in `core/config.py`

**Naming Conventions**
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

**Type Hints**
```python
from typing import List, Dict, Optional

async def get_items(
    item_id: str,
    limit: Optional[int] = 100
) -> List[Dict[str, Any]]:
    """
    Docstring with clear description
    
    Args:
        item_id: Unique identifier
        limit: Maximum items to return
        
    Returns:
        List of item dictionaries
        
    Raises:
        ValueError: If item_id is invalid
    """
    pass
```

**Async/Await**
- Use `async def` for I/O operations
- Use `await` for database calls, HTTP requests
- Use `asyncio.gather()` for parallel operations

**Error Handling**
```python
try:
    result = await some_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(
        status_code=500,
        detail="User-friendly error message"
    )
```

**Logging**
```python
import logging

logger = logging.getLogger(__name__)

logger.info("Operation started")
logger.warning("Potential issue detected")
logger.error("Operation failed", exc_info=True)
```

### API Design

**Endpoint Structure**
```
/api/{domain}/{resource}
/api/etl/connections
/api/etl/jobs
/api/reports
/api/explore/connections/{id}/tables
```

**HTTP Methods**
- `GET`: Retrieve resources
- `POST`: Create resources
- `PUT`: Full update
- `PATCH`: Partial update
- `DELETE`: Remove resources

**Response Format**
```python
# Success
{
    "data": [...],
    "meta": {
        "count": 10,
        "limit": 100,
        "offset": 0
    }
}

# Error
{
    "detail": "Error message",
    "status_code": 400
}
```

**Status Codes**
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `500`: Internal Server Error

### Database

**Models**
```python
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Model(Base):
    __tablename__ = "models"
    
    id = Column(String, primary_key=True)
    organization_id = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Queries**
```python
# Use async SQLAlchemy
from sqlalchemy import select

async def get_items(db: AsyncSession, org_id: str):
    result = await db.execute(
        select(Model).where(Model.organization_id == org_id)
    )
    return result.scalars().all()
```

### Security

**Authentication**
- Integrate with Buildly Core OAuth2
- Use JWT tokens
- Validate on every protected endpoint

**Multi-Tenancy**
- All queries filter by `organization_id`
- No cross-organization data access
- Validate ownership before operations

**Input Validation**
- Use Pydantic models for all inputs
- Sanitize SQL queries
- Validate file uploads
- Rate limit endpoints (future)

**Secrets Management**
- Environment variables for config
- Never commit credentials
- Use `.env` files (gitignored)

### Testing

**Unit Tests**
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_connection():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/etl/connections",
            json={...},
            headers={"Authorization": "Bearer token"}
        )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Connection"
```

**Coverage**
- Aim for >80% code coverage
- Test happy paths and error cases
- Mock external services
- Test authentication/authorization

### Documentation

**Code Comments**
- Explain "why", not "what"
- Document complex algorithms
- Add TODOs with ticket numbers
- Keep comments updated

**API Documentation**
- FastAPI auto-generates OpenAPI docs
- Add descriptions to endpoints
- Document request/response models
- Include example payloads

**README.md**
```markdown
# Project Name

Brief description

## Features
- Feature 1
- Feature 2

## Quick Start
\`\`\`bash
./ops/startup.sh setup
./ops/startup.sh start
\`\`\`

## Configuration
Environment variables...

## API Documentation
Visit /api/docs

## License
BSL-1.1 (converts to Apache-2.0)
```

## Git Workflow

**Branch Naming**
- `feature/description`
- `fix/bug-description`
- `docs/what-changed`
- `refactor/what-refactored`

**Commit Messages**
```
type: Short description (50 chars)

Longer explanation if needed (wrap at 72 chars)

Fixes #issue-number
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

**Pull Requests**
- Clear title and description
- Reference related issues
- Include tests
- Update documentation
- Pass CI checks

## Deployment

**ops/startup.sh Standard**
```bash
#!/bin/bash
# Commands: setup, start, stop, restart

setup)   # Install dependencies, initialize database
start)   # Start the application
stop)    # Stop the application  
restart) # Restart the application
```

**Environment Variables**
- Required vars documented in README
- `.env.example` file provided
- Validation on startup

**Docker**
- Multi-stage builds for smaller images
- Non-root user
- Health checks
- Volume mounts for data persistence

**Kubernetes**
- Helm charts in `ops/helm/`
- ConfigMaps for config
- Secrets for credentials
- Resource limits defined
- Readiness/liveness probes

## Buildly Forge Integration

**Branding**
- Use `forge-logo.png` in all UIs
- Follow Buildly color scheme
- Consistent typography

**Buildly Core Integration**
- OAuth2 authentication
- Organization management
- User management
- API token validation

**Licensing**
- BSL-1.1 initially
- Converts to Apache-2.0 after change date
- Include LICENSE file
- Copyright notices in files

## AI Assistant Context

**`.github/prompts/` Files**

1. **app-overview.md**: High-level description, features, purpose
2. **architecture.md**: Technical architecture, data flow, components
3. **development-standards.md**: This file
4. **todo.md**: Current tasks, completed items, future enhancements

**Purpose**
- Help AI assistants understand the project quickly
- Maintain consistency across conversations
- Document architectural decisions
- Track progress and TODOs

## Code Quality

**Linting**
- Use `ruff` or `flake8` for Python
- Fix all warnings before commit
- Configure in `pyproject.toml` or `.flake8`

**Formatting**
- Use `black` for Python
- 88 character line length
- Auto-format on save

**Type Checking**
- Use `mypy` for static type checking
- Strict mode recommended
- Fix type errors before merge

## Performance

**Database**
- Index foreign keys
- Use pagination for large datasets
- Avoid N+1 queries
- Connection pooling

**API**
- Async endpoints for I/O
- Background tasks for long operations
- Caching where appropriate
- Compression for large responses

**Frontend**
- Lazy loading
- Pagination
- Debounce user inputs
- Optimize images

## Monitoring

**Logging Levels**
- DEBUG: Development debugging
- INFO: Normal operations
- WARNING: Unexpected but handled
- ERROR: Operation failed
- CRITICAL: System-level failure

**What to Log**
- User actions (without PII)
- System errors with context
- Performance metrics
- Security events

**What NOT to Log**
- Passwords or tokens
- Full credit card numbers
- Personal identifiable information (PII)
- Session cookies

## Release Process

1. Update version in `BUILDLY.yaml`
2. Update CHANGELOG.md
3. Create git tag `vX.Y.Z`
4. Build Docker image
5. Push to registry
6. Deploy to staging
7. Run smoke tests
8. Deploy to production
9. Monitor for issues

## Continuous Improvement

- Regular dependency updates
- Security vulnerability scanning
- Performance profiling
- User feedback incorporation
- Code review best practices
- Refactor technical debt
- Update documentation

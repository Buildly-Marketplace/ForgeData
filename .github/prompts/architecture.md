# ForgeData Architecture

## System Architecture

ForgeData follows a modern, layered architecture pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Layer                             │
│  (Web Browser, API Clients, CLI Tools)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS/REST
┌──────────────────────▼──────────────────────────────────────┐
│                  FastAPI Application                         │
│  ┌────────────────────────────────────────────────────┐     │
│  │  API Routers                                        │     │
│  │  ├── /api/auth   (Authentication)                  │     │
│  │  ├── /api/etl    (ETL Management)                  │     │
│  │  ├── /api/reports (Reporting)                      │     │
│  │  └── /api/explore (Data Explorer)                  │     │
│  └────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Business Logic (Services)                          │     │
│  │  ├── ETLService                                     │     │
│  │  ├── ReportingService                               │     │
│  │  └── ExplorerService                                │     │
│  └────────────────────────────────────────────────────┘     │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Core Components                                    │     │
│  │  ├── DatabaseConnectionFactory                      │     │
│  │  ├── Configuration Management                       │     │
│  │  └── Authentication Middleware                      │     │
│  └────────────────────────────────────────────────────┘     │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌────▼────┐ ┌───────▼──────────┐
│  Local DB    │ │ Buildly │ │  Target Databases│
│  (SQLite)    │ │  Core   │ │  (Multi-Cloud)   │
│              │ │  API    │ │                  │
│ - Connections│ │         │ │ - GCP Cloud SQL  │
│ - ETL Jobs   │ │ - Auth  │ │ - AWS RDS        │
│ - Reports    │ │ - Users │ │ - Digital Ocean  │
└──────────────┘ │ - Orgs  │ └──────────────────┘
                 └─────────┘
```

## Component Details

### 1. API Layer (Routers)

**Authentication Router** (`routers/auth.py`)
- OAuth2 password flow integration
- Token validation via Buildly Core
- User and organization data retrieval
- Development mode fallback

**ETL Router** (`routers/etl.py`)
- Connection CRUD operations
- ETL job creation and management
- Table listing and metadata
- Background job execution

**Reporting Router** (`routers/reporting.py`)
- Report definition CRUD
- Report execution with filters
- Query result formatting
- Visualization config storage

**Explorer Router** (`routers/explorer.py`)
- Schema inspection
- Table data browsing
- Ad-hoc query execution
- Database statistics

### 2. Service Layer

**ETLService** (`services/etl_service.py`)
- Connection management and validation
- ETL job orchestration
- Data anonymization algorithms
- Deduplication logic
- Async job execution

**ReportingService** (`services/reporting_service.py`)
- Query builder from configuration
- Report execution engine
- Filter application
- Result aggregation

**ExplorerService** (`services/explorer_service.py`)
- Real-time schema introspection
- Safe query execution
- SQL injection prevention
- Metadata collection

### 3. Core Components

**DatabaseConnectionFactory** (`core/database.py`)
- Provider-agnostic connection string generation
- Cloud-specific connection logic
- SSL/TLS configuration
- Connection pooling

**Configuration** (`core/config.py`)
- Environment variable management
- Pydantic settings validation
- Multi-environment support
- Secret management

**Database Models** (`core/database.py`)
- ConnectionConfig: Database connection metadata
- ETLJob: ETL job tracking and status
- Report: Saved report definitions

## Data Flow Patterns

### ETL Process Flow
```
1. User creates connection → Stored in local DB
2. User creates ETL job → Job record created (pending)
3. Background task starts → Job status: running
4. Read from source → Apply transformations
5. Anonymize data → Based on rules
6. Deduplicate → Based on columns
7. Write to target → Append/Reset mode
8. Update job status → Completed/Failed
```

### Report Execution Flow
```
1. User creates report → Query config saved
2. User executes report → Load config
3. Build SQL query → Apply filters
4. Execute on target DB → Get results
5. Format results → Return JSON
6. Client renders → Table/Chart
```

### Data Explorer Flow
```
1. User selects connection → Validate access
2. Request schema → Introspect database
3. Select table → Load sample data
4. Execute query → Validate safety
5. Return results → Paginated response
```

## Security Architecture

### Authentication Flow
```
┌──────┐          ┌──────────┐          ┌─────────────┐
│Client│          │ForgeData │          │Buildly Core │
└───┬──┘          └────┬─────┘          └──────┬──────┘
    │                  │                        │
    │ Login Request    │                        │
    ├─────────────────>│                        │
    │                  │ Validate Credentials   │
    │                  ├───────────────────────>│
    │                  │                        │
    │                  │  JWT Token + User Data │
    │                  │<───────────────────────┤
    │  JWT Token       │                        │
    │<─────────────────┤                        │
    │                  │                        │
    │ API Request      │                        │
    │ + Token          │                        │
    ├─────────────────>│                        │
    │                  │ Validate Token         │
    │                  ├───────────────────────>│
    │                  │ User Info              │
    │                  │<───────────────────────┤
    │  Response        │                        │
    │<─────────────────┤                        │
```

### Multi-Tenancy Isolation
- All data scoped by `organization_id`
- Database-level filtering on every query
- Connection credentials isolated per org
- ETL jobs isolated per org
- Reports isolated per org

### Data Security Measures
1. **Credential Storage**: Encrypted connection configs
2. **Query Validation**: SQL injection prevention
3. **Access Control**: Organization-based permissions
4. **Anonymization**: Multiple PII protection methods
5. **Audit Logging**: Job and query history

## Scalability Considerations

### Horizontal Scaling
- Stateless API servers
- Background job queue (future: Celery/Redis)
- Shared database for state
- Load balancer ready

### Performance Optimizations
- Async I/O for database operations
- Connection pooling
- Query result pagination
- Cached metadata (future)

### Resource Management
- Configurable batch sizes for ETL
- Max workers for parallel processing
- Query timeout limits
- Memory-efficient pandas operations

## Deployment Architecture

### Docker Deployment
```
┌─────────────────────────────────────────┐
│          Docker Container               │
│  ┌────────────────────────────────┐    │
│  │   ForgeData FastAPI App        │    │
│  │   (Port 8000)                  │    │
│  └────────────────────────────────┘    │
│  ┌────────────────────────────────┐    │
│  │   SQLite Database              │    │
│  │   (Volume mounted)             │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### Kubernetes Deployment
```
┌──────────────── Namespace: forgedata ────────────────┐
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  Deployment: forgedata                      │    │
│  │  ├── Pod 1: forgedata-xxx                   │    │
│  │  ├── Pod 2: forgedata-yyy                   │    │
│  │  └── Pod 3: forgedata-zzz                   │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  Service: forgedata-svc                     │    │
│  │  (LoadBalancer)                              │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  PersistentVolumeClaim: forgedata-data      │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  ConfigMap: forgedata-config                │    │
│  └─────────────────────────────────────────────┘    │
│                                                       │
│  ┌─────────────────────────────────────────────┐    │
│  │  Secret: forgedata-secrets                  │    │
│  └─────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────┘
```

## Extension Points

### Adding New Cloud Providers
1. Extend `DatabaseConnectionFactory._create_*_connection()`
2. Add provider-specific configuration schema
3. Update validation logic
4. Add provider to documentation

### Adding New Anonymization Methods
1. Add method to `ETLService._anonymize_data()`
2. Update anonymization rules schema
3. Document method behavior
4. Add tests

### Adding New Database Types
1. Install database-specific driver
2. Update connection factory
3. Test connection and queries
4. Update requirements.txt

## Monitoring & Observability

### Health Checks
- `/health` - Basic health status
- `/api/info` - Application metadata
- Database connectivity checks (future)

### Logging
- Structured logging with timestamps
- Log levels: INFO, WARNING, ERROR
- Request/response logging (future)
- Performance metrics (future)

### Metrics (Future)
- ETL job success/failure rates
- Query execution times
- Active connections count
- API endpoint latencies

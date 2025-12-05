# ForgeData UI Functional Testing Checklist

## Testing Instructions
Open your browser to http://localhost:8000 and follow this checklist to test all functionality.

---

## ✅ 1. HOME PAGE (`/`)
### Navigation
- [ ] Logo and branding displayed correctly
- [ ] Navigation links present: Home, ETL, Visualizations, Configuration, API Docs
- [ ] Current page (Home) is highlighted in navigation

### Content
- [ ] Hero section with ForgeData title visible
- [ ] Features section displays key capabilities
- [ ] Quick start guide section visible
- [ ] Setup status section shows onboarding steps

### Actions
- [ ] Click "Get Started" button (if present)
- [ ] Verify all navigation links work

---

## ✅ 2. CONFIGURATION PAGE (`/configuration`)
### Navigation
- [ ] Configuration page highlighted in nav
- [ ] All nav links functional

### Cloud Credentials Tab
- [ ] Cloud credentials list loads
- [ ] Can view credential information (without sensitive data)
- [ ] Instructions for adding credentials via API are clear

### Database Connections Tab  
- [ ] Database connections list loads
- [ ] Can view connection information
- [ ] Can see connection status (active/inactive)
- [ ] Test connection button present

### System Status Tab
- [ ] System health information displayed
- [ ] Database status shown
- [ ] Environment information visible

### Actions to Test
1. **Add GCP Credentials** (via API):
   ```bash
   curl -X POST http://localhost:8000/api/onboarding/credentials/gcp \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test GCP Project",
       "project_id": "test-project-123",
       "use_gcloud_cli": true,
       "is_primary": true
     }'
   ```
   - [ ] Credential appears in list after refresh
   
2. **Add Database Connection** (via API):
   ```bash
   curl -X POST http://localhost:8000/api/onboarding/database-connection \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test PostgreSQL",
       "provider": "gcp",
       "db_type": "postgresql",
       "host": "localhost",
       "port": 5432,
       "username": "testuser",
       "password": "testpass",
       "database": "testdb",
       "ssl_enabled": false,
       "is_primary": true
     }'
   ```
   - [ ] Connection appears in list after refresh

---

## ✅ 3. ETL PAGE (`/etl`)
### Navigation  
- [ ] ETL page highlighted in nav
- [ ] Sub-navigation tabs visible: Backup, Restore, Transform, Jobs

### Backup Tab
- [ ] Database selection dropdown present
- [ ] Backup destination options available
- [ ] Backup configuration form visible
- [ ] Start Backup button present

### Restore Tab
- [ ] Source database selection
- [ ] Target database selection
- [ ] Restore options configurable
- [ ] Start Restore button present

### Transform Tab
- [ ] Anonymization options displayed
- [ ] De-duplication settings visible
- [ ] Transform rules configurable
- [ ] Start Transform button present

### Jobs Tab
- [ ] ETL jobs list loads
- [ ] Job status visible (pending, running, completed, failed)
- [ ] Job details can be viewed
- [ ] Can filter/search jobs

### Actions to Test
1. **View Databases**:
   ```bash
   curl http://localhost:8000/api/etl/databases
   ```
   - [ ] Databases list returns successfully

2. **Check Jobs**:
   ```bash
   curl http://localhost:8000/api/etl/jobs
   ```
   - [ ] Jobs list loads (may be empty)

---

## ✅ 4. VISUALIZATIONS PAGE (`/visualizations`)
### Navigation
- [ ] Visualizations page highlighted in nav

### Database Selection
- [ ] Database dropdown populated with available connections
- [ ] Can select a database

### Query Interface
- [ ] SQL query editor present
- [ ] Execute query button available
- [ ] Results table displays after query

### Visualization Options
- [ ] Chart type selector (bar, line, pie, etc.)
- [ ] Column mapping for X/Y axes
- [ ] Visualization renders after configuration

### Actions to Test
1. **List Analytics Databases**:
   ```bash
   curl http://localhost:8000/api/analytics/databases
   ```
   - [ ] Returns available databases

2. **Execute Test Query** (if you have a database connected):
   ```bash
   curl -X POST http://localhost:8000/api/analytics/query/sql \
     -H "Content-Type: application/json" \
     -d '{
       "connection_id": 1,
       "query": "SELECT * FROM information_schema.tables LIMIT 5"
     }'
   ```
   - [ ] Query executes successfully
   - [ ] Results returned in JSON format

---

## ✅ 5. API DOCUMENTATION (`/api/docs`)
### Navigation
- [ ] API Docs link works from any page

### Swagger UI
- [ ] OpenAPI/Swagger interface loads
- [ ] API endpoints grouped by category:
  - [ ] Authentication
  - [ ] ETL
  - [ ] Onboarding
  - [ ] Analytics
  - [ ] Reporting
  - [ ] Data Explorer

### Functionality
- [ ] Can expand endpoint groups
- [ ] Can view endpoint details
- [ ] "Try it out" button present
- [ ] Can execute test requests
- [ ] Responses shown with status codes

---

## ✅ 6. END-TO-END WORKFLOW TEST

### Scenario: Set up database and run simple ETL

1. **Add Cloud Credentials**
   - [ ] Use Configuration page or API to add GCP/AWS/DO credentials
   - [ ] Verify credentials appear in list

2. **Add Database Connection**
   - [ ] Add a database connection via API or future UI
   - [ ] Test connection works

3. **Backup Database**
   - [ ] Go to ETL > Backup tab
   - [ ] Select source database
   - [ ] Configure backup options
   - [ ] Start backup job
   - [ ] Verify job appears in Jobs tab

4. **Transform Data**
   - [ ] Go to ETL > Transform tab
   - [ ] Select database
   - [ ] Configure anonymization rules
   - [ ] Start transform job
   - [ ] Check job status

5. **Restore to Another Database**
   - [ ] Go to ETL > Restore tab
   - [ ] Select backup file
   - [ ] Select target database
   - [ ] Start restore job
   - [ ] Verify completion

6. **Visualize Data**
   - [ ] Go to Visualizations page
   - [ ] Select restored database
   - [ ] Write and execute query
   - [ ] Create visualization from results
   - [ ] Export or save visualization

---

## ✅ 7. CROSS-BROWSER TESTING
Test in multiple browsers:
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge

---

## ✅ 8. RESPONSIVE DESIGN
Test at different screen sizes:
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

---

## 🐛 KNOWN ISSUES TO FIX

1. **Onboarding Status Endpoint Error**
   - Status: ❌ CRITICAL
   - Error: `AttributeError: 'coroutine' object has no attribute 'scalars'`
   - Location: `src/services/credential_service.py:325`
   - Fix: Needs async/await correction

2. **Health Endpoint**
   - Status: ⚠️ MINOR
   - Issue: Returns empty response
   - Location: `src/main.py:100`
   - Fix: Add proper response model

---

## 📝 TEST RESULTS

### Date: ___________
### Tester: ___________

| Section | Status | Notes |
|---------|--------|-------|
| Home Page | ⬜ | |
| Configuration | ⬜ | |
| ETL | ⬜ | |
| Visualizations | ⬜ | |
| API Docs | ⬜ | |
| End-to-End | ⬜ | |

### Overall Status: ⬜ Pass / ⬜ Fail

### Critical Issues Found:
_List any blocking issues here_

### Minor Issues Found:
_List any non-blocking issues here_

---

## 🚀 QUICK API TESTS

Run these curl commands to quickly test API functionality:

```bash
# Health check
curl http://localhost:8000/health

# List ETL jobs
curl http://localhost:8000/api/etl/jobs

# List cloud credentials  
curl http://localhost:8000/api/onboarding/cloud-credentials

# List database connections
curl http://localhost:8000/api/onboarding/database-connections

# List analytics databases
curl http://localhost:8000/api/analytics/databases

# Get API info
curl http://localhost:8000/api/info
```

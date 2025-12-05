# Production Deployment Checklist

## Pre-Deployment

### 1. Code Preparation
- [ ] All hardcoded credentials removed
- [ ] Database migrations completed
- [ ] Tests passing
- [ ] Dependencies updated in `requirements.txt`
- [ ] `.env.example` updated with all required variables
- [ ] `.gitignore` includes sensitive files

### 2. Security Audit
- [ ] No API keys in code
- [ ] No passwords in code
- [ ] No tokens in code
- [ ] No usernames hardcoded (except system defaults)
- [ ] All secrets moved to database
- [ ] Audit logs enabled for credential access
- [ ] Strong `SECRET_KEY` configured

### 3. Database Setup
- [ ] Production database created
- [ ] Database migrations run
- [ ] Credentials migrated to database
- [ ] Database backups configured
- [ ] Database credentials secured

### 4. Configuration
- [ ] System config in database
- [ ] Brand configurations complete
- [ ] Email providers configured
- [ ] API credentials added via admin UI
- [ ] All environment variables set (if used)
- [ ] Logging configured
- [ ] HTTPS/SSL certificates obtained

## Deployment Steps

### 1. Server Setup
```bash
# Clone repository
git clone <repository-url>
cd ForgeMarketing

# Create virtualenv and install dependencies
./ops/startup.sh setup

# Initialize database
python3 ops/init_database.py

# Migrate credentials
python3 ops/migrate_credentials.py
```

### 2. Configuration
```bash
# Access admin panel
# http://your-domain.com/admin

# Configure:
# - System settings
# - Brand settings
# - Email providers
# - API credentials
```

### 3. Start Services
```bash
# Start server
./ops/startup.sh start

# Or use systemd (recommended for production)
sudo systemctl enable forgemarketing
sudo systemctl start forgemarketing
```

### 4. Verification
- [ ] Server responds on configured port
- [ ] Admin panel accessible
- [ ] Database connections working
- [ ] Email sending functional
- [ ] API integrations working
- [ ] Logs being written
- [ ] Health checks passing

## Post-Deployment

### 1. Monitoring Setup
- [ ] Server monitoring configured
- [ ] Log aggregation setup
- [ ] Error alerting configured
- [ ] Performance monitoring enabled
- [ ] Uptime monitoring active

### 2. Security Hardening
- [ ] Firewall configured
- [ ] HTTPS enforced
- [ ] Rate limiting enabled
- [ ] Security headers set
- [ ] CORS configured
- [ ] Authentication enabled

### 3. Backup Configuration
- [ ] Database backups scheduled
- [ ] Backup retention policy set
- [ ] Backup restoration tested
- [ ] File backups configured
- [ ] Disaster recovery plan documented

### 4. Documentation
- [ ] Deployment documented
- [ ] Runbook created
- [ ] Troubleshooting guide updated
- [ ] API documentation published
- [ ] User guides available

## Rollback Plan

### If Deployment Fails
1. Stop new server: `./ops/startup.sh stop`
2. Restore database backup
3. Revert code changes: `git checkout <previous-tag>`
4. Start old version: `./ops/startup.sh start`
5. Verify functionality
6. Investigate and fix issues

## Maintenance

### Regular Tasks
- [ ] Review audit logs weekly
- [ ] Rotate credentials quarterly
- [ ] Update dependencies monthly
- [ ] Test backups monthly
- [ ] Review error logs daily
- [ ] Monitor performance metrics
- [ ] Update documentation as needed

## Support Contacts

### Critical Issues
- **System Administrator**: [contact info]
- **Database Administrator**: [contact info]
- **Security Team**: [contact info]

### Escalation Path
1. On-call engineer
2. Team lead
3. Engineering manager
4. CTO

## Compliance

### Data Protection
- [ ] GDPR compliance verified
- [ ] Data encryption enabled
- [ ] Access controls configured
- [ ] Audit logging enabled
- [ ] Data retention policies set

### Security Standards
- [ ] Password policies enforced
- [ ] MFA enabled for admin access
- [ ] Regular security audits scheduled
- [ ] Vulnerability scanning configured
- [ ] Incident response plan documented

## Environment-Specific Notes

### Production
- Database: [connection details]
- Server: [server details]
- Domain: [domain name]
- SSL: [certificate provider]
- Monitoring: [monitoring service]

### Staging
- Database: [connection details]
- Server: [server details]
- Domain: [domain name]
- Purpose: Pre-production testing

### Development
- Local setup only
- No production credentials
- Mock external services

## Sign-Off

- [ ] Technical Lead Approval: ________________ Date: ________
- [ ] Security Review: ________________ Date: ________
- [ ] Operations Approval: ________________ Date: ________
- [ ] Product Owner Approval: ________________ Date: ________

---

**Deployment Date**: _______________
**Version**: _______________
**Deployed By**: _______________
**Sign-Off**: _______________

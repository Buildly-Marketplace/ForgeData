# ForgeData - Universal Data Platform

<div align="center">
  <img src="forge-logo.png" alt="Forge Logo" width="200"/>
  
  **Universal Data Exploration, ETL, Reporting & Visualization Platform**
  
  [![License](https://img.shields.io/badge/License-BSL--1.1-blue.svg)](LICENSE)
  [![Python](https://img.shields.io/badge/Python-3.9+-green.svg)](https://python.org)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-teal.svg)](https://fastapi.tiangolo.com)
</div>

## Overview

ForgeData consolidates data exploration, ETL processing, reporting, and visualization into a single, unified FastAPI application. Connect to databases across Google Cloud, AWS, Digital Ocean, and more—transform data with built-in anonymization and deduplication, build star schema reports, and visualize insights.

### Key Features

- 🔍 **Data Explorer**: Browse databases, inspect schemas, query data in real-time
- 🔄 **ETL Pipeline**: Extract, transform, load with anonymization and deduplication
- 📊 **Reporting**: Star schema queries, custom aggregations, saved reports
- ☁️ **Multi-Cloud**: Universal connectors for GCP, AWS, Digital Ocean
- 🔐 **Secure**: Data anonymization, SQL injection protection, multi-tenant isolation
- 🏢 **Enterprise**: API-based authentication and organization management

### Supported Databases

- PostgreSQL (GCP Cloud SQL, AWS RDS, Digital Ocean)
- MySQL (GCP Cloud SQL, AWS RDS, Digital Ocean)

## Quick Start

### Prerequisites

- Python 3.9 or higher
- pip
- (Optional) Docker for containerized deployment

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd forgedata
   ```

2. **Set up the environment**
   ```bash
   ./ops/startup.sh setup
   ```

3. **Configure environment variables**
   
   Edit `.env` file with your settings:
   ```env
   # Application
   DEBUG=true
   HOST=0.0.0.0
   PORT=8000
   
   # Database
   DATABASE_URL=sqlite:///./forgedata.db
   
   # Authentication (optional)
   # Configure your authentication settings in .env
   ```

4. **Start the server**
   ```bash
   ./ops/startup.sh start
   ```

5. **Access the application**
   - Web UI: http://localhost:8000
   - API Docs: http://localhost:8000/api/docs
   - Health Check: http://localhost:8000/health

## Documentation

- [App Overview](.github/prompts/app-overview.md) - High-level features and purpose
- [Architecture](.github/prompts/architecture.md) - Technical architecture and data flow
- [Development Standards](.github/prompts/development-standards.md) - Coding standards and best practices
- [TODO List](.github/prompts/todo.md) - Current tasks and future enhancements
- [API Documentation](http://localhost:8003/api/docs) - Interactive API documentation (when running)

## License

This project is licensed under the Business Source License 1.1 (BSL-1.1), which converts to Apache License 2.0 on December 5, 2026.

See [LICENSE](LICENSE) for details.

## Support

- 🐛 Issues: GitHub Issues
- 📖 Documentation: See docs in the repository

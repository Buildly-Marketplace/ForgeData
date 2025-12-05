"""
Universal database connection management
Supports multiple cloud providers: GCP, AWS, Digital Ocean
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData, Table, Column, String, DateTime, Text, JSON
from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
import logging

from src.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()
metadata = MetaData()

# Application database (SQLite for local state)
engine = None
async_session_maker = None


class ConnectionConfig(Base):
    """Store database connection configurations"""
    __tablename__ = "connection_configs"
    
    id = Column(String, primary_key=True)
    organization_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    provider = Column(String, nullable=False)  # gcp, aws, digitalocean
    connection_type = Column(String, nullable=False)  # postgres, mysql, etc
    config = Column(JSON, nullable=False)  # Provider-specific config
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ETLJob(Base):
    """ETL job tracking"""
    __tablename__ = "etl_jobs"
    
    id = Column(String, primary_key=True)
    organization_id = Column(String, index=True, nullable=False)
    connection_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False)  # pending, running, completed, failed
    config = Column(JSON, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    """Saved reports"""
    __tablename__ = "reports"
    
    id = Column(String, primary_key=True)
    organization_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    query_config = Column(JSON, nullable=False)
    visualization_config = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


async def init_db():
    """Initialize the application database"""
    global engine, async_session_maker
    
    logger.info("Initializing database...")
    
    # Use async SQLite for local state
    database_url = settings.DATABASE_URL
    if database_url.startswith("sqlite"):
        database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
    
    engine = create_async_engine(database_url, echo=settings.DEBUG)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized successfully")


async def get_session() -> AsyncSession:
    """Get database session"""
    async with async_session_maker() as session:
        yield session


class DatabaseConnectionFactory:
    """
    Factory for creating database connections to various cloud providers
    """
    
    @staticmethod
    def create_connection_string(provider: str, config: Dict[str, Any]) -> str:
        """
        Create a connection string based on provider and config
        
        Args:
            provider: Cloud provider (gcp, aws, digitalocean)
            config: Provider-specific configuration
            
        Returns:
            Database connection string
        """
        if provider == "gcp":
            return DatabaseConnectionFactory._create_gcp_connection(config)
        elif provider == "aws":
            return DatabaseConnectionFactory._create_aws_connection(config)
        elif provider == "digitalocean":
            return DatabaseConnectionFactory._create_do_connection(config)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    @staticmethod
    def _create_gcp_connection(config: Dict[str, Any]) -> str:
        """Create GCP Cloud SQL connection string"""
        db_type = config.get("db_type", "postgresql")
        user = config["user"]
        password = config["password"]
        host = config["host"]  # Can be IP or Cloud SQL instance connection name
        port = config.get("port", 5432 if db_type == "postgresql" else 3306)
        database = config["database"]
        
        if db_type == "postgresql":
            driver = "postgresql+psycopg2"
        elif db_type == "mysql":
            driver = "mysql+pymysql"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        return f"{driver}://{user}:{password}@{host}:{port}/{database}"
    
    @staticmethod
    def _create_aws_connection(config: Dict[str, Any]) -> str:
        """Create AWS RDS connection string"""
        db_type = config.get("db_type", "postgresql")
        user = config["user"]
        password = config["password"]
        host = config["host"]  # RDS endpoint
        port = config.get("port", 5432 if db_type == "postgresql" else 3306)
        database = config["database"]
        
        if db_type == "postgresql":
            driver = "postgresql+psycopg2"
        elif db_type == "mysql":
            driver = "mysql+pymysql"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        return f"{driver}://{user}:{password}@{host}:{port}/{database}"
    
    @staticmethod
    def _create_do_connection(config: Dict[str, Any]) -> str:
        """Create Digital Ocean managed database connection string"""
        db_type = config.get("db_type", "postgresql")
        user = config["user"]
        password = config["password"]
        host = config["host"]
        port = config.get("port", 25060)  # DO default port
        database = config["database"]
        
        # Digital Ocean requires SSL
        ssl_mode = config.get("ssl_mode", "require")
        
        if db_type == "postgresql":
            driver = "postgresql+psycopg2"
            return f"{driver}://{user}:{password}@{host}:{port}/{database}?sslmode={ssl_mode}"
        elif db_type == "mysql":
            driver = "mysql+pymysql"
            return f"{driver}://{user}:{password}@{host}:{port}/{database}?ssl=true"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    @staticmethod
    def create_engine(connection_string: str, **kwargs):
        """Create SQLAlchemy engine with connection string"""
        return create_engine(connection_string, **kwargs)

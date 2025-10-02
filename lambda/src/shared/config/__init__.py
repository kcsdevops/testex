"""
Configuration management for the TESTEX system
"""
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration"""
    contracts_table: str
    clients_table: str
    audit_logs_table: str
    region: str
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        return cls(
            contracts_table=os.environ.get('CONTRACTS_TABLE', 'testex-contracts'),
            clients_table=os.environ.get('CLIENTS_TABLE', 'testex-clients'),
            audit_logs_table=os.environ.get('AUDIT_LOGS_TABLE', 'testex-audit-logs'),
            region=os.environ.get('AWS_REGION', 'us-east-1')
        )


@dataclass
class StorageConfig:
    """Storage configuration"""
    files_bucket: str
    archives_bucket: str
    backups_bucket: str
    templates_bucket: str
    region: str
    
    @classmethod
    def from_env(cls) -> 'StorageConfig':
        return cls(
            files_bucket=os.environ.get('FILES_BUCKET', 'testex-files'),
            archives_bucket=os.environ.get('ARCHIVES_BUCKET', 'testex-archives'),
            backups_bucket=os.environ.get('BACKUPS_BUCKET', 'testex-backups'),
            templates_bucket=os.environ.get('TEMPLATES_BUCKET', 'testex-templates'),
            region=os.environ.get('AWS_REGION', 'us-east-1')
        )


@dataclass
class NotificationConfig:
    """Notification configuration"""
    sender_email: str
    sender_name: str
    ses_region: str
    template_bucket: str
    
    @classmethod
    def from_env(cls) -> 'NotificationConfig':
        return cls(
            sender_email=os.environ.get('SENDER_EMAIL', 'noreply@testex.com'),
            sender_name=os.environ.get('SENDER_NAME', 'TESTEX System'),
            ses_region=os.environ.get('SES_REGION', 'us-east-1'),
            template_bucket=os.environ.get('TEMPLATES_BUCKET', 'testex-templates')
        )


@dataclass
class LambdaConfig:
    """Lambda functions configuration"""
    contract_processor_function: str
    database_manager_function: str
    file_handler_function: str
    notification_service_function: str
    api_gateway_function: str
    
    @classmethod
    def from_env(cls) -> 'LambdaConfig':
        return cls(
            contract_processor_function=os.environ.get('CONTRACT_PROCESSOR_FUNCTION', 'testex-contract-processor'),
            database_manager_function=os.environ.get('DATABASE_MANAGER_FUNCTION', 'testex-database-manager'),
            file_handler_function=os.environ.get('FILE_HANDLER_FUNCTION', 'testex-file-handler'),
            notification_service_function=os.environ.get('NOTIFICATION_SERVICE_FUNCTION', 'testex-notification-service'),
            api_gateway_function=os.environ.get('API_GATEWAY_FUNCTION', 'testex-api-gateway')
        )


@dataclass
class SecurityConfig:
    """Security configuration"""
    allowed_origins: List[str]
    allowed_file_types: List[str]
    max_file_size: int  # in bytes
    encryption_key_id: Optional[str]
    
    @classmethod
    def from_env(cls) -> 'SecurityConfig':
        allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
        allowed_file_types = os.environ.get(
            'ALLOWED_FILE_TYPES', 
            '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.zip'
        ).split(',')
        
        return cls(
            allowed_origins=[origin.strip() for origin in allowed_origins],
            allowed_file_types=[ext.strip() for ext in allowed_file_types],
            max_file_size=int(os.environ.get('MAX_FILE_SIZE', str(10 * 1024 * 1024))),  # 10MB default
            encryption_key_id=os.environ.get('ENCRYPTION_KEY_ID')
        )


@dataclass
class LoggingConfig:
    """Logging configuration"""
    log_level: str
    log_format: str
    enable_cloudwatch: bool
    log_retention_days: int
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        return cls(
            log_level=os.environ.get('LOG_LEVEL', 'INFO'),
            log_format=os.environ.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            enable_cloudwatch=os.environ.get('ENABLE_CLOUDWATCH', 'true').lower() == 'true',
            log_retention_days=int(os.environ.get('LOG_RETENTION_DAYS', '30'))
        )


@dataclass
class ProcessingConfig:
    """Contract processing configuration"""
    processing_timeout: int  # seconds
    retry_attempts: int
    retry_delay: float  # seconds
    batch_size: int
    
    @classmethod
    def from_env(cls) -> 'ProcessingConfig':
        return cls(
            processing_timeout=int(os.environ.get('PROCESSING_TIMEOUT', '300')),  # 5 minutes
            retry_attempts=int(os.environ.get('RETRY_ATTEMPTS', '3')),
            retry_delay=float(os.environ.get('RETRY_DELAY', '1.0')),
            batch_size=int(os.environ.get('BATCH_SIZE', '10'))
        )


class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.database = DatabaseConfig.from_env()
        self.storage = StorageConfig.from_env()
        self.notification = NotificationConfig.from_env()
        self.lambda_functions = LambdaConfig.from_env()
        self.security = SecurityConfig.from_env()
        self.logging = LoggingConfig.from_env()
        self.processing = ProcessingConfig.from_env()
        
        # Environment-specific settings
        self.environment = os.environ.get('ENVIRONMENT', 'development')
        self.debug = os.environ.get('DEBUG', 'false').lower() == 'true'
        self.aws_region = os.environ.get('AWS_REGION', 'us-east-1')
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == 'production'
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == 'development'
    
    def get_table_name(self, table_type: str) -> str:
        """Get table name with environment prefix"""
        table_mapping = {
            'contracts': self.database.contracts_table,
            'clients': self.database.clients_table,
            'audit_logs': self.database.audit_logs_table
        }
        
        table_name = table_mapping.get(table_type)
        if not table_name:
            raise ValueError(f"Unknown table type: {table_type}")
        
        # Add environment prefix if not in production
        if not self.is_production():
            return f"{self.environment}-{table_name}"
        
        return table_name
    
    def get_bucket_name(self, bucket_type: str) -> str:
        """Get bucket name with environment prefix"""
        bucket_mapping = {
            'files': self.storage.files_bucket,
            'archives': self.storage.archives_bucket,
            'backups': self.storage.backups_bucket,
            'templates': self.storage.templates_bucket
        }
        
        bucket_name = bucket_mapping.get(bucket_type)
        if not bucket_name:
            raise ValueError(f"Unknown bucket type: {bucket_type}")
        
        # Add environment prefix if not in production
        if not self.is_production():
            return f"{self.environment}-{bucket_name}"
        
        return bucket_name
    
    def get_function_name(self, function_type: str) -> str:
        """Get Lambda function name with environment prefix"""
        function_mapping = {
            'contract_processor': self.lambda_functions.contract_processor_function,
            'database_manager': self.lambda_functions.database_manager_function,
            'file_handler': self.lambda_functions.file_handler_function,
            'notification_service': self.lambda_functions.notification_service_function,
            'api_gateway': self.lambda_functions.api_gateway_function
        }
        
        function_name = function_mapping.get(function_type)
        if not function_name:
            raise ValueError(f"Unknown function type: {function_type}")
        
        # Add environment prefix if not in production
        if not self.is_production():
            return f"{self.environment}-{function_name}"
        
        return function_name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'environment': self.environment,
            'debug': self.debug,
            'aws_region': self.aws_region,
            'database': {
                'contracts_table': self.get_table_name('contracts'),
                'clients_table': self.get_table_name('clients'),
                'audit_logs_table': self.get_table_name('audit_logs'),
                'region': self.database.region
            },
            'storage': {
                'files_bucket': self.get_bucket_name('files'),
                'archives_bucket': self.get_bucket_name('archives'),
                'backups_bucket': self.get_bucket_name('backups'),
                'templates_bucket': self.get_bucket_name('templates'),
                'region': self.storage.region
            },
            'notification': {
                'sender_email': self.notification.sender_email,
                'sender_name': self.notification.sender_name,
                'ses_region': self.notification.ses_region,
                'template_bucket': self.get_bucket_name('templates')
            },
            'lambda_functions': {
                'contract_processor': self.get_function_name('contract_processor'),
                'database_manager': self.get_function_name('database_manager'),
                'file_handler': self.get_function_name('file_handler'),
                'notification_service': self.get_function_name('notification_service'),
                'api_gateway': self.get_function_name('api_gateway')
            },
            'security': {
                'allowed_origins': self.security.allowed_origins,
                'allowed_file_types': self.security.allowed_file_types,
                'max_file_size': self.security.max_file_size,
                'encryption_key_id': self.security.encryption_key_id
            },
            'logging': {
                'log_level': self.logging.log_level,
                'log_format': self.logging.log_format,
                'enable_cloudwatch': self.logging.enable_cloudwatch,
                'log_retention_days': self.logging.log_retention_days
            },
            'processing': {
                'processing_timeout': self.processing.processing_timeout,
                'retry_attempts': self.processing.retry_attempts,
                'retry_delay': self.processing.retry_delay,
                'batch_size': self.processing.batch_size
            }
        }


# Global configuration instance
config = Config()


# Environment-specific configurations
DEVELOPMENT_CONFIG = {
    'ENVIRONMENT': 'development',
    'DEBUG': 'true',
    'LOG_LEVEL': 'DEBUG',
    'CONTRACTS_TABLE': 'dev-testex-contracts',
    'CLIENTS_TABLE': 'dev-testex-clients',
    'AUDIT_LOGS_TABLE': 'dev-testex-audit-logs',
    'FILES_BUCKET': 'dev-testex-files',
    'ARCHIVES_BUCKET': 'dev-testex-archives',
    'BACKUPS_BUCKET': 'dev-testex-backups',
    'TEMPLATES_BUCKET': 'dev-testex-templates'
}

STAGING_CONFIG = {
    'ENVIRONMENT': 'staging',
    'DEBUG': 'false',
    'LOG_LEVEL': 'INFO',
    'CONTRACTS_TABLE': 'staging-testex-contracts',
    'CLIENTS_TABLE': 'staging-testex-clients',
    'AUDIT_LOGS_TABLE': 'staging-testex-audit-logs',
    'FILES_BUCKET': 'staging-testex-files',
    'ARCHIVES_BUCKET': 'staging-testex-archives',
    'BACKUPS_BUCKET': 'staging-testex-backups',
    'TEMPLATES_BUCKET': 'staging-testex-templates'
}

PRODUCTION_CONFIG = {
    'ENVIRONMENT': 'production',
    'DEBUG': 'false',
    'LOG_LEVEL': 'WARN',
    'CONTRACTS_TABLE': 'testex-contracts',
    'CLIENTS_TABLE': 'testex-clients',
    'AUDIT_LOGS_TABLE': 'testex-audit-logs',
    'FILES_BUCKET': 'testex-files',
    'ARCHIVES_BUCKET': 'testex-archives',
    'BACKUPS_BUCKET': 'testex-backups',
    'TEMPLATES_BUCKET': 'testex-templates'
}


def get_config_for_environment(environment: str) -> Dict[str, str]:
    """Get configuration for specific environment"""
    configs = {
        'development': DEVELOPMENT_CONFIG,
        'staging': STAGING_CONFIG,
        'production': PRODUCTION_CONFIG
    }
    
    return configs.get(environment.lower(), DEVELOPMENT_CONFIG)


def validate_configuration() -> List[str]:
    """Validate current configuration and return list of errors"""
    errors = []
    
    # Check required environment variables
    required_vars = [
        'AWS_REGION',
        'CONTRACTS_TABLE',
        'CLIENTS_TABLE',
        'AUDIT_LOGS_TABLE',
        'FILES_BUCKET',
        'ARCHIVES_BUCKET',
        'BACKUPS_BUCKET',
        'TEMPLATES_BUCKET',
        'SENDER_EMAIL'
    ]
    
    for var in required_vars:
        if not os.environ.get(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Validate email format
    sender_email = os.environ.get('SENDER_EMAIL', '')
    if sender_email and '@' not in sender_email:
        errors.append("Invalid SENDER_EMAIL format")
    
    # Validate numeric values
    try:
        int(os.environ.get('MAX_FILE_SIZE', '10485760'))
    except ValueError:
        errors.append("MAX_FILE_SIZE must be a valid integer")
    
    try:
        int(os.environ.get('PROCESSING_TIMEOUT', '300'))
    except ValueError:
        errors.append("PROCESSING_TIMEOUT must be a valid integer")
    
    try:
        int(os.environ.get('RETRY_ATTEMPTS', '3'))
    except ValueError:
        errors.append("RETRY_ATTEMPTS must be a valid integer")
    
    try:
        float(os.environ.get('RETRY_DELAY', '1.0'))
    except ValueError:
        errors.append("RETRY_DELAY must be a valid float")
    
    return errors
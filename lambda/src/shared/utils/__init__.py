"""
Shared utility functions for the TESTEX system
"""
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError


# Logger setup
def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Set up logger with consistent formatting"""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


# Date/time utilities
def get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO format"""
    return datetime.utcnow().isoformat()


def get_current_timestamp_with_tz() -> str:
    """Get current timestamp with timezone"""
    return datetime.now(timezone.utc).isoformat()


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp string to datetime object"""
    try:
        # Handle different timestamp formats
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        return datetime.fromisoformat(timestamp_str)
    except ValueError as e:
        raise ValueError(f"Invalid timestamp format: {timestamp_str}") from e


def format_date(date_obj: datetime, format_str: str = "%Y-%m-%d") -> str:
    """Format datetime object to string"""
    return date_obj.strftime(format_str)


def format_datetime(date_obj: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime object to string"""
    return date_obj.strftime(format_str)


# Validation utilities
def validate_contract_id(contract_id: str) -> bool:
    """Validate contract ID format"""
    pattern = r'^CT[A-Z0-9]{3,20}$'
    return bool(re.match(pattern, contract_id.upper()))


def validate_client_id(client_id: str) -> bool:
    """Validate client ID format"""
    pattern = r'^CL[A-Z0-9]{3,20}$'
    return bool(re.match(pattern, client_id.upper()))


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def normalize_contract_id(contract_id: str) -> str:
    """Normalize contract ID to uppercase"""
    if not contract_id.startswith('CT'):
        raise ValueError("Contract ID must start with 'CT'")
    return contract_id.upper()


def normalize_client_id(client_id: str) -> str:
    """Normalize client ID to uppercase"""
    if not client_id.startswith('CL'):
        raise ValueError("Client ID must start with 'CL'")
    return client_id.upper()


# Data conversion utilities
def convert_floats_to_decimal(obj: Any) -> Any:
    """Convert float values to Decimal for DynamoDB compatibility"""
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj


def convert_decimal_to_float(obj: Any) -> Any:
    """Convert Decimal values to float for JSON serialization"""
    if isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


def sanitize_json(obj: Any) -> Any:
    """Sanitize object for JSON serialization"""
    if isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_json(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    else:
        return str(obj)


# Response utilities
def create_success_response(data: Any = None, message: str = None) -> Dict[str, Any]:
    """Create standardized success response"""
    response = {
        'status': 'success',
        'timestamp': get_current_timestamp()
    }
    
    if data is not None:
        response['data'] = sanitize_json(data)
    
    if message:
        response['message'] = message
    
    return response


def create_error_response(error: str, message: str = None, details: Any = None) -> Dict[str, Any]:
    """Create standardized error response"""
    response = {
        'status': 'error',
        'error': error,
        'timestamp': get_current_timestamp()
    }
    
    if message:
        response['message'] = message
    
    if details:
        response['details'] = sanitize_json(details)
    
    return response


def create_lambda_response(status_code: int, body: Dict[str, Any], headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Create standardized Lambda response"""
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body, default=str)
    }


# AWS utilities
def get_aws_client(service_name: str, region: str = None):
    """Get AWS service client"""
    if region is None:
        region = os.environ.get('AWS_REGION', 'us-east-1')
    
    return boto3.client(service_name, region_name=region)


def get_aws_resource(service_name: str, region: str = None):
    """Get AWS service resource"""
    if region is None:
        region = os.environ.get('AWS_REGION', 'us-east-1')
    
    return boto3.resource(service_name, region_name=region)


def invoke_lambda_function(function_name: str, payload: Dict[str, Any], invocation_type: str = 'RequestResponse') -> Dict[str, Any]:
    """Invoke Lambda function"""
    lambda_client = get_aws_client('lambda')
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType=invocation_type,
            Payload=json.dumps(payload, default=str)
        )
        
        if invocation_type == 'RequestResponse':
            result = json.loads(response['Payload'].read())
            return result
        else:
            return {'status': 'invoked', 'status_code': response['StatusCode']}
            
    except ClientError as e:
        raise Exception(f"Failed to invoke Lambda function {function_name}: {str(e)}")


# File utilities
def get_file_extension(filename: str) -> str:
    """Get file extension"""
    return os.path.splitext(filename)[1].lower()


def is_allowed_file_type(filename: str, allowed_extensions: List[str] = None) -> bool:
    """Check if file type is allowed"""
    if allowed_extensions is None:
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.zip']
    
    extension = get_file_extension(filename)
    return extension in allowed_extensions


def generate_s3_key(contract_id: str, filename: str, prefix: str = 'contracts') -> str:
    """Generate S3 key for file storage"""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
    return f"{prefix}/{contract_id}/files/{timestamp}_{safe_filename}"


def generate_backup_s3_key(contract_id: str, filename: str, prefix: str = 'backups') -> str:
    """Generate S3 key for backup storage"""
    date_str = datetime.utcnow().strftime('%Y%m%d')
    timestamp = datetime.utcnow().strftime('%H%M%S')
    safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
    return f"{prefix}/{contract_id}/{date_str}/{timestamp}_{safe_filename}"


# String utilities
def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def clean_string(text: str) -> str:
    """Clean string for safe processing"""
    if not text:
        return ""
    
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def mask_sensitive_data(text: str, pattern: str = r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b') -> str:
    """Mask sensitive data in strings"""
    return re.sub(pattern, '****-****-****-****', text)


# Encryption utilities (for sensitive data)
def hash_string(text: str) -> str:
    """Create hash of string for comparison"""
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()


# Environment utilities
def get_env_var(name: str, default: str = None, required: bool = False) -> str:
    """Get environment variable with validation"""
    value = os.environ.get(name, default)
    
    if required and not value:
        raise ValueError(f"Required environment variable {name} is not set")
    
    return value


def get_env_bool(name: str, default: bool = False) -> bool:
    """Get boolean environment variable"""
    value = os.environ.get(name, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')


def get_env_int(name: str, default: int = 0) -> int:
    """Get integer environment variable"""
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def get_env_list(name: str, default: List[str] = None, separator: str = ',') -> List[str]:
    """Get list environment variable"""
    if default is None:
        default = []
    
    value = os.environ.get(name)
    if not value:
        return default
    
    return [item.strip() for item in value.split(separator) if item.strip()]


# Pagination utilities
def paginate_results(items: List[Any], page: int = 1, page_size: int = 50) -> Dict[str, Any]:
    """Paginate list of items"""
    total_items = len(items)
    total_pages = (total_items + page_size - 1) // page_size
    
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    
    paginated_items = items[start_index:end_index]
    
    return {
        'items': paginated_items,
        'pagination': {
            'current_page': page,
            'page_size': page_size,
            'total_items': total_items,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1
        }
    }


# Retry utilities
def retry_operation(operation, max_retries: int = 3, delay: float = 1.0):
    """Retry operation with exponential backoff"""
    import time
    
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            time.sleep(delay * (2 ** attempt))
    
    return None


# Cache utilities
class SimpleCache:
    """Simple in-memory cache"""
    
    def __init__(self, ttl: int = 300):  # 5 minutes default TTL
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Any:
        """Get item from cache"""
        if key in self.cache:
            item, timestamp = self.cache[key]
            if datetime.utcnow().timestamp() - timestamp < self.ttl:
                return item
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Set item in cache"""
        self.cache[key] = (value, datetime.utcnow().timestamp())
    
    def delete(self, key: str):
        """Delete item from cache"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()


# Global cache instance
cache = SimpleCache()


# Metrics utilities
def track_execution_time(func):
    """Decorator to track function execution time"""
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger = setup_logger(func.__module__)
            logger.info(f"{func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger = setup_logger(func.__module__)
            logger.error(f"{func.__name__} failed after {execution_time:.2f} seconds: {str(e)}")
            raise
    
    return wrapper
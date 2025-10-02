"""
Test configuration and fixtures for TESTEX Lambda functions
"""
import pytest
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List
from decimal import Decimal
from unittest.mock import MagicMock, patch
import boto3
from moto import mock_dynamodb, mock_s3, mock_ses, mock_lambda

# Test data fixtures
@pytest.fixture
def sample_contract_data():
    """Sample contract data for testing"""
    return {
        'contract_id': 'CT001ABC',
        'client_id': 'CL001XYZ',
        'contract_type': 'SERVICE',
        'start_date': '2023-01-01',
        'end_date': '2024-01-01',
        'value': Decimal('10000.00'),
        'status': 'ACTIVE',
        'termination_reason': 'MUTUAL_AGREEMENT',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_client_data():
    """Sample client data for testing"""
    return {
        'client_id': 'CL001XYZ',
        'name': 'Test Client Corp',
        'email': 'contact@testclient.com',
        'phone': '+1-555-0123',
        'address': '123 Test Street, Test City, TC 12345',
        'status': 'ACTIVE',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def sample_lambda_event():
    """Sample Lambda event for testing"""
    return {
        'requestContext': {
            'requestId': 'test-request-id',
            'functionName': 'test-function',
            'requestTimeEpoch': 1640995200000
        },
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'action': 'test_action',
            'contract_id': 'CT001ABC'
        }),
        'httpMethod': 'POST',
        'path': '/api/contracts',
        'pathParameters': None,
        'queryStringParameters': None
    }


@pytest.fixture
def sample_api_gateway_event():
    """Sample API Gateway event for testing"""
    return {
        'httpMethod': 'POST',
        'path': '/api/contracts',
        'pathParameters': {'contract_id': 'CT001ABC'},
        'queryStringParameters': {'include_files': 'true'},
        'headers': {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer test-token'
        },
        'body': json.dumps({
            'contract_id': 'CT001ABC',
            'client_id': 'CL001XYZ',
            'action': 'terminate'
        }),
        'requestContext': {
            'requestId': 'test-api-request',
            'httpMethod': 'POST',
            'path': '/api/contracts',
            'stage': 'test',
            'requestTimeEpoch': 1640995200000,
            'identity': {
                'sourceIp': '127.0.0.1'
            }
        }
    }


@pytest.fixture
def sample_s3_event():
    """Sample S3 event for testing"""
    return {
        'Records': [{
            'eventVersion': '2.1',
            'eventSource': 'aws:s3',
            'eventName': 'ObjectCreated:Put',
            's3': {
                'bucket': {
                    'name': 'test-files-bucket'
                },
                'object': {
                    'key': 'contracts/CT001ABC/files/test-document.pdf',
                    'size': 1024
                }
            }
        }]
    }


@pytest.fixture
def sample_file_data():
    """Sample file data for testing"""
    return {
        'file_id': 'file-123',
        'contract_id': 'CT001ABC',
        'filename': 'test-document.pdf',
        'file_type': 'application/pdf',
        'file_size': 1024,
        'upload_date': datetime.now(timezone.utc).isoformat(),
        's3_key': 'contracts/CT001ABC/files/test-document.pdf',
        'status': 'UPLOADED'
    }


@pytest.fixture
def sample_notification_data():
    """Sample notification data for testing"""
    return {
        'notification_id': 'notif-123',
        'contract_id': 'CT001ABC',
        'recipient_email': 'test@example.com',
        'notification_type': 'CONTRACT_TERMINATION',
        'subject': 'Contract Termination Notice',
        'template': 'termination_notice',
        'status': 'PENDING',
        'created_at': datetime.now(timezone.utc).isoformat()
    }


# AWS Mock fixtures
@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for testing"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'


@pytest.fixture
def mock_dynamodb_table(aws_credentials):
    """Mock DynamoDB table for testing"""
    with mock_dynamodb():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create contracts table
        contracts_table = dynamodb.create_table(
            TableName='testex-contracts',
            KeySchema=[
                {'AttributeName': 'contract_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'contract_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create clients table
        clients_table = dynamodb.create_table(
            TableName='testex-clients',
            KeySchema=[
                {'AttributeName': 'client_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'client_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create audit logs table
        audit_table = dynamodb.create_table(
            TableName='testex-audit-logs',
            KeySchema=[
                {'AttributeName': 'log_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'log_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        yield {
            'contracts': contracts_table,
            'clients': clients_table,
            'audit_logs': audit_table
        }


@pytest.fixture
def mock_s3_bucket(aws_credentials):
    """Mock S3 bucket for testing"""
    with mock_s3():
        s3 = boto3.resource('s3', region_name='us-east-1')
        
        # Create test buckets
        files_bucket = s3.create_bucket(Bucket='testex-files')
        archives_bucket = s3.create_bucket(Bucket='testex-archives')
        backups_bucket = s3.create_bucket(Bucket='testex-backups')
        templates_bucket = s3.create_bucket(Bucket='testex-templates')
        
        yield {
            'files': files_bucket,
            'archives': archives_bucket,
            'backups': backups_bucket,
            'templates': templates_bucket
        }


@pytest.fixture
def mock_ses_service(aws_credentials):
    """Mock SES service for testing"""
    with mock_ses():
        ses = boto3.client('ses', region_name='us-east-1')
        
        # Verify email addresses for testing
        ses.verify_email_identity(EmailAddress='test@example.com')
        ses.verify_email_identity(EmailAddress='noreply@testex.com')
        
        yield ses


@pytest.fixture
def mock_lambda_service(aws_credentials):
    """Mock Lambda service for testing"""
    with mock_lambda():
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        # Create mock Lambda functions
        functions = [
            'testex-contract-processor',
            'testex-database-manager',
            'testex-file-handler',
            'testex-notification-service',
            'testex-api-gateway'
        ]
        
        for function_name in functions:
            lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.11',
                Role='arn:aws:iam::123456789012:role/test-role',
                Handler='handler.lambda_handler',
                Code={'ZipFile': b'fake code'},
                Description=f'Test function {function_name}'
            )
        
        yield lambda_client


# Environment fixtures
@pytest.fixture
def test_environment():
    """Set up test environment variables"""
    test_env = {
        'ENVIRONMENT': 'test',
        'AWS_REGION': 'us-east-1',
        'CONTRACTS_TABLE': 'testex-contracts',
        'CLIENTS_TABLE': 'testex-clients',
        'AUDIT_LOGS_TABLE': 'testex-audit-logs',
        'FILES_BUCKET': 'testex-files',
        'ARCHIVES_BUCKET': 'testex-archives',
        'BACKUPS_BUCKET': 'testex-backups',
        'TEMPLATES_BUCKET': 'testex-templates',
        'SENDER_EMAIL': 'noreply@testex.com',
        'SENDER_NAME': 'TESTEX System',
        'LOG_LEVEL': 'DEBUG',
        'MAX_FILE_SIZE': '10485760',
        'CONTRACT_PROCESSOR_FUNCTION': 'testex-contract-processor',
        'DATABASE_MANAGER_FUNCTION': 'testex-database-manager',
        'FILE_HANDLER_FUNCTION': 'testex-file-handler',
        'NOTIFICATION_SERVICE_FUNCTION': 'testex-notification-service',
        'API_GATEWAY_FUNCTION': 'testex-api-gateway'
    }
    
    # Store original environment
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield test_env
    
    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


# Utility functions for testing
def create_lambda_context():
    """Create a mock Lambda context object"""
    context = MagicMock()
    context.function_name = 'test-function'
    context.function_version = '$LATEST'
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test-function'
    context.memory_limit_in_mb = 128
    context.remaining_time_in_millis.return_value = 30000
    context.aws_request_id = 'test-request-id'
    context.log_group_name = '/aws/lambda/test-function'
    context.log_stream_name = '2023/01/01/[$LATEST]test-stream'
    return context


def assert_lambda_response(response: Dict[str, Any], expected_status_code: int = 200):
    """Assert Lambda response format and status code"""
    assert 'statusCode' in response
    assert 'headers' in response
    assert 'body' in response
    assert response['statusCode'] == expected_status_code
    assert response['headers']['Content-Type'] == 'application/json'
    
    # Parse body if it's a string
    if isinstance(response['body'], str):
        body = json.loads(response['body'])
    else:
        body = response['body']
    
    assert 'status' in body
    assert 'timestamp' in body
    
    return body


def assert_success_response(response: Dict[str, Any], expected_data: Any = None):
    """Assert successful Lambda response"""
    body = assert_lambda_response(response, 200)
    assert body['status'] == 'success'
    
    if expected_data is not None:
        assert 'data' in body
        assert body['data'] == expected_data
    
    return body


def assert_error_response(response: Dict[str, Any], expected_status_code: int = 400, expected_error: str = None):
    """Assert error Lambda response"""
    body = assert_lambda_response(response, expected_status_code)
    assert body['status'] == 'error'
    assert 'error' in body
    
    if expected_error:
        assert body['error'] == expected_error
    
    return body


def create_test_file_content(file_type: str = 'pdf') -> bytes:
    """Create test file content"""
    if file_type == 'pdf':
        return b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n'
    elif file_type == 'txt':
        return b'This is a test text file content.'
    elif file_type == 'json':
        return json.dumps({'test': 'data', 'timestamp': datetime.now().isoformat()}).encode()
    else:
        return b'Test file content'


# Test database utilities
def populate_test_data(tables: Dict[str, Any], sample_contract_data: Dict, sample_client_data: Dict):
    """Populate test data in mock DynamoDB tables"""
    # Add contract data
    contracts_table = tables['contracts']
    contracts_table.put_item(Item=sample_contract_data)
    
    # Add client data
    clients_table = tables['clients']
    clients_table.put_item(Item=sample_client_data)
    
    # Add audit log
    audit_table = tables['audit_logs']
    audit_table.put_item(Item={
        'log_id': 'log-123',
        'contract_id': sample_contract_data['contract_id'],
        'action': 'CONTRACT_CREATED',
        'details': json.dumps({'created_by': 'test_user'}),
        'timestamp': datetime.now(timezone.utc).isoformat()
    })


def upload_test_files(buckets: Dict[str, Any]):
    """Upload test files to mock S3 buckets"""
    files_bucket = buckets['files']
    templates_bucket = buckets['templates']
    
    # Upload test contract file
    files_bucket.put_object(
        Key='contracts/CT001ABC/files/test-document.pdf',
        Body=create_test_file_content('pdf'),
        ContentType='application/pdf'
    )
    
    # Upload email templates
    templates_bucket.put_object(
        Key='email-templates/termination_notice.html',
        Body='<html><body>Contract {{contract_id}} has been terminated.</body></html>',
        ContentType='text/html'
    )
    
    templates_bucket.put_object(
        Key='email-templates/status_update.html',
        Body='<html><body>Status update for contract {{contract_id}}: {{status}}</body></html>',
        ContentType='text/html'
    )
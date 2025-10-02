"""
API Gateway Lambda
Provides REST API endpoints for the TESTEX system
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
lambda_client = boto3.client('lambda')

# Environment variables
CONTRACT_PROCESSOR_FUNCTION = os.environ.get('CONTRACT_PROCESSOR_FUNCTION', 'testex-contract-processor')
DATABASE_FUNCTION = os.environ.get('DATABASE_FUNCTION', 'testex-database-manager')
FILE_HANDLER_FUNCTION = os.environ.get('FILE_HANDLER_FUNCTION', 'testex-file-handler')
NOTIFICATION_FUNCTION = os.environ.get('NOTIFICATION_FUNCTION', 'testex-notification-service')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for API Gateway
    
    Args:
        event: API Gateway event
        context: Lambda context object
        
    Returns:
        API Gateway response
    """
    try:
        logger.info(f"API request: {json.dumps(event, default=str)}")
        
        # Extract request details
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        headers = event.get('headers', {})
        query_params = event.get('queryStringParameters') or {}
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        
        # Add request metadata
        request_context = event.get('requestContext', {})
        client_ip = request_context.get('identity', {}).get('sourceIp', 'unknown')
        user_agent = headers.get('User-Agent', 'unknown')
        
        # Route request
        if path.startswith('/contracts'):
            return handle_contracts_api(http_method, path, query_params, body, client_ip, user_agent)
        elif path.startswith('/files'):
            return handle_files_api(http_method, path, query_params, body, client_ip, user_agent)
        elif path.startswith('/notifications'):
            return handle_notifications_api(http_method, path, query_params, body, client_ip, user_agent)
        elif path == '/health':
            return handle_health_check()
        else:
            return create_api_response(404, {
                'error': 'Not Found',
                'message': f'Path {path} not found'
            })
        
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return create_api_response(500, {
            'error': 'Internal Server Error',
            'message': str(e)
        })


def handle_contracts_api(method: str, path: str, query_params: Dict, body: Dict, client_ip: str, user_agent: str) -> Dict[str, Any]:
    """Handle /contracts API endpoints"""
    
    # Extract contract ID from path if present
    path_parts = path.strip('/').split('/')
    contract_id = path_parts[1] if len(path_parts) > 1 else None
    
    try:
        if method == 'POST' and path == '/contracts/terminate':
            # Terminate contract
            return terminate_contract(body, client_ip, user_agent)
            
        elif method == 'GET' and contract_id:
            if path.endswith('/status'):
                # Get contract status
                return get_contract_status(contract_id)
            elif path.endswith('/files'):
                # Get contract files
                return get_contract_files(contract_id, query_params)
            elif path.endswith('/history'):
                # Get contract history
                return get_contract_history(contract_id, query_params)
            else:
                # Get contract details
                return get_contract_details(contract_id)
                
        elif method == 'PUT' and contract_id:
            # Update contract
            return update_contract_details(contract_id, body, client_ip, user_agent)
            
        elif method == 'DELETE' and contract_id:
            # Delete contract
            return delete_contract_details(contract_id, client_ip, user_agent)
            
        elif method == 'GET' and path == '/contracts':
            # List contracts
            return list_contracts(query_params)
            
        elif method == 'POST' and path == '/contracts':
            # Create contract
            return create_contract(body, client_ip, user_agent)
            
        else:
            return create_api_response(405, {
                'error': 'Method Not Allowed',
                'message': f'Method {method} not allowed for {path}'
            })
            
    except Exception as e:
        logger.error(f"Contracts API error: {str(e)}")
        return create_api_response(500, {
            'error': 'Contract operation failed',
            'message': str(e)
        })


def handle_files_api(method: str, path: str, query_params: Dict, body: Dict, client_ip: str, user_agent: str) -> Dict[str, Any]:
    """Handle /files API endpoints"""
    
    path_parts = path.strip('/').split('/')
    contract_id = query_params.get('contract_id')
    
    try:
        if method == 'POST' and path == '/files/upload':
            # Upload files
            if not contract_id:
                return create_api_response(400, {
                    'error': 'Bad Request',
                    'message': 'contract_id parameter is required'
                })
            return upload_files(contract_id, body)
            
        elif method == 'GET' and path == '/files/download':
            # Download file
            file_key = query_params.get('file_key')
            file_name = query_params.get('file_name')
            
            if not contract_id or (not file_key and not file_name):
                return create_api_response(400, {
                    'error': 'Bad Request',
                    'message': 'contract_id and (file_key or file_name) parameters are required'
                })
            return download_file(contract_id, file_key, file_name)
            
        elif method == 'POST' and path == '/files/archive':
            # Archive files
            if not contract_id:
                return create_api_response(400, {
                    'error': 'Bad Request',
                    'message': 'contract_id parameter is required'
                })
            return archive_files(contract_id, body)
            
        elif method == 'GET' and path == '/files/list':
            # List files
            if not contract_id:
                return create_api_response(400, {
                    'error': 'Bad Request',
                    'message': 'contract_id parameter is required'
                })
            return list_files(contract_id, query_params)
            
        elif method == 'DELETE' and path == '/files/delete':
            # Delete files
            if not contract_id:
                return create_api_response(400, {
                    'error': 'Bad Request',
                    'message': 'contract_id parameter is required'
                })
            return delete_files(contract_id, body)
            
        else:
            return create_api_response(405, {
                'error': 'Method Not Allowed',
                'message': f'Method {method} not allowed for {path}'
            })
            
    except Exception as e:
        logger.error(f"Files API error: {str(e)}")
        return create_api_response(500, {
            'error': 'File operation failed',
            'message': str(e)
        })


def handle_notifications_api(method: str, path: str, query_params: Dict, body: Dict, client_ip: str, user_agent: str) -> Dict[str, Any]:
    """Handle /notifications API endpoints"""
    
    try:
        if method == 'POST' and path == '/notifications/send':
            # Send notification
            return send_notification(body)
            
        elif method == 'POST' and path == '/notifications/test':
            # Send test notification
            return send_test_notification(body)
            
        else:
            return create_api_response(405, {
                'error': 'Method Not Allowed',
                'message': f'Method {method} not allowed for {path}'
            })
            
    except Exception as e:
        logger.error(f"Notifications API error: {str(e)}")
        return create_api_response(500, {
            'error': 'Notification operation failed',
            'message': str(e)
        })


def handle_health_check() -> Dict[str, Any]:
    """Handle health check endpoint"""
    return create_api_response(200, {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'TESTEX API Gateway',
        'version': '1.0.0'
    })


# Contract operations
def terminate_contract(body: Dict, client_ip: str, user_agent: str) -> Dict[str, Any]:
    """Initiate contract termination"""
    
    # Add audit information
    body['initiated_from_ip'] = client_ip
    body['user_agent'] = user_agent
    body['initiated_at'] = datetime.utcnow().isoformat()
    
    response = lambda_client.invoke(
        FunctionName=CONTRACT_PROCESSOR_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(body)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        return create_api_response(202, json.loads(result['body']))
    else:
        return result


def get_contract_status(contract_id: str) -> Dict[str, Any]:
    """Get contract status"""
    
    payload = {
        'operation': 'get_contract',
        'data': {'contract_id': contract_id}
    }
    
    response = lambda_client.invoke(
        FunctionName=DATABASE_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        contract_data = json.loads(result['body'])['result']
        if contract_data:
            return create_api_response(200, {
                'contract_id': contract_id,
                'status': contract_data.get('status'),
                'last_updated': contract_data.get('updated_at'),
                'processing_details': contract_data.get('processing_details')
            })
        else:
            return create_api_response(404, {
                'error': 'Contract not found',
                'contract_id': contract_id
            })
    else:
        return result


def get_contract_details(contract_id: str) -> Dict[str, Any]:
    """Get full contract details"""
    
    payload = {
        'operation': 'get_contract',
        'data': {'contract_id': contract_id}
    }
    
    response = lambda_client.invoke(
        FunctionName=DATABASE_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        contract_data = json.loads(result['body'])['result']
        if contract_data:
            return create_api_response(200, contract_data)
        else:
            return create_api_response(404, {
                'error': 'Contract not found',
                'contract_id': contract_id
            })
    else:
        return result


def get_contract_files(contract_id: str, query_params: Dict) -> Dict[str, Any]:
    """Get contract files"""
    
    payload = {
        'action': 'list',
        'contract_id': contract_id,
        'include_deleted': query_params.get('include_deleted', 'false').lower() == 'true'
    }
    
    response = lambda_client.invoke(
        FunctionName=FILE_HANDLER_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        return create_api_response(200, json.loads(result['body'])['result'])
    else:
        return result


def get_contract_history(contract_id: str, query_params: Dict) -> Dict[str, Any]:
    """Get contract audit history"""
    
    limit = int(query_params.get('limit', 50))
    
    payload = {
        'operation': 'get_audit_logs',
        'data': {
            'contract_id': contract_id,
            'limit': limit
        }
    }
    
    response = lambda_client.invoke(
        FunctionName=DATABASE_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        return create_api_response(200, json.loads(result['body'])['result'])
    else:
        return result


def create_contract(body: Dict, client_ip: str, user_agent: str) -> Dict[str, Any]:
    """Create new contract"""
    
    body['created_from_ip'] = client_ip
    body['user_agent'] = user_agent
    
    payload = {
        'operation': 'create_contract',
        'data': body
    }
    
    response = lambda_client.invoke(
        FunctionName=DATABASE_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        return create_api_response(201, json.loads(result['body'])['result'])
    else:
        return result


def update_contract_details(contract_id: str, body: Dict, client_ip: str, user_agent: str) -> Dict[str, Any]:
    """Update contract"""
    
    body['updated_from_ip'] = client_ip
    body['user_agent'] = user_agent
    
    payload = {
        'operation': 'update_contract',
        'data': {
            'contract_id': contract_id,
            'updates': body
        }
    }
    
    response = lambda_client.invoke(
        FunctionName=DATABASE_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        return create_api_response(200, json.loads(result['body'])['result'])
    else:
        return result


def delete_contract_details(contract_id: str, client_ip: str, user_agent: str) -> Dict[str, Any]:
    """Delete contract (soft delete)"""
    
    payload = {
        'operation': 'delete_contract',
        'data': {
            'contract_id': contract_id,
            'deleted_from_ip': client_ip,
            'user_agent': user_agent
        }
    }
    
    response = lambda_client.invoke(
        FunctionName=DATABASE_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        return create_api_response(200, json.loads(result['body'])['result'])
    else:
        return result


def list_contracts(query_params: Dict) -> Dict[str, Any]:
    """List contracts with filters"""
    
    filters = {}
    if query_params.get('status'):
        filters['status'] = query_params['status']
    if query_params.get('client_id'):
        filters['client_id'] = query_params['client_id']
    if query_params.get('termination_type'):
        filters['termination_type'] = query_params['termination_type']
    if query_params.get('created_after'):
        filters['created_after'] = query_params['created_after']
    if query_params.get('created_before'):
        filters['created_before'] = query_params['created_before']
    
    payload = {
        'operation': 'list_contracts',
        'data': {'filters': filters}
    }
    
    response = lambda_client.invoke(
        FunctionName=DATABASE_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        contracts = json.loads(result['body'])['result']
        return create_api_response(200, {
            'contracts': contracts,
            'count': len(contracts),
            'filters': filters
        })
    else:
        return result


# File operations
def upload_files(contract_id: str, body: Dict) -> Dict[str, Any]:
    """Upload files"""
    
    payload = {
        'action': 'upload',
        'contract_id': contract_id,
        'files': body.get('files', [])
    }
    
    response = lambda_client.invoke(
        FunctionName=FILE_HANDLER_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        return create_api_response(200, json.loads(result['body'])['result'])
    else:
        return result


def download_file(contract_id: str, file_key: str = None, file_name: str = None) -> Dict[str, Any]:
    """Download file"""
    
    payload = {
        'action': 'download',
        'contract_id': contract_id,
        'file_key': file_key,
        'file_name': file_name
    }
    
    response = lambda_client.invoke(
        FunctionName=FILE_HANDLER_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        return create_api_response(200, json.loads(result['body'])['result'])
    else:
        return result


def archive_files(contract_id: str, body: Dict) -> Dict[str, Any]:
    """Archive files"""
    
    payload = {
        'action': 'archive',
        'contract_id': contract_id,
        'files': body.get('files', [])
    }
    
    response = lambda_client.invoke(
        FunctionName=FILE_HANDLER_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        return create_api_response(200, json.loads(result['body'])['result'])
    else:
        return result


def list_files(contract_id: str, query_params: Dict) -> Dict[str, Any]:
    """List files"""
    
    payload = {
        'action': 'list',
        'contract_id': contract_id,
        'include_deleted': query_params.get('include_deleted', 'false').lower() == 'true'
    }
    
    response = lambda_client.invoke(
        FunctionName=FILE_HANDLER_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        return create_api_response(200, json.loads(result['body'])['result'])
    else:
        return result


def delete_files(contract_id: str, body: Dict) -> Dict[str, Any]:
    """Delete files"""
    
    payload = {
        'action': 'delete',
        'contract_id': contract_id,
        'files': body.get('files', []),
        'permanent': body.get('permanent', False)
    }
    
    response = lambda_client.invoke(
        FunctionName=FILE_HANDLER_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        return create_api_response(200, json.loads(result['body'])['result'])
    else:
        return result


# Notification operations
def send_notification(body: Dict) -> Dict[str, Any]:
    """Send notification"""
    
    response = lambda_client.invoke(
        FunctionName=NOTIFICATION_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(body)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        return create_api_response(200, json.loads(result['body']))
    else:
        return result


def send_test_notification(body: Dict) -> Dict[str, Any]:
    """Send test notification"""
    
    test_payload = {
        'type': 'test',
        'recipients': body.get('recipients', []),
        'contract_data': {
            'contract_id': 'TEST001',
            'client_id': 'CL001',
            'message': 'This is a test notification from the TESTEX API'
        }
    }
    
    response = lambda_client.invoke(
        FunctionName=NOTIFICATION_FUNCTION,
        InvocationType='RequestResponse',
        Payload=json.dumps(test_payload)
    )
    
    result = json.loads(response['Payload'].read())
    
    if result.get('statusCode') == 200:
        return create_api_response(200, json.loads(result['body']))
    else:
        return result


def create_api_response(status_code: int, body: Dict[str, Any], headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Create standardized API Gateway response"""
    
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
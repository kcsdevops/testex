"""
API Gateway Lambda Handler
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for API Gateway requests
    """
    try:
        logger.info(f"API Gateway invoked with event: {json.dumps(event, default=str)}")
        
        # Extract request information
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        
        # Route requests based on path and method
        if path.startswith('/api/contracts'):
            return handle_contracts_api(event, context)
        elif path.startswith('/api/files'):
            return handle_files_api(event, context)
        elif path.startswith('/api/notifications'):
            return handle_notifications_api(event, context)
        else:
            return create_error_response(
                status_code=404,
                error='NOT_FOUND',
                message=f'Path {path} not found'
            )
    
    except Exception as e:
        logger.error(f"Error in API Gateway handler: {str(e)}")
        return create_error_response(
            status_code=500,
            error='INTERNAL_SERVER_ERROR',
            message='An unexpected error occurred'
        )


def handle_contracts_api(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle contracts API endpoints"""
    try:
        http_method = event.get('httpMethod')
        path = event.get('path')
        path_parameters = event.get('pathParameters') or {}
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        
        contract_id = path_parameters.get('contract_id')
        
        if http_method == 'GET':
            if contract_id:
                # GET /api/contracts/{contract_id}
                result = {
                    'contract_id': contract_id,
                    'client_id': 'CL001XYZ',
                    'status': 'ACTIVE',
                    'contract_type': 'SERVICE',
                    'value': 10000.00,
                    'created_at': datetime.utcnow().isoformat()
                }
                return create_success_response(
                    data=result,
                    message='Contract retrieved successfully'
                )
            else:
                # GET /api/contracts (list contracts)
                contracts = []
                for i in range(5):
                    contracts.append({
                        'contract_id': f'CT{i+1:03d}ABC',
                        'client_id': f'CL{i+1:03d}XYZ',
                        'status': 'ACTIVE' if i % 2 == 0 else 'TERMINATED',
                        'contract_type': 'SERVICE'
                    })
                
                result = {
                    'contracts': contracts,
                    'total': len(contracts)
                }
                return create_success_response(
                    data=result,
                    message='Contracts retrieved successfully'
                )
        
        elif http_method == 'POST':
            # POST /api/contracts (create contract)
            contract_data = body.get('contract_data', body)
            new_contract_id = contract_data.get('contract_id', f'CT{datetime.utcnow().strftime("%Y%m%d%H%M%S")}')
            
            result = {
                'contract_id': new_contract_id,
                'status': 'CREATED',
                'created_at': datetime.utcnow().isoformat()
            }
            return create_success_response(
                data=result,
                message='Contract created successfully',
                status_code=201
            )
        
        elif http_method == 'PUT' and contract_id:
            # PUT /api/contracts/{contract_id} (update contract)
            updates = body.get('updates', body)
            
            result = {
                'contract_id': contract_id,
                'updated_fields': list(updates.keys()),
                'updated_at': datetime.utcnow().isoformat(),
                'status': 'UPDATED'
            }
            return create_success_response(
                data=result,
                message='Contract updated successfully'
            )
        
        elif http_method == 'DELETE' and contract_id:
            # DELETE /api/contracts/{contract_id}
            result = {
                'contract_id': contract_id,
                'deleted_at': datetime.utcnow().isoformat(),
                'status': 'DELETED'
            }
            return create_success_response(
                data=result,
                message='Contract deleted successfully'
            )
        
        else:
            return create_error_response(
                status_code=405,
                error='METHOD_NOT_ALLOWED',
                message=f'Method {http_method} not allowed for {path}'
            )
    
    except Exception as e:
        logger.error(f"Error handling contracts API: {str(e)}")
        return create_error_response(
            status_code=500,
            error='API_ERROR',
            message=str(e)
        )


def handle_files_api(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle files API endpoints"""
    try:
        http_method = event.get('httpMethod')
        path = event.get('path')
        path_parameters = event.get('pathParameters') or {}
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        
        contract_id = path_parameters.get('contract_id')
        file_id = path_parameters.get('file_id')
        
        if http_method == 'GET':
            if file_id:
                # GET /api/contracts/{contract_id}/files/{file_id}
                result = {
                    'file_id': file_id,
                    'contract_id': contract_id,
                    'filename': 'sample_document.pdf',
                    'download_url': f'https://s3.amazonaws.com/testex-files/contracts/{contract_id}/files/{file_id}',
                    'file_size': 1024,
                    'content_type': 'application/pdf'
                }
                return create_success_response(
                    data=result,
                    message='File download URL generated'
                )
            else:
                # GET /api/contracts/{contract_id}/files (list files)
                files = []
                for i in range(3):
                    files.append({
                        'file_id': f'file-{i+1:03d}',
                        'filename': f'document_{i+1}.pdf',
                        'upload_date': datetime.utcnow().isoformat(),
                        'file_size': 1024 * (i+1),
                        'content_type': 'application/pdf'
                    })
                
                result = {
                    'contract_id': contract_id,
                    'files': files,
                    'total_files': len(files)
                }
                return create_success_response(
                    data=result,
                    message='Files listed successfully'
                )
        
        elif http_method == 'POST':
            # POST /api/contracts/{contract_id}/files (upload file)
            filename = body.get('filename')
            file_content = body.get('file_content')
            
            if not filename:
                return create_error_response(
                    status_code=400,
                    error='MISSING_FILENAME',
                    message='Filename is required'
                )
            
            new_file_id = f"file-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            result = {
                'file_id': new_file_id,
                'contract_id': contract_id,
                'filename': filename,
                'upload_date': datetime.utcnow().isoformat(),
                'status': 'UPLOADED'
            }
            return create_success_response(
                data=result,
                message='File uploaded successfully',
                status_code=201
            )
        
        elif http_method == 'DELETE' and file_id:
            # DELETE /api/contracts/{contract_id}/files/{file_id}
            result = {
                'file_id': file_id,
                'contract_id': contract_id,
                'deleted_at': datetime.utcnow().isoformat(),
                'status': 'DELETED'
            }
            return create_success_response(
                data=result,
                message='File deleted successfully'
            )
        
        else:
            return create_error_response(
                status_code=405,
                error='METHOD_NOT_ALLOWED',
                message=f'Method {http_method} not allowed for {path}'
            )
    
    except Exception as e:
        logger.error(f"Error handling files API: {str(e)}")
        return create_error_response(
            status_code=500,
            error='API_ERROR',
            message=str(e)
        )


def handle_notifications_api(event: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle notifications API endpoints"""
    try:
        http_method = event.get('httpMethod')
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        
        if http_method == 'POST':
            # POST /api/notifications (send notification)
            recipient_email = body.get('recipient_email')
            subject = body.get('subject')
            message = body.get('message')
            notification_type = body.get('notification_type', 'GENERAL')
            
            if not all([recipient_email, subject, message]):
                return create_error_response(
                    status_code=400,
                    error='MISSING_REQUIRED_FIELDS',
                    message='Recipient email, subject, and message are required'
                )
            
            notification_id = f"notif-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            result = {
                'notification_id': notification_id,
                'recipient_email': recipient_email,
                'notification_type': notification_type,
                'subject': subject,
                'sent_at': datetime.utcnow().isoformat(),
                'status': 'SENT'
            }
            return create_success_response(
                data=result,
                message='Notification sent successfully',
                status_code=201
            )
        
        else:
            return create_error_response(
                status_code=405,
                error='METHOD_NOT_ALLOWED',
                message=f'Method {http_method} not allowed for notifications endpoint'
            )
    
    except Exception as e:
        logger.error(f"Error handling notifications API: {str(e)}")
        return create_error_response(
            status_code=500,
            error='API_ERROR',
            message=str(e)
        )


def create_success_response(data: Any = None, message: str = None, status_code: int = 200) -> Dict[str, Any]:
    """Create standardized success response"""
    response = {
        'status': 'success',
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(response, default=str)
    }


def create_error_response(status_code: int, error: str, message: str = None) -> Dict[str, Any]:
    """Create standardized error response"""
    response = {
        'status': 'error',
        'error': error,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if message:
        response['message'] = message
    
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps(response)
    }
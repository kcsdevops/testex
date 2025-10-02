"""
File Handler Lambda Handler
"""
import json
import logging
import base64
from datetime import datetime
from typing import Dict, Any

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for file operations
    """
    try:
        logger.info(f"File Handler invoked with event: {json.dumps(event, default=str)}")
        
        # Extract request data
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event.get('body', {})
        action = body.get('action', 'unknown')
        
        # Route to appropriate handler
        if action == 'upload_file':
            return handle_file_upload(body, context)
        elif action == 'download_file':
            return handle_file_download(body, context)
        elif action == 'list_files':
            return handle_list_files(body, context)
        elif action == 'delete_file':
            return handle_file_delete(body, context)
        elif action == 'backup_files':
            return handle_backup_files(body, context)
        else:
            return create_error_response(
                status_code=400,
                error='INVALID_ACTION',
                message=f'Unknown action: {action}'
            )
    
    except Exception as e:
        logger.error(f"Error in file handler: {str(e)}")
        return create_error_response(
            status_code=500,
            error='INTERNAL_SERVER_ERROR',
            message='An unexpected error occurred'
        )


def handle_file_upload(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle file upload"""
    try:
        contract_id = body.get('contract_id')
        filename = body.get('filename')
        file_content = body.get('file_content')  # Base64 encoded
        
        if not all([contract_id, filename, file_content]):
            return create_error_response(
                status_code=400,
                error='MISSING_REQUIRED_FIELDS',
                message='Contract ID, filename, and file content are required'
            )
        
        # Validate file type
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png']
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if f'.{file_ext}' not in allowed_extensions:
            return create_error_response(
                status_code=400,
                error='INVALID_FILE_TYPE',
                message=f'File type .{file_ext} not allowed'
            )
        
        # Simulate file upload to S3
        file_id = f"file-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        s3_key = f"contracts/{contract_id}/files/{file_id}_{filename}"
        
        result = {
            'file_id': file_id,
            'contract_id': contract_id,
            'filename': filename,
            's3_key': s3_key,
            'upload_date': datetime.utcnow().isoformat(),
            'file_size': len(base64.b64decode(file_content)) if file_content else 0,
            'status': 'UPLOADED'
        }
        
        return create_success_response(
            data=result,
            message='File uploaded successfully'
        )
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return create_error_response(
            status_code=500,
            error='UPLOAD_ERROR',
            message=str(e)
        )


def handle_file_download(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle file download"""
    try:
        file_id = body.get('file_id')
        contract_id = body.get('contract_id')
        
        if not file_id:
            return create_error_response(
                status_code=400,
                error='MISSING_FILE_ID',
                message='File ID is required'
            )
        
        # Simulate file retrieval from S3
        result = {
            'file_id': file_id,
            'contract_id': contract_id,
            'filename': 'sample_document.pdf',
            'download_url': f's3://testex-files/contracts/{contract_id}/files/{file_id}',
            'expires_at': datetime.utcnow().isoformat(),
            'file_size': 1024,
            'content_type': 'application/pdf'
        }
        
        return create_success_response(
            data=result,
            message='File download URL generated successfully'
        )
    
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return create_error_response(
            status_code=500,
            error='DOWNLOAD_ERROR',
            message=str(e)
        )


def handle_list_files(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle file listing"""
    try:
        contract_id = body.get('contract_id')
        
        if not contract_id:
            return create_error_response(
                status_code=400,
                error='MISSING_CONTRACT_ID',
                message='Contract ID is required'
            )
        
        # Simulate file listing from S3
        files = []
        for i in range(3):  # Return 3 sample files
            files.append({
                'file_id': f'file-{i+1:03d}',
                'filename': f'document_{i+1}.pdf',
                'upload_date': datetime.utcnow().isoformat(),
                'file_size': 1024 * (i+1),
                'content_type': 'application/pdf',
                'status': 'ACTIVE'
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
    
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return create_error_response(
            status_code=500,
            error='LIST_ERROR',
            message=str(e)
        )


def handle_file_delete(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle file deletion"""
    try:
        file_id = body.get('file_id')
        contract_id = body.get('contract_id')
        
        if not file_id:
            return create_error_response(
                status_code=400,
                error='MISSING_FILE_ID',
                message='File ID is required'
            )
        
        # Simulate file deletion from S3
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
    
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return create_error_response(
            status_code=500,
            error='DELETE_ERROR',
            message=str(e)
        )


def handle_backup_files(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle file backup"""
    try:
        contract_id = body.get('contract_id')
        
        if not contract_id:
            return create_error_response(
                status_code=400,
                error='MISSING_CONTRACT_ID',
                message='Contract ID is required'
            )
        
        # Simulate backup operation
        backup_id = f"backup-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        result = {
            'backup_id': backup_id,
            'contract_id': contract_id,
            'backup_location': f's3://testex-backups/contracts/{contract_id}/{backup_id}',
            'backup_date': datetime.utcnow().isoformat(),
            'files_backed_up': 3,
            'status': 'COMPLETED'
        }
        
        return create_success_response(
            data=result,
            message='Files backed up successfully'
        )
    
    except Exception as e:
        logger.error(f"Error backing up files: {str(e)}")
        return create_error_response(
            status_code=500,
            error='BACKUP_ERROR',
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
            'Access-Control-Allow-Origin': '*'
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
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(response)
    }
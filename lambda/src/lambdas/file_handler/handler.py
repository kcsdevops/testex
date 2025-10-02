"""
File Handler Lambda
Manages file operations with S3 for the TESTEX system
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError
import zipfile
import tempfile
from urllib.parse import urlparse

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')

# Environment variables
FILES_BUCKET = os.environ.get('FILES_BUCKET', 'testex-files')
ARCHIVE_BUCKET = os.environ.get('ARCHIVE_BUCKET', 'testex-archive')
DATABASE_FUNCTION = os.environ.get('DATABASE_FUNCTION', 'testex-database-manager')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for file operations
    
    Args:
        event: Lambda event containing file operation details
        context: Lambda context object
        
    Returns:
        Response dictionary with operation results
    """
    try:
        logger.info(f"File operation request: {json.dumps(event, default=str)}")
        
        # Extract operation details
        operation = event.get('action', event.get('operation'))
        contract_id = event.get('contract_id')
        
        # Route to appropriate handler
        if operation == 'upload':
            result = handle_file_upload(event)
        elif operation == 'download':
            result = handle_file_download(event)
        elif operation == 'archive':
            result = handle_file_archive(event)
        elif operation == 'delete':
            result = handle_file_delete(event)
        elif operation == 'list':
            result = handle_file_list(event)
        elif operation == 'backup':
            result = handle_file_backup(event)
        elif operation == 'restore':
            result = handle_file_restore(event)
        else:
            return create_response(400, {
                'error': 'Invalid operation',
                'supported_operations': ['upload', 'download', 'archive', 'delete', 'list', 'backup', 'restore']
            })
        
        logger.info(f"File operation {operation} completed successfully")
        
        return create_response(200, {
            'operation': operation,
            'contract_id': contract_id,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in file operation: {str(e)}")
        return create_response(500, {
            'error': 'File operation failed',
            'message': str(e)
        })


def handle_file_upload(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle file upload to S3"""
    try:
        contract_id = event['contract_id']
        files = event.get('files', [])
        
        uploaded_files = []
        
        for file_info in files:
            file_name = file_info['name']
            file_content = file_info.get('content')  # Base64 encoded
            file_type = file_info.get('type', 'application/octet-stream')
            
            # Generate S3 key
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            s3_key = f"contracts/{contract_id}/files/{timestamp}_{file_name}"
            
            # Upload to S3
            if file_content:
                # Decode base64 content
                import base64
                file_data = base64.b64decode(file_content)
                
                s3_client.put_object(
                    Bucket=FILES_BUCKET,
                    Key=s3_key,
                    Body=file_data,
                    ContentType=file_type,
                    Metadata={
                        'contract_id': contract_id,
                        'original_name': file_name,
                        'uploaded_at': datetime.utcnow().isoformat()
                    }
                )
            else:
                # Handle pre-signed URL or direct upload
                s3_key = file_info.get('s3_key', s3_key)
            
            uploaded_files.append({
                'name': file_name,
                's3_key': s3_key,
                'bucket': FILES_BUCKET,
                'type': file_type,
                'uploaded_at': datetime.utcnow().isoformat()
            })
            
            logger.info(f"File {file_name} uploaded to {s3_key}")
        
        # Update contract record with file information
        update_contract_files(contract_id, uploaded_files, 'uploaded')
        
        return {
            'status': 'success',
            'uploaded_files': uploaded_files,
            'count': len(uploaded_files)
        }
        
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise


def handle_file_download(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle file download from S3"""
    try:
        contract_id = event['contract_id']
        file_key = event.get('file_key')
        file_name = event.get('file_name')
        
        if not file_key and not file_name:
            raise ValueError("Either file_key or file_name must be provided")
        
        # If only file_name provided, construct the key
        if not file_key:
            file_key = find_file_key_by_name(contract_id, file_name)
            if not file_key:
                raise ValueError(f"File {file_name} not found for contract {contract_id}")
        
        # Generate pre-signed URL for download
        download_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': FILES_BUCKET, 'Key': file_key},
            ExpiresIn=3600  # 1 hour
        )
        
        # Get file metadata
        response = s3_client.head_object(Bucket=FILES_BUCKET, Key=file_key)
        
        logger.info(f"Download URL generated for file {file_key}")
        
        return {
            'status': 'success',
            'download_url': download_url,
            'file_key': file_key,
            'metadata': response.get('Metadata', {}),
            'size': response.get('ContentLength'),
            'last_modified': response.get('LastModified').isoformat() if response.get('LastModified') else None,
            'expires_in': 3600
        }
        
    except Exception as e:
        logger.error(f"File download failed: {str(e)}")
        raise


def handle_file_archive(event: Dict[str, Any]) -> Dict[str, Any]:
    """Archive files for a contract"""
    try:
        contract_id = event['contract_id']
        files = event.get('files', [])
        
        # List all files for the contract if not specified
        if not files:
            files = list_contract_files(contract_id)
        
        if not files:
            return {
                'status': 'success',
                'message': 'No files to archive',
                'archived_files': []
            }
        
        # Create archive
        archive_key = f"archives/{contract_id}/contract_files_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip"
        
        # Create temporary zip file
        with tempfile.NamedTemporaryFile(delete=False) as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                
                for file_info in files:
                    try:
                        # Download file from S3
                        file_key = file_info.get('s3_key') or file_info.get('key')
                        file_name = file_info.get('name') or file_info.get('original_name', os.path.basename(file_key))
                        
                        response = s3_client.get_object(Bucket=FILES_BUCKET, Key=file_key)
                        file_content = response['Body'].read()
                        
                        # Add to zip
                        zip_file.writestr(file_name, file_content)
                        logger.info(f"Added {file_name} to archive")
                        
                    except Exception as e:
                        logger.warning(f"Failed to add file {file_info} to archive: {str(e)}")
            
            # Upload archive to S3
            with open(temp_zip.name, 'rb') as archive_file:
                s3_client.put_object(
                    Bucket=ARCHIVE_BUCKET,
                    Key=archive_key,
                    Body=archive_file.read(),
                    ContentType='application/zip',
                    Metadata={
                        'contract_id': contract_id,
                        'created_at': datetime.utcnow().isoformat(),
                        'file_count': str(len(files))
                    }
                )
        
        # Clean up temp file
        os.unlink(temp_zip.name)
        
        # Update contract record
        update_contract_files(contract_id, [{'archive_key': archive_key, 'file_count': len(files)}], 'archived')
        
        logger.info(f"Created archive {archive_key} with {len(files)} files")
        
        return {
            'status': 'success',
            'archive_key': archive_key,
            'archive_bucket': ARCHIVE_BUCKET,
            'file_count': len(files),
            'created_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"File archiving failed: {str(e)}")
        raise


def handle_file_delete(event: Dict[str, Any]) -> Dict[str, Any]:
    """Delete files from S3"""
    try:
        contract_id = event['contract_id']
        files = event.get('files', [])
        permanent = event.get('permanent', False)
        
        deleted_files = []
        
        for file_info in files:
            file_key = file_info.get('s3_key') or file_info.get('key')
            
            if permanent:
                # Permanent delete
                s3_client.delete_object(Bucket=FILES_BUCKET, Key=file_key)
                logger.info(f"Permanently deleted file {file_key}")
            else:
                # Move to deleted folder (soft delete)
                deleted_key = f"deleted/{contract_id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(file_key)}"
                
                s3_client.copy_object(
                    Bucket=FILES_BUCKET,
                    CopySource={'Bucket': FILES_BUCKET, 'Key': file_key},
                    Key=deleted_key,
                    Metadata={
                        'original_key': file_key,
                        'deleted_at': datetime.utcnow().isoformat(),
                        'contract_id': contract_id
                    },
                    MetadataDirective='REPLACE'
                )
                
                s3_client.delete_object(Bucket=FILES_BUCKET, Key=file_key)
                logger.info(f"Soft deleted file {file_key} to {deleted_key}")
            
            deleted_files.append({
                'original_key': file_key,
                'deleted_key': deleted_key if not permanent else None,
                'permanent': permanent,
                'deleted_at': datetime.utcnow().isoformat()
            })
        
        # Update contract record
        update_contract_files(contract_id, deleted_files, 'deleted')
        
        return {
            'status': 'success',
            'deleted_files': deleted_files,
            'count': len(deleted_files),
            'permanent': permanent
        }
        
    except Exception as e:
        logger.error(f"File deletion failed: {str(e)}")
        raise


def handle_file_list(event: Dict[str, Any]) -> Dict[str, Any]:
    """List files for a contract"""
    try:
        contract_id = event['contract_id']
        include_deleted = event.get('include_deleted', False)
        
        files = list_contract_files(contract_id, include_deleted)
        
        return {
            'status': 'success',
            'contract_id': contract_id,
            'files': files,
            'count': len(files),
            'include_deleted': include_deleted
        }
        
    except Exception as e:
        logger.error(f"File listing failed: {str(e)}")
        raise


def handle_file_backup(event: Dict[str, Any]) -> Dict[str, Any]:
    """Backup files to archive bucket"""
    try:
        contract_id = event['contract_id']
        
        # List all files for the contract
        files = list_contract_files(contract_id)
        
        if not files:
            return {
                'status': 'success',
                'message': 'No files to backup',
                'backed_up_files': []
            }
        
        backed_up_files = []
        
        for file_info in files:
            file_key = file_info['key']
            backup_key = f"backups/{contract_id}/{datetime.utcnow().strftime('%Y%m%d')}/{os.path.basename(file_key)}"
            
            # Copy to archive bucket
            s3_client.copy_object(
                Bucket=ARCHIVE_BUCKET,
                CopySource={'Bucket': FILES_BUCKET, 'Key': file_key},
                Key=backup_key,
                Metadata={
                    'original_key': file_key,
                    'contract_id': contract_id,
                    'backed_up_at': datetime.utcnow().isoformat()
                },
                MetadataDirective='REPLACE'
            )
            
            backed_up_files.append({
                'original_key': file_key,
                'backup_key': backup_key,
                'backed_up_at': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Backed up file {file_key} to {backup_key}")
        
        return {
            'status': 'success',
            'backed_up_files': backed_up_files,
            'count': len(backed_up_files)
        }
        
    except Exception as e:
        logger.error(f"File backup failed: {str(e)}")
        raise


def handle_file_restore(event: Dict[str, Any]) -> Dict[str, Any]:
    """Restore files from backup"""
    try:
        contract_id = event['contract_id']
        backup_date = event.get('backup_date')  # Format: YYYYMMDD
        
        if not backup_date:
            backup_date = datetime.utcnow().strftime('%Y%m%d')
        
        # List backup files
        backup_prefix = f"backups/{contract_id}/{backup_date}/"
        
        response = s3_client.list_objects_v2(
            Bucket=ARCHIVE_BUCKET,
            Prefix=backup_prefix
        )
        
        if 'Contents' not in response:
            return {
                'status': 'success',
                'message': f'No backup files found for date {backup_date}',
                'restored_files': []
            }
        
        restored_files = []
        
        for obj in response['Contents']:
            backup_key = obj['Key']
            file_name = os.path.basename(backup_key)
            restore_key = f"contracts/{contract_id}/restored/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file_name}"
            
            # Copy back to main bucket
            s3_client.copy_object(
                Bucket=FILES_BUCKET,
                CopySource={'Bucket': ARCHIVE_BUCKET, 'Key': backup_key},
                Key=restore_key,
                Metadata={
                    'backup_key': backup_key,
                    'contract_id': contract_id,
                    'restored_at': datetime.utcnow().isoformat()
                },
                MetadataDirective='REPLACE'
            )
            
            restored_files.append({
                'backup_key': backup_key,
                'restored_key': restore_key,
                'file_name': file_name,
                'restored_at': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Restored file {backup_key} to {restore_key}")
        
        return {
            'status': 'success',
            'restored_files': restored_files,
            'count': len(restored_files),
            'backup_date': backup_date
        }
        
    except Exception as e:
        logger.error(f"File restore failed: {str(e)}")
        raise


def list_contract_files(contract_id: str, include_deleted: bool = False) -> List[Dict[str, Any]]:
    """List all files for a contract"""
    files = []
    
    # List active files
    prefix = f"contracts/{contract_id}/"
    response = s3_client.list_objects_v2(Bucket=FILES_BUCKET, Prefix=prefix)
    
    if 'Contents' in response:
        for obj in response['Contents']:
            # Get metadata
            head_response = s3_client.head_object(Bucket=FILES_BUCKET, Key=obj['Key'])
            
            files.append({
                'key': obj['Key'],
                'name': os.path.basename(obj['Key']),
                'size': obj['Size'],
                'last_modified': obj['LastModified'].isoformat(),
                'metadata': head_response.get('Metadata', {}),
                'status': 'active'
            })
    
    # List deleted files if requested
    if include_deleted:
        deleted_prefix = f"deleted/{contract_id}/"
        deleted_response = s3_client.list_objects_v2(Bucket=FILES_BUCKET, Prefix=deleted_prefix)
        
        if 'Contents' in deleted_response:
            for obj in deleted_response['Contents']:
                head_response = s3_client.head_object(Bucket=FILES_BUCKET, Key=obj['Key'])
                
                files.append({
                    'key': obj['Key'],
                    'name': os.path.basename(obj['Key']),
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat(),
                    'metadata': head_response.get('Metadata', {}),
                    'status': 'deleted'
                })
    
    return files


def find_file_key_by_name(contract_id: str, file_name: str) -> str:
    """Find S3 key for a file by name"""
    files = list_contract_files(contract_id)
    
    for file_info in files:
        if file_info['name'] == file_name or file_info['name'].endswith(file_name):
            return file_info['key']
    
    return None


def update_contract_files(contract_id: str, file_info: List[Dict[str, Any]], action: str):
    """Update contract record with file information"""
    try:
        payload = {
            'operation': 'update_contract',
            'data': {
                'contract_id': contract_id,
                'updates': {
                    f'files_{action}': file_info,
                    f'{action}_at': datetime.utcnow().isoformat()
                }
            }
        }
        
        lambda_client.invoke(
            FunctionName=DATABASE_FUNCTION,
            InvocationType='Event',
            Payload=json.dumps(payload)
        )
        
        logger.info(f"Contract {contract_id} updated with file {action} information")
        
    except Exception as e:
        logger.warning(f"Failed to update contract with file information: {str(e)}")


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized Lambda response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body, default=str)
    }
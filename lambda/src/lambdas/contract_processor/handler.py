"""
Contract Processor Lambda
Handles contract termination processing logic
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
dynamodb = boto3.resource('dynamodb')
s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')

# Environment variables
CONTRACTS_TABLE = os.environ.get('CONTRACTS_TABLE', 'testex-contracts')
FILES_BUCKET = os.environ.get('FILES_BUCKET', 'testex-files')
NOTIFICATION_FUNCTION = os.environ.get('NOTIFICATION_FUNCTION', 'testex-notification-service')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for contract processing
    
    Args:
        event: Lambda event containing contract information
        context: Lambda context object
        
    Returns:
        Response dictionary with processing results
    """
    try:
        logger.info(f"Processing contract termination request: {json.dumps(event)}")
        
        # Extract contract information from event
        contract_data = extract_contract_data(event)
        
        # Validate contract data
        validation_result = validate_contract_data(contract_data)
        if not validation_result['valid']:
            return create_response(400, {
                'error': 'Invalid contract data',
                'details': validation_result['errors']
            })
        
        # Process contract termination
        processing_result = process_contract_termination(contract_data)
        
        # Update contract status in database
        update_contract_status(contract_data['contract_id'], 'processing', processing_result)
        
        # Trigger file processing if needed
        if contract_data.get('files'):
            trigger_file_processing(contract_data['contract_id'], contract_data['files'])
        
        # Send notification
        send_termination_notification(contract_data)
        
        logger.info(f"Contract {contract_data['contract_id']} processing completed successfully")
        
        return create_response(200, {
            'message': 'Contract termination processed successfully',
            'contract_id': contract_data['contract_id'],
            'status': 'processing',
            'processing_details': processing_result
        })
        
    except Exception as e:
        logger.error(f"Error processing contract: {str(e)}")
        return create_response(500, {
            'error': 'Internal server error',
            'message': str(e)
        })


def extract_contract_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """Extract contract data from Lambda event"""
    
    # Handle API Gateway event
    if 'body' in event:
        body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        contract_data = body
    else:
        # Handle direct Lambda invocation
        contract_data = event
    
    # Add processing metadata
    contract_data['processed_at'] = datetime.utcnow().isoformat()
    contract_data['status'] = 'received'
    
    return contract_data


def validate_contract_data(contract_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate contract data structure and required fields"""
    
    errors = []
    required_fields = ['contract_id', 'client_id', 'termination_type', 'requested_by']
    
    # Check required fields
    for field in required_fields:
        if field not in contract_data or not contract_data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate contract_id format
    if 'contract_id' in contract_data:
        contract_id = contract_data['contract_id']
        if not contract_id.startswith('CT'):
            errors.append("Contract ID must start with 'CT'")
    
    # Validate client_id format
    if 'client_id' in contract_data:
        client_id = contract_data['client_id']
        if not client_id.startswith('CL'):
            errors.append("Client ID must start with 'CL'")
    
    # Validate termination type
    valid_termination_types = ['voluntary', 'involuntary', 'expired', 'breach']
    if 'termination_type' in contract_data:
        if contract_data['termination_type'] not in valid_termination_types:
            errors.append(f"Invalid termination type. Must be one of: {valid_termination_types}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def process_contract_termination(contract_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process the contract termination logic"""
    
    contract_id = contract_data['contract_id']
    termination_type = contract_data['termination_type']
    
    logger.info(f"Processing {termination_type} termination for contract {contract_id}")
    
    processing_steps = []
    
    # Step 1: Backup contract data
    backup_result = backup_contract_data(contract_data)
    processing_steps.append({
        'step': 'backup',
        'status': 'completed' if backup_result else 'failed',
        'timestamp': datetime.utcnow().isoformat()
    })
    
    # Step 2: Calculate termination details
    termination_details = calculate_termination_details(contract_data)
    processing_steps.append({
        'step': 'calculate_termination',
        'status': 'completed',
        'details': termination_details,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    # Step 3: Process termination based on type
    if termination_type == 'voluntary':
        result = process_voluntary_termination(contract_data)
    elif termination_type == 'involuntary':
        result = process_involuntary_termination(contract_data)
    elif termination_type == 'expired':
        result = process_expired_termination(contract_data)
    elif termination_type == 'breach':
        result = process_breach_termination(contract_data)
    else:
        result = {'status': 'error', 'message': 'Unknown termination type'}
    
    processing_steps.append({
        'step': f'process_{termination_type}_termination',
        'status': result.get('status', 'unknown'),
        'details': result,
        'timestamp': datetime.utcnow().isoformat()
    })
    
    return {
        'contract_id': contract_id,
        'termination_type': termination_type,
        'steps': processing_steps,
        'final_status': 'processing'
    }


def backup_contract_data(contract_data: Dict[str, Any]) -> bool:
    """Backup contract data to S3"""
    try:
        contract_id = contract_data['contract_id']
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        
        backup_key = f"backups/{contract_id}/contract_data_{timestamp}.json"
        
        s3_client.put_object(
            Bucket=FILES_BUCKET,
            Key=backup_key,
            Body=json.dumps(contract_data, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"Contract data backed up to s3://{FILES_BUCKET}/{backup_key}")
        return True
        
    except ClientError as e:
        logger.error(f"Failed to backup contract data: {str(e)}")
        return False


def calculate_termination_details(contract_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate termination-specific details"""
    
    termination_date = datetime.utcnow().isoformat()
    
    return {
        'termination_date': termination_date,
        'effective_date': contract_data.get('effective_date', termination_date),
        'notice_period_days': contract_data.get('notice_period_days', 30),
        'penalty_amount': contract_data.get('penalty_amount', 0),
        'refund_amount': contract_data.get('refund_amount', 0)
    }


def process_voluntary_termination(contract_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process voluntary termination"""
    return {
        'status': 'completed',
        'message': 'Voluntary termination processed',
        'requires_approval': False,
        'notice_required': True
    }


def process_involuntary_termination(contract_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process involuntary termination"""
    return {
        'status': 'completed',
        'message': 'Involuntary termination processed',
        'requires_approval': True,
        'notice_required': True,
        'legal_review_required': True
    }


def process_expired_termination(contract_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process expired contract termination"""
    return {
        'status': 'completed',
        'message': 'Expired contract termination processed',
        'requires_approval': False,
        'notice_required': False
    }


def process_breach_termination(contract_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process breach termination"""
    return {
        'status': 'completed',
        'message': 'Breach termination processed',
        'requires_approval': True,
        'notice_required': True,
        'legal_review_required': True,
        'penalty_applicable': True
    }


def update_contract_status(contract_id: str, status: str, details: Dict[str, Any]):
    """Update contract status in DynamoDB"""
    try:
        table = dynamodb.Table(CONTRACTS_TABLE)
        
        response = table.update_item(
            Key={'contract_id': contract_id},
            UpdateExpression='SET #status = :status, processing_details = :details, updated_at = :timestamp',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': status,
                ':details': details,
                ':timestamp': datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"Contract {contract_id} status updated to {status}")
        
    except ClientError as e:
        logger.error(f"Failed to update contract status: {str(e)}")
        raise


def trigger_file_processing(contract_id: str, files: list):
    """Trigger file processing Lambda"""
    try:
        payload = {
            'contract_id': contract_id,
            'files': files,
            'action': 'archive'
        }
        
        lambda_client.invoke(
            FunctionName='testex-file-handler',
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(payload)
        )
        
        logger.info(f"File processing triggered for contract {contract_id}")
        
    except ClientError as e:
        logger.error(f"Failed to trigger file processing: {str(e)}")


def send_termination_notification(contract_data: Dict[str, Any]):
    """Send termination notification"""
    try:
        payload = {
            'type': 'contract_termination',
            'contract_data': contract_data,
            'recipients': contract_data.get('notification_emails', []),
            'template': 'termination_processing'
        }
        
        lambda_client.invoke(
            FunctionName=NOTIFICATION_FUNCTION,
            InvocationType='Event',  # Async invocation
            Payload=json.dumps(payload)
        )
        
        logger.info(f"Notification sent for contract {contract_data['contract_id']}")
        
    except ClientError as e:
        logger.error(f"Failed to send notification: {str(e)}")


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized Lambda response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }
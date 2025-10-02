"""
Notification Service Lambda Handler
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
    Main Lambda handler for notification operations
    """
    try:
        logger.info(f"Notification Service invoked with event: {json.dumps(event, default=str)}")
        
        # Extract request data
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event.get('body', {})
        action = body.get('action', 'unknown')
        
        # Route to appropriate handler
        if action == 'send_termination_notice':
            return handle_termination_notice(body, context)
        elif action == 'send_status_update':
            return handle_status_update(body, context)
        elif action == 'send_approval_request':
            return handle_approval_request(body, context)
        elif action == 'send_notification':
            return handle_send_notification(body, context)
        else:
            return create_error_response(
                status_code=400,
                error='INVALID_ACTION',
                message=f'Unknown action: {action}'
            )
    
    except Exception as e:
        logger.error(f"Error in notification service: {str(e)}")
        return create_error_response(
            status_code=500,
            error='INTERNAL_SERVER_ERROR',
            message='An unexpected error occurred'
        )


def handle_termination_notice(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle contract termination notice"""
    try:
        contract_id = body.get('contract_id')
        client_email = body.get('client_email')
        termination_reason = body.get('termination_reason')
        
        if not all([contract_id, client_email]):
            return create_error_response(
                status_code=400,
                error='MISSING_REQUIRED_FIELDS',
                message='Contract ID and client email are required'
            )
        
        # Simulate email sending
        notification_id = f"notif-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        result = {
            'notification_id': notification_id,
            'contract_id': contract_id,
            'recipient_email': client_email,
            'notification_type': 'CONTRACT_TERMINATION',
            'subject': f'Contract Termination Notice - {contract_id}',
            'termination_reason': termination_reason,
            'sent_at': datetime.utcnow().isoformat(),
            'status': 'SENT',
            'message_id': f'ses-{notification_id}'
        }
        
        return create_success_response(
            data=result,
            message='Termination notice sent successfully'
        )
    
    except Exception as e:
        logger.error(f"Error sending termination notice: {str(e)}")
        return create_error_response(
            status_code=500,
            error='NOTIFICATION_ERROR',
            message=str(e)
        )


def handle_status_update(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle status update notification"""
    try:
        contract_id = body.get('contract_id')
        client_email = body.get('client_email')
        new_status = body.get('new_status')
        
        if not all([contract_id, client_email, new_status]):
            return create_error_response(
                status_code=400,
                error='MISSING_REQUIRED_FIELDS',
                message='Contract ID, client email, and new status are required'
            )
        
        # Simulate email sending
        notification_id = f"notif-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        result = {
            'notification_id': notification_id,
            'contract_id': contract_id,
            'recipient_email': client_email,
            'notification_type': 'STATUS_UPDATE',
            'subject': f'Contract Status Update - {contract_id}',
            'new_status': new_status,
            'sent_at': datetime.utcnow().isoformat(),
            'status': 'SENT',
            'message_id': f'ses-{notification_id}'
        }
        
        return create_success_response(
            data=result,
            message='Status update notification sent successfully'
        )
    
    except Exception as e:
        logger.error(f"Error sending status update: {str(e)}")
        return create_error_response(
            status_code=500,
            error='NOTIFICATION_ERROR',
            message=str(e)
        )


def handle_approval_request(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle approval request notification"""
    try:
        contract_id = body.get('contract_id')
        approver_email = body.get('approver_email')
        approval_type = body.get('approval_type', 'TERMINATION')
        
        if not all([contract_id, approver_email]):
            return create_error_response(
                status_code=400,
                error='MISSING_REQUIRED_FIELDS',
                message='Contract ID and approver email are required'
            )
        
        # Simulate email sending
        notification_id = f"notif-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        result = {
            'notification_id': notification_id,
            'contract_id': contract_id,
            'recipient_email': approver_email,
            'notification_type': 'APPROVAL_REQUEST',
            'subject': f'Approval Required - {approval_type} for {contract_id}',
            'approval_type': approval_type,
            'sent_at': datetime.utcnow().isoformat(),
            'status': 'SENT',
            'message_id': f'ses-{notification_id}'
        }
        
        return create_success_response(
            data=result,
            message='Approval request sent successfully'
        )
    
    except Exception as e:
        logger.error(f"Error sending approval request: {str(e)}")
        return create_error_response(
            status_code=500,
            error='NOTIFICATION_ERROR',
            message=str(e)
        )


def handle_send_notification(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle general notification sending"""
    try:
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
        
        # Validate email format
        if '@' not in recipient_email:
            return create_error_response(
                status_code=400,
                error='INVALID_EMAIL',
                message='Invalid email format'
            )
        
        # Simulate email sending
        notification_id = f"notif-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        result = {
            'notification_id': notification_id,
            'recipient_email': recipient_email,
            'notification_type': notification_type,
            'subject': subject,
            'sent_at': datetime.utcnow().isoformat(),
            'status': 'SENT',
            'message_id': f'ses-{notification_id}'
        }
        
        return create_success_response(
            data=result,
            message='Notification sent successfully'
        )
    
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return create_error_response(
            status_code=500,
            error='NOTIFICATION_ERROR',
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
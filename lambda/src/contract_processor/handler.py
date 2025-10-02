"""
Contract Processor Lambda Handler
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
    Main Lambda handler for contract processing
    """
    try:
        logger.info(f"Contract Processor invoked with event: {json.dumps(event, default=str)}")
        
        # Extract request data
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event.get('body', {})
        action = body.get('action', 'unknown')
        
        # Route to appropriate handler
        if action == 'terminate_contract':
            return handle_contract_termination(body, context)
        elif action == 'validate_contract':
            return handle_contract_validation(body, context)
        elif action == 'process_contract':
            return handle_contract_processing(body, context)
        else:
            return create_error_response(
                status_code=400,
                error='INVALID_ACTION',
                message=f'Unknown action: {action}'
            )
    
    except Exception as e:
        logger.error(f"Error in contract processor: {str(e)}")
        return create_error_response(
            status_code=500,
            error='INTERNAL_SERVER_ERROR',
            message='An unexpected error occurred'
        )


def handle_contract_termination(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle contract termination"""
    try:
        contract_id = body.get('contract_id')
        termination_reason = body.get('termination_reason', 'NOT_SPECIFIED')
        
        if not contract_id:
            return create_error_response(
                status_code=400,
                error='MISSING_CONTRACT_ID',
                message='Contract ID is required'
            )
        
        # Simulate contract termination processing
        result = {
            'contract_id': contract_id,
            'status': 'TERMINATED',
            'termination_reason': termination_reason,
            'termination_date': datetime.utcnow().isoformat(),
            'processed_by': 'contract_processor'
        }
        
        return create_success_response(
            data=result,
            message='Contract terminated successfully'
        )
    
    except Exception as e:
        logger.error(f"Error terminating contract: {str(e)}")
        return create_error_response(
            status_code=500,
            error='TERMINATION_ERROR',
            message=str(e)
        )


def handle_contract_validation(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle contract validation"""
    try:
        contract_data = body.get('contract_data', {})
        
        # Basic validation
        required_fields = ['contract_id', 'client_id', 'contract_type']
        missing_fields = [field for field in required_fields if not contract_data.get(field)]
        
        if missing_fields:
            return create_error_response(
                status_code=400,
                error='VALIDATION_ERROR',
                message=f'Missing required fields: {", ".join(missing_fields)}'
            )
        
        # Validate contract ID format
        contract_id = contract_data.get('contract_id', '')
        if not contract_id.startswith('CT'):
            return create_error_response(
                status_code=400,
                error='VALIDATION_ERROR',
                message='Contract ID must start with CT'
            )
        
        return create_success_response(
            data={'valid': True, 'contract_id': contract_id},
            message='Contract validation successful'
        )
    
    except Exception as e:
        logger.error(f"Error validating contract: {str(e)}")
        return create_error_response(
            status_code=500,
            error='VALIDATION_ERROR',
            message=str(e)
        )


def handle_contract_processing(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle general contract processing"""
    try:
        contract_id = body.get('contract_id')
        processing_type = body.get('processing_type', 'standard')
        
        result = {
            'contract_id': contract_id,
            'processing_type': processing_type,
            'processed_at': datetime.utcnow().isoformat(),
            'status': 'PROCESSED'
        }
        
        return create_success_response(
            data=result,
            message='Contract processed successfully'
        )
    
    except Exception as e:
        logger.error(f"Error processing contract: {str(e)}")
        return create_error_response(
            status_code=500,
            error='PROCESSING_ERROR',
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
        'body': json.dumps(response)
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
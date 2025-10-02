"""
Database Manager Lambda Handler
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
    Main Lambda handler for database operations
    """
    try:
        logger.info(f"Database Manager invoked with event: {json.dumps(event, default=str)}")
        
        # Extract request data
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event.get('body', {})
        action = body.get('action', 'unknown')
        
        # Route to appropriate handler
        if action == 'create_contract':
            return handle_create_contract(body, context)
        elif action == 'get_contract':
            return handle_get_contract(body, context)
        elif action == 'update_contract':
            return handle_update_contract(body, context)
        elif action == 'list_contracts':
            return handle_list_contracts(body, context)
        elif action == 'create_audit_log':
            return handle_create_audit_log(body, context)
        else:
            return create_error_response(
                status_code=400,
                error='INVALID_ACTION',
                message=f'Unknown action: {action}'
            )
    
    except Exception as e:
        logger.error(f"Error in database manager: {str(e)}")
        return create_error_response(
            status_code=500,
            error='INTERNAL_SERVER_ERROR',
            message='An unexpected error occurred'
        )


def handle_create_contract(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle contract creation"""
    try:
        contract_data = body.get('contract_data', {})
        contract_id = contract_data.get('contract_id')
        
        if not contract_id:
            return create_error_response(
                status_code=400,
                error='MISSING_CONTRACT_ID',
                message='Contract ID is required'
            )
        
        # Simulate database creation
        result = {
            'contract_id': contract_id,
            'status': 'CREATED',
            'created_at': datetime.utcnow().isoformat()
        }
        
        return create_success_response(
            data=result,
            message='Contract created successfully'
        )
    
    except Exception as e:
        logger.error(f"Error creating contract: {str(e)}")
        return create_error_response(
            status_code=500,
            error='CREATE_ERROR',
            message=str(e)
        )


def handle_get_contract(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle contract retrieval"""
    try:
        contract_id = body.get('contract_id')
        
        if not contract_id:
            return create_error_response(
                status_code=400,
                error='MISSING_CONTRACT_ID',
                message='Contract ID is required'
            )
        
        # Simulate database retrieval
        if contract_id.startswith('CT'):
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
            return create_error_response(
                status_code=404,
                error='CONTRACT_NOT_FOUND',
                message='Contract not found'
            )
    
    except Exception as e:
        logger.error(f"Error retrieving contract: {str(e)}")
        return create_error_response(
            status_code=500,
            error='RETRIEVE_ERROR',
            message=str(e)
        )


def handle_update_contract(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle contract update"""
    try:
        contract_id = body.get('contract_id')
        updates = body.get('updates', {})
        
        if not contract_id:
            return create_error_response(
                status_code=400,
                error='MISSING_CONTRACT_ID',
                message='Contract ID is required'
            )
        
        # Simulate database update
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
    
    except Exception as e:
        logger.error(f"Error updating contract: {str(e)}")
        return create_error_response(
            status_code=500,
            error='UPDATE_ERROR',
            message=str(e)
        )


def handle_list_contracts(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle contract listing"""
    try:
        page = body.get('page', 1)
        page_size = body.get('page_size', 10)
        filters = body.get('filters', {})
        
        # Simulate database query
        contracts = []
        for i in range(min(page_size, 5)):  # Return up to 5 sample contracts
            contracts.append({
                'contract_id': f'CT{i+1:03d}ABC',
                'client_id': f'CL{i+1:03d}XYZ',
                'status': 'ACTIVE' if i % 2 == 0 else 'TERMINATED',
                'contract_type': 'SERVICE',
                'created_at': datetime.utcnow().isoformat()
            })
        
        result = {
            'contracts': contracts,
            'pagination': {
                'current_page': page,
                'page_size': page_size,
                'total_items': 25,
                'total_pages': 3,
                'has_next': page < 3,
                'has_previous': page > 1
            }
        }
        
        return create_success_response(
            data=result,
            message='Contracts retrieved successfully'
        )
    
    except Exception as e:
        logger.error(f"Error listing contracts: {str(e)}")
        return create_error_response(
            status_code=500,
            error='LIST_ERROR',
            message=str(e)
        )


def handle_create_audit_log(body: Dict[str, Any], context) -> Dict[str, Any]:
    """Handle audit log creation"""
    try:
        contract_id = body.get('contract_id')
        action = body.get('audit_action')
        details = body.get('details', {})
        
        if not contract_id or not action:
            return create_error_response(
                status_code=400,
                error='MISSING_REQUIRED_FIELDS',
                message='Contract ID and action are required'
            )
        
        # Simulate audit log creation
        log_id = f"log-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        result = {
            'log_id': log_id,
            'contract_id': contract_id,
            'action': action,
            'details': details,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'LOGGED'
        }
        
        return create_success_response(
            data=result,
            message='Audit log created successfully'
        )
    
    except Exception as e:
        logger.error(f"Error creating audit log: {str(e)}")
        return create_error_response(
            status_code=500,
            error='AUDIT_ERROR',
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
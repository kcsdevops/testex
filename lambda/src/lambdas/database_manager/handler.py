"""
Database Manager Lambda
Handles all DynamoDB operations for the TESTEX system
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
CONTRACTS_TABLE = os.environ.get('CONTRACTS_TABLE', 'testex-contracts')
CLIENTS_TABLE = os.environ.get('CLIENTS_TABLE', 'testex-clients')
AUDIT_TABLE = os.environ.get('AUDIT_TABLE', 'testex-audit')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for database operations
    
    Args:
        event: Lambda event containing database operation details
        context: Lambda context object
        
    Returns:
        Response dictionary with operation results
    """
    try:
        logger.info(f"Database operation request: {json.dumps(event, default=str)}")
        
        # Extract operation details
        operation = event.get('operation')
        table_name = event.get('table', CONTRACTS_TABLE)
        data = event.get('data', {})
        
        # Route to appropriate handler
        if operation == 'create_contract':
            result = create_contract(data)
        elif operation == 'get_contract':
            result = get_contract(data.get('contract_id'))
        elif operation == 'update_contract':
            result = update_contract(data.get('contract_id'), data.get('updates'))
        elif operation == 'delete_contract':
            result = delete_contract(data.get('contract_id'))
        elif operation == 'list_contracts':
            result = list_contracts(data.get('filters', {}))
        elif operation == 'create_client':
            result = create_client(data)
        elif operation == 'get_client':
            result = get_client(data.get('client_id'))
        elif operation == 'update_client':
            result = update_client(data.get('client_id'), data.get('updates'))
        elif operation == 'audit_log':
            result = create_audit_log(data)
        elif operation == 'get_audit_logs':
            result = get_audit_logs(data.get('contract_id'))
        else:
            return create_response(400, {
                'error': 'Invalid operation',
                'supported_operations': [
                    'create_contract', 'get_contract', 'update_contract', 'delete_contract', 'list_contracts',
                    'create_client', 'get_client', 'update_client',
                    'audit_log', 'get_audit_logs'
                ]
            })
        
        logger.info(f"Database operation {operation} completed successfully")
        
        return create_response(200, {
            'operation': operation,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in database operation: {str(e)}")
        return create_response(500, {
            'error': 'Database operation failed',
            'message': str(e)
        })


def create_contract(contract_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new contract record"""
    try:
        table = dynamodb.Table(CONTRACTS_TABLE)
        
        # Add metadata
        now = datetime.utcnow().isoformat()
        contract_data['created_at'] = now
        contract_data['updated_at'] = now
        contract_data['status'] = contract_data.get('status', 'active')
        
        # Convert float values to Decimal for DynamoDB
        contract_data = convert_floats_to_decimal(contract_data)
        
        # Create contract
        response = table.put_item(
            Item=contract_data,
            ConditionExpression='attribute_not_exists(contract_id)'
        )
        
        # Create audit log
        audit_data = {
            'contract_id': contract_data['contract_id'],
            'action': 'contract_created',
            'details': contract_data,
            'performed_by': contract_data.get('created_by', 'system')
        }
        create_audit_log(audit_data)
        
        logger.info(f"Contract {contract_data['contract_id']} created successfully")
        
        return {
            'contract_id': contract_data['contract_id'],
            'status': 'created',
            'created_at': contract_data['created_at']
        }
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise ValueError(f"Contract {contract_data['contract_id']} already exists")
        raise


def get_contract(contract_id: str) -> Optional[Dict[str, Any]]:
    """Get contract by ID"""
    try:
        table = dynamodb.Table(CONTRACTS_TABLE)
        
        response = table.get_item(Key={'contract_id': contract_id})
        
        if 'Item' in response:
            contract = convert_decimal_to_float(response['Item'])
            logger.info(f"Contract {contract_id} retrieved successfully")
            return contract
        else:
            logger.warning(f"Contract {contract_id} not found")
            return None
            
    except ClientError as e:
        logger.error(f"Failed to get contract {contract_id}: {str(e)}")
        raise


def update_contract(contract_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update contract record"""
    try:
        table = dynamodb.Table(CONTRACTS_TABLE)
        
        # Prepare update expression
        updates['updated_at'] = datetime.utcnow().isoformat()
        updates = convert_floats_to_decimal(updates)
        
        update_expression_parts = []
        expression_attribute_names = {}
        expression_attribute_values = {}
        
        for key, value in updates.items():
            if key == 'contract_id':  # Skip primary key
                continue
                
            placeholder_name = f"#{key}"
            placeholder_value = f":{key}"
            
            update_expression_parts.append(f"{placeholder_name} = {placeholder_value}")
            expression_attribute_names[placeholder_name] = key
            expression_attribute_values[placeholder_value] = value
        
        update_expression = "SET " + ", ".join(update_expression_parts)
        
        response = table.update_item(
            Key={'contract_id': contract_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ConditionExpression='attribute_exists(contract_id)',
            ReturnValues='ALL_NEW'
        )
        
        # Create audit log
        audit_data = {
            'contract_id': contract_id,
            'action': 'contract_updated',
            'details': updates,
            'performed_by': updates.get('updated_by', 'system')
        }
        create_audit_log(audit_data)
        
        updated_contract = convert_decimal_to_float(response['Attributes'])
        logger.info(f"Contract {contract_id} updated successfully")
        
        return updated_contract
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise ValueError(f"Contract {contract_id} not found")
        raise


def delete_contract(contract_id: str) -> Dict[str, Any]:
    """Delete contract record (soft delete)"""
    try:
        # Perform soft delete by updating status
        updates = {
            'status': 'deleted',
            'deleted_at': datetime.utcnow().isoformat(),
            'deleted_by': 'system'
        }
        
        result = update_contract(contract_id, updates)
        
        # Create audit log
        audit_data = {
            'contract_id': contract_id,
            'action': 'contract_deleted',
            'details': {'soft_delete': True},
            'performed_by': 'system'
        }
        create_audit_log(audit_data)
        
        logger.info(f"Contract {contract_id} deleted (soft delete)")
        
        return {
            'contract_id': contract_id,
            'status': 'deleted',
            'deleted_at': updates['deleted_at']
        }
        
    except Exception as e:
        logger.error(f"Failed to delete contract {contract_id}: {str(e)}")
        raise


def list_contracts(filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """List contracts with optional filters"""
    try:
        table = dynamodb.Table(CONTRACTS_TABLE)
        
        if filters is None:
            filters = {}
        
        # Build scan parameters
        scan_kwargs = {}
        
        # Add filters
        if filters:
            filter_expressions = []
            expression_attribute_names = {}
            expression_attribute_values = {}
            
            for key, value in filters.items():
                if key == 'status' and value:
                    filter_expressions.append(Attr('status').eq(value))
                elif key == 'client_id' and value:
                    filter_expressions.append(Attr('client_id').eq(value))
                elif key == 'termination_type' and value:
                    filter_expressions.append(Attr('termination_type').eq(value))
                elif key == 'created_after' and value:
                    filter_expressions.append(Attr('created_at').gte(value))
                elif key == 'created_before' and value:
                    filter_expressions.append(Attr('created_at').lte(value))
            
            if filter_expressions:
                filter_expression = filter_expressions[0]
                for expr in filter_expressions[1:]:
                    filter_expression = filter_expression & expr
                scan_kwargs['FilterExpression'] = filter_expression
        
        # Perform scan
        response = table.scan(**scan_kwargs)
        contracts = [convert_decimal_to_float(item) for item in response['Items']]
        
        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = table.scan(**scan_kwargs)
            contracts.extend([convert_decimal_to_float(item) for item in response['Items']])
        
        logger.info(f"Retrieved {len(contracts)} contracts with filters: {filters}")
        
        return contracts
        
    except ClientError as e:
        logger.error(f"Failed to list contracts: {str(e)}")
        raise


def create_client(client_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new client record"""
    try:
        table = dynamodb.Table(CLIENTS_TABLE)
        
        # Add metadata
        now = datetime.utcnow().isoformat()
        client_data['created_at'] = now
        client_data['updated_at'] = now
        client_data['status'] = client_data.get('status', 'active')
        
        # Convert float values to Decimal
        client_data = convert_floats_to_decimal(client_data)
        
        response = table.put_item(
            Item=client_data,
            ConditionExpression='attribute_not_exists(client_id)'
        )
        
        logger.info(f"Client {client_data['client_id']} created successfully")
        
        return {
            'client_id': client_data['client_id'],
            'status': 'created',
            'created_at': client_data['created_at']
        }
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise ValueError(f"Client {client_data['client_id']} already exists")
        raise


def get_client(client_id: str) -> Optional[Dict[str, Any]]:
    """Get client by ID"""
    try:
        table = dynamodb.Table(CLIENTS_TABLE)
        
        response = table.get_item(Key={'client_id': client_id})
        
        if 'Item' in response:
            client = convert_decimal_to_float(response['Item'])
            logger.info(f"Client {client_id} retrieved successfully")
            return client
        else:
            logger.warning(f"Client {client_id} not found")
            return None
            
    except ClientError as e:
        logger.error(f"Failed to get client {client_id}: {str(e)}")
        raise


def update_client(client_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update client record"""
    try:
        table = dynamodb.Table(CLIENTS_TABLE)
        
        # Prepare update
        updates['updated_at'] = datetime.utcnow().isoformat()
        updates = convert_floats_to_decimal(updates)
        
        # Build update expression
        update_expression_parts = []
        expression_attribute_names = {}
        expression_attribute_values = {}
        
        for key, value in updates.items():
            if key == 'client_id':  # Skip primary key
                continue
                
            placeholder_name = f"#{key}"
            placeholder_value = f":{key}"
            
            update_expression_parts.append(f"{placeholder_name} = {placeholder_value}")
            expression_attribute_names[placeholder_name] = key
            expression_attribute_values[placeholder_value] = value
        
        update_expression = "SET " + ", ".join(update_expression_parts)
        
        response = table.update_item(
            Key={'client_id': client_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ConditionExpression='attribute_exists(client_id)',
            ReturnValues='ALL_NEW'
        )
        
        updated_client = convert_decimal_to_float(response['Attributes'])
        logger.info(f"Client {client_id} updated successfully")
        
        return updated_client
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            raise ValueError(f"Client {client_id} not found")
        raise


def create_audit_log(audit_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create audit log entry"""
    try:
        table = dynamodb.Table(AUDIT_TABLE)
        
        # Generate audit ID
        timestamp = datetime.utcnow()
        audit_id = f"{audit_data['contract_id']}#{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
        
        audit_entry = {
            'audit_id': audit_id,
            'contract_id': audit_data['contract_id'],
            'action': audit_data['action'],
            'details': audit_data.get('details', {}),
            'performed_by': audit_data.get('performed_by', 'system'),
            'timestamp': timestamp.isoformat(),
            'ip_address': audit_data.get('ip_address'),
            'user_agent': audit_data.get('user_agent')
        }
        
        # Convert floats to Decimal
        audit_entry = convert_floats_to_decimal(audit_entry)
        
        response = table.put_item(Item=audit_entry)
        
        logger.info(f"Audit log created: {audit_id}")
        
        return {
            'audit_id': audit_id,
            'status': 'created',
            'timestamp': audit_entry['timestamp']
        }
        
    except ClientError as e:
        logger.error(f"Failed to create audit log: {str(e)}")
        raise


def get_audit_logs(contract_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get audit logs for a contract"""
    try:
        table = dynamodb.Table(AUDIT_TABLE)
        
        response = table.query(
            KeyConditionExpression=Key('contract_id').eq(contract_id),
            ScanIndexForward=False,  # Sort by timestamp descending
            Limit=limit
        )
        
        audit_logs = [convert_decimal_to_float(item) for item in response['Items']]
        logger.info(f"Retrieved {len(audit_logs)} audit logs for contract {contract_id}")
        
        return audit_logs
        
    except ClientError as e:
        logger.error(f"Failed to get audit logs: {str(e)}")
        raise


def convert_floats_to_decimal(obj):
    """Convert float values to Decimal for DynamoDB compatibility"""
    if isinstance(obj, dict):
        return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats_to_decimal(item) for item in obj]
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj


def convert_decimal_to_float(obj):
    """Convert Decimal values to float for JSON serialization"""
    if isinstance(obj, dict):
        return {k: convert_decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_float(item) for item in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


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
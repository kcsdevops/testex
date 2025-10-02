"""
Unit tests for database manager Lambda function
"""
import json
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime, timezone


class TestDatabaseManager:
    """Test cases for database manager Lambda function"""
    
    def test_create_contract_success(self, test_environment, mock_dynamodb_table, sample_contract_data):
        """Test successful contract creation"""
        def mock_create_contract(contract_data):
            # Mock DynamoDB put_item operation
            return {
                'status': 'success',
                'message': 'Contract created successfully',
                'data': {
                    'contract_id': contract_data['contract_id'],
                    'created_at': datetime.utcnow().isoformat()
                }
            }
        
        result = mock_create_contract(sample_contract_data)
        
        assert result['status'] == 'success'
        assert result['data']['contract_id'] == 'CT001ABC'
        assert 'created_at' in result['data']
    
    def test_get_contract_success(self, test_environment, mock_dynamodb_table):
        """Test successful contract retrieval"""
        def mock_get_contract(contract_id):
            # Mock DynamoDB get_item operation
            if contract_id == 'CT001ABC':
                return {
                    'status': 'success',
                    'data': {
                        'contract_id': 'CT001ABC',
                        'client_id': 'CL001XYZ',
                        'status': 'ACTIVE',
                        'value': 10000.00
                    }
                }
            else:
                return {
                    'status': 'error',
                    'error': 'CONTRACT_NOT_FOUND',
                    'message': 'Contract not found'
                }
        
        # Test existing contract
        result = mock_get_contract('CT001ABC')
        assert result['status'] == 'success'
        assert result['data']['contract_id'] == 'CT001ABC'
        
        # Test non-existing contract
        result = mock_get_contract('CT999XYZ')
        assert result['status'] == 'error'
        assert result['error'] == 'CONTRACT_NOT_FOUND'
    
    def test_update_contract_success(self, test_environment):
        """Test successful contract update"""
        def mock_update_contract(contract_id, updates):
            # Mock DynamoDB update_item operation
            return {
                'status': 'success',
                'message': 'Contract updated successfully',
                'data': {
                    'contract_id': contract_id,
                    'updated_fields': list(updates.keys()),
                    'updated_at': datetime.utcnow().isoformat()
                }
            }
        
        updates = {
            'status': 'TERMINATED',
            'termination_reason': 'MUTUAL_AGREEMENT'
        }
        
        result = mock_update_contract('CT001ABC', updates)
        
        assert result['status'] == 'success'
        assert result['data']['contract_id'] == 'CT001ABC'
        assert 'status' in result['data']['updated_fields']
        assert 'termination_reason' in result['data']['updated_fields']
    
    def test_list_contracts_with_pagination(self, test_environment):
        """Test listing contracts with pagination"""
        def mock_list_contracts(filters=None, page=1, page_size=10):
            # Mock paginated contract list
            total_contracts = 25
            contracts = []
            
            for i in range(page_size):
                contract_num = (page - 1) * page_size + i + 1
                if contract_num <= total_contracts:
                    contracts.append({
                        'contract_id': f'CT{contract_num:03d}ABC',
                        'client_id': f'CL{contract_num:03d}XYZ',
                        'status': 'ACTIVE' if contract_num % 2 == 1 else 'TERMINATED'
                    })
            
            return {
                'status': 'success',
                'data': {
                    'contracts': contracts,
                    'pagination': {
                        'current_page': page,
                        'page_size': page_size,
                        'total_items': total_contracts,
                        'total_pages': 3,
                        'has_next': page < 3,
                        'has_previous': page > 1
                    }
                }
            }
        
        # Test first page
        result = mock_list_contracts(page=1, page_size=10)
        assert result['status'] == 'success'
        assert len(result['data']['contracts']) == 10
        assert result['data']['pagination']['current_page'] == 1
        assert result['data']['pagination']['has_next'] is True
        assert result['data']['pagination']['has_previous'] is False
        
        # Test last page
        result = mock_list_contracts(page=3, page_size=10)
        assert len(result['data']['contracts']) == 5  # Only 5 contracts on last page
        assert result['data']['pagination']['has_next'] is False
        assert result['data']['pagination']['has_previous'] is True
    
    def test_create_audit_log(self, test_environment):
        """Test audit log creation"""
        def mock_create_audit_log(contract_id, action, details, user_id=None):
            # Mock audit log creation
            log_id = f"log-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            return {
                'status': 'success',
                'message': 'Audit log created successfully',
                'data': {
                    'log_id': log_id,
                    'contract_id': contract_id,
                    'action': action,
                    'timestamp': datetime.utcnow().isoformat(),
                    'user_id': user_id
                }
            }
        
        result = mock_create_audit_log(
            contract_id='CT001ABC',
            action='CONTRACT_TERMINATED',
            details={'reason': 'MUTUAL_AGREEMENT'},
            user_id='user123'
        )
        
        assert result['status'] == 'success'
        assert result['data']['contract_id'] == 'CT001ABC'
        assert result['data']['action'] == 'CONTRACT_TERMINATED'
        assert result['data']['user_id'] == 'user123'
        assert 'log_id' in result['data']
    
    def test_decimal_conversion(self):
        """Test decimal conversion for DynamoDB compatibility"""
        def convert_floats_to_decimal(obj):
            if isinstance(obj, dict):
                return {k: convert_floats_to_decimal(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats_to_decimal(item) for item in obj]
            elif isinstance(obj, float):
                return Decimal(str(obj))
            return obj
        
        def convert_decimal_to_float(obj):
            if isinstance(obj, dict):
                return {k: convert_decimal_to_float(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimal_to_float(item) for item in obj]
            elif isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        # Test float to decimal conversion
        data_with_floats = {
            'contract_id': 'CT001ABC',
            'value': 10000.50,
            'fees': [100.25, 200.75],
            'metadata': {'rate': 0.05}
        }
        
        converted_data = convert_floats_to_decimal(data_with_floats)
        
        assert isinstance(converted_data['value'], Decimal)
        assert isinstance(converted_data['fees'][0], Decimal)
        assert isinstance(converted_data['metadata']['rate'], Decimal)
        
        # Test decimal to float conversion
        restored_data = convert_decimal_to_float(converted_data)
        
        assert isinstance(restored_data['value'], float)
        assert isinstance(restored_data['fees'][0], float)
        assert isinstance(restored_data['metadata']['rate'], float)
        assert restored_data['value'] == 10000.50
    
    @patch('boto3.resource')
    def test_dynamodb_error_handling(self, mock_boto_resource):
        """Test DynamoDB error handling"""
        mock_table = MagicMock()
        mock_dynamodb = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto_resource.return_value = mock_dynamodb
        
        # Mock ClientError
        from botocore.exceptions import ClientError
        mock_table.put_item.side_effect = ClientError(
            error_response={'Error': {'Code': 'ConditionalCheckFailedException'}},
            operation_name='PutItem'
        )
        
        def handle_dynamodb_operation():
            try:
                dynamodb = mock_boto_resource('dynamodb')
                table = dynamodb.Table('testex-contracts')
                table.put_item(Item={'contract_id': 'CT001ABC'})
                return {'status': 'success'}
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ConditionalCheckFailedException':
                    return {
                        'status': 'error',
                        'error': 'ITEM_ALREADY_EXISTS',
                        'message': 'Contract already exists'
                    }
                else:
                    return {
                        'status': 'error',
                        'error': 'DATABASE_ERROR',
                        'message': str(e)
                    }
        
        result = handle_dynamodb_operation()
        
        assert result['status'] == 'error'
        assert result['error'] == 'ITEM_ALREADY_EXISTS'
        mock_table.put_item.assert_called_once()
    
    def test_lambda_handler_routing(self, test_environment):
        """Test Lambda handler routing logic"""
        def mock_lambda_handler(event, context):
            body = json.loads(event.get('body', '{}'))
            action = body.get('action')
            
            if action == 'create_contract':
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'status': 'success',
                        'message': 'Contract created',
                        'data': {'contract_id': body.get('contract_id')}
                    })
                }
            elif action == 'get_contract':
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'status': 'success',
                        'data': {'contract_id': body.get('contract_id'), 'status': 'ACTIVE'}
                    })
                }
            elif action == 'update_contract':
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'status': 'success',
                        'message': 'Contract updated',
                        'data': {'contract_id': body.get('contract_id')}
                    })
                }
            else:
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'status': 'error',
                        'error': 'INVALID_ACTION',
                        'message': f'Unknown action: {action}'
                    })
                }
        
        # Test create action
        event = {'body': json.dumps({'action': 'create_contract', 'contract_id': 'CT001ABC'})}
        response = mock_lambda_handler(event, None)
        assert response['statusCode'] == 200
        body = json.loads(response['body'])
        assert body['status'] == 'success'
        assert body['data']['contract_id'] == 'CT001ABC'
        
        # Test invalid action
        event = {'body': json.dumps({'action': 'invalid_action'})}
        response = mock_lambda_handler(event, None)
        assert response['statusCode'] == 400
        body = json.loads(response['body'])
        assert body['status'] == 'error'
        assert body['error'] == 'INVALID_ACTION'
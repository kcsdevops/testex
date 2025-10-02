#!/usr/bin/env python3
"""
TESTEX System Test - Verify installation and basic functionality
"""
import sys
import os
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test all required imports"""
    print("🧪 Testing imports...")
    
    try:
        import boto3
        print("  ✅ boto3")
        
        import pydantic
        print("  ✅ pydantic")
        
        import pytest
        print("  ✅ pytest")
        
        import aws_cdk as cdk
        print("  ✅ aws-cdk-lib")
        
        # Test shared modules
        from shared.models import Contract, Client, ContractStatus
        print("  ✅ shared.models")
        
        from shared.utils import setup_logger, get_current_timestamp
        print("  ✅ shared.utils")
        
        from shared.config import Config
        print("  ✅ shared.config")
        
        print("  🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False


def test_models():
    """Test Pydantic models"""
    print("\n🧪 Testing data models...")
    
    try:
        from shared.models import Contract, ContractStatus
        
        # Test contract creation
        contract = Contract(
            contract_id="CT001TEST",
            client_id="CL001TEST",
            contract_type="SERVICE",
            status=ContractStatus.ACTIVE,
            start_date="2025-01-01",
            end_date="2025-12-31",
            value=10000.00
        )
        
        print(f"  ✅ Contract created: {contract.contract_id}")
        print(f"  ✅ Contract status: {contract.status}")
        print(f"  ✅ Contract value: ${contract.value}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Model test error: {e}")
        return False


def test_utilities():
    """Test utility functions"""
    print("\n🧪 Testing utilities...")
    
    try:
        from shared.utils import (
            setup_logger, 
            get_current_timestamp,
            validate_contract_id,
            create_success_response
        )
        
        # Test logger
        logger = setup_logger("test", "INFO")
        print("  ✅ Logger created")
        
        # Test timestamp
        timestamp = get_current_timestamp()
        print(f"  ✅ Timestamp: {timestamp}")
        
        # Test validation
        is_valid = validate_contract_id("CT001TEST")
        print(f"  ✅ Contract ID validation: {is_valid}")
        
        # Test response creation
        response = create_success_response({"test": "data"}, "Test successful")
        print(f"  ✅ Response created: {response['status']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Utility test error: {e}")
        return False


def test_configuration():
    """Test configuration management"""
    print("\n🧪 Testing configuration...")
    
    try:
        from shared.config import Config
        
        # Set test environment variables
        os.environ['ENVIRONMENT'] = 'test'
        os.environ['CONTRACTS_TABLE'] = 'test-contracts'
        os.environ['AWS_REGION'] = 'us-east-1'
        
        config = Config()
        print(f"  ✅ Environment: {config.environment}")
        print(f"  ✅ Debug mode: {config.debug}")
        print(f"  ✅ AWS region: {config.aws_region}")
        
        # Test table name generation
        table_name = config.get_table_name('contracts')
        print(f"  ✅ Table name: {table_name}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration test error: {e}")
        return False


def check_file_structure():
    """Check if all required files exist"""
    print("\n🧪 Checking file structure...")
    
    required_files = [
        'src/contract_processor/handler.py',
        'src/database_manager/handler.py',
        'src/file_handler/handler.py',
        'src/notification_service/handler.py',
        'src/api_gateway/handler.py',
        'src/shared/models/__init__.py',
        'src/shared/utils/__init__.py',
        'src/shared/config/__init__.py',
        'infrastructure/cdk_stack.py',
        'tests/conftest.py',
        'requirements.txt',
        'deploy.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    if missing_files:
        print(f"  ❌ Missing files: {missing_files}")
        return False
    
    print("  🎉 All required files present!")
    return True


def main():
    """Run all tests"""
    print("🚀 TESTEX Lambda System - Installation Test")
    print("=" * 50)
    
    tests = [
        ("File Structure", check_file_structure),
        ("Python Imports", test_imports),
        ("Data Models", test_models),
        ("Utilities", test_utilities),
        ("Configuration", test_configuration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 TESTEX Lambda system is ready for deployment!")
        print("\nNext steps:")
        print("1. Configure AWS credentials: aws configure")
        print("2. Install AWS CDK: npm install -g aws-cdk")
        print("3. Deploy system: python deploy.py --environment development")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please review the errors above.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
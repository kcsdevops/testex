# TESTEX AWS Lambda System

A complete serverless contract termination system built with AWS Lambda, DynamoDB, S3, and SES.

## 🏗️ Architecture

The system consists of 5 main Lambda functions:

- **Contract Processor**: Main business logic for contract termination
- **Database Manager**: DynamoDB operations and data management
- **File Handler**: S3 file operations and document management
- **Notification Service**: SES email notifications
- **API Gateway**: REST API endpoints

## 📁 Project Structure

```
lambda/
├── src/
│   ├── contract_processor/         # Main contract processing logic
│   ├── database_manager/           # DynamoDB operations
│   ├── file_handler/              # S3 file management
│   ├── notification_service/       # Email notifications
│   ├── api_gateway/               # REST API endpoints
│   └── shared/                    # Common utilities and models
│       ├── models/                # Pydantic data models
│       ├── utils/                 # Utility functions
│       └── config/                # Configuration management
├── tests/                         # Unit tests
├── infrastructure/                # AWS CDK infrastructure code
├── templates/                     # Email templates
├── requirements.txt               # Python dependencies
├── deploy.py                     # Deployment script
└── README.md                     # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- AWS CLI configured
- AWS CDK installed
- pip package manager

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd lambda
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r infrastructure/requirements.txt
   ```

3. **Deploy to development environment:**
   ```bash
   python deploy.py --environment development
   ```

## 🔧 Configuration

### Environment Variables

The system uses environment-specific configuration:

```bash
# Development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
SENDER_EMAIL=noreply@testex-dev.com

# Production
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARN
SENDER_EMAIL=noreply@testex.com
```

### AWS Resources

The deployment creates the following AWS resources:

- **DynamoDB Tables:**
  - `{env}-testex-contracts` - Contract data
  - `{env}-testex-clients` - Client information
  - `{env}-testex-audit-logs` - Audit trail

- **S3 Buckets:**
  - `{env}-testex-files` - Contract files
  - `{env}-testex-archives` - Archived documents
  - `{env}-testex-backups` - Data backups
  - `{env}-testex-templates` - Email templates

- **Lambda Functions:**
  - `{env}-testex-contract-processor`
  - `{env}-testex-database-manager`
  - `{env}-testex-file-handler`
  - `{env}-testex-notification-service`
  - `{env}-testex-api-gateway`

## 📊 API Endpoints

### Contracts

```http
GET    /api/contracts              # List contracts
POST   /api/contracts              # Create contract
GET    /api/contracts/{id}         # Get contract
PUT    /api/contracts/{id}         # Update contract
DELETE /api/contracts/{id}         # Delete contract
```

### Files

```http
GET    /api/contracts/{id}/files           # List files
POST   /api/contracts/{id}/files           # Upload file
GET    /api/contracts/{id}/files/{file_id} # Download file
DELETE /api/contracts/{id}/files/{file_id} # Delete file
```

### Notifications

```http
POST   /api/notifications          # Send notification
```

## 🧪 Testing

Run unit tests:

```bash
python -m pytest tests/ -v --cov=src
```

Run specific test file:

```bash
python -m pytest tests/test_contract_processor.py -v
```

## 🚢 Deployment

### Development Environment

```bash
python deploy.py --environment development
```

### Staging Environment

```bash
python deploy.py --environment staging --profile staging-profile
```

### Production Environment

```bash
python deploy.py --environment production --profile production-profile
```

### Deployment Options

```bash
python deploy.py --help

options:
  --environment {development,staging,production}
  --profile PROFILE       AWS profile to use
  --skip-tests           Skip running tests
  --skip-deps            Skip installing dependencies
  --config-only          Only create configuration files
```

## 🔐 Security

- All S3 buckets use server-side encryption
- DynamoDB tables have point-in-time recovery (production)
- Lambda functions have least-privilege IAM roles
- API Gateway includes CORS configuration
- Audit logging for all operations

## 📈 Monitoring

The system includes:

- CloudWatch logs for all Lambda functions
- DynamoDB CloudWatch metrics
- S3 access logging
- Custom metrics for business events

## 🗃️ Data Models

### Contract

```python
{
    "contract_id": "CT001ABC",
    "client_id": "CL001XYZ", 
    "contract_type": "SERVICE",
    "status": "ACTIVE|TERMINATED|SUSPENDED",
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "value": 10000.00,
    "termination_reason": "MUTUAL_AGREEMENT",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
}
```

### Client

```python
{
    "client_id": "CL001XYZ",
    "name": "Client Company",
    "email": "contact@client.com",
    "phone": "+1-555-0123",
    "address": "123 Business St",
    "status": "ACTIVE",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
}
```

## 🔄 Business Process

1. **Contract Processing:**
   - Validate contract data
   - Update contract status
   - Create audit log
   - Backup original data
   - Trigger notifications

2. **File Management:**
   - Upload contract documents
   - Archive old files
   - Backup important documents
   - Manage file lifecycle

3. **Notifications:**
   - Send termination notices
   - Status update emails
   - Approval requests
   - System alerts

## 🛠️ Development

### Adding New Lambda Function

1. Create function directory: `src/new_function/`
2. Add `handler.py` with `lambda_handler` function
3. Update CDK stack in `infrastructure/cdk_stack.py`
4. Add tests in `tests/test_new_function.py`
5. Update deployment script

### Adding New API Endpoint

1. Update `src/api_gateway/handler.py`
2. Add route handling logic
3. Update CDK API Gateway configuration
4. Add tests for new endpoint
5. Update API documentation

## 🐛 Troubleshooting

### Common Issues

1. **Deployment Fails:**
   - Check AWS credentials
   - Verify CDK is bootstrapped
   - Check IAM permissions

2. **Lambda Timeouts:**
   - Increase timeout in CDK stack
   - Optimize function code
   - Check external service latency

3. **DynamoDB Errors:**
   - Check table exists
   - Verify IAM permissions
   - Check item size limits

4. **S3 Upload Failures:**
   - Check bucket permissions
   - Verify file size limits
   - Check network connectivity

### Logs and Debugging

View Lambda logs:

```bash
aws logs tail /aws/lambda/{function-name} --follow
```

Check DynamoDB metrics:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --start-time 2023-01-01T00:00:00Z \
  --end-time 2023-01-01T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Run the test suite
5. Submit a pull request

## 📞 Support

For support and questions:

- Create an issue in the repository
- Check the troubleshooting section
- Review CloudWatch logs for errors

---

**Built with ❤️ using AWS Lambda and Python**
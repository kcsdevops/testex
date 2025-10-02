"""
Infrastructure as Code for TESTEX AWS Lambda system using AWS CDK
"""
import os
from aws_cdk import (
    App,
    Stack,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_ses as ses,
    aws_apigateway as apigateway,
    aws_iam as iam,
    aws_logs as logs,
    CfnOutput
)
from constructs import Construct


class TestexLambdaStack(Stack):
    """Main stack for TESTEX Lambda infrastructure"""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Environment configuration
        self.environment = os.environ.get('ENVIRONMENT', 'development')
        
        # Create DynamoDB tables
        self.create_dynamodb_tables()
        
        # Create S3 buckets
        self.create_s3_buckets()
        
        # Create Lambda functions
        self.create_lambda_functions()
        
        # Create API Gateway
        self.create_api_gateway()
        
        # Create IAM roles and policies
        self.setup_iam_permissions()
        
        # Create CloudWatch log groups
        self.create_log_groups()
        
        # Output important resources
        self.create_outputs()
    
    def create_dynamodb_tables(self):
        """Create DynamoDB tables"""
        # Contracts table
        self.contracts_table = dynamodb.Table(
            self, f"{self.environment}-contracts-table",
            table_name=f"{self.environment}-testex-contracts",
            partition_key=dynamodb.Attribute(
                name="contract_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY if self.environment != 'production' else RemovalPolicy.RETAIN,
            point_in_time_recovery=self.environment == 'production',
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )
        
        # Add global secondary index for client queries
        self.contracts_table.add_global_secondary_index(
            index_name="ClientIndex",
            partition_key=dynamodb.Attribute(
                name="client_id",
                type=dynamodb.AttributeType.STRING
            )
        )
        
        # Add global secondary index for status queries
        self.contracts_table.add_global_secondary_index(
            index_name="StatusIndex",
            partition_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="created_at",
                type=dynamodb.AttributeType.STRING
            )
        )
        
        # Clients table
        self.clients_table = dynamodb.Table(
            self, f"{self.environment}-clients-table",
            table_name=f"{self.environment}-testex-clients",
            partition_key=dynamodb.Attribute(
                name="client_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY if self.environment != 'production' else RemovalPolicy.RETAIN,
            point_in_time_recovery=self.environment == 'production'
        )
        
        # Audit logs table
        self.audit_logs_table = dynamodb.Table(
            self, f"{self.environment}-audit-logs-table",
            table_name=f"{self.environment}-testex-audit-logs",
            partition_key=dynamodb.Attribute(
                name="log_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY if self.environment != 'production' else RemovalPolicy.RETAIN,
            time_to_live_attribute="ttl"  # Auto-delete old logs
        )
        
        # Add global secondary index for contract queries
        self.audit_logs_table.add_global_secondary_index(
            index_name="ContractIndex",
            partition_key=dynamodb.Attribute(
                name="contract_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING
            )
        )
    
    def create_s3_buckets(self):
        """Create S3 buckets"""
        # Files bucket
        self.files_bucket = s3.Bucket(
            self, f"{self.environment}-files-bucket",
            bucket_name=f"{self.environment}-testex-files",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY if self.environment != 'production' else RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldVersions",
                    noncurrent_version_expiration=Duration.days(30),
                    abort_incomplete_multipart_upload_after=Duration.days(7)
                )
            ]
        )
        
        # Archives bucket
        self.archives_bucket = s3.Bucket(
            self, f"{self.environment}-archives-bucket",
            bucket_name=f"{self.environment}-testex-archives",
            versioned=False,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY if self.environment != 'production' else RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="TransitionToIA",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        )
                    ]
                )
            ]
        )
        
        # Backups bucket
        self.backups_bucket = s3.Bucket(
            self, f"{self.environment}-backups-bucket",
            bucket_name=f"{self.environment}-testex-backups",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY if self.environment != 'production' else RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="TransitionToGlacier",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(30)
                        )
                    ]
                )
            ]
        )
        
        # Templates bucket
        self.templates_bucket = s3.Bucket(
            self, f"{self.environment}-templates-bucket",
            bucket_name=f"{self.environment}-testex-templates",
            versioned=False,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY if self.environment != 'production' else RemovalPolicy.RETAIN
        )
    
    def create_lambda_functions(self):
        """Create Lambda functions"""
        # Common Lambda configuration
        lambda_environment = {
            'ENVIRONMENT': self.environment,
            'CONTRACTS_TABLE': self.contracts_table.table_name,
            'CLIENTS_TABLE': self.clients_table.table_name,
            'AUDIT_LOGS_TABLE': self.audit_logs_table.table_name,
            'FILES_BUCKET': self.files_bucket.bucket_name,
            'ARCHIVES_BUCKET': self.archives_bucket.bucket_name,
            'BACKUPS_BUCKET': self.backups_bucket.bucket_name,
            'TEMPLATES_BUCKET': self.templates_bucket.bucket_name,
            'LOG_LEVEL': 'DEBUG' if self.environment == 'development' else 'INFO'
        }
        
        # Lambda layer for common dependencies
        self.lambda_layer = _lambda.LayerVersion(
            self, f"{self.environment}-testex-layer",
            code=_lambda.Code.from_asset("lambda-layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
            description="Common dependencies for TESTEX Lambda functions"
        )
        
        # Contract Processor Lambda
        self.contract_processor = _lambda.Function(
            self, f"{self.environment}-contract-processor",
            function_name=f"{self.environment}-testex-contract-processor",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("src/contract_processor"),
            layers=[self.lambda_layer],
            environment=lambda_environment,
            timeout=Duration.minutes(5),
            memory_size=512,
            reserved_concurrent_executions=10 if self.environment == 'production' else None
        )
        
        # Database Manager Lambda
        self.database_manager = _lambda.Function(
            self, f"{self.environment}-database-manager",
            function_name=f"{self.environment}-testex-database-manager",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("src/database_manager"),
            layers=[self.lambda_layer],
            environment=lambda_environment,
            timeout=Duration.minutes(2),
            memory_size=256,
            reserved_concurrent_executions=20 if self.environment == 'production' else None
        )
        
        # File Handler Lambda
        self.file_handler = _lambda.Function(
            self, f"{self.environment}-file-handler",
            function_name=f"{self.environment}-testex-file-handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("src/file_handler"),
            layers=[self.lambda_layer],
            environment=lambda_environment,
            timeout=Duration.minutes(10),
            memory_size=1024,
            reserved_concurrent_executions=5 if self.environment == 'production' else None
        )
        
        # Notification Service Lambda
        self.notification_service = _lambda.Function(
            self, f"{self.environment}-notification-service",
            function_name=f"{self.environment}-testex-notification-service",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("src/notification_service"),
            layers=[self.lambda_layer],
            environment=lambda_environment,
            timeout=Duration.minutes(3),
            memory_size=256,
            reserved_concurrent_executions=10 if self.environment == 'production' else None
        )
        
        # API Gateway Lambda
        self.api_gateway_lambda = _lambda.Function(
            self, f"{self.environment}-api-gateway",
            function_name=f"{self.environment}-testex-api-gateway",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("src/api_gateway"),
            layers=[self.lambda_layer],
            environment=lambda_environment,
            timeout=Duration.minutes(1),
            memory_size=256,
            reserved_concurrent_executions=50 if self.environment == 'production' else None
        )
        
        # Update environment variables with function names
        function_names = {
            'CONTRACT_PROCESSOR_FUNCTION': self.contract_processor.function_name,
            'DATABASE_MANAGER_FUNCTION': self.database_manager.function_name,
            'FILE_HANDLER_FUNCTION': self.file_handler.function_name,
            'NOTIFICATION_SERVICE_FUNCTION': self.notification_service.function_name,
            'API_GATEWAY_FUNCTION': self.api_gateway_lambda.function_name
        }
        
        # Add function names to all Lambda environments
        for function in [self.contract_processor, self.database_manager, 
                        self.file_handler, self.notification_service, self.api_gateway_lambda]:
            for key, value in function_names.items():
                function.add_environment(key, value)
    
    def create_api_gateway(self):
        """Create API Gateway"""
        self.api = apigateway.RestApi(
            self, f"{self.environment}-testex-api",
            rest_api_name=f"{self.environment}-testex-api",
            description=f"TESTEX API for {self.environment} environment",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"]
            )
        )
        
        # Lambda integration
        api_integration = apigateway.LambdaIntegration(
            self.api_gateway_lambda,
            request_templates={"application/json": '{ "statusCode": "200" }'}
        )
        
        # API routes
        # /api/contracts
        api_resource = self.api.root.add_resource("api")
        contracts_resource = api_resource.add_resource("contracts")
        contracts_resource.add_method("GET", api_integration)  # List contracts
        contracts_resource.add_method("POST", api_integration)  # Create contract
        
        # /api/contracts/{contract_id}
        contract_resource = contracts_resource.add_resource("{contract_id}")
        contract_resource.add_method("GET", api_integration)  # Get contract
        contract_resource.add_method("PUT", api_integration)  # Update contract
        contract_resource.add_method("DELETE", api_integration)  # Delete contract
        
        # /api/contracts/{contract_id}/files
        files_resource = contract_resource.add_resource("files")
        files_resource.add_method("GET", api_integration)  # List files
        files_resource.add_method("POST", api_integration)  # Upload file
        
        # /api/contracts/{contract_id}/files/{file_id}
        file_resource = files_resource.add_resource("{file_id}")
        file_resource.add_method("GET", api_integration)  # Download file
        file_resource.add_method("DELETE", api_integration)  # Delete file
        
        # /api/notifications
        notifications_resource = api_resource.add_resource("notifications")
        notifications_resource.add_method("POST", api_integration)  # Send notification
    
    def setup_iam_permissions(self):
        """Setup IAM roles and policies"""
        # DynamoDB permissions
        for table in [self.contracts_table, self.clients_table, self.audit_logs_table]:
            table.grant_read_write_data(self.contract_processor)
            table.grant_read_write_data(self.database_manager)
            table.grant_read_data(self.file_handler)
            table.grant_read_data(self.notification_service)
            table.grant_read_data(self.api_gateway_lambda)
        
        # S3 permissions
        for bucket in [self.files_bucket, self.archives_bucket, self.backups_bucket, self.templates_bucket]:
            bucket.grant_read_write(self.contract_processor)
            bucket.grant_read_write(self.file_handler)
            bucket.grant_read(self.notification_service)
            bucket.grant_read(self.api_gateway_lambda)
            bucket.grant_read_write(self.database_manager)
        
        # Lambda invoke permissions
        lambda_functions = [self.contract_processor, self.database_manager, 
                          self.file_handler, self.notification_service]
        
        for function in lambda_functions:
            function.grant_invoke(self.contract_processor)
            function.grant_invoke(self.api_gateway_lambda)
        
        # SES permissions
        ses_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "ses:SendEmail",
                "ses:SendRawEmail",
                "ses:GetSendQuota",
                "ses:GetSendStatistics"
            ],
            resources=["*"]
        )
        
        self.notification_service.add_to_role_policy(ses_policy)
        self.contract_processor.add_to_role_policy(ses_policy)
    
    def create_log_groups(self):
        """Create CloudWatch log groups"""
        functions = [
            self.contract_processor,
            self.database_manager,
            self.file_handler,
            self.notification_service,
            self.api_gateway_lambda
        ]
        
        for function in functions:
            logs.LogGroup(
                self, f"{function.function_name}-logs",
                log_group_name=f"/aws/lambda/{function.function_name}",
                retention=logs.RetentionDays.ONE_MONTH if self.environment != 'production' else logs.RetentionDays.ONE_YEAR,
                removal_policy=RemovalPolicy.DESTROY if self.environment != 'production' else RemovalPolicy.RETAIN
            )
    
    def create_outputs(self):
        """Create CloudFormation outputs"""
        CfnOutput(
            self, "ApiGatewayUrl",
            value=self.api.url,
            description="API Gateway URL"
        )
        
        CfnOutput(
            self, "ContractsTableName",
            value=self.contracts_table.table_name,
            description="Contracts DynamoDB table name"
        )
        
        CfnOutput(
            self, "FilesBucketName",
            value=self.files_bucket.bucket_name,
            description="Files S3 bucket name"
        )


def main():
    """Main function to deploy the stack"""
    app = App()
    
    # Get environment from context or environment variable
    environment = app.node.try_get_context("environment") or os.environ.get("ENVIRONMENT", "development")
    
    TestexLambdaStack(
        app, 
        f"TestexLambdaStack-{environment}",
        env={
            'account': os.environ.get('CDK_DEFAULT_ACCOUNT'),
            'region': os.environ.get('CDK_DEFAULT_REGION', 'us-east-1')
        }
    )
    
    app.synth()


if __name__ == "__main__":
    main()
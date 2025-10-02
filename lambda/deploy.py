#!/usr/bin/env python3
"""
TESTEX AWS Lambda Deployment Script
"""
import os
import sys
import json
import subprocess
import argparse
from pathlib import Path


def run_command(command, cwd=None, check=True):
    """Run a shell command"""
    print(f"Running: {command}")
    if isinstance(command, str):
        command = command.split()
    
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check
    )
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result


def check_prerequisites():
    """Check if required tools are installed"""
    tools = ['python', 'pip', 'aws', 'cdk']
    missing_tools = []
    
    for tool in tools:
        try:
            run_command([tool, '--version'], check=False)
        except FileNotFoundError:
            missing_tools.append(tool)
    
    if missing_tools:
        print(f"Missing required tools: {', '.join(missing_tools)}")
        print("Please install the missing tools before proceeding.")
        return False
    
    return True


def install_dependencies():
    """Install Python dependencies"""
    print("Installing Lambda dependencies...")
    run_command(['pip', 'install', '-r', 'requirements.txt'])
    
    print("Installing CDK dependencies...")
    run_command(['pip', 'install', '-r', 'infrastructure/requirements.txt'])


def create_lambda_layer():
    """Create Lambda layer with dependencies"""
    layer_dir = Path('lambda-layer/python')
    layer_dir.mkdir(parents=True, exist_ok=True)
    
    print("Creating Lambda layer...")
    run_command([
        'pip', 'install', 
        '-r', 'requirements.txt',
        '-t', str(layer_dir)
    ])


def package_lambda_functions():
    """Package Lambda functions"""
    functions = [
        'contract_processor',
        'database_manager', 
        'file_handler',
        'notification_service',
        'api_gateway'
    ]
    
    for function in functions:
        src_dir = Path(f'src/{function}')
        if not src_dir.exists():
            print(f"Warning: Function directory {src_dir} not found")
            continue
        
        print(f"Packaging {function}...")
        
        # Copy shared modules to function directory
        shared_dir = Path('src/shared')
        if shared_dir.exists():
            dest_shared = src_dir / 'shared'
            if dest_shared.exists():
                run_command(['rm', '-rf', str(dest_shared)])
            run_command(['cp', '-r', str(shared_dir), str(dest_shared)])


def deploy_infrastructure(environment='development', profile=None):
    """Deploy CDK infrastructure"""
    print(f"Deploying infrastructure for {environment} environment...")
    
    # Set environment variables
    env = os.environ.copy()
    env['ENVIRONMENT'] = environment
    
    # Bootstrap CDK if needed
    bootstrap_cmd = ['cdk', 'bootstrap']
    if profile:
        bootstrap_cmd.extend(['--profile', profile])
    
    try:
        run_command(bootstrap_cmd, cwd='infrastructure', check=False)
    except subprocess.CalledProcessError:
        print("CDK bootstrap already completed or failed (continuing anyway)")
    
    # Deploy stack
    deploy_cmd = [
        'cdk', 'deploy', 
        f'TestexLambdaStack-{environment}',
        '--require-approval', 'never'
    ]
    if profile:
        deploy_cmd.extend(['--profile', profile])
    
    run_command(deploy_cmd, cwd='infrastructure', env=env)


def create_environment_config(environment='development'):
    """Create environment-specific configuration"""
    config = {
        'development': {
            'ENVIRONMENT': 'development',
            'DEBUG': 'true',
            'LOG_LEVEL': 'DEBUG',
            'SENDER_EMAIL': 'noreply@testex-dev.com',
            'MAX_FILE_SIZE': '10485760'  # 10MB
        },
        'staging': {
            'ENVIRONMENT': 'staging',
            'DEBUG': 'false',
            'LOG_LEVEL': 'INFO',
            'SENDER_EMAIL': 'noreply@testex-staging.com',
            'MAX_FILE_SIZE': '10485760'
        },
        'production': {
            'ENVIRONMENT': 'production',
            'DEBUG': 'false',
            'LOG_LEVEL': 'WARN',
            'SENDER_EMAIL': 'noreply@testex.com',
            'MAX_FILE_SIZE': '10485760'
        }
    }
    
    env_config = config.get(environment, config['development'])
    
    # Write to .env file
    env_file = Path(f'.env.{environment}')
    with open(env_file, 'w') as f:
        for key, value in env_config.items():
            f.write(f"{key}={value}\n")
    
    print(f"Created environment configuration: {env_file}")


def run_tests():
    """Run unit tests"""
    print("Running unit tests...")
    try:
        run_command(['python', '-m', 'pytest', 'tests/', '-v', '--cov=src'])
    except subprocess.CalledProcessError:
        print("Some tests failed. Please review the output above.")
        return False
    return True


def upload_email_templates(environment='development'):
    """Upload email templates to S3"""
    bucket_name = f"{environment}-testex-templates"
    templates_dir = Path('templates')
    
    if not templates_dir.exists():
        print("Templates directory not found, creating sample templates...")
        templates_dir.mkdir(exist_ok=True)
        
        # Create sample templates
        termination_template = """
        <html>
        <body>
            <h1>Contract Termination Notice</h1>
            <p>Dear {{client_name}},</p>
            <p>This is to notify you that contract {{contract_id}} has been terminated.</p>
            <p>Termination Date: {{termination_date}}</p>
            <p>Reason: {{termination_reason}}</p>
            <p>Best regards,<br>TESTEX System</p>
        </body>
        </html>
        """
        
        status_template = """
        <html>
        <body>
            <h1>Contract Status Update</h1>
            <p>Dear {{client_name}},</p>
            <p>The status of contract {{contract_id}} has been updated to: {{status}}</p>
            <p>Update Date: {{update_date}}</p>
            <p>Best regards,<br>TESTEX System</p>
        </body>
        </html>
        """
        
        with open(templates_dir / 'termination_notice.html', 'w') as f:
            f.write(termination_template)
        
        with open(templates_dir / 'status_update.html', 'w') as f:
            f.write(status_template)
    
    # Upload templates to S3
    for template_file in templates_dir.glob('*.html'):
        print(f"Uploading template: {template_file.name}")
        run_command([
            'aws', 's3', 'cp',
            str(template_file),
            f's3://{bucket_name}/email-templates/{template_file.name}',
            '--content-type', 'text/html'
        ])


def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description='Deploy TESTEX Lambda system')
    parser.add_argument('--environment', '-e', default='development',
                       choices=['development', 'staging', 'production'],
                       help='Deployment environment')
    parser.add_argument('--profile', '-p', help='AWS profile to use')
    parser.add_argument('--skip-tests', action='store_true',
                       help='Skip running tests')
    parser.add_argument('--skip-deps', action='store_true',
                       help='Skip installing dependencies')
    parser.add_argument('--config-only', action='store_true',
                       help='Only create configuration files')
    
    args = parser.parse_args()
    
    print(f"Deploying TESTEX Lambda system to {args.environment} environment")
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Create configuration
    create_environment_config(args.environment)
    
    if args.config_only:
        print("Configuration files created. Exiting.")
        return
    
    # Install dependencies
    if not args.skip_deps:
        install_dependencies()
    
    # Run tests
    if not args.skip_tests:
        if not run_tests():
            response = input("Tests failed. Continue with deployment? (y/N): ")
            if response.lower() != 'y':
                print("Deployment cancelled.")
                sys.exit(1)
    
    # Create Lambda layer
    create_lambda_layer()
    
    # Package functions
    package_lambda_functions()
    
    # Deploy infrastructure
    deploy_infrastructure(args.environment, args.profile)
    
    # Upload templates
    upload_email_templates(args.environment)
    
    print(f"\nDeployment to {args.environment} completed successfully!")
    print("\nNext steps:")
    print("1. Configure SES email verification")
    print("2. Set up API Gateway custom domain (optional)")
    print("3. Configure monitoring and alerts")
    print("4. Test the deployed functions")


if __name__ == "__main__":
    main()
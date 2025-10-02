"""
Notification Service Lambda
Handles email notifications using AWS SES for the TESTEX system
"""
import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS clients
ses_client = boto3.client('ses')
s3_client = boto3.client('s3')

# Environment variables
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@testex.com')
TEMPLATE_BUCKET = os.environ.get('TEMPLATE_BUCKET', 'testex-templates')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')


def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    Main Lambda handler for notification service
    
    Args:
        event: Lambda event containing notification details
        context: Lambda context object
        
    Returns:
        Response dictionary with notification results
    """
    try:
        logger.info(f"Notification request: {json.dumps(event, default=str)}")
        
        # Extract notification details
        notification_type = event.get('type', 'general')
        recipients = event.get('recipients', [])
        template = event.get('template')
        data = event.get('contract_data', {})
        
        # Validate inputs
        if not recipients:
            return create_response(400, {
                'error': 'No recipients specified'
            })
        
        # Route to appropriate handler
        if notification_type == 'contract_termination':
            result = send_contract_termination_notification(recipients, data, template)
        elif notification_type == 'status_update':
            result = send_status_update_notification(recipients, data, template)
        elif notification_type == 'approval_request':
            result = send_approval_request_notification(recipients, data, template)
        elif notification_type == 'completion':
            result = send_completion_notification(recipients, data, template)
        elif notification_type == 'error_alert':
            result = send_error_alert_notification(recipients, data, template)
        elif notification_type == 'reminder':
            result = send_reminder_notification(recipients, data, template)
        else:
            result = send_generic_notification(recipients, data, template)
        
        logger.info(f"Notification {notification_type} sent successfully")
        
        return create_response(200, {
            'notification_type': notification_type,
            'recipients_count': len(recipients),
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return create_response(500, {
            'error': 'Notification failed',
            'message': str(e)
        })


def send_contract_termination_notification(recipients: List[str], data: Dict[str, Any], template: str = None) -> Dict[str, Any]:
    """Send contract termination notification"""
    
    contract_id = data.get('contract_id', 'N/A')
    client_id = data.get('client_id', 'N/A')
    termination_type = data.get('termination_type', 'N/A')
    
    subject = f"Contract Termination Started - {contract_id}"
    
    if template:
        html_body, text_body = load_email_template(template, data)
    else:
        html_body = f"""
        <html>
        <head></head>
        <body>
            <h2>Contract Termination Notification</h2>
            <p>A contract termination process has been initiated with the following details:</p>
            
            <table border="1" cellpadding="5" cellspacing="0">
                <tr><td><strong>Contract ID:</strong></td><td>{contract_id}</td></tr>
                <tr><td><strong>Client ID:</strong></td><td>{client_id}</td></tr>
                <tr><td><strong>Termination Type:</strong></td><td>{termination_type}</td></tr>
                <tr><td><strong>Requested By:</strong></td><td>{data.get('requested_by', 'System')}</td></tr>
                <tr><td><strong>Date:</strong></td><td>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</td></tr>
            </table>
            
            <p>The termination process is now in progress. You will receive updates as the process continues.</p>
            
            <p><em>This is an automated message from the TESTEX Contract Management System.</em></p>
        </body>
        </html>
        """
        
        text_body = f"""
        Contract Termination Notification
        
        A contract termination process has been initiated:
        
        Contract ID: {contract_id}
        Client ID: {client_id}
        Termination Type: {termination_type}
        Requested By: {data.get('requested_by', 'System')}
        Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        
        The termination process is now in progress. You will receive updates as the process continues.
        
        This is an automated message from the TESTEX Contract Management System.
        """
    
    return send_email(recipients, subject, html_body, text_body)


def send_status_update_notification(recipients: List[str], data: Dict[str, Any], template: str = None) -> Dict[str, Any]:
    """Send status update notification"""
    
    contract_id = data.get('contract_id', 'N/A')
    status = data.get('status', 'N/A')
    
    subject = f"Contract Status Update - {contract_id}"
    
    if template:
        html_body, text_body = load_email_template(template, data)
    else:
        html_body = f"""
        <html>
        <head></head>
        <body>
            <h2>Contract Status Update</h2>
            <p>The status of contract <strong>{contract_id}</strong> has been updated:</p>
            
            <p><strong>New Status:</strong> {status}</p>
            <p><strong>Updated At:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            
            {generate_processing_details_html(data.get('processing_details', {}))}
            
            <p><em>This is an automated message from the TESTEX Contract Management System.</em></p>
        </body>
        </html>
        """
        
        text_body = f"""
        Contract Status Update
        
        The status of contract {contract_id} has been updated:
        
        New Status: {status}
        Updated At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
        
        {generate_processing_details_text(data.get('processing_details', {}))}
        
        This is an automated message from the TESTEX Contract Management System.
        """
    
    return send_email(recipients, subject, html_body, text_body)


def send_approval_request_notification(recipients: List[str], data: Dict[str, Any], template: str = None) -> Dict[str, Any]:
    """Send approval request notification"""
    
    contract_id = data.get('contract_id', 'N/A')
    approval_type = data.get('approval_type', 'Contract Termination')
    
    subject = f"Approval Required - {approval_type} - {contract_id}"
    
    if template:
        html_body, text_body = load_email_template(template, data)
    else:
        html_body = f"""
        <html>
        <head></head>
        <body>
            <h2>Approval Required</h2>
            <p>Your approval is required for the following action:</p>
            
            <table border="1" cellpadding="5" cellspacing="0">
                <tr><td><strong>Contract ID:</strong></td><td>{contract_id}</td></tr>
                <tr><td><strong>Action:</strong></td><td>{approval_type}</td></tr>
                <tr><td><strong>Requested By:</strong></td><td>{data.get('requested_by', 'System')}</td></tr>
                <tr><td><strong>Priority:</strong></td><td>{data.get('priority', 'Normal')}</td></tr>
            </table>
            
            <p><strong>Next Steps:</strong></p>
            <ul>
                <li>Review the contract termination details</li>
                <li>Access the TESTEX dashboard to approve or reject</li>
                <li>Provide any necessary comments</li>
            </ul>
            
            <p><em>This approval request was generated automatically by the TESTEX system.</em></p>
        </body>
        </html>
        """
        
        text_body = f"""
        Approval Required
        
        Your approval is required for the following action:
        
        Contract ID: {contract_id}
        Action: {approval_type}
        Requested By: {data.get('requested_by', 'System')}
        Priority: {data.get('priority', 'Normal')}
        
        Next Steps:
        - Review the contract termination details
        - Access the TESTEX dashboard to approve or reject
        - Provide any necessary comments
        
        This approval request was generated automatically by the TESTEX system.
        """
    
    return send_email(recipients, subject, html_body, text_body)


def send_completion_notification(recipients: List[str], data: Dict[str, Any], template: str = None) -> Dict[str, Any]:
    """Send completion notification"""
    
    contract_id = data.get('contract_id', 'N/A')
    
    subject = f"Contract Termination Completed - {contract_id}"
    
    if template:
        html_body, text_body = load_email_template(template, data)
    else:
        completion_date = data.get('completion_date', datetime.utcnow().isoformat())
        
        html_body = f"""
        <html>
        <head></head>
        <body>
            <h2>Contract Termination Completed</h2>
            <p>The contract termination process has been completed successfully:</p>
            
            <table border="1" cellpadding="5" cellspacing="0">
                <tr><td><strong>Contract ID:</strong></td><td>{contract_id}</td></tr>
                <tr><td><strong>Completion Date:</strong></td><td>{completion_date}</td></tr>
                <tr><td><strong>Final Status:</strong></td><td>{data.get('final_status', 'Terminated')}</td></tr>
            </table>
            
            <h3>Summary:</h3>
            <ul>
                <li>All required approvals obtained</li>
                <li>Files archived successfully</li>
                <li>Notifications sent to all stakeholders</li>
                <li>Audit trail completed</li>
            </ul>
            
            <p>All contract termination activities have been completed. The contract is now officially terminated.</p>
            
            <p><em>This is an automated completion notification from the TESTEX system.</em></p>
        </body>
        </html>
        """
        
        text_body = f"""
        Contract Termination Completed
        
        The contract termination process has been completed successfully:
        
        Contract ID: {contract_id}
        Completion Date: {completion_date}
        Final Status: {data.get('final_status', 'Terminated')}
        
        Summary:
        - All required approvals obtained
        - Files archived successfully
        - Notifications sent to all stakeholders
        - Audit trail completed
        
        All contract termination activities have been completed. The contract is now officially terminated.
        
        This is an automated completion notification from the TESTEX system.
        """
    
    return send_email(recipients, subject, html_body, text_body)


def send_error_alert_notification(recipients: List[str], data: Dict[str, Any], template: str = None) -> Dict[str, Any]:
    """Send error alert notification"""
    
    contract_id = data.get('contract_id', 'N/A')
    error_message = data.get('error_message', 'Unknown error')
    
    subject = f"ALERT: Contract Processing Error - {contract_id}"
    
    html_body = f"""
    <html>
    <head></head>
    <body>
        <h2 style="color: red;">Contract Processing Error Alert</h2>
        <p>An error occurred during contract processing:</p>
        
        <table border="1" cellpadding="5" cellspacing="0">
            <tr><td><strong>Contract ID:</strong></td><td>{contract_id}</td></tr>
            <tr><td><strong>Error:</strong></td><td style="color: red;">{error_message}</td></tr>
            <tr><td><strong>Timestamp:</strong></td><td>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</td></tr>
            <tr><td><strong>Processing Step:</strong></td><td>{data.get('processing_step', 'Unknown')}</td></tr>
        </table>
        
        <p><strong>Immediate Action Required:</strong></p>
        <ul>
            <li>Review the error details</li>
            <li>Check system logs for additional information</li>
            <li>Determine if manual intervention is needed</li>
            <li>Contact system administrator if necessary</li>
        </ul>
        
        <p><em>This is an automated error alert from the TESTEX system.</em></p>
    </body>
    </html>
    """
    
    text_body = f"""
    CONTRACT PROCESSING ERROR ALERT
    
    An error occurred during contract processing:
    
    Contract ID: {contract_id}
    Error: {error_message}
    Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
    Processing Step: {data.get('processing_step', 'Unknown')}
    
    IMMEDIATE ACTION REQUIRED:
    - Review the error details
    - Check system logs for additional information
    - Determine if manual intervention is needed
    - Contact system administrator if necessary
    
    This is an automated error alert from the TESTEX system.
    """
    
    return send_email(recipients, subject, html_body, text_body, priority='high')


def send_reminder_notification(recipients: List[str], data: Dict[str, Any], template: str = None) -> Dict[str, Any]:
    """Send reminder notification"""
    
    contract_id = data.get('contract_id', 'N/A')
    reminder_type = data.get('reminder_type', 'General')
    
    subject = f"Reminder: {reminder_type} - {contract_id}"
    
    html_body = f"""
    <html>
    <head></head>
    <body>
        <h2>Reminder: {reminder_type}</h2>
        <p>This is a reminder regarding contract {contract_id}:</p>
        
        <p><strong>Message:</strong> {data.get('message', 'No specific message provided.')}</p>
        <p><strong>Due Date:</strong> {data.get('due_date', 'Not specified')}</p>
        
        <p>Please take appropriate action as needed.</p>
        
        <p><em>This is an automated reminder from the TESTEX system.</em></p>
    </body>
    </html>
    """
    
    text_body = f"""
    Reminder: {reminder_type}
    
    This is a reminder regarding contract {contract_id}:
    
    Message: {data.get('message', 'No specific message provided.')}
    Due Date: {data.get('due_date', 'Not specified')}
    
    Please take appropriate action as needed.
    
    This is an automated reminder from the TESTEX system.
    """
    
    return send_email(recipients, subject, html_body, text_body)


def send_generic_notification(recipients: List[str], data: Dict[str, Any], template: str = None) -> Dict[str, Any]:
    """Send generic notification"""
    
    subject = data.get('subject', 'TESTEX System Notification')
    message = data.get('message', 'No message content provided.')
    
    html_body = f"""
    <html>
    <head></head>
    <body>
        <h2>TESTEX System Notification</h2>
        <p>{message}</p>
        
        <p><em>This is an automated notification from the TESTEX system.</em></p>
    </body>
    </html>
    """
    
    text_body = f"""
    TESTEX System Notification
    
    {message}
    
    This is an automated notification from the TESTEX system.
    """
    
    return send_email(recipients, subject, html_body, text_body)


def send_email(recipients: List[str], subject: str, html_body: str, text_body: str, priority: str = 'normal') -> Dict[str, Any]:
    """Send email using AWS SES"""
    try:
        # Prepare email
        message = {
            'Subject': {'Data': subject, 'Charset': 'UTF-8'},
            'Body': {
                'Html': {'Data': html_body, 'Charset': 'UTF-8'},
                'Text': {'Data': text_body, 'Charset': 'UTF-8'}
            }
        }
        
        # Set priority headers
        headers = {}
        if priority == 'high':
            headers['X-Priority'] = '1'
            headers['X-MSMail-Priority'] = 'High'
            headers['Importance'] = 'High'
        
        sent_results = []
        failed_results = []
        
        # Send to each recipient
        for recipient in recipients:
            try:
                response = ses_client.send_email(
                    Source=FROM_EMAIL,
                    Destination={'ToAddresses': [recipient]},
                    Message=message
                )
                
                sent_results.append({
                    'recipient': recipient,
                    'message_id': response['MessageId'],
                    'status': 'sent'
                })
                
                logger.info(f"Email sent to {recipient}, MessageId: {response['MessageId']}")
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                
                failed_results.append({
                    'recipient': recipient,
                    'error_code': error_code,
                    'error_message': error_message,
                    'status': 'failed'
                })
                
                logger.error(f"Failed to send email to {recipient}: {error_code} - {error_message}")
        
        return {
            'status': 'completed',
            'total_recipients': len(recipients),
            'sent_count': len(sent_results),
            'failed_count': len(failed_results),
            'sent_results': sent_results,
            'failed_results': failed_results
        }
        
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        raise


def load_email_template(template_name: str, data: Dict[str, Any]) -> tuple:
    """Load email template from S3 and replace placeholders"""
    try:
        # Load HTML template
        html_key = f"templates/{template_name}.html"
        html_response = s3_client.get_object(Bucket=TEMPLATE_BUCKET, Key=html_key)
        html_template = html_response['Body'].read().decode('utf-8')
        
        # Load text template
        text_key = f"templates/{template_name}.txt"
        try:
            text_response = s3_client.get_object(Bucket=TEMPLATE_BUCKET, Key=text_key)
            text_template = text_response['Body'].read().decode('utf-8')
        except ClientError:
            # Generate simple text version from HTML if text template doesn't exist
            text_template = html_template.replace('<br>', '\n').replace('<p>', '\n').replace('</p>', '\n')
            # Remove HTML tags
            import re
            text_template = re.sub('<[^<]+?>', '', text_template)
        
        # Replace placeholders
        html_body = replace_template_placeholders(html_template, data)
        text_body = replace_template_placeholders(text_template, data)
        
        return html_body, text_body
        
    except ClientError as e:
        logger.warning(f"Failed to load template {template_name}: {str(e)}")
        # Return empty templates if loading fails
        return "", ""


def replace_template_placeholders(template: str, data: Dict[str, Any]) -> str:
    """Replace placeholders in template with actual data"""
    try:
        # Replace common placeholders
        replacements = {
            '{{contract_id}}': data.get('contract_id', 'N/A'),
            '{{client_id}}': data.get('client_id', 'N/A'),
            '{{termination_type}}': data.get('termination_type', 'N/A'),
            '{{requested_by}}': data.get('requested_by', 'System'),
            '{{current_date}}': datetime.utcnow().strftime('%Y-%m-%d'),
            '{{current_datetime}}': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S') + ' UTC',
            '{{status}}': data.get('status', 'N/A')
        }
        
        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, str(value))
        
        return result
        
    except Exception as e:
        logger.warning(f"Failed to replace template placeholders: {str(e)}")
        return template


def generate_processing_details_html(details: Dict[str, Any]) -> str:
    """Generate HTML for processing details"""
    if not details:
        return ""
    
    html = "<h3>Processing Details:</h3><ul>"
    
    steps = details.get('steps', [])
    for step in steps:
        status_color = "green" if step.get('status') == 'completed' else "red"
        html += f"<li><strong>{step.get('step', 'Unknown')}:</strong> "
        html += f"<span style='color: {status_color};'>{step.get('status', 'Unknown')}</span>"
        html += f" ({step.get('timestamp', 'N/A')})</li>"
    
    html += "</ul>"
    return html


def generate_processing_details_text(details: Dict[str, Any]) -> str:
    """Generate text for processing details"""
    if not details:
        return ""
    
    text = "Processing Details:\n"
    
    steps = details.get('steps', [])
    for step in steps:
        text += f"- {step.get('step', 'Unknown')}: {step.get('status', 'Unknown')} ({step.get('timestamp', 'N/A')})\n"
    
    return text


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
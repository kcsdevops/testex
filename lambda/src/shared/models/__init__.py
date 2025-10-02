"""
Shared data models for the TESTEX system
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class ContractStatus(str, Enum):
    """Contract status enumeration"""
    ACTIVE = "active"
    PROCESSING = "processing"
    TERMINATED = "terminated"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class TerminationType(str, Enum):
    """Contract termination type enumeration"""
    VOLUNTARY = "voluntary"
    INVOLUNTARY = "involuntary"
    EXPIRED = "expired"
    BREACH = "breach"


class ProcessingStatus(str, Enum):
    """Processing step status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class NotificationType(str, Enum):
    """Notification type enumeration"""
    CONTRACT_TERMINATION = "contract_termination"
    STATUS_UPDATE = "status_update"
    APPROVAL_REQUEST = "approval_request"
    COMPLETION = "completion"
    ERROR_ALERT = "error_alert"
    REMINDER = "reminder"
    GENERAL = "general"


class ProcessingStep(BaseModel):
    """Processing step model"""
    step: str = Field(..., description="Step name")
    status: ProcessingStatus = Field(..., description="Step status")
    timestamp: str = Field(..., description="Step timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional step details")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class ProcessingDetails(BaseModel):
    """Contract processing details model"""
    contract_id: str = Field(..., description="Contract ID")
    termination_type: TerminationType = Field(..., description="Type of termination")
    steps: List[ProcessingStep] = Field(default_factory=list, description="Processing steps")
    final_status: str = Field(..., description="Final processing status")
    started_at: Optional[str] = Field(None, description="Processing start timestamp")
    completed_at: Optional[str] = Field(None, description="Processing completion timestamp")


class FileInfo(BaseModel):
    """File information model"""
    name: str = Field(..., description="File name")
    s3_key: Optional[str] = Field(None, description="S3 object key")
    bucket: Optional[str] = Field(None, description="S3 bucket name")
    size: Optional[int] = Field(None, description="File size in bytes")
    type: Optional[str] = Field(None, description="MIME type")
    uploaded_at: Optional[str] = Field(None, description="Upload timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class Contract(BaseModel):
    """Contract model"""
    contract_id: str = Field(..., pattern=r'^CT[A-Z0-9]+$', description="Contract ID (format: CT followed by alphanumeric)")
    client_id: str = Field(..., pattern=r'^CL[A-Z0-9]+$', description="Client ID (format: CL followed by alphanumeric)")
    status: ContractStatus = Field(ContractStatus.ACTIVE, description="Contract status")
    
    # Contract details
    title: Optional[str] = Field(None, description="Contract title")
    description: Optional[str] = Field(None, description="Contract description")
    start_date: Optional[str] = Field(None, description="Contract start date")
    end_date: Optional[str] = Field(None, description="Contract end date")
    value: Optional[float] = Field(None, description="Contract value")
    currency: Optional[str] = Field("USD", description="Currency code")
    
    # Termination details
    termination_type: Optional[TerminationType] = Field(None, description="Type of termination")
    termination_reason: Optional[str] = Field(None, description="Reason for termination")
    termination_date: Optional[str] = Field(None, description="Termination date")
    effective_date: Optional[str] = Field(None, description="Effective termination date")
    notice_period_days: Optional[int] = Field(30, description="Notice period in days")
    penalty_amount: Optional[float] = Field(0, description="Penalty amount")
    refund_amount: Optional[float] = Field(0, description="Refund amount")
    
    # Processing information
    processing_details: Optional[ProcessingDetails] = Field(None, description="Processing details")
    
    # Files
    files_uploaded: Optional[List[FileInfo]] = Field(None, description="Uploaded files")
    files_archived: Optional[List[Dict[str, Any]]] = Field(None, description="Archived files")
    files_deleted: Optional[List[Dict[str, Any]]] = Field(None, description="Deleted files")
    
    # Metadata
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Created by user")
    updated_by: Optional[str] = Field(None, description="Updated by user")
    requested_by: Optional[str] = Field(None, description="Termination requested by")
    
    # Audit fields
    created_from_ip: Optional[str] = Field(None, description="IP address of creation")
    updated_from_ip: Optional[str] = Field(None, description="IP address of last update")
    user_agent: Optional[str] = Field(None, description="User agent")
    
    # Notification settings
    notification_emails: Optional[List[str]] = Field(None, description="Email addresses for notifications")
    
    @validator('contract_id')
    def validate_contract_id(cls, v):
        if not v.startswith('CT'):
            raise ValueError('Contract ID must start with CT')
        return v.upper()
    
    @validator('client_id')
    def validate_client_id(cls, v):
        if not v.startswith('CL'):
            raise ValueError('Client ID must start with CL')
        return v.upper()


class Client(BaseModel):
    """Client model"""
    client_id: str = Field(..., pattern=r'^CL[A-Z0-9]+$', description="Client ID")
    name: str = Field(..., description="Client name")
    email: str = Field(
        ..., 
        description="Client email address",
        pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    phone: Optional[str] = Field(None, description="Phone number")
    address: Optional[str] = Field(None, description="Address")
    
    # Company details
    company_name: Optional[str] = Field(None, description="Company name")
    tax_id: Optional[str] = Field(None, description="Tax ID")
    industry: Optional[str] = Field(None, description="Industry")
    
    # Contact details
    primary_contact_name: Optional[str] = Field(None, description="Primary contact person")
    primary_contact_email: Optional[str] = Field(None, description="Primary contact email")
    primary_contact_phone: Optional[str] = Field(None, description="Primary contact phone")
    
    # Status
    status: str = Field("active", description="Client status")
    
    # Metadata
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    created_by: Optional[str] = Field(None, description="Created by user")


class AuditLog(BaseModel):
    """Audit log model"""
    audit_id: str = Field(..., description="Audit log ID")
    contract_id: str = Field(..., description="Contract ID")
    action: str = Field(..., description="Action performed")
    details: Optional[Dict[str, Any]] = Field(None, description="Action details")
    performed_by: str = Field(..., description="User who performed the action")
    timestamp: str = Field(..., description="Action timestamp")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent")


class NotificationRequest(BaseModel):
    """Notification request model"""
    type: NotificationType = Field(..., description="Notification type")
    recipients: List[str] = Field(..., description="Email recipients")
    template: Optional[str] = Field(None, description="Email template name")
    contract_data: Optional[Dict[str, Any]] = Field(None, description="Contract data for templates")
    subject: Optional[str] = Field(None, description="Custom subject line")
    message: Optional[str] = Field(None, description="Custom message content")
    priority: Optional[str] = Field("normal", description="Priority level")


class FileOperation(BaseModel):
    """File operation model"""
    action: str = Field(..., description="File operation action")
    contract_id: str = Field(..., description="Contract ID")
    files: Optional[List[Dict[str, Any]]] = Field(None, description="Files to operate on")
    permanent: Optional[bool] = Field(False, description="Permanent deletion flag")
    include_deleted: Optional[bool] = Field(False, description="Include deleted files flag")


class APIResponse(BaseModel):
    """Standard API response model"""
    status: str = Field(..., description="Response status")
    message: Optional[str] = Field(None, description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")


class DatabaseOperation(BaseModel):
    """Database operation model"""
    operation: str = Field(..., description="Database operation")
    table: Optional[str] = Field(None, description="Target table")
    data: Dict[str, Any] = Field(..., description="Operation data")


class LambdaEvent(BaseModel):
    """Generic Lambda event model"""
    source: Optional[str] = Field(None, description="Event source")
    detail_type: Optional[str] = Field(None, description="Event detail type")
    detail: Optional[Dict[str, Any]] = Field(None, description="Event details")
    resources: Optional[List[str]] = Field(None, description="Event resources")
    account: Optional[str] = Field(None, description="AWS account ID")
    region: Optional[str] = Field(None, description="AWS region")
    time: Optional[str] = Field(None, description="Event timestamp")


# Validation schemas for API requests
class ContractTerminationRequest(BaseModel):
    """Contract termination request schema"""
    contract_id: str = Field(..., description="Contract ID to terminate")
    client_id: str = Field(..., description="Client ID")
    termination_type: TerminationType = Field(..., description="Type of termination")
    termination_reason: Optional[str] = Field(None, description="Reason for termination")
    effective_date: Optional[str] = Field(None, description="Effective termination date")
    requested_by: str = Field(..., description="User requesting termination")
    notification_emails: Optional[List[str]] = Field(None, description="Email addresses for notifications")
    files: Optional[List[Dict[str, Any]]] = Field(None, description="Files to process")


class ContractUpdateRequest(BaseModel):
    """Contract update request schema"""
    title: Optional[str] = Field(None, description="Contract title")
    description: Optional[str] = Field(None, description="Contract description")
    status: Optional[ContractStatus] = Field(None, description="Contract status")
    end_date: Optional[str] = Field(None, description="Contract end date")
    value: Optional[float] = Field(None, description="Contract value")
    notification_emails: Optional[List[str]] = Field(None, description="Notification emails")
    updated_by: Optional[str] = Field(None, description="User making the update")


class FileUploadRequest(BaseModel):
    """File upload request schema"""
    files: List[Dict[str, Any]] = Field(..., description="Files to upload")
    
    class Config:
        schema_extra = {
            "example": {
                "files": [
                    {
                        "name": "contract_document.pdf",
                        "content": "base64_encoded_content",
                        "type": "application/pdf"
                    }
                ]
            }
        }


# Error models
class ValidationError(BaseModel):
    """Validation error model"""
    field: str = Field(..., description="Field with validation error")
    message: str = Field(..., description="Validation error message")
    value: Optional[Any] = Field(None, description="Invalid value")


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[List[ValidationError]] = Field(None, description="Validation error details")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
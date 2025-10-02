```mermaid
graph TB
    %% External inputs
    Client[👤 Client/User]
    Admin[👨‍💼 Administrator]
    System[🖥️ External Systems]
    
    %% API Gateway
    API[🌐 API Gateway<br/>REST Endpoints]
    
    %% Lambda Functions
    ApiLambda[⚡ API Gateway Lambda<br/>Route & Validate Requests]
    ContractProc[⚡ Contract Processor<br/>Business Logic]
    DbManager[⚡ Database Manager<br/>CRUD Operations]
    FileHandler[⚡ File Handler<br/>S3 Operations]
    NotificationSvc[⚡ Notification Service<br/>Email System]
    
    %% AWS Services
    DynamoDB[(🗄️ DynamoDB<br/>Contracts, Clients,<br/>Audit Logs)]
    S3Files[(📁 S3 Files Bucket<br/>Contract Documents)]
    S3Archives[(📦 S3 Archives Bucket<br/>Archived Files)]
    S3Backups[(💾 S3 Backups Bucket<br/>Data Backups)]
    S3Templates[(📄 S3 Templates Bucket<br/>Email Templates)]
    SES[📧 Amazon SES<br/>Email Service]
    CloudWatch[📊 CloudWatch<br/>Logs & Monitoring]
    
    %% External outputs
    Email[📧 Email Recipients]
    
    %% User interactions
    Client --> API
    Admin --> API
    System --> API
    
    %% API Gateway routing
    API --> ApiLambda
    
    %% API Lambda routing to other functions
    ApiLambda -->|Contract Operations| ContractProc
    ApiLambda -->|Database Operations| DbManager
    ApiLambda -->|File Operations| FileHandler
    ApiLambda -->|Send Notifications| NotificationSvc
    
    %% Contract Processor flows
    ContractProc -->|Validate & Process| DbManager
    ContractProc -->|Backup Data| FileHandler
    ContractProc -->|Send Notifications| NotificationSvc
    ContractProc -->|Log Activity| DbManager
    
    %% Database Manager connections
    DbManager <--> DynamoDB
    DbManager --> CloudWatch
    
    %% File Handler connections
    FileHandler <--> S3Files
    FileHandler <--> S3Archives
    FileHandler <--> S3Backups
    FileHandler --> CloudWatch
    FileHandler -->|Update Metadata| DbManager
    
    %% Notification Service connections
    NotificationSvc <--> S3Templates
    NotificationSvc --> SES
    NotificationSvc --> CloudWatch
    NotificationSvc -->|Log Notifications| DbManager
    
    %% SES to recipients
    SES --> Email
    
    %% All Lambda functions log to CloudWatch
    ApiLambda --> CloudWatch
    ContractProc --> CloudWatch
    
    %% Styling
    classDef lambda fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef aws fill:#232F3E,stroke:#FF9900,stroke-width:2px,color:#fff
    classDef user fill:#4CAF50,stroke:#2E7D32,stroke-width:2px,color:#fff
    classDef storage fill:#1976D2,stroke:#0D47A1,stroke-width:2px,color:#fff
    classDef external fill:#9C27B0,stroke:#4A148C,stroke-width:2px,color:#fff
    
    class ApiLambda,ContractProc,DbManager,FileHandler,NotificationSvc lambda
    class API,SES,CloudWatch aws
    class Client,Admin,System user
    class DynamoDB,S3Files,S3Archives,S3Backups,S3Templates storage
    class Email external
```

# TESTEX System Architecture Flowchart

## 🏗️ System Components Overview

### 📱 **User Interfaces**
- **Client/User**: End users accessing contract services
- **Administrator**: System administrators managing contracts
- **External Systems**: Third-party integrations

### 🌐 **API Layer**
- **API Gateway**: Main entry point for all requests
- **API Gateway Lambda**: Request routing and validation

### ⚡ **Core Lambda Functions**
1. **Contract Processor**: Main business logic for contract operations
2. **Database Manager**: All database CRUD operations
3. **File Handler**: File management and S3 operations
4. **Notification Service**: Email notifications and alerts

### 🗄️ **Data Storage**
- **DynamoDB**: NoSQL database for contracts, clients, and audit logs
- **S3 Buckets**: File storage, archives, backups, and email templates

### 📧 **Communication**
- **Amazon SES**: Email delivery service
- **CloudWatch**: Monitoring and logging

## 🔄 **Process Flows**

### 1. **Contract Termination Flow**
```
User Request → API Gateway → API Lambda → Contract Processor
                                          ↓
Database Update ← Database Manager ← Contract Processor
                                          ↓
File Backup ← File Handler ← Contract Processor
                                          ↓
Email Notification ← Notification Service ← Contract Processor
```

### 2. **File Management Flow**
```
File Upload → API Gateway → API Lambda → File Handler
                                         ↓
S3 Storage ← File Handler
                                         ↓
Metadata Update ← Database Manager ← File Handler
```

### 3. **Notification Flow**
```
Trigger Event → Notification Service
                     ↓
Load Template ← S3 Templates
                     ↓
Send Email → Amazon SES → Recipients
                     ↓
Log Activity → Database Manager
```

## 📊 **Data Flow Patterns**

### **Synchronous Operations**
- API Gateway → Lambda Functions
- Lambda Functions → DynamoDB
- Lambda Functions → S3

### **Asynchronous Operations**
- Email notifications via SES
- File backup operations
- Audit log creation

### **Cross-Function Communication**
- Contract Processor → Database Manager
- Contract Processor → File Handler
- Contract Processor → Notification Service
- File Handler → Database Manager
- Notification Service → Database Manager

## 🔐 **Security & Monitoring**

### **Access Control**
- IAM roles for each Lambda function
- Least privilege access to AWS services
- API Gateway authorization

### **Monitoring & Logging**
- All Lambda functions → CloudWatch Logs
- DynamoDB metrics → CloudWatch
- S3 access logging
- SES delivery notifications

## 🚀 **Scalability Features**

### **Auto-scaling**
- Lambda functions scale automatically
- DynamoDB on-demand billing
- S3 unlimited storage capacity

### **Performance Optimization**
- Shared Lambda layers for common dependencies
- DynamoDB Global Secondary Indexes
- S3 lifecycle policies for cost optimization

This flowchart represents the complete TESTEX AWS Lambda system architecture, showing how all components interact to provide a robust, scalable contract termination solution.
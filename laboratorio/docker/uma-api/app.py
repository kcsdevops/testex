#!/usr/bin/env python3
"""
TESTEX UMA API Simulator
Simula uma API UMA para testes do sistema TESTEX
"""

from flask import Flask, jsonify, request, abort
import json
import os
import datetime
import logging
from typing import Dict, List, Any
import uuid

app = Flask(__name__)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/uma-api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurações
API_KEY = os.getenv('API_KEY', 'testex-uma-key-2024')
DATA_DIR = '/app/data'

# Dados em memória (simulação)
clients_data = {}
purge_operations = {}

def load_sample_data():
    """Carrega dados de exemplo"""
    global clients_data
    
    sample_clients = {
        "CLI001": {
            "clientId": "CLI001",
            "name": "Empresa ABC Ltda",
            "status": "ACTIVE",
            "createdDate": "2024-01-15T10:30:00Z",
            "settings": {
                "notifications": True,
                "autoBackup": False,
                "retentionDays": 90
            },
            "services": ["hosting", "support", "backup"]
        },
        "CLI002": {
            "clientId": "CLI002",
            "name": "XYZ Corporation",
            "status": "ACTIVE",
            "createdDate": "2024-02-20T14:15:00Z",
            "settings": {
                "notifications": True,
                "autoBackup": True,
                "retentionDays": 365
            },
            "services": ["hosting", "database", "monitoring"]
        },
        "CLI003": {
            "clientId": "CLI003",
            "name": "TechStart Solutions",
            "status": "INACTIVE",
            "createdDate": "2024-03-10T09:45:00Z",
            "settings": {
                "notifications": False,
                "autoBackup": False,
                "retentionDays": 30
            },
            "services": ["consulting"]
        }
    }
    
    clients_data.update(sample_clients)
    logger.info(f"Loaded {len(sample_clients)} sample clients")

def validate_api_key():
    """Valida a chave da API"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        abort(401, 'Missing or invalid authorization header')
    
    token = auth_header.split(' ')[1]
    if token != API_KEY:
        abort(401, 'Invalid API key')

@app.before_request
def before_request():
    """Middleware para validar API key em todas as rotas (exceto health)"""
    if request.endpoint and request.endpoint != 'health':
        validate_api_key()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "1.0.0",
        "clients_count": len(clients_data)
    })

@app.route('/clients/<client_id>', methods=['GET'])
def get_client(client_id: str):
    """Obtém informações de um cliente"""
    if client_id not in clients_data:
        abort(404, f'Client {client_id} not found')
    
    logger.info(f"Retrieved client info for {client_id}")
    return jsonify(clients_data[client_id])

@app.route('/clients/<client_id>/disable', methods=['POST'])
def disable_client(client_id: str):
    """Desabilita um cliente"""
    if client_id not in clients_data:
        abort(404, f'Client {client_id} not found')
    
    data = request.get_json() or {}
    
    clients_data[client_id]['status'] = 'DISABLED'
    clients_data[client_id]['disabledDate'] = datetime.datetime.now().isoformat()
    clients_data[client_id]['disabledBy'] = data.get('disabledBy', 'system')
    clients_data[client_id]['disabledReason'] = data.get('reason', 'No reason provided')
    
    logger.info(f"Client {client_id} disabled by {data.get('disabledBy', 'system')}")
    
    return jsonify({
        "success": True,
        "clientId": client_id,
        "status": "DISABLED",
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/clients/<client_id>/services/<service>', methods=['DELETE'])
def remove_service(client_id: str, service: str):
    """Remove um serviço de um cliente"""
    if client_id not in clients_data:
        abort(404, f'Client {client_id} not found')
    
    client = clients_data[client_id]
    if service not in client.get('services', []):
        abort(404, f'Service {service} not found for client {client_id}')
    
    client['services'].remove(service)
    
    logger.info(f"Service {service} removed from client {client_id}")
    
    return jsonify({
        "success": True,
        "clientId": client_id,
        "removedService": service,
        "remainingServices": client['services'],
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/clients/<client_id>/status', methods=['PUT'])
def update_client_status(client_id: str):
    """Atualiza o status de um cliente"""
    if client_id not in clients_data:
        abort(404, f'Client {client_id} not found')
    
    data = request.get_json()
    if not data or 'status' not in data:
        abort(400, 'Status is required')
    
    new_status = data['status']
    valid_statuses = ['ACTIVE', 'INACTIVE', 'TERMINATED', 'SUSPENDED']
    
    if new_status not in valid_statuses:
        abort(400, f'Invalid status. Must be one of: {", ".join(valid_statuses)}')
    
    clients_data[client_id]['status'] = new_status
    clients_data[client_id]['updatedDate'] = datetime.datetime.now().isoformat()
    clients_data[client_id]['updatedBy'] = data.get('updatedBy', 'system')
    
    if data.get('notes'):
        clients_data[client_id]['notes'] = data['notes']
    
    logger.info(f"Client {client_id} status updated to {new_status}")
    
    return jsonify({
        "success": True,
        "clientId": client_id,
        "status": new_status,
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/clients/<client_id>/logs', methods=['GET'])
def get_client_logs(client_id: str):
    """Obtém logs de um cliente"""
    if client_id not in clients_data:
        abort(404, f'Client {client_id} not found')
    
    # Simular logs
    sample_logs = [
        {
            "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat(),
            "level": "INFO",
            "message": f"Client {client_id} accessed service",
            "component": "auth",
            "userId": "system"
        },
        {
            "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=2)).isoformat(),
            "level": "WARNING",
            "message": f"High resource usage detected for {client_id}",
            "component": "monitor",
            "userId": "monitor"
        },
        {
            "timestamp": (datetime.datetime.now() - datetime.timedelta(hours=3)).isoformat(),
            "level": "INFO",
            "message": f"Backup completed for {client_id}",
            "component": "backup",
            "userId": "system"
        }
    ]
    
    logger.info(f"Retrieved logs for client {client_id}")
    
    return jsonify({
        "clientId": client_id,
        "logs": sample_logs,
        "total": len(sample_logs)
    })

@app.route('/clients/<client_id>/purge', methods=['POST'])
def start_purge(client_id: str):
    """Inicia um processo de purge para um cliente"""
    if client_id not in clients_data:
        abort(404, f'Client {client_id} not found')
    
    data = request.get_json() or {}
    
    purge_id = str(uuid.uuid4())
    purge_operations[purge_id] = {
        "purgeId": purge_id,
        "clientId": client_id,
        "status": "IN_PROGRESS",
        "progress": 0,
        "startTime": datetime.datetime.now().isoformat(),
        "endTime": None,
        "requestedBy": data.get('requestedBy', 'system'),
        "force": data.get('force', False),
        "details": {
            "phase": "initialization",
            "processedItems": 0,
            "totalItems": 100
        }
    }
    
    logger.info(f"Purge started for client {client_id} with ID {purge_id}")
    
    return jsonify({
        "success": True,
        "purgeId": purge_id,
        "status": "IN_PROGRESS",
        "clientId": client_id,
        "timestamp": datetime.datetime.now().isoformat()
    }), 202

@app.route('/purge/<purge_id>/status', methods=['GET'])
def get_purge_status(purge_id: str):
    """Obtém o status de um processo de purge"""
    if purge_id not in purge_operations:
        abort(404, f'Purge operation {purge_id} not found')
    
    # Simular progresso
    purge = purge_operations[purge_id]
    if purge['status'] == 'IN_PROGRESS':
        # Incrementar progresso simulado
        purge['progress'] = min(purge['progress'] + 10, 100)
        purge['details']['processedItems'] = purge['progress']
        
        if purge['progress'] >= 100:
            purge['status'] = 'COMPLETED'
            purge['endTime'] = datetime.datetime.now().isoformat()
            purge['details']['phase'] = 'completed'
    
    logger.info(f"Purge status requested for {purge_id}: {purge['progress']}%")
    
    return jsonify(purge)

@app.route('/clients', methods=['GET'])
def list_clients():
    """Lista todos os clientes"""
    clients_list = list(clients_data.values())
    
    # Filtros opcionais
    status_filter = request.args.get('status')
    if status_filter:
        clients_list = [c for c in clients_list if c['status'] == status_filter.upper()]
    
    logger.info(f"Listed {len(clients_list)} clients")
    
    return jsonify({
        "clients": clients_list,
        "total": len(clients_list),
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Obtém estatísticas da API"""
    stats = {
        "totalClients": len(clients_data),
        "clientsByStatus": {},
        "activePurges": len([p for p in purge_operations.values() if p['status'] == 'IN_PROGRESS']),
        "completedPurges": len([p for p in purge_operations.values() if p['status'] == 'COMPLETED']),
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # Contar por status
    for client in clients_data.values():
        status = client['status']
        stats["clientsByStatus"][status] = stats["clientsByStatus"].get(status, 0) + 1
    
    return jsonify(stats)

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not Found",
        "message": str(error.description),
        "timestamp": datetime.datetime.now().isoformat()
    }), 404

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "error": "Bad Request",
        "message": str(error.description),
        "timestamp": datetime.datetime.now().isoformat()
    }), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "error": "Unauthorized",
        "message": str(error.description),
        "timestamp": datetime.datetime.now().isoformat()
    }), 401

if __name__ == '__main__':
    # Carregar dados de exemplo
    load_sample_data()
    
    # Criar diretórios se não existirem
    os.makedirs(DATA_DIR, exist_ok=True)
    
    logger.info("Starting TESTEX UMA API Simulator")
    logger.info(f"API Key: {API_KEY}")
    logger.info(f"Loaded {len(clients_data)} clients")
    
    # Iniciar servidor
    app.run(host='0.0.0.0', port=5000, debug=True)
# TESTEX Database Simulator
# Simula operações de banco de dados para testes do sistema

import json
import sqlite3
import os
import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

class DatabaseSimulator:
    def __init__(self, db_path: str = "testex_simulator.db"):
        """Inicializa o simulador de banco de dados"""
        self.db_path = db_path
        self.connection = None
        self.setup_logging()
        self.init_database()
    
    def setup_logging(self):
        """Configura logging para o simulador"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('database_simulator.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def init_database(self):
        """Inicializa o banco de dados com tabelas de teste"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            
            # Criar tabelas de teste
            self.create_tables()
            self.populate_sample_data()
            
            self.logger.info(f"Banco de dados simulado inicializado: {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar banco: {e}")
            raise
    
    def create_tables(self):
        """Cria as tabelas necessárias para simulação"""
        cursor = self.connection.cursor()
        
        # Tabela de clientes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT,
                telefone TEXT,
                status TEXT DEFAULT 'ACTIVE',
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                observacoes TEXT
            )
        ''')
        
        # Tabela de contratos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contratos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id TEXT NOT NULL,
                numero_contrato TEXT UNIQUE NOT NULL,
                valor DECIMAL(10,2),
                data_inicio DATE,
                data_fim DATE,
                status TEXT DEFAULT 'ACTIVE',
                tipo_servico TEXT,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            )
        ''')
        
        # Tabela de logs de operações
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id TEXT,
                operation_type TEXT NOT NULL,
                operation_details TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT
            )
        ''')
        
        # Tabela de backups
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id TEXT,
                backup_path TEXT NOT NULL,
                backup_type TEXT DEFAULT 'FULL',
                file_size INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'COMPLETED'
            )
        ''')
        
        self.connection.commit()
        self.logger.info("Tabelas criadas com sucesso")
    
    def populate_sample_data(self):
        """Popula o banco com dados de exemplo"""
        cursor = self.connection.cursor()
        
        # Verificar se já existe dados
        cursor.execute("SELECT COUNT(*) FROM clientes")
        if cursor.fetchone()[0] > 0:
            return
        
        # Dados de exemplo
        sample_clients = [
            ("CLI001", "Empresa ABC Ltda", "contato@empresaabc.com", "11999887766", "ACTIVE"),
            ("CLI002", "XYZ Corporation", "admin@xyzcorp.com", "11888776655", "ACTIVE"),
            ("CLI003", "TechStart Solutions", "info@techstart.com", "11777665544", "INACTIVE"),
            ("CLI004", "Global Services Inc", "support@globalservices.com", "11666554433", "ACTIVE"),
            ("CLI005", "Local Business SA", "contact@localbiz.com", "11555443322", "TERMINATED")
        ]
        
        cursor.executemany('''
            INSERT INTO clientes (id, nome, email, telefone, status)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_clients)
        
        # Contratos de exemplo
        sample_contracts = [
            ("CLI001", "CONT-2024-001", 15000.00, "2024-01-01", "2024-12-31", "ACTIVE", "Hosting"),
            ("CLI001", "CONT-2024-002", 8500.00, "2024-06-01", "2025-05-31", "ACTIVE", "Support"),
            ("CLI002", "CONT-2024-003", 25000.00, "2024-03-01", "2024-12-31", "ACTIVE", "Development"),
            ("CLI003", "CONT-2023-001", 12000.00, "2023-01-01", "2023-12-31", "EXPIRED", "Consulting"),
            ("CLI004", "CONT-2024-004", 30000.00, "2024-02-01", "2025-01-31", "ACTIVE", "Infrastructure"),
            ("CLI005", "CONT-2023-002", 5000.00, "2023-06-01", "2023-12-31", "TERMINATED", "Maintenance")
        ]
        
        cursor.executemany('''
            INSERT INTO contratos (cliente_id, numero_contrato, valor, data_inicio, data_fim, status, tipo_servico)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', sample_contracts)
        
        self.connection.commit()
        self.logger.info("Dados de exemplo inseridos")
    
    def get_client_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Obtém informações de um cliente"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT c.*, COUNT(ct.id) as total_contratos
                FROM clientes c
                LEFT JOIN contratos ct ON c.id = ct.cliente_id
                WHERE c.id = ?
                GROUP BY c.id
            ''', (client_id,))
            
            row = cursor.fetchone()
            if row:
                client_info = dict(row)
                self.logger.info(f"Cliente {client_id} encontrado")
                return client_info
            else:
                self.logger.warning(f"Cliente {client_id} não encontrado")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao buscar cliente: {e}")
            raise
    
    def update_client_status(self, client_id: str, new_status: str, notes: str = "") -> bool:
        """Atualiza o status de um cliente"""
        try:
            cursor = self.connection.cursor()
            
            # Verificar se cliente existe
            if not self.get_client_info(client_id):
                return False
            
            cursor.execute('''
                UPDATE clientes 
                SET status = ?, observacoes = ?, data_atualizacao = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_status, notes, client_id))
            
            # Log da operação
            self.log_operation(
                client_id=client_id,
                operation_type="STATUS_UPDATE",
                details=f"Status alterado para {new_status}",
                success=True
            )
            
            self.connection.commit()
            self.logger.info(f"Status do cliente {client_id} atualizado para {new_status}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar status: {e}")
            self.log_operation(
                client_id=client_id,
                operation_type="STATUS_UPDATE",
                details=f"Falha ao alterar status para {new_status}",
                success=False,
                error_message=str(e)
            )
            return False
    
    def create_backup(self, client_id: str, backup_path: str, backup_type: str = "FULL") -> Dict[str, Any]:
        """Simula criação de backup"""
        try:
            # Simular tamanho do backup
            import random
            file_size = random.randint(100000, 10000000)  # 100KB a 10MB
            
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO backups (cliente_id, backup_path, backup_type, file_size, status)
                VALUES (?, ?, ?, ?, 'COMPLETED')
            ''', (client_id, backup_path, backup_type, file_size))
            
            backup_id = cursor.lastrowid
            
            # Log da operação
            self.log_operation(
                client_id=client_id,
                operation_type="BACKUP_CREATED",
                details=f"Backup {backup_type} criado: {backup_path} ({file_size} bytes)",
                success=True
            )
            
            self.connection.commit()
            self.logger.info(f"Backup criado para cliente {client_id}: {backup_path}")
            
            return {
                "backup_id": backup_id,
                "backup_path": backup_path,
                "file_size": file_size,
                "status": "COMPLETED"
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {e}")
            self.log_operation(
                client_id=client_id,
                operation_type="BACKUP_CREATED",
                details=f"Falha ao criar backup: {backup_path}",
                success=False,
                error_message=str(e)
            )
            raise
    
    def terminate_client_contracts(self, client_id: str) -> List[str]:
        """Termina todos os contratos de um cliente"""
        try:
            cursor = self.connection.cursor()
            
            # Buscar contratos ativos
            cursor.execute('''
                SELECT numero_contrato FROM contratos 
                WHERE cliente_id = ? AND status != 'TERMINATED'
            ''', (client_id,))
            
            contracts = [row[0] for row in cursor.fetchall()]
            
            if contracts:
                # Terminar contratos
                cursor.execute('''
                    UPDATE contratos 
                    SET status = 'TERMINATED' 
                    WHERE cliente_id = ? AND status != 'TERMINATED'
                ''', (client_id,))
                
                # Log da operação
                self.log_operation(
                    client_id=client_id,
                    operation_type="CONTRACTS_TERMINATED",
                    details=f"Contratos terminados: {', '.join(contracts)}",
                    success=True
                )
                
                self.connection.commit()
                self.logger.info(f"Contratos terminados para cliente {client_id}: {len(contracts)} contratos")
            
            return contracts
            
        except Exception as e:
            self.logger.error(f"Erro ao terminar contratos: {e}")
            self.log_operation(
                client_id=client_id,
                operation_type="CONTRACTS_TERMINATED",
                details=f"Falha ao terminar contratos",
                success=False,
                error_message=str(e)
            )
            raise
    
    def log_operation(self, client_id: str, operation_type: str, details: str, 
                     success: bool = True, error_message: str = None):
        """Registra uma operação no log"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO operation_logs 
                (cliente_id, operation_type, operation_details, user_id, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (client_id, operation_type, details, os.getenv('USERNAME', 'simulator'), success, error_message))
            
            self.connection.commit()
            
        except Exception as e:
            self.logger.error(f"Erro ao registrar log: {e}")
    
    def get_client_logs(self, client_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtém logs de operações de um cliente"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT * FROM operation_logs 
                WHERE cliente_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (client_id, limit))
            
            logs = [dict(row) for row in cursor.fetchall()]
            return logs
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar logs: {e}")
            return []
    
    def get_all_clients(self) -> List[Dict[str, Any]]:
        """Obtém lista de todos os clientes"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT c.*, COUNT(ct.id) as total_contratos
                FROM clientes c
                LEFT JOIN contratos ct ON c.id = ct.cliente_id
                GROUP BY c.id
                ORDER BY c.nome
            ''')
            
            clients = [dict(row) for row in cursor.fetchall()]
            return clients
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar clientes: {e}")
            return []
    
    def generate_report(self, output_path: str = "database_report.json"):
        """Gera relatório do estado atual do banco"""
        try:
            report = {
                "timestamp": datetime.datetime.now().isoformat(),
                "database_path": self.db_path,
                "clients": self.get_all_clients(),
                "summary": {
                    "total_clients": 0,
                    "active_clients": 0,
                    "terminated_clients": 0,
                    "total_operations": 0
                }
            }
            
            # Calcular estatísticas
            cursor = self.connection.cursor()
            
            # Total de clientes por status
            cursor.execute("SELECT status, COUNT(*) FROM clientes GROUP BY status")
            status_counts = dict(cursor.fetchall())
            
            report["summary"]["total_clients"] = sum(status_counts.values())
            report["summary"]["active_clients"] = status_counts.get("ACTIVE", 0)
            report["summary"]["terminated_clients"] = status_counts.get("TERMINATED", 0)
            
            # Total de operações
            cursor.execute("SELECT COUNT(*) FROM operation_logs")
            report["summary"]["total_operations"] = cursor.fetchone()[0]
            
            # Salvar relatório
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"Relatório gerado: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {e}")
            raise
    
    def close(self):
        """Fecha a conexão com o banco"""
        if self.connection:
            self.connection.close()
            self.logger.info("Conexão com banco fechada")

def main():
    """Função principal para testes"""
    simulator = DatabaseSimulator()
    
    try:
        # Listar todos os clientes
        print("=== CLIENTES DISPONÍVEIS ===")
        clients = simulator.get_all_clients()
        for client in clients:
            print(f"ID: {client['id']} | Nome: {client['nome']} | Status: {client['status']}")
        
        # Testar operações com um cliente
        test_client = "CLI001"
        print(f"\n=== TESTANDO OPERAÇÕES COM CLIENTE {test_client} ===")
        
        # Obter informações do cliente
        client_info = simulator.get_client_info(test_client)
        if client_info:
            print(f"Cliente: {client_info['nome']}")
            print(f"Status atual: {client_info['status']}")
            print(f"Total de contratos: {client_info['total_contratos']}")
        
        # Criar backup
        backup_result = simulator.create_backup(test_client, f"./backups/{test_client}-{datetime.datetime.now().strftime('%Y%m%d')}.bak")
        print(f"Backup criado: {backup_result['backup_path']} ({backup_result['file_size']} bytes)")
        
        # Atualizar status
        simulator.update_client_status(test_client, "TERMINATED", "Teste de terminação via simulador")
        print("Status atualizado para TERMINATED")
        
        # Terminar contratos
        terminated_contracts = simulator.terminate_client_contracts(test_client)
        print(f"Contratos terminados: {len(terminated_contracts)}")
        
        # Verificar logs
        logs = simulator.get_client_logs(test_client, 10)
        print(f"\n=== ÚLTIMAS {len(logs)} OPERAÇÕES ===")
        for log in logs:
            status = "✓" if log['success'] else "✗"
            print(f"{status} {log['timestamp']} - {log['operation_type']}: {log['operation_details']}")
        
        # Gerar relatório
        report_path = simulator.generate_report()
        print(f"\nRelatório gerado: {report_path}")
        
    finally:
        simulator.close()

if __name__ == "__main__":
    main()
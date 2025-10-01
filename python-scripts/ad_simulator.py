# TESTEX Active Directory Simulator
# Simula operações do Active Directory para testes do sistema

import json
import os
import datetime
import logging
import random
import string
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

@dataclass
class ADUser:
    """Representa um usuário do Active Directory"""
    username: str
    display_name: str
    email: str
    client_id: str
    ou_path: str
    enabled: bool = True
    created_date: datetime.datetime = None
    last_login: datetime.datetime = None
    groups: List[str] = None
    
    def __post_init__(self):
        if self.created_date is None:
            self.created_date = datetime.datetime.now()
        if self.groups is None:
            self.groups = []

@dataclass
class ADGroup:
    """Representa um grupo do Active Directory"""
    name: str
    display_name: str
    client_id: str
    ou_path: str
    group_type: str = "Security"
    members: List[str] = None
    created_date: datetime.datetime = None
    
    def __post_init__(self):
        if self.created_date is None:
            self.created_date = datetime.datetime.now()
        if self.members is None:
            self.members = []

class ActiveDirectorySimulator:
    def __init__(self, data_file: str = "ad_simulator_data.json"):
        """Inicializa o simulador do Active Directory"""
        self.data_file = data_file
        self.users = {}
        self.groups = {}
        self.operations_log = []
        self.setup_logging()
        self.load_data()
        self.init_sample_data()
    
    def setup_logging(self):
        """Configura logging para o simulador"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ad_simulator.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_data(self):
        """Carrega dados do arquivo"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Carregar usuários
                for user_data in data.get('users', []):
                    user = ADUser(**user_data)
                    self.users[user.username] = user
                
                # Carregar grupos
                for group_data in data.get('groups', []):
                    group = ADGroup(**group_data)
                    self.groups[group.name] = group
                
                self.operations_log = data.get('operations_log', [])
                self.logger.info(f"Dados carregados: {len(self.users)} usuários, {len(self.groups)} grupos")
            
        except Exception as e:
            self.logger.warning(f"Erro ao carregar dados: {e}")
            self.users = {}
            self.groups = {}
            self.operations_log = []
    
    def save_data(self):
        """Salva dados no arquivo"""
        try:
            data = {
                'users': [user.__dict__.copy() for user in self.users.values()],
                'groups': [group.__dict__.copy() for group in self.groups.values()],
                'operations_log': self.operations_log
            }
            
            # Converter datetime para string
            for user in data['users']:
                if user.get('created_date'):
                    user['created_date'] = user['created_date'].isoformat() if isinstance(user['created_date'], datetime.datetime) else user['created_date']
                if user.get('last_login'):
                    user['last_login'] = user['last_login'].isoformat() if isinstance(user['last_login'], datetime.datetime) else user['last_login']
            
            for group in data['groups']:
                if group.get('created_date'):
                    group['created_date'] = group['created_date'].isoformat() if isinstance(group['created_date'], datetime.datetime) else group['created_date']
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info("Dados salvos com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados: {e}")
    
    def init_sample_data(self):
        """Inicializa dados de exemplo se não existirem"""
        if len(self.users) == 0 and len(self.groups) == 0:
            self.create_sample_data()
    
    def create_sample_data(self):
        """Cria dados de exemplo"""
        sample_clients = ["CLI001", "CLI002", "CLI003", "CLI004", "CLI005"]
        
        for client_id in sample_clients:
            # Criar grupos para o cliente
            groups_to_create = [
                f"{client_id}_Users",
                f"{client_id}_Admins",
                f"{client_id}_Support",
                f"{client_id}_Finance"
            ]
            
            for group_name in groups_to_create:
                group = ADGroup(
                    name=group_name,
                    display_name=f"Grupo {group_name.replace('_', ' ')}",
                    client_id=client_id,
                    ou_path=f"OU=Groups,OU={client_id},DC=testex,DC=local"
                )
                self.groups[group_name] = group
            
            # Criar usuários para o cliente
            num_users = random.randint(3, 8)
            for i in range(num_users):
                username = f"{client_id.lower()}.user{i+1:02d}"
                display_name = f"Usuário {i+1} - {client_id}"
                email = f"{username}@{client_id.lower()}.testex.local"
                
                user = ADUser(
                    username=username,
                    display_name=display_name,
                    email=email,
                    client_id=client_id,
                    ou_path=f"OU=Users,OU={client_id},DC=testex,DC=local",
                    groups=[f"{client_id}_Users"]
                )
                
                # Adicionar a grupo admin se for o primeiro usuário
                if i == 0:
                    user.groups.append(f"{client_id}_Admins")
                
                self.users[username] = user
                
                # Adicionar usuário aos grupos
                for group_name in user.groups:
                    if group_name in self.groups:
                        self.groups[group_name].members.append(username)
        
        self.log_operation("SYSTEM", "INIT", f"Dados de exemplo criados: {len(self.users)} usuários, {len(self.groups)} grupos")
        self.save_data()
        self.logger.info("Dados de exemplo criados")
    
    def get_users_by_client(self, client_id: str) -> List[ADUser]:
        """Obtém todos os usuários de um cliente"""
        try:
            client_users = [user for user in self.users.values() if user.client_id == client_id and user.enabled]
            self.logger.info(f"Encontrados {len(client_users)} usuários para cliente {client_id}")
            return client_users
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar usuários: {e}")
            return []
    
    def get_groups_by_client(self, client_id: str) -> List[ADGroup]:
        """Obtém todos os grupos de um cliente"""
        try:
            client_groups = [group for group in self.groups.values() if group.client_id == client_id]
            self.logger.info(f"Encontrados {len(client_groups)} grupos para cliente {client_id}")
            return client_groups
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar grupos: {e}")
            return []
    
    def disable_user(self, username: str, reason: str = "Contract termination") -> bool:
        """Desabilita um usuário"""
        try:
            if username in self.users:
                user = self.users[username]
                user.enabled = False
                
                self.log_operation(
                    user.client_id,
                    "USER_DISABLED",
                    f"Usuário {username} desabilitado: {reason}"
                )
                
                self.logger.info(f"Usuário {username} desabilitado")
                return True
            else:
                self.logger.warning(f"Usuário {username} não encontrado")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao desabilitar usuário: {e}")
            return False
    
    def remove_user(self, username: str, reason: str = "Contract termination") -> bool:
        """Remove um usuário"""
        try:
            if username in self.users:
                user = self.users[username]
                client_id = user.client_id
                
                # Remover usuário de todos os grupos
                for group in self.groups.values():
                    if username in group.members:
                        group.members.remove(username)
                
                # Remover usuário
                del self.users[username]
                
                self.log_operation(
                    client_id,
                    "USER_REMOVED",
                    f"Usuário {username} removido: {reason}"
                )
                
                self.logger.info(f"Usuário {username} removido")
                return True
            else:
                self.logger.warning(f"Usuário {username} não encontrado")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao remover usuário: {e}")
            return False
    
    def remove_group(self, group_name: str, reason: str = "Contract termination") -> bool:
        """Remove um grupo"""
        try:
            if group_name in self.groups:
                group = self.groups[group_name]
                client_id = group.client_id
                
                # Remover referências do grupo dos usuários
                for user in self.users.values():
                    if group_name in user.groups:
                        user.groups.remove(group_name)
                
                # Remover grupo
                del self.groups[group_name]
                
                self.log_operation(
                    client_id,
                    "GROUP_REMOVED",
                    f"Grupo {group_name} removido: {reason}"
                )
                
                self.logger.info(f"Grupo {group_name} removido")
                return True
            else:
                self.logger.warning(f"Grupo {group_name} não encontrado")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao remover grupo: {e}")
            return False
    
    def remove_client_users(self, client_id: str, what_if: bool = False) -> Dict[str, Any]:
        """Remove todos os usuários de um cliente"""
        try:
            users_to_remove = self.get_users_by_client(client_id)
            removed_users = []
            
            if what_if:
                self.logger.info(f"SIMULAÇÃO: Removeria {len(users_to_remove)} usuários do cliente {client_id}")
                return {
                    "success": True,
                    "removed_count": len(users_to_remove),
                    "users": [user.username for user in users_to_remove],
                    "simulation": True
                }
            
            for user in users_to_remove:
                if self.remove_user(user.username, f"Client {client_id} termination"):
                    removed_users.append(user.username)
            
            self.log_operation(
                client_id,
                "BULK_USER_REMOVAL",
                f"Removidos {len(removed_users)} usuários: {', '.join(removed_users)}"
            )
            
            return {
                "success": True,
                "removed_count": len(removed_users),
                "users": removed_users,
                "simulation": False
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao remover usuários do cliente: {e}")
            self.log_operation(
                client_id,
                "BULK_USER_REMOVAL",
                f"Erro ao remover usuários: {str(e)}",
                success=False
            )
            return {"success": False, "error": str(e)}
    
    def remove_client_groups(self, client_id: str, what_if: bool = False) -> Dict[str, Any]:
        """Remove todos os grupos de um cliente"""
        try:
            groups_to_remove = self.get_groups_by_client(client_id)
            removed_groups = []
            
            if what_if:
                self.logger.info(f"SIMULAÇÃO: Removeria {len(groups_to_remove)} grupos do cliente {client_id}")
                return {
                    "success": True,
                    "removed_count": len(groups_to_remove),
                    "groups": [group.name for group in groups_to_remove],
                    "simulation": True
                }
            
            for group in groups_to_remove:
                if self.remove_group(group.name, f"Client {client_id} termination"):
                    removed_groups.append(group.name)
            
            self.log_operation(
                client_id,
                "BULK_GROUP_REMOVAL",
                f"Removidos {len(removed_groups)} grupos: {', '.join(removed_groups)}"
            )
            
            return {
                "success": True,
                "removed_count": len(removed_groups),
                "groups": removed_groups,
                "simulation": False
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao remover grupos do cliente: {e}")
            self.log_operation(
                client_id,
                "BULK_GROUP_REMOVAL",
                f"Erro ao remover grupos: {str(e)}",
                success=False
            )
            return {"success": False, "error": str(e)}
    
    def search_objects(self, search_filter: str, object_type: str = "all") -> List[Dict[str, Any]]:
        """Busca objetos no AD"""
        try:
            results = []
            
            if object_type in ["all", "users"]:
                for user in self.users.values():
                    if (search_filter.lower() in user.username.lower() or 
                        search_filter.lower() in user.display_name.lower() or
                        search_filter.lower() in user.client_id.lower()):
                        results.append({
                            "type": "user",
                            "name": user.username,
                            "display_name": user.display_name,
                            "client_id": user.client_id,
                            "enabled": user.enabled
                        })
            
            if object_type in ["all", "groups"]:
                for group in self.groups.values():
                    if (search_filter.lower() in group.name.lower() or 
                        search_filter.lower() in group.display_name.lower() or
                        search_filter.lower() in group.client_id.lower()):
                        results.append({
                            "type": "group",
                            "name": group.name,
                            "display_name": group.display_name,
                            "client_id": group.client_id,
                            "members_count": len(group.members)
                        })
            
            self.logger.info(f"Busca '{search_filter}' retornou {len(results)} resultados")
            return results
            
        except Exception as e:
            self.logger.error(f"Erro na busca: {e}")
            return []
    
    def log_operation(self, client_id: str, operation_type: str, details: str, success: bool = True):
        """Registra uma operação no log"""
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "client_id": client_id,
            "operation_type": operation_type,
            "details": details,
            "success": success,
            "user": os.getenv('USERNAME', 'simulator')
        }
        
        self.operations_log.append(log_entry)
        
        # Manter apenas os últimos 1000 logs
        if len(self.operations_log) > 1000:
            self.operations_log = self.operations_log[-1000:]
    
    def get_client_operations(self, client_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Obtém operações de um cliente"""
        try:
            client_ops = [op for op in self.operations_log if op['client_id'] == client_id]
            return sorted(client_ops, key=lambda x: x['timestamp'], reverse=True)[:limit]
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar operações: {e}")
            return []
    
    def generate_client_report(self, client_id: str) -> Dict[str, Any]:
        """Gera relatório de um cliente"""
        try:
            users = self.get_users_by_client(client_id)
            groups = self.get_groups_by_client(client_id)
            operations = self.get_client_operations(client_id, 100)
            
            report = {
                "client_id": client_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "summary": {
                    "total_users": len(users),
                    "enabled_users": len([u for u in users if u.enabled]),
                    "disabled_users": len([u for u in users if not u.enabled]),
                    "total_groups": len(groups),
                    "total_operations": len(operations)
                },
                "users": [
                    {
                        "username": user.username,
                        "display_name": user.display_name,
                        "email": user.email,
                        "enabled": user.enabled,
                        "groups": user.groups,
                        "created_date": user.created_date.isoformat() if isinstance(user.created_date, datetime.datetime) else user.created_date
                    } for user in users
                ],
                "groups": [
                    {
                        "name": group.name,
                        "display_name": group.display_name,
                        "members_count": len(group.members),
                        "members": group.members,
                        "created_date": group.created_date.isoformat() if isinstance(group.created_date, datetime.datetime) else group.created_date
                    } for group in groups
                ],
                "recent_operations": operations[:20]  # Últimas 20 operações
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {e}")
            return {"error": str(e)}
    
    def export_report(self, client_id: str, output_path: str = None) -> str:
        """Exporta relatório de um cliente"""
        try:
            if output_path is None:
                output_path = f"AD_Report_{client_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            report = self.generate_client_report(client_id)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Relatório exportado: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Erro ao exportar relatório: {e}")
            raise
    
    def get_all_clients(self) -> List[str]:
        """Obtém lista de todos os clientes"""
        clients = set()
        
        for user in self.users.values():
            clients.add(user.client_id)
        
        for group in self.groups.values():
            clients.add(group.client_id)
        
        return sorted(list(clients))
    
    def cleanup_and_save(self):
        """Limpa dados e salva"""
        self.save_data()

def main():
    """Função principal para testes"""
    simulator = ActiveDirectorySimulator()
    
    try:
        # Listar todos os clientes
        print("=== CLIENTES DISPONÍVEIS ===")
        clients = simulator.get_all_clients()
        for client in clients:
            users = simulator.get_users_by_client(client)
            groups = simulator.get_groups_by_client(client)
            print(f"Cliente: {client} | Usuários: {len(users)} | Grupos: {len(groups)}")
        
        # Testar operações com um cliente
        test_client = "CLI001"
        print(f"\n=== TESTANDO OPERAÇÕES COM CLIENTE {test_client} ===")
        
        # Listar usuários e grupos
        users = simulator.get_users_by_client(test_client)
        groups = simulator.get_groups_by_client(test_client)
        
        print(f"Usuários encontrados: {len(users)}")
        for user in users:
            print(f"  - {user.username} ({user.display_name}) - Ativo: {user.enabled}")
        
        print(f"Grupos encontrados: {len(groups)}")
        for group in groups:
            print(f"  - {group.name} ({len(group.members)} membros)")
        
        # Simular remoção (what-if)
        print("\n=== SIMULAÇÃO DE REMOÇÃO ===")
        users_result = simulator.remove_client_users(test_client, what_if=True)
        groups_result = simulator.remove_client_groups(test_client, what_if=True)
        
        print(f"Usuários que seriam removidos: {users_result['removed_count']}")
        print(f"Grupos que seriam removidos: {groups_result['removed_count']}")
        
        # Gerar relatório
        report_path = simulator.export_report(test_client)
        print(f"\nRelatório gerado: {report_path}")
        
        # Buscar objetos
        print("\n=== BUSCA DE OBJETOS ===")
        search_results = simulator.search_objects("CLI001")
        print(f"Resultados da busca 'CLI001': {len(search_results)}")
        for result in search_results[:5]:  # Mostrar apenas os primeiros 5
            print(f"  - {result['type']}: {result['name']} ({result['client_id']})")
        
    finally:
        simulator.cleanup_and_save()

if __name__ == "__main__":
    main()
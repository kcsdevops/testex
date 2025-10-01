# TESTEX File System Simulator
# Simula operações de sistema de arquivos para testes

import json
import os
import shutil
import datetime
import logging
import random
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import zipfile

@dataclass
class FileInfo:
    """Representa informações de um arquivo"""
    path: str
    name: str
    size: int
    client_id: str
    file_type: str
    created_date: datetime.datetime
    modified_date: datetime.datetime
    checksum: str = ""
    archived: bool = False
    backed_up: bool = False
    
    def __post_init__(self):
        if isinstance(self.created_date, str):
            self.created_date = datetime.datetime.fromisoformat(self.created_date)
        if isinstance(self.modified_date, str):
            self.modified_date = datetime.datetime.fromisoformat(self.modified_date)

class FileSystemSimulator:
    def __init__(self, base_path: str = "./simulator_files", data_file: str = "files_simulator_data.json"):
        """Inicializa o simulador de sistema de arquivos"""
        self.base_path = Path(base_path)
        self.data_file = data_file
        self.files_registry = {}
        self.operations_log = []
        
        self.setup_logging()
        self.init_directories()
        self.load_registry()
        self.init_sample_files()
    
    def setup_logging(self):
        """Configura logging para o simulador"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('files_simulator.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def init_directories(self):
        """Inicializa estrutura de diretórios"""
        directories = [
            self.base_path,
            self.base_path / "clients",
            self.base_path / "backups",
            self.base_path / "archives",
            self.base_path / "temp"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Estrutura de diretórios inicializada em {self.base_path}")
    
    def load_registry(self):
        """Carrega registro de arquivos"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Carregar arquivos
                for file_data in data.get('files', []):
                    file_info = FileInfo(**file_data)
                    self.files_registry[file_info.path] = file_info
                
                self.operations_log = data.get('operations_log', [])
                self.logger.info(f"Registro carregado: {len(self.files_registry)} arquivos")
        
        except Exception as e:
            self.logger.warning(f"Erro ao carregar registro: {e}")
            self.files_registry = {}
            self.operations_log = []
    
    def save_registry(self):
        """Salva registro de arquivos"""
        try:
            data = {
                'files': [file_info.__dict__.copy() for file_info in self.files_registry.values()],
                'operations_log': self.operations_log
            }
            
            # Converter datetime para string
            for file_data in data['files']:
                if isinstance(file_data.get('created_date'), datetime.datetime):
                    file_data['created_date'] = file_data['created_date'].isoformat()
                if isinstance(file_data.get('modified_date'), datetime.datetime):
                    file_data['modified_date'] = file_data['modified_date'].isoformat()
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info("Registro salvo com sucesso")
        
        except Exception as e:
            self.logger.error(f"Erro ao salvar registro: {e}")
    
    def init_sample_files(self):
        """Cria arquivos de exemplo se não existirem"""
        if len(self.files_registry) == 0:
            self.create_sample_files()
    
    def create_sample_files(self):
        """Cria arquivos de exemplo"""
        sample_clients = ["CLI001", "CLI002", "CLI003", "CLI004", "CLI005"]
        
        for client_id in sample_clients:
            client_dir = self.base_path / "clients" / client_id
            client_dir.mkdir(parents=True, exist_ok=True)
            
            # Criar diferentes tipos de arquivos
            file_types = [
                (".pr4", "Project File"),
                (".doc", "Document"),
                (".pdf", "PDF Document"),
                (".xls", "Spreadsheet"),
                (".txt", "Text File"),
                (".log", "Log File")
            ]
            
            num_files = random.randint(5, 15)
            
            for i in range(num_files):
                # Escolher tipo de arquivo aleatório
                extension, file_type = random.choice(file_types)
                filename = f"{client_id}_file_{i+1:03d}{extension}"
                filepath = client_dir / filename
                
                # Criar conteúdo do arquivo
                content = self.generate_sample_content(client_id, file_type, i+1)
                
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # Calcular checksum
                    checksum = self.calculate_checksum(filepath)
                    
                    # Registrar arquivo
                    file_info = FileInfo(
                        path=str(filepath),
                        name=filename,
                        size=len(content.encode('utf-8')),
                        client_id=client_id,
                        file_type=file_type,
                        created_date=datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 365)),
                        modified_date=datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 30)),
                        checksum=checksum
                    )
                    
                    self.files_registry[str(filepath)] = file_info
                    
                except Exception as e:
                    self.logger.error(f"Erro ao criar arquivo {filepath}: {e}")
        
        self.log_operation("SYSTEM", "INIT", f"Arquivos de exemplo criados: {len(self.files_registry)} arquivos")
        self.save_registry()
        self.logger.info("Arquivos de exemplo criados")
    
    def generate_sample_content(self, client_id: str, file_type: str, file_number: int) -> str:
        """Gera conteúdo de exemplo para arquivos"""
        base_content = f"""# Arquivo de exemplo para {client_id}
# Tipo: {file_type}
# Número: {file_number}
# Criado em: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Cliente: {client_id}
Arquivo: {file_number}
Tipo: {file_type}

"""
        
        if file_type == "Project File":
            base_content += """
[PROJECT]
Name=Projeto Exemplo
Version=1.0
Client={client_id}
Status=Active

[SETTINGS]
Database=TESTEX_DB
Environment=Production
Debug=False

[FILES]
""".format(client_id=client_id)
            
            # Adicionar lista de arquivos fictícios
            for i in range(random.randint(3, 10)):
                base_content += f"File{i+1}=module_{i+1}.dll\n"
        
        elif file_type == "Log File":
            # Gerar entradas de log
            for i in range(random.randint(10, 50)):
                timestamp = datetime.datetime.now() - datetime.timedelta(minutes=random.randint(1, 1440))
                level = random.choice(["INFO", "WARNING", "ERROR", "DEBUG"])
                message = random.choice([
                    "Operação concluída com sucesso",
                    "Conectando ao banco de dados",
                    "Processando arquivo de entrada",
                    "Enviando notificação por email",
                    "Backup realizado",
                    "Validação de dados concluída"
                ])
                base_content += f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{level}] {message}\n"
        
        else:
            # Conteúdo genérico
            base_content += "Conteúdo do documento...\n" * random.randint(5, 20)
        
        return base_content
    
    def calculate_checksum(self, filepath: Path) -> str:
        """Calcula checksum MD5 de um arquivo"""
        try:
            hash_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.logger.error(f"Erro ao calcular checksum: {e}")
            return ""
    
    def get_client_files(self, client_id: str, file_pattern: str = "*") -> List[FileInfo]:
        """Obtém todos os arquivos de um cliente"""
        try:
            client_files = []
            
            for file_info in self.files_registry.values():
                if file_info.client_id == client_id:
                    # Aplicar filtro de padrão se especificado
                    if file_pattern == "*" or file_pattern.lower() in file_info.name.lower():
                        client_files.append(file_info)
            
            self.logger.info(f"Encontrados {len(client_files)} arquivos para cliente {client_id}")
            return client_files
        
        except Exception as e:
            self.logger.error(f"Erro ao buscar arquivos: {e}")
            return []
    
    def backup_files(self, client_id: str, files: List[FileInfo], backup_path: str, what_if: bool = False) -> Dict[str, Any]:
        """Faz backup dos arquivos de um cliente"""
        try:
            backup_dir = Path(backup_path) / client_id
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{client_id}_{timestamp}.zip"
            backup_file = backup_dir / backup_name
            
            if what_if:
                total_size = sum(file_info.size for file_info in files)
                self.logger.info(f"SIMULAÇÃO: Backup de {len(files)} arquivos ({total_size} bytes) para {backup_file}")
                return {
                    "success": True,
                    "backup_path": str(backup_file),
                    "files_count": len(files),
                    "total_size": total_size,
                    "simulation": True
                }
            
            # Criar diretório de backup se não existir
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backed_up_files = []
            total_size = 0
            
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_info in files:
                    if os.path.exists(file_info.path):
                        # Adicionar arquivo ao ZIP
                        arcname = os.path.relpath(file_info.path, self.base_path)
                        zipf.write(file_info.path, arcname)
                        
                        # Marcar como backup
                        file_info.backed_up = True
                        backed_up_files.append(file_info.name)
                        total_size += file_info.size
            
            self.log_operation(
                client_id,
                "BACKUP_CREATED",
                f"Backup de {len(backed_up_files)} arquivos criado: {backup_name}"
            )
            
            self.logger.info(f"Backup criado: {backup_file} ({len(backed_up_files)} arquivos, {total_size} bytes)")
            
            return {
                "success": True,
                "backup_path": str(backup_file),
                "files_count": len(backed_up_files),
                "total_size": total_size,
                "backed_up_files": backed_up_files,
                "simulation": False
            }
        
        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {e}")
            self.log_operation(
                client_id,
                "BACKUP_ERROR",
                f"Erro ao criar backup: {str(e)}",
                success=False
            )
            return {"success": False, "error": str(e)}
    
    def remove_files(self, client_id: str, files: List[FileInfo], what_if: bool = False, force: bool = False) -> Dict[str, Any]:
        """Remove arquivos de um cliente"""
        try:
            if what_if:
                total_size = sum(file_info.size for file_info in files)
                self.logger.info(f"SIMULAÇÃO: Removeria {len(files)} arquivos ({total_size} bytes) do cliente {client_id}")
                return {
                    "success": True,
                    "removed_count": len(files),
                    "remaining_files": [],
                    "total_size_removed": total_size,
                    "simulation": True
                }
            
            removed_files = []
            remaining_files = []
            total_size_removed = 0
            
            for file_info in files:
                try:
                    # Verificar se deve forçar remoção ou se arquivo tem backup
                    if force or file_info.backed_up:
                        if os.path.exists(file_info.path):
                            os.remove(file_info.path)
                            
                        # Remover do registro
                        if file_info.path in self.files_registry:
                            del self.files_registry[file_info.path]
                        
                        removed_files.append(file_info.name)
                        total_size_removed += file_info.size
                        
                        self.logger.info(f"Arquivo removido: {file_info.name}")
                    else:
                        remaining_files.append(file_info)
                        self.logger.warning(f"Arquivo não removido (sem backup): {file_info.name}")
                
                except Exception as e:
                    self.logger.error(f"Erro ao remover arquivo {file_info.name}: {e}")
                    remaining_files.append(file_info)
            
            self.log_operation(
                client_id,
                "FILES_REMOVED",
                f"Removidos {len(removed_files)} arquivos, {len(remaining_files)} mantidos"
            )
            
            return {
                "success": True,
                "removed_count": len(removed_files),
                "remaining_files": remaining_files,
                "removed_files": removed_files,
                "total_size_removed": total_size_removed,
                "simulation": False
            }
        
        except Exception as e:
            self.logger.error(f"Erro ao remover arquivos: {e}")
            self.log_operation(
                client_id,
                "FILES_REMOVAL_ERROR",
                f"Erro ao remover arquivos: {str(e)}",
                success=False
            )
            return {"success": False, "error": str(e)}
    
    def archive_files(self, client_id: str, files: List[FileInfo], archive_path: str, what_if: bool = False) -> Dict[str, Any]:
        """Arquiva arquivos remanescentes"""
        try:
            archive_dir = Path(archive_path) / client_id
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            archive_name = f"archive_{client_id}_{timestamp}.zip"
            archive_file = archive_dir / archive_name
            
            if what_if:
                total_size = sum(file_info.size for file_info in files)
                self.logger.info(f"SIMULAÇÃO: Arquivaria {len(files)} arquivos ({total_size} bytes) em {archive_file}")
                return {
                    "success": True,
                    "archive_path": str(archive_file),
                    "files_count": len(files),
                    "total_size": total_size,
                    "simulation": True
                }
            
            # Criar diretório de arquivo se não existir
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            archived_files = []
            total_size = 0
            
            with zipfile.ZipFile(archive_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_info in files:
                    if os.path.exists(file_info.path):
                        # Adicionar arquivo ao ZIP
                        arcname = os.path.relpath(file_info.path, self.base_path)
                        zipf.write(file_info.path, arcname)
                        
                        # Remover arquivo original
                        os.remove(file_info.path)
                        
                        # Marcar como arquivado
                        file_info.archived = True
                        file_info.path = str(archive_file)  # Atualizar caminho para o arquivo
                        
                        archived_files.append(file_info.name)
                        total_size += file_info.size
            
            self.log_operation(
                client_id,
                "FILES_ARCHIVED",
                f"Arquivados {len(archived_files)} arquivos: {archive_name}"
            )
            
            self.logger.info(f"Arquivo criado: {archive_file} ({len(archived_files)} arquivos, {total_size} bytes)")
            
            return {
                "success": True,
                "archive_path": str(archive_file),
                "files_count": len(archived_files),
                "total_size": total_size,
                "archived_files": archived_files,
                "simulation": False
            }
        
        except Exception as e:
            self.logger.error(f"Erro ao arquivar arquivos: {e}")
            self.log_operation(
                client_id,
                "ARCHIVE_ERROR",
                f"Erro ao arquivar arquivos: {str(e)}",
                success=False
            )
            return {"success": False, "error": str(e)}
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de armazenamento"""
        try:
            stats = {
                "total_files": len(self.files_registry),
                "total_size": 0,
                "files_by_client": {},
                "files_by_type": {},
                "backed_up_files": 0,
                "archived_files": 0
            }
            
            for file_info in self.files_registry.values():
                stats["total_size"] += file_info.size
                
                # Por cliente
                if file_info.client_id not in stats["files_by_client"]:
                    stats["files_by_client"][file_info.client_id] = {"count": 0, "size": 0}
                stats["files_by_client"][file_info.client_id]["count"] += 1
                stats["files_by_client"][file_info.client_id]["size"] += file_info.size
                
                # Por tipo
                if file_info.file_type not in stats["files_by_type"]:
                    stats["files_by_type"][file_info.file_type] = {"count": 0, "size": 0}
                stats["files_by_type"][file_info.file_type]["count"] += 1
                stats["files_by_type"][file_info.file_type]["size"] += file_info.size
                
                # Estados
                if file_info.backed_up:
                    stats["backed_up_files"] += 1
                if file_info.archived:
                    stats["archived_files"] += 1
            
            return stats
        
        except Exception as e:
            self.logger.error(f"Erro ao calcular estatísticas: {e}")
            return {"error": str(e)}
    
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
        """Gera relatório de arquivos de um cliente"""
        try:
            files = self.get_client_files(client_id)
            operations = self.get_client_operations(client_id, 100)
            
            total_size = sum(file_info.size for file_info in files)
            backed_up_count = len([f for f in files if f.backed_up])
            archived_count = len([f for f in files if f.archived])
            
            report = {
                "client_id": client_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "summary": {
                    "total_files": len(files),
                    "total_size": total_size,
                    "backed_up_files": backed_up_count,
                    "archived_files": archived_count,
                    "file_types": {}
                },
                "files": [
                    {
                        "name": file_info.name,
                        "path": file_info.path,
                        "size": file_info.size,
                        "file_type": file_info.file_type,
                        "created_date": file_info.created_date.isoformat() if isinstance(file_info.created_date, datetime.datetime) else file_info.created_date,
                        "modified_date": file_info.modified_date.isoformat() if isinstance(file_info.modified_date, datetime.datetime) else file_info.modified_date,
                        "backed_up": file_info.backed_up,
                        "archived": file_info.archived,
                        "checksum": file_info.checksum
                    } for file_info in files
                ],
                "recent_operations": operations[:20]
            }
            
            # Calcular tipos de arquivo
            for file_info in files:
                if file_info.file_type not in report["summary"]["file_types"]:
                    report["summary"]["file_types"][file_info.file_type] = 0
                report["summary"]["file_types"][file_info.file_type] += 1
            
            return report
        
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {e}")
            return {"error": str(e)}
    
    def export_report(self, client_id: str, output_path: str = None) -> str:
        """Exporta relatório de arquivos de um cliente"""
        try:
            if output_path is None:
                output_path = f"Files_Report_{client_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            report = self.generate_client_report(client_id)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Relatório exportado: {output_path}")
            return output_path
        
        except Exception as e:
            self.logger.error(f"Erro ao exportar relatório: {e}")
            raise
    
    def cleanup_and_save(self):
        """Limpa dados e salva"""
        self.save_registry()

def main():
    """Função principal para testes"""
    simulator = FileSystemSimulator()
    
    try:
        # Mostrar estatísticas gerais
        print("=== ESTATÍSTICAS GERAIS ===")
        stats = simulator.get_storage_stats()
        print(f"Total de arquivos: {stats['total_files']}")
        print(f"Tamanho total: {stats['total_size']:,} bytes")
        print(f"Arquivos com backup: {stats['backed_up_files']}")
        print(f"Arquivos arquivados: {stats['archived_files']}")
        
        print("\nArquivos por cliente:")
        for client_id, client_stats in stats['files_by_client'].items():
            print(f"  {client_id}: {client_stats['count']} arquivos ({client_stats['size']:,} bytes)")
        
        # Testar operações com um cliente
        test_client = "CLI001"
        print(f"\n=== TESTANDO OPERAÇÕES COM CLIENTE {test_client} ===")
        
        # Obter arquivos do cliente
        files = simulator.get_client_files(test_client)
        print(f"Arquivos encontrados: {len(files)}")
        
        for file_info in files[:5]:  # Mostrar apenas os primeiros 5
            print(f"  - {file_info.name} ({file_info.size:,} bytes) - Backup: {file_info.backed_up}")
        
        # Simular backup
        print("\n=== SIMULAÇÃO DE BACKUP ===")
        backup_result = simulator.backup_files(test_client, files, "./backups", what_if=True)
        print(f"Arquivos para backup: {backup_result['files_count']}")
        print(f"Tamanho total: {backup_result['total_size']:,} bytes")
        
        # Fazer backup real
        backup_result = simulator.backup_files(test_client, files, "./backups", what_if=False)
        if backup_result['success']:
            print(f"Backup criado: {backup_result['backup_path']}")
        
        # Simular remoção
        print("\n=== SIMULAÇÃO DE REMOÇÃO ===")
        removal_result = simulator.remove_files(test_client, files, what_if=True, force=False)
        print(f"Arquivos que seriam removidos: {removal_result['removed_count']}")
        
        # Gerar relatório
        report_path = simulator.export_report(test_client)
        print(f"\nRelatório gerado: {report_path}")
        
    finally:
        simulator.cleanup_and_save()

if __name__ == "__main__":
    main()
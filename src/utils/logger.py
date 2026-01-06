"""
Sistema de logging estruturado para o bot
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import structlog
from colorlog import ColoredFormatter

from src.config import settings, LOGS_DIR


def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Configura o sistema de logging estruturado
    
    Args:
        log_level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level = log_level or settings.LOG_LEVEL
    
    # Configurar logging padrão
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )
    
    # Configurar structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.is_production 
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Obtém um logger estruturado
    
    Args:
        name: Nome do logger (geralmente __name__)
        
    Returns:
        Logger estruturado
    """
    return structlog.get_logger(name)


class FileLogger:
    """Logger para salvar logs em arquivo"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        
        # Handler para arquivo diário
        log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Formato do arquivo
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Handler para console colorido
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        
        color_formatter = ColoredFormatter(
            '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'red,bg_white',
            }
        )
        console_handler.setFormatter(color_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        self.logger.critical(message, extra=kwargs)


class AuditLogger:
    """Logger específico para auditoria de ações críticas"""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Arquivo separado para auditoria
        audit_file = LOGS_DIR / "audit.log"
        handler = logging.FileHandler(audit_file, encoding='utf-8')
        
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log(self, action: str, user: str, details: dict):
        """
        Registra uma ação de auditoria
        
        Args:
            action: Tipo de ação (CREATE_POST, DELETE_POST, etc)
            user: Identificador do usuário
            details: Detalhes adicionais
        """
        message = f"ACTION={action} USER={user} DETAILS={details}"
        self.logger.info(message)


# Instâncias globais
setup_logging()
audit_logger = AuditLogger()


# Exemplo de uso
if __name__ == "__main__":
    # Logger estruturado
    log = get_logger(__name__)
    log.info("Bot iniciado", version="1.0", environment=settings.ENVIRONMENT)
    log.warning("Token do Instagram expira em 7 dias", days_left=7)
    
    # Logger de arquivo
    file_log = FileLogger("test")
    file_log.info("Teste de log em arquivo")
    file_log.error("Erro de teste", error_code=500)
    
    # Logger de auditoria
    audit_logger.log(
        action="CREATE_POST",
        user="admin",
        details={"platform": "instagram", "post_id": "123"}
    )
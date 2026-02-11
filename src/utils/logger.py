"""
Configuration du système de logging professionnel.

Utilise Loguru pour un logging structuré et performant.
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional


class LoggerConfig:
    """Configuration centralisée du logger."""
    
    def __init__(
        self,
        level: str = "INFO",
        log_file: Optional[str] = None,
        rotation: str = "100 MB",
        retention: str = "30 days",
        format_type: str = "text"
    ):
        """
        Initialise la configuration du logger.
        
        Args:
            level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Chemin du fichier de log
            rotation: Taille de rotation des logs
            retention: Durée de rétention des logs
            format_type: Type de format (text ou json)
        """
        self.level = level
        self.log_file = log_file
        self.rotation = rotation
        self.retention = retention
        self.format_type = format_type
        
        # Supprimer les handlers par défaut
        logger.remove()
        
        # Configurer le logger
        self._setup_logger()
    
    def _setup_logger(self):
        """Configure les handlers du logger."""
        # Format pour la console (coloré et lisible)
        console_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        # Format JSON pour les fichiers (structuré)
        json_format = (
            "{{"
            '"timestamp": "{time:YYYY-MM-DD HH:mm:ss}", '
            '"level": "{level}", '
            '"logger": "{name}", '
            '"function": "{function}", '
            '"line": {line}, '
            '"message": "{message}"'
            "}}"
        )
        
        # Handler console
        logger.add(
            sys.stdout,
            format=console_format,
            level=self.level,
            colorize=True
        )
        
        # Handler fichier (si spécifié)
        if self.log_file:
            log_path = Path(self.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            format_to_use = json_format if self.format_type == "json" else console_format
            
            logger.add(
                self.log_file,
                format=format_to_use,
                level=self.level,
                rotation=self.rotation,
                retention=self.retention,
                compression="zip",
                serialize=self.format_type == "json"
            )
    
    @staticmethod
    def get_logger():
        """Retourne l'instance du logger."""
        return logger


# Fonction helper pour obtenir le logger
def get_logger():
    """
    Retourne le logger configuré.
    
    Usage:
        from utils.logger import get_logger
        logger = get_logger()
        logger.info("Message")
    """
    return logger


# Décorateur pour logger les appels de fonction
def log_function_call(func):
    """
    Décorateur pour logger automatiquement les appels de fonction.
    
    Usage:
        @log_function_call
        def ma_fonction(param1, param2):
            pass
    """
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {e}")
            raise
    return wrapper
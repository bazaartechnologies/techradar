"""
Configuration management for Tech Radar ETL.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """Manages configuration from YAML and environment variables."""

    def __init__(self, config_path: str = None):
        """
        Initialize configuration.

        Args:
            config_path: Path to config YAML file
        """
        # Load environment variables
        load_dotenv()

        # Load YAML config
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                '..',
                'config',
                'config.yaml'
            )

        self.config_path = config_path
        self.config = self._load_yaml(config_path)

        # Validate configuration
        self._validate()

    def _load_yaml(self, path: str) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {path}")
                return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML configuration: {e}")
            raise

    def _validate(self) -> None:
        """Validate configuration and environment variables."""
        errors = []

        # Check required environment variables
        if not os.getenv('GITHUB_TOKEN'):
            errors.append("GITHUB_TOKEN environment variable not set")

        if not os.getenv('OPENAI_API_KEY'):
            errors.append("OPENAI_API_KEY environment variable not set")

        # Check required config sections
        required_sections = ['github', 'openai', 'classification', 'output']
        for section in required_sections:
            if section not in self.config:
                errors.append(f"Missing required config section: {section}")

        # Check GitHub organizations
        if not self.config.get('github', {}).get('organizations'):
            errors.append("No GitHub organizations configured")

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("Configuration validated successfully")

    def get_github_token(self) -> str:
        """Get GitHub token from environment."""
        return os.getenv('GITHUB_TOKEN')

    def get_openai_key(self) -> str:
        """Get OpenAI API key from environment."""
        return os.getenv('OPENAI_API_KEY')

    def get_output_path(self) -> Path:
        """Get output file path."""
        output_file = self.config['output']['file']

        # If relative path, make it relative to data-etl directory
        if not os.path.isabs(output_file):
            base_dir = os.path.dirname(os.path.dirname(__file__))
            output_file = os.path.join(base_dir, output_file)

        return Path(output_file)

    def get_log_path(self) -> Path:
        """Get log file path."""
        log_file = self.config.get('logging', {}).get('file', 'logs/scan.log')

        # If relative path, make it relative to data-etl directory
        if not os.path.isabs(log_file):
            base_dir = os.path.dirname(os.path.dirname(__file__))
            log_file = os.path.join(base_dir, log_file)

        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        return log_path

    def get_checkpoint_path(self) -> Path:
        """Get checkpoint file path."""
        checkpoint_file = self.config.get('checkpoint', {}).get('file', '.scan_progress.json')

        # If relative path, make it relative to data-etl directory
        if not os.path.isabs(checkpoint_file):
            base_dir = os.path.dirname(os.path.dirname(__file__))
            checkpoint_file = os.path.join(base_dir, checkpoint_file)

        return Path(checkpoint_file)

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access to config."""
        return self.config[key]

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value with default."""
        return self.config.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary."""
        return self.config.copy()


def setup_logging(config: Config) -> None:
    """
    Setup logging based on configuration.

    Args:
        config: Config instance
    """
    log_config = config.get('logging', {})
    log_level = getattr(logging, log_config.get('level', 'INFO'))
    log_path = config.get_log_path()
    console = log_config.get('console', True)

    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    logger.info(f"Logging initialized. Log file: {log_path}")

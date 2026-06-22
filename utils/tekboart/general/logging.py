# My custom logging module

import sys
import logging
import logging.config

logger = logging.getLogger(__name__)

def configure_logging(file_path: str = 'logs/main.log', verbosity: str = 'default',
                      log_lvl_console: str = 'INFO', log_lvl_file: str = 'DEBUG'):
    """
    Configures the logging system for the application.

    Args:
        file_path (str): The file path for the log file. Default is 'logs/main.log'.
        verbosity (str): The verbosity level for log output. Choose between 'default', 'verbose', or 'clean'.
                         Default is 'default'.
        log_lvl_console (str): The log level for the console handler. Default is 'INFO'.
        log_lvl_file (str): The log level for the file handler. Default is 'DEBUG'.

    This function sets up:
    - The root logger (__main__) with both 'console' and 'file' handlers.
    - All submodules (imported inside main.py) with only the 'file' handler.

    Example:
        configure_logging(file_path='logs/app.log', verbosity='verbose', log_lvl_console='DEBUG', log_lvl_file='ERROR')
    """
    # List of valid verbosity levels
    verbosity_options = ['default', 'verbose', 'clean']

    # Ensure verbosity is a valid option
    if verbosity not in verbosity_options:
        raise ValueError(f"Verbosity must be one of {verbosity_options}")

    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s - %(filename)s - %(levelname)s - %(message)s'  # Simplified format for default
            },
            'verbose': {
                # 'format': '%(asctime)s - %(filename)s - %(name)s - %(levelname)s - %(message)s - %(funcName)s - %(lineno)d'  # More detailed format
                'format': '%(asctime)s - %(filename)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s - %(lineno)d - %(message)s'  # More detailed format
            },
            'clean': {
                'format': '%(asctime)s - %(levelname)s - %(message)s'  # Simplified format for 'clean' verbosity
            },
        },
        'handlers': {
            'console': {
                'level': log_lvl_console,  # Use the log level for the console handler
                'class': 'logging.StreamHandler',
                'formatter': verbosity,  # Use the selected verbosity level
            },
            'file': {
                'level': log_lvl_file,  # Use the log level for the file handler
                'class': 'logging.FileHandler',
                'filename': file_path,
                'formatter': verbosity,  # Use the selected verbosity level
            },
        },
        # the root logger is a special logger, and any logger that doesn't explicitly have a parent will inherit from the root logger.
        'root': {
            'level': 'DEBUG',  # Set to DEBUG to allow logs through if not handled by the handlers
            'handlers': ['console', 'file'],  # Both handlers for root logger
        },
        'loggers': {
            # Configure the 'main' logger explicitly
            '__main__': {
                'level': 'DEBUG',
                'handlers': ['console', 'file'],  # the handler(s) for the main logger
                'propagate': False,  # Don't propagate to parent loggers
            }
        }
    }
    # Dynamically configure all other submodules (anything other than __main__)
    for key in sys.modules.keys():
        if key != "__main__" and not key.startswith("logging"):
            log_config['loggers'][key] = {
                'level': 'DEBUG',
                'handlers': ['file'],  # the handler(s) for all other loggers
                'propagate': False,
            }

    logging.config.dictConfig(log_config)
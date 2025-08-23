import os

from .development import DevelopmentConfig
from .production import ProductionConfig

config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

env = os.getenv('FLASK_ENV', 'development')
settings = config_by_name[env]

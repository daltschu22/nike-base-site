import os
from dotenv import load_dotenv

# Load environment variables from .env in local development.
load_dotenv()


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'nike_sites.db')
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    DATABASE_PATH = 'test.db'


class ProductionConfig(Config):
    """Production configuration."""

    pass


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}


def get_config():
    env = os.environ.get('APP_ENV', 'default')
    return config.get(env, config['default'])

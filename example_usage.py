from config.manager import ConfigManager
from config.database.settings import DatabaseConfig
from config.cache.settings import CacheConfig
from config.queue.settings import QueueConfig
from config.security.settings import SecurityConfig
from config.settings.environment import EnvironmentConfig, Environment

# Initialize config manager
manager = ConfigManager()

# Register configurations
manager.register('env', EnvironmentConfig(Environment.DEV))
manager.register('db', DatabaseConfig())
manager.register('cache', CacheConfig())
manager.register('queue', QueueConfig(RabbitMQDriver()))
manager.register('security', SecurityConfig())

# Load all configurations
manager.load_all()

# Validate configurations
if manager.validate_all():
    print("All configurations are valid")
else:
    print("Invalid configurations found")

# Get specific configuration
db_config = manager.get_config('db')
db_host = db_config.get('HOST')
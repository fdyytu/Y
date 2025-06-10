from config.settings.manager import settings

# Menggunakan settings
app_name = settings.app.name
jwt_secret = settings.auth.jwt_secret_key
is_dev = settings.environment.is_development

# Mengakses settings berdasarkan environment
if settings.environment.is_production:
    print("Running in production mode")
else:
    print("Running in development mode")
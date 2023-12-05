from pydantic import BaseSettings

class Settings(BaseSettings):
    # General Config
    app_name: str = "Gamification API"
    admin_email: str = "admin@example.com"
    items_per_user: int = 50  # just an example of a custom setting

    # Database Config
    database_url: str

    # Security and Authentication Config
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Add other configurations here
    # ...

    class Config:
        # This is to read the variables from environment variables.
        # For example, 'database_url' can be set as an environment variable.
        env_file = ".env"

# Create an instance of the Settings class which can be imported and used in other parts of the application.
settings = Settings()

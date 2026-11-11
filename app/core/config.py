
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    orthanc_url: str
    orthanc_username: str
    orthanc_password: str

    database_url: str
    jwt_secret_key: str

    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_from_email: str

    class Config:
        env_file = ".env"


settings = Settings()

from pydantic_settings import BaseSettings

class RedisConfig(BaseSettings):        
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None


class Config(BaseSettings):
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        extra = "ignore"
        
    port: int = 3000
    debug: bool = False
    secret_key: str
    redis: RedisConfig
    
config = Config()  # type: ignore
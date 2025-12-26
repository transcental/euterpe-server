from pydantic import RedisDsn
from pydantic_settings import BaseSettings

class RedisConfig(BaseSettings):        
    url: RedisDsn


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
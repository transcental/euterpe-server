from pydantic_settings import BaseSettings

class Config(BaseSettings):
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        extra = "ignore"
        
    port: int = 3000
    debug: bool = False
    secret_key: str
    
config = Config()  # type: ignore
import os
from dotenv import load_dotenv
import yaml
from typing import Any, Dict


class Secrets:
    def __init__(self):
        # Load environment variables from the .env file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        dotenv_path = os.path.join(base_dir, 'config', 'secrets.env')
        load_dotenv(dotenv_path)
        self.cryptocompare_api_key = os.getenv("CRYPTOCOMPARE_API_KEY")
        self.coinbase_api_key = os.getenv("COINBASE_API_KEY")
        self.coinbase_signing = os.getenv("COINBASE_SIGNING_KEY")
        self.database_password = os.getenv("DATABASE_PASSWORD")


class NestedConfig:
    def __init__(self, data: Dict[str, Any]):
        for key, value in data.items():
            if isinstance(value, dict):
                value = NestedConfig(value)
            setattr(self, key, value)

    def to_dict(self):
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, NestedConfig):
                value = value.to_dict()
            result[key] = value
        return result


class Config:
    def __init__(self, config_file: str):
        with open(config_file, "r") as file:
            self._config = yaml.safe_load(file)
        self._nested_config = NestedConfig(self._config)

    def __getattr__(self, item):
        return getattr(self._nested_config, item)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._config
        for k in keys:
            value = value.get(k)
            if value is None:
                return default
        return value


# Load the configuration when the module is imported
secrets = Secrets()
config = Config(dotenv_path)

import os
import yaml

from dataclasses import dataclass
from typing import List, Dict, Any

DEBUG = False

@dataclass
class Config:
    username: str = ''
    password: str = ''
    accounts: List[Dict[str, str]] = None
    search: Dict[str, Any] = None
    output: str = None
    verbose: bool = False

    @classmethod
    def load(cls, filename: str):
        if not os.path.isfile(filename):
            raise FileNotFoundError(f'{filename} not found!')

        with open(filename, 'r') as yaml_file:
            config = yaml.safe_load(yaml_file)

        fields = {
            'username': os.getenv('GPS_USERNAME', ''),
            'password': os.getenv('GPS_PASSWORD', ''),
            'accounts': None,
            'search': None,
            'output': None,
            'verbose': False
        }
        if 'credentials' in config:
            if 'username' in config['credentials'] and not fields['username']:
                fields['username'] = config['credentials']['username']
            if 'password' in config['credentials'] and not fields['password']:
                fields['password'] = config['credentials']['password']
        if 'accounts' in config:
            fields['accounts'] = config['accounts']
        if 'search' in config:
            fields['search'] = config['search']
        if 'download' in config:
            if 'enable' in config['download']:
                if config['download']['enable']:
                    if 'path' in config['download']:
                        fields['output'] = config['download']['path']
        fields['verbose'] = 'verbose' in config and config['verbose']

        return cls(**fields)

    @property
    def has_credentials(self):
        return self.username and self.password

    @property
    def has_accounts(self):
        return self.accounts and True

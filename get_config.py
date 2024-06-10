import importlib.util
from pathlib import Path
from A00_default_config import ParserConfig


# Function to update configuration from a module
def update_config_from_module(config, module):
    for attr_name in dir(module):
        if not attr_name.startswith('__'):
            setattr(config, attr_name, getattr(module, attr_name))

p_filters = Path('filters')
p_filters.mkdir(exist_ok=True)
filters = list(filter(lambda x: x.suffix == '.py', p_filters.iterdir()))

# Load user configurations and update BristolConfig
for fil in filters:
    # Attempt to load user configuration file
    try:
        spec = importlib.util.spec_from_file_location('UserConfigModule', fil)
        user_config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_config_module)
        update_config_from_module(ParserConfig, user_config_module.ParserConfig)
    except (FileNotFoundError, AttributeError):
        pass

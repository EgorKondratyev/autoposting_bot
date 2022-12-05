import logging.config
import yaml
import logging


logger = logging.getLogger('__main__')
with open(r'/home/autoposting_bot/log/config.yml', 'r') as obj:
    logging.config.dictConfig(yaml.safe_load(obj))

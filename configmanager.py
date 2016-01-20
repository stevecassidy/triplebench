"""
This code has been borrowed from the BlackBox application
"""

import os, ConfigParser
import sys

# the configuration key used in the INI file
CONFIG_KEY = "DEFAULT"

__all__ = ['configinit', 'config', 'print_config', 'set_config']

# locate the home dir of the package
homedir = os.path.abspath(os.path.dirname(__name__))

DEFAULT_CONFIG_FILE = os.path.join(homedir, "config.ini")

default_config = { 
    'home': homedir, 
}

config_loaded = False
config = None


def configinit(configfile=DEFAULT_CONFIG_FILE):
  """Load the configuration file """
  
  global config_loaded, config, default_config
  
  if config_loaded:
    return config
  else:
    config = ConfigParser.ConfigParser(default_config) 
    config.read(configfile)
    
    # print 'Initialising Configuration Of File->', configfile
    # print_config()
    
    config_loaded = True
    
 
def set_config(key, value):
  """Set the value for some key in the configuration"""
  global config
  config.set(CONFIG_KEY, key, value)
    
        
def get_config(key, default=''):
  """Get the value for the given key in the configuration
  returning default if there is no such key"""
  global config
  
  if config.has_option(CONFIG_KEY, key):
    return config.get(CONFIG_KEY, key)
  else:
    return default


def print_config():
  """Print out the current configuration"""
  global config
  config.write(sys.stdout)
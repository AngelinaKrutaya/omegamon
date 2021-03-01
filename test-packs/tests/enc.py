from taf.af_support_tools import Config
# Default non-encrypted config config.ini located in TafVars.config_folder_path
m = Config('cred_config.ini')
m.encrypt()
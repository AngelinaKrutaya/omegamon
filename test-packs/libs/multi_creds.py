from taf.af_support_tools import Config

m = Config('multi_config.ini', encrypted=False)
c = m.get_section('zos_credentials')
username = c['username']
password = c['password']
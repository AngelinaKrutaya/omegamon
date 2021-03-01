from taf.af_support_tools import Config

m = Config('cred_config.ini', encrypted=True)
c = m.get_section('zos_credentials')
username = c['mf_user']
password = c['mf_password']


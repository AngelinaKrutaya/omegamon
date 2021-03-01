import os
from libs.creds import *

hostname = 'rsd1'
rte_hlq = 'itm.ite'
rte_name = 'ite1'
omegamon = 'cics'
applid = 'ITE1OC0'
cics_job = 'CICQ55Z1'
stc_job = 'ITE1OC0'


applid = os.environ.get('applid', applid)
hostname = os.environ.get('hostname', hostname)
username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)
rte_hlq = os.environ.get('rte_hlq', rte_hlq)
rte_name = os.environ.get('rte_name', rte_name)

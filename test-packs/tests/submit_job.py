import time

from taf.zos.jes import JESAdapter

from libs.ite1db2 import *
from libs.creds import *
from libs.ivtenv import rtes

rte = os.environ.get('rte', 'ite1')
hostname = rtes[rte]['hostname']
applid = rtes[rte]['tom_applid']

username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)


WAIT_JOB = 'IVT99999'


secs = 90
while True:
    try:
        z = JESAdapter(hostname, username, password)
        job = z.submit_jcl(path_relative=True, path='resources/jobs/wait.jcl',
                           params={'{seconds}': str(secs), '{job}': WAIT_JOB}, wait=True)
        time.sleep(70)
    except:
        print('Exception')
        break

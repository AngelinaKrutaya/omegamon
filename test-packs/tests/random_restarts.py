import random
from libs.utils import *

from taf.zos.jes import JESAdapter
from libs.creds import *


username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)

rsd2_l = ['ITE2C5', 'ITE2D5', 'ITE2I5', 'ITE2MQ', 'ITE2JJ', 'ITE2N3']
rsd4_l = ['ITE4C5', 'ITE4D5', 'ITE4I5', 'ITE4MQ', 'ITE4JJ', 'ITE4N3']

rsd2_j = JESAdapter('rsd2', username, password)
rsd4_j = JESAdapter('rsd4', username, password)


logger = logging.getLogger(__name__)


def restart(host, j_l, jes_a):
    stc1 = random.choice(j_l)
    print(f'Restarting {stc1}')
    jes_a.submit_jcl(text=stop_start.replace('#CMD#', 'P').replace('#JOB#', stc1))
    wait_job_to_finish(host, username, password, stc1)
    jes_a.submit_jcl(text=stop_start.replace('#CMD#', 'S').replace('#JOB#', stc1))


logger.info('Start')
count = 0
try:
    while True:
        count += 1
        restart('rsd2', rsd2_l, rsd2_j)
        restart('rsd4', rsd4_l, rsd4_j)
        time.sleep(60)
finally:
    logger.info(f'Stop, ran {count} times')

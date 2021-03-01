import os
import time
import random
import string

from taf.zos.jes import JESAdapter

from libs.soapreq import SoapReq
from libs.ivtenv import rtes
from libs.creds import *

rte = os.environ.get('rte', 'ite4')
username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)

soapreq = SoapReq(rtes[rte]['hostname'], rtes[rte]['tems_http'])


'''
N = Reset
Y = Raised
P = Stopped
S = Started
X = Error
D = Deleted
A = Ack
E = Resurfaced
F = Expired
'''


def sit_get_status(sit_name):
    soap_req = f'''
    <table>O4SRV.UTCTIME</table>
    <sql>
    SELECT DELTASTAT FROM O4SRV.ISITSTSH 
    WHERE SITNAME='{sit_name}' ORDER BY GBLTMSTMP DESC
    </sql>
    '''
    res = soapreq.get(soap_req)
    # res looks like <ROW><DELTASTAT>S</DELTASTAT></ROW>
    if res:
        start = res.index('<DELTASTAT>')
        status = res[start+11]
        return status
    else:
        False


def sit_is_raised(sit_name):
    return True if sit_get_status(sit_name) == 'Y' else False


# started or reset
def sit_is_started(sit_name):
    return True if sit_get_status(sit_name) in ['S', 'N'] else False


def sit_is_started_or_raised(sit_name):
    return True if sit_get_status(sit_name) in ['Y', 'S'] else False


# situation is not true anymore
def sit_is_reset(sit_name):
    return True if sit_get_status(sit_name) == 'N' else False


# TESTS ------------------------------------------


def test_sit_always_true():
    assert sit_is_raised('IVT_DP_Always_True')


def test_sit_always_false():
    sit = 'IVT_DP_Always_False'
    # started means it is not raised
    assert sit_is_started(sit)
    # assert not sit_is_raised(sit)


# sit expect specific job name
def test_sit_can_be_true():
    sit = 'IVT_M5_Can_Be_True'
    assert sit_is_started(sit)
    z = JESAdapter(rtes[rte]['hostname'], username, password)
    job = z.submit_jcl(path_relative=True, path='resources/jobs/wait.jcl',
                       params={'{seconds}': '60', '{job}': 'IVTCANTR'}, wait=False)
    time.sleep(50)
    assert sit_is_raised(sit)
    time.sleep(65)
    assert sit_is_reset(sit)


def test_verify_utf8_sit_message():
    """
    https://jira.rocketsoftware.com/browse/ITMZ-1111
    IVT_M5_SOAP_UTF8 sit already creted, so it is triggered
    and then we check that message is readable
    :return:
    """
    sit = 'IVT_M5_SOAP_UTF8'
    source = 'ITE4RSD4:RSD4:MVSSYS'
    message = 'Message text related to ITMZ-1111'
    # generate random item_id to make sure we will check exactly this
    item_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=9))
    # rise the situation
    soapreq.alert(sit, source, message, item_id)
    # check result, this sql was found by tracing TEPS, result is:
    # <RESULTS><![CDATA[*PREDICATE=SYSTEM.PARMA("SITNAME", "IVT_M5_SOAP_UTF8", 13);
    # KRAMESG.MESSAGE="Message text related to ITMZ-1111";KRAMESG.SEVERITY=1;KRAMESG.CATEGORY=Critical]]></RESULTS>

    sql = f"""
    SELECT RESULTS FROM O4SRV.TSITSTSH WHERE (SITNAME = '{sit}') 
    AND (ORIGINNODE = '{source}') AND (ATOMIZE = '{item_id}')
    """
    soap_req = f'''
    <table>O4SRV.UTCTIME</table>
    <sql>{sql}</sql>
    '''
    res = soapreq.get(soap_req)
    assert message in res
    # reset sit
    soapreq.reset(sit, source, item_id)


import os
import requests
import pytest
from libs.ivtenv import rtes
from libs.soapreq import SoapReq, SoapException

from libs.creds import *


rte = 'ite4'
rte = os.environ.get('rte', rte)

hostname = rtes[rte]['hostname']
port = rtes[rte]['tems_http']
host_p = f"http://{rtes[rte]['hostname']}:{rtes[rte]['tems_http']}"
action = '/kdh/console/command.html'


success_mess = '</SOAP-CHK:Success></SOAP-ENV:Body></SOAP-ENV:Envelope>'
fail_mess = '<faultstring>CMS logon validation failed.</faultstring>'


@pytest.mark.parametrize("pwd, expected", [
    (c['mf_password'], success_mess),
    (c['mf_passphrase'], success_mess),
],
                         ids=[
                             'soap_password_ok',
                             'soap_passphrase_ok',
                              ]
                         )
def test_soap_login_ok(pwd, expected):
    """
    Verify password and passphrase auth in soap
    :param pwd:
    :param expected:
    :return:
    """
    soapreq = SoapReq(hostname, port, username, pwd)
    soap_req = '''
    <object>ManagedSystem</object><target>ManagedSystemName</target>
    '''
    res = soapreq.get(soap_req)
    assert expected in res


@pytest.mark.parametrize("pwd, expected", [
    ('short', fail_mess),
    ('long567890', fail_mess),
],
                         ids=[
                              'soap_password_incorrect',
                              'soap_passphrase_incorrect',
                              ]
                         )
def test_soap_login_fail(pwd, expected):
    """
    Verify that incorrect password and passphrase fail to auth in soap
    :param pwd:
    :param expected:
    :return:
    """
    soapreq = SoapReq(hostname, port, username, pwd)
    soap_req = '''
    <object>ManagedSystem</object><target>ManagedSystemName</target>
    '''
    with pytest.raises(SoapException) as excinfo:
        # this is the last executed line inside "with"
        soapreq.get(soap_req)
    assert expected in str(excinfo.value)


@pytest.mark.parametrize("pwd, expected", [
    (c['mf_password'], 200),
    (c['mf_passphrase'], 200),
    ('short', 401),
    ('long56789012345', 401),
],
                         ids=[
                             'console_password_ok',
                             'console_passphrase_ok',
                             'console_password_incorrect',
                             'console_passphrase_incorrect',
                              ]
                         )
def test_tems_console_login(pwd, expected):
    """
    Verify correct and incorrect password and passphrase auth in web console
    :param pwd:
    :param expected:
    :return:
    """
    web_session = requests.Session()
    web_session.auth = (username, pwd)
    r = web_session.get(host_p + action,
                        data={'command1': 'res1'}
                        )
    assert expected == r.status_code

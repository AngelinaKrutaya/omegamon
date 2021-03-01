import socket
import time
import os

from libs.ivtenv import rtes
from libs.soapreq import SoapReq
from libs.creds import *

rte = 'ite4'
rte = os.environ.get('rte', rte)
hostname = rtes[rte]['hostname']
port = rtes[rte]['tems_http']
db2 = rtes[rte]['db2']

def netcat(host, port, content):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, int(port)))
    s.sendall(content.encode())
    time.sleep(1)
    s.shutdown(socket.SHUT_WR)
    res = b''
    while True:
        resp = s.recv(4096)
        res += resp
        if not resp:
            break
    s.close()
    return res.decode()


def test_simple_soap():
    soapreq = SoapReq(hostname, port)
    soap_req = '''
    <object>ManagedSystem</object><target>ManagedSystemName</target>
    '''
    res = soapreq.get(soap_req)
    assert f'<Managing_System>{rte.upper()}:CMS</Managing_System>' in res
    assert '</SOAP-CHK:Success></SOAP-ENV:Body></SOAP-ENV:Envelope>' in res


def test_raw_request():
    """
    https://jira.rocketsoftware.com/browse/ITMZ-1275
    check that raw request, which is produced by netview, returned not "chunked"
    :return:
    """
    data = f'''
    <CT_Get><userid>{username}</userid><password>{password}</password>
    <table>O4SRV.LOCALTIME</table><sql>SELECT
     LCLTMSTMP,FULLNAME,ATOMIZE,NODE,ORIGINNODE,DELTASTAT FROM
     O4SRV.ISITSTSH WHERE DELTASTAT = 'X'</sql></CT_Get>      '''

    headers = f'POST http://{hostname}:{port}///cms/soap HTTP/1.1\n' \
              f'Host: {hostname}\n' \
              f'Content-length: {len(data)}\n' \
              f'Content-type: text/xml\n\n'

    r = netcat(hostname, port, headers + data)
    assert ('SOAP-CHK:Succes' in r and 'chunked' not in r.lower()), f'Expected is not found in:\n{r}'


def test_db2_workspaces_consists_no_duplicate_values():
    """
    https://jira.rocketsoftware.com/browse/ITMZ-1566
    Testing if there are no duplicate values displayed in DB2 workspace KDPSQL1.
    """
    soapreq = SoapReq(hostname, port)
    soap_req = f'''
    <table>KDP.STATQXST</table><sql>SELECT ORIGINNODE, FIELDNAME,
        MVSID, DB2ID, SEQUENCE,
        VALUE, DELTA, RATE, INTRVAL
        FROM KDP.STATQXST
        WHERE FIELDNAME = "QXSELECT"
        OR FIELDNAME = "QXINSRT "
        OR FIELDNAME = "QXUPDTE "
        OR FIELDNAME = "QXMERGE "
        OR FIELDNAME = "QXDELET "
        OR FIELDNAME = "QXOPEN  "
        OR FIELDNAME = "QXCLOSE "
        OR FIELDNAME = "QXFETCH "
        OR FIELDNAME = "QXPREP  "
        OR FIELDNAME = "QXDESC  "
        OR FIELDNAME = "QXDSCRTB"
        OR FIELDNAME = "QXRWFETC"
        OR FIELDNAME = "QXRWINST"
        OR FIELDNAME = "QXRWUPDT"
        OR FIELDNAME = "QXRWDELT"
        OR FIELDNAME = "QXREFTBL"
        OR FIELDNAME = "SSCDMLZ "
        OR FIELDNAME = "SSCDML  "
        AND ORIGINNODE ="{db2}:{hostname.upper()}:DB2"
        ORDER BY SEQUENCE  ASC;</sql>
    '''
    res = soapreq.get(soap_req)
    count = res.count('</ROW>')
    assert count == 17
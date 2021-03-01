import os
import pytest
import re
import datetime
import logging

from libs.ivtenv import rtes
from libs.soapreq import SoapReq


logger = logging.getLogger(__name__)


# from C:\IBM\ITM\CNPS\dockdp
# *OBJECT:   ALL_THREADS

# target = '*HUB'

db2_target = 'IB1D:RSD4:DB2'
cics_target = 'RSD4.CICQ55Z4'
ims_target = 'IEK4:RSD4:IMS'
jvm_target = 'ITE4:RSD4:JVM'
mfn_target = 'TCPIP:RSD4'
mq_target = 'Q490:RSD4:MQESA'
mqi_target = 'RSD4:KQIA'
mqb_target = 'Q490BRK::KQIB'
mvs_target = 'RSPLEXL4:RSD4:MVSSYS'
s3_target = 'ITE4DS:RSD4:STORAGE'


rte = os.environ.get('rte', 'ite4')
target_env = os.environ.get('target_env', 'QA').upper()


# for dev, they need to provide host:port in Jenkins job
if target_env == 'DEV':
    soapreq = SoapReq(os.environ['hostname'], os.environ['tems_http'])
    db2_target = cics_target = ims_target = jvm_target = mfn_target = mq_target = mqi_target = \
        mqb_target = mvs_target = s3_target = ''
else:
    soapreq = SoapReq(rtes[rte]['hostname'], rtes[rte]['tems_http'])


def run_soap_for_history(soap_req) -> bool:
    res = soapreq.get(soap_req)
    logger.debug(res)
    values = set()
    # find all write_time and check that we have differences, means we have more than 1 history period
    for m in re.finditer(r'<Write_Time>(?P<value>[0-9]+)</Write_Time>', res):
        values.add(m.group('value'))
    logger.debug(values)
    return len(values) > 1


product_parameters = [
    (db2_target, 'ALL_THREADS', ['Plan', 'Elapsed_Time', 'Cancel_Command']),
    (db2_target, 'Storage_Consumption', ['24_Bit_Low_Private', '24_Bit_High_Private']),
    (cics_target, 'CICSplex_DB2_Summary', ['Attached_to_DB2', 'DB2_Subsystem_Name']),
    (cics_target, 'CICSplex_Transaction_Analysis', ['Transaction_ID', 'Task_Number']),
    (ims_target, 'IMS_Health', ['IMS_ID', 'FF_ENQ_Rate']),
    (ims_target, 'Address_Spaces', ['IMS_ID', 'Job_Name']),
    (jvm_target, 'JVM_Address_Space', ['Job_Name', 'Process_ID']),
    (jvm_target, 'JVM_CPU', ['Job_Name', 'Process_ID']),
    (mfn_target, 'TCPIP_Address_Space', ['Host_IP_Address', 'CSA_Usage_Below_16MB']),
    (mfn_target, 'TCPIP_Applications', ['Application_Name', 'Connection_Count']),
    (mq_target, 'Application_Statistics', ['Application_Identifier', 'Application_Type']),
    (mq_target, 'Buffer_Pools', ['Pool_ID', 'Number_of_Buffers']),
    (mqi_target, 'Components', ['Component', 'Process_Identifier']),
    (mqb_target, 'Broker_Status', ['Broker_U', 'Broker_Status']),
    (mvs_target, 'Address_Space_Summary', ['Address_Space_Count', 'Started_Task_Count']),
    (mvs_target, 'Common_Storage', ['Area', 'Allocation']),
    (s3_target, 'S3_Application_Monitoring', ['Application', 'ASID']),
    (s3_target, 'S3_Channel_Path', ['Path_ID', 'Status']),

]


@pytest.mark.parametrize("target, s_object, attributes", product_parameters)
def test_products(target, s_object, attributes):
    soap_req = f'''
        <target>{target}</target>
        <object>{s_object}</object>
        '''
    for atr in attributes:
        soap_req += f'<attribute>{atr}</attribute>'

    res = soapreq.get(soap_req)
    # checking that the data is returned, e.g we have <ROW>...</ROW>
    assert '</ROW>' in res


# remove MQ normal wks
product_parameters_history = [(t, w) for t, w, a in product_parameters if w not in
                              ('Application_Statistics', 'Buffer_Pools')]
# add mq history wks
product_parameters_history.extend([(mq_target, 'Application_Long-Term_History'),
                                   (mq_target, 'Buffer_Manager_Long-Term_History')])


@pytest.mark.skipif(target_env == 'DEV', reason="skip history for dev")
@pytest.mark.parametrize("target, s_object", product_parameters_history)
def test_products_history(target, s_object):
    """
    RTE needs to run at least 1 hour, as we check that there at least 2 periods of history and history is collected
    every 30 minutes. However, agents do not connect to the TEMS right after start,
    so it's better if RTE runs several hours.
    :param target:
    :param s_object:
    :return:
    """
    history_from = '1' + (datetime.datetime.now() - datetime.timedelta(minutes=80)).strftime('%y%m%d%H')
    soap_req = f'''
        <target>{target}</target>
        <object>{s_object}</object>
        <history>Y</history>
        '''
    soap_req += f'<afilter>write_time;GE;{history_from}</afilter>'
    assert run_soap_for_history(soap_req)


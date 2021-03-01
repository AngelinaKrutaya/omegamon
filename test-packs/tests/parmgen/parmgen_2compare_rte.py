import os
import re
import allure
import pytest
from taf.zos.zosmflib import zOSMFConnector
from taf.zos.jes import JESAdapter

import logging

from libs.parmgen import Parmgen
from libs.creds import *

hostname = Parmgen.exec_host
username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)

rte_hlq_1 = 'ITM.ITE.ITE1'
rte_hlq_2 = 'ITM.ITE.ITP1'

logger = logging.getLogger(__name__)

jes_adapter = JESAdapter(hostname, username, password)
zsmf = zOSMFConnector(hostname, username, password)

jcl_compare_word = '''
//IEBCOMPR JOB NOTIFY=&SYSUID  
//COMPARE  EXEC PGM=ISRSUPC,
// PARM=('WORDCMP,DELTAL')
//NEWDD DD DSN=#NEWDS#,
//         DISP=SHR
//OLDDD DD DSN=#OLDDS#,
//         DISP=SHR
//OUTDD  DD SYSOUT=*
/*
'''


@allure.step('Added new dataset: {dataset}')
def show_new_datasets(dataset, members, type):
    pass


@allure.step('Datasets does not exists in {rte}')
def show_exclude_datasets(dataset, rte):
    assert False


@allure.description("Show the differences between two rte after their compare")
@pytest.mark.parametrize("rte1_mask,rte2_mask", [(rte_hlq_1, rte_hlq_2)])
def test_compare_rte(rte1_mask, rte2_mask):
    '''

    :param rte1_mask: name of hlq the first rte to which the second is compared (for example: 'ITM.ITE.ITP1')
    :param rte2_mask: name of hlq the second rte (for example: 'ITM.ITE.ITP2')
    :return:
    See report from folder './report'. Can see using command 'allure serve report' from cmd.
    Showed new created datasets in second rte that not exist in first rte.
    Showed datasets that were in first rte and excluded from second rte.
    Added attachment files with differents between members in the same datasets rtes.
    '''
    datasets_rte1 = list(zsmf.list_ds(ds_mask=f'{rte1_mask}.R*') + zsmf.list_ds(ds_mask=f'{rte1_mask}.W*'))
    datasets_rte2 = list(zsmf.list_ds(ds_mask=f'{rte2_mask}.R*') + zsmf.list_ds(ds_mask=f'{rte1_mask}.W*'))
    ps_ds_rte2 = []
    rte2_ds = {}
    exclude_ds = {}
    # search vsam ds and add their to array
    vsam_ds_rte1 = [re.findall(r'(?<=[\w+].)\w+', datasets_rte1.pop(datasets_rte1.index(dataset) - 1))[-1] for dataset
                    in
                    datasets_rte1 if re.findall(r'(?<=[\w+].)\w+', dataset)[-1] == 'DATA']
    vsam_ds_rte2 = [re.findall(r'(?<=[\w+].)\w+', datasets_rte2.pop(datasets_rte2.index(dataset) - 1))[-1] for dataset
                    in
                    datasets_rte2 if re.findall(r'(?<=[\w+].)\w+', dataset)[-1] == 'DATA']
    for dataset in datasets_rte2:
        members = zsmf.list(dataset=dataset)
        # check datasets for PO and PS
        if members:
            rte2_ds.update({re.findall(r'(?<=[\w+].)\w+', dataset)[-2]: members})
        else:
            ps_ds_rte2.append(re.findall(r'(?<=[\w+].)\w+', dataset)[-2])
    for dataset in datasets_rte1:
        # check for all ds without vsam
        if dataset == re.findall(r'\w+.\w+.\w+.\w+', dataset)[0]:
            members = zsmf.list(dataset=dataset)
            name = re.findall(r'(?<=[\w+].)\w+', dataset)[-1]
            if members:
                try:
                    diff = list(set(members) - set(rte2_ds[name]))
                    if diff:
                        show_new_datasets(dataset, diff, 'PO')
                    diff = list(set(rte2_ds[name]) - set(members))
                    if diff:
                        exclude_ds.update({dataset: diff})
                    res = jes_adapter.submit_jcl(
                        text=jcl_compare_word.replace('#OLDDS#', f'{rte2_mask}.{name}').replace('#NEWDS#',
                                                                                                f'{dataset}'))
                    if res.rc != '0000':
                        allure.attach(jes_adapter.get_job_output(job_name=res.jobname, job_id=res.jobid,
                                                                 utf_8_errors='ignore'), name,
                                      allure.attachment_type.TEXT)
                except KeyError:
                    show_new_datasets(dataset, members, 'PO')
            else:
                # check datasets that exist in rte1 but not in rte2
                if name not in ps_ds_rte2:
                    show_new_datasets(dataset, '', 'PS')
    for member in set(vsam_ds_rte1) - set(vsam_ds_rte2):
        show_new_datasets(f'{rte1_mask}.{member}', '', 'VSAM')
    for member in set(vsam_ds_rte2) - set(vsam_ds_rte1):
        exclude_ds.update({f'{rte2_mask}.{member} -- VSAM': ''})
    if exclude_ds:
        show_exclude_datasets(
            ',\n '.join("Dataset: {!s} \n Members: {!r}".format(ds, memb) for (ds, memb) in exclude_ds.items()),
            rte1_mask)

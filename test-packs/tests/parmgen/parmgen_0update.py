import os
import pytest
import re
import allure
from taf.zos.jes import JESAdapter

import logging

from libs.parmgen import Parmgen, ParmException
from libs.creds import *
from libs.ivtenv import rtes
from taf.zos.zosmflib import zOSMFConnector

rtes_ = ('itp2',)

hostname = Parmgen.exec_host
username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)

logger = logging.getLogger(__name__)

"""
itp1:old share
itp2: old full
itp3: will be new - _ $MDLHFV   Full RTE w/ Static Hub TEMS/Agents w/ variables. 
"""

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


@allure.step("Datasets does not exists in new rte")
def show_exclude_datasets(dataset, rte):
    assert False


def update_rte(rte_):
    hlq_ = rtes[rte_]['rte_hlq']

    rte1_ = Parmgen(username, password, hlq_[0:hlq_.rfind('.')], rte_, rte_model=rtes[rte_]['rte_model'],
                   rte_products=rtes[rte_]['rte_products'], rte_type=rtes[rte_]['type'])
    try:
        rte1_.logon()
        rte1_.full_update()
        return rte1_
    finally:
        rte1_.logoff()


# UPDATE RTE(s) #########################


# delete ITP3 rte
hlq = rtes['itp3']['rte_hlq']

# create new itp3, add to the list
new_rte = 'itp3'
itp3 = Parmgen(username, password, hlq[0:hlq.rfind('.')], new_rte, is_new=True, rte_model=rtes[new_rte]['rte_model'],
               rte_products=rtes[new_rte]['rte_products'])

try:
    itp3.logon()
    itp3.full_update()
finally:
    itp3.logoff()


##########################################


# Prepare parameters list: (rte_name, step, result)





def test_delete_rte():
    assert rte_del_result


@allure.description("Show the differences between archive rte and updated rte")
@pytest.mark.parametrize("rte_name", [_ for _ in rtes_ if _ != new_rte])
def test_compare_rte(rte_name):
    jes_adapter = JESAdapter(hostname, username, password)
    zosmf = zOSMFConnector(hostname, username, password)
    datasets_back = zosmf.list_ds(ds_mask=f'ITM.PARM.ARCH.{rte_name.upper()}.*')
    last_gdg = []
    ps_ds_back = []
    exclude_ds = {}
    old_ds = {}
    datasets_new = [dataset for dataset in zosmf.list_ds(ds_mask=f'{rtes[rte_name]["rte_hlq"]}.R*') + zosmf.list_ds(
        ds_mask=f'{rtes[rte_name]["rte_hlq"]}.W*') + zosmf.list_ds(ds_mask=f'{rtes[rte_name]["rte_hlq"][:-4]}BASE.R*')]
    # search vsam ds and add their to array
    vsam_ds_new = [re.findall(r'(?<=[\w+].)\w+', datasets_new.pop(datasets_new.index(dataset) - 1))[-1] for dataset in
                   datasets_new if re.findall(r'(?<=[\w+].)\w+', dataset)[-1] == 'DATA']
    vsam_ds_back = [re.findall(r'(?<=[\w+].)\w+', ds)[-2] for ds in
                    list(zosmf.list_ds(ds_mask=f'ITM.PARM.ARCH.{rte_name.upper()}.*.VSAM'))]
    for dataset in datasets_back:
        if dataset == re.findall(r'\w+.\w+.\w+.\w+.\w+', dataset)[0] and dataset not in vsam_ds_back:
            try:
                last_gdg.append(zosmf.list_ds(ds_mask=f'{dataset}(0)')[0])
            except:
                logging.error(f'Generation does not found for {dataset}')
    gdg_name = re.findall(r'(?<=[\w+].)\w+', last_gdg[0])[-1]
    for dataset in last_gdg:
        members = zosmf.list(dataset=dataset)
        # check datasets for PO and PS
        if members:
            old_ds.update({re.findall(r'(?<=[\w+].)\w+', dataset)[-2]: members})
        else:
            ps_ds_back.append(re.findall(r'(?<=[\w+].)\w+', dataset)[-2])
    for dataset in datasets_new:
        # check for all ds without vsam
        if dataset == re.findall(r'\w+.\w+.\w+.\w+', dataset)[0]:
            members = zosmf.list(dataset=dataset)
            name = re.findall(r'(?<=[\w+].)\w+', dataset)[-1]
            if members:
                try:
                    diff = list(set(members) - set(old_ds[name]))
                    if diff:
                        show_new_datasets(dataset, diff, 'PO')
                    diff = list(set(old_ds[name]) - set(members))
                    if diff:
                        exclude_ds.update({dataset: diff})
                    res = jes_adapter.submit_jcl(
                        text=jcl_compare_word.replace('#OLDDS#', f'ITM.PARM.ARCH.{rte_name.upper()}.'
                        f'{name}.{gdg_name}').replace('#NEWDS#', f'{dataset}'))
                    if res.rc != '0000':
                        allure.attach(
                            jes_adapter.get_job_output(job_name=res.jobname, job_id=res.jobid, utf_8_errors='ignore'),
                            name,
                            allure.attachment_type.TEXT)
                except KeyError:
                    show_new_datasets(dataset, members, 'PO')
            else:
                # check added new datasets after updates rte
                if name not in ps_ds_back:
                    show_new_datasets(dataset, '', 'PS')
    for member in set(vsam_ds_new) - set(vsam_ds_back):
        show_new_datasets(f'{rtes[rte_name]["rte_hlq"].upper()}.{member}', '', 'VSAM')
    for member in set(vsam_ds_back) - set(vsam_ds_new):
        exclude_ds.update({f'{rtes[rte_name]["rte_hlq"].upper()}.{member} -- VSAM': ''})
    if exclude_ds:
        show_exclude_datasets(',\n '.join("Dataset: {!s} \n Members: {!r}".format(ds, memb)
                                      for (ds, memb) in exclude_ds.items()), rte_name)


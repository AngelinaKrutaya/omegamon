import os
import re
from taf.zos.zosmflib import zOSMFConnector
from taf.zos.jes import JESAdapter
from libs.rte import RteType

import logging

from libs.parmgen import Parmgen
from libs.creds import *
from libs.ivtenv import rtes

rtes_ = ('itp1', 'itp2')

hostname = Parmgen.exec_host
username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)

logger = logging.getLogger(__name__)

zsmf = zOSMFConnector(hostname, username, password)
jes_adapter = JESAdapter(hostname, username, password)

gdg_delete = '''
//IVTGDGXX JOB (ACCOUNT),'',CLASS=A,               
//         MSGCLASS=X,REGION=0M 
//STEP010 EXEC PGM=IDCAMS
//SYSPRINT DD SYSOUT=*
//SYSIN DD *
    DELETE #OUTDS#
    DELETE #OUTDS# GENERATIONDATAGROUP PURGE 
    IF MAXCC <= 8 THEN SET MAXCC = 0
'''

gdg_define = '''
//IVTGDGXX JOB (ACCOUNT),'',CLASS=A,               
//         MSGCLASS=X,REGION=0M 
//IDCAMS EXEC PGM=IDCAMS           
//SYSPRINT DD SYSOUT=*             
//SYSIN DD *                       
 DEFINE GDG (NAME(#NEWDS#) -
 LIMIT(5) -                        
 NOEMPTY -                          
 SCRATCH)                           
//* 
'''

gdg = '''
//IVTGDGXX JOB (ACCOUNT),'',CLASS=A,               
//         MSGCLASS=X,REGION=0M                                            
//STEP010 EXEC PGM=IEBCOPY                        
//SYSPRINT DD SYSOUT=*                             
//SYSIN DD DUMMY                                   
//SYSUT1 DD DSN=#INDS#,DISP=SHR     
//*                                *                                  
//SYSUT2 DD DSN=#OUTDS#(+1), 
// DISP=(NEW,CATLG,DELETE),          
// LIKE=#INDS#       
//SYSIN    DD   *
   COPY OUTDD=SYSUT1,INDD=SYSUT2                
//SYSOUT DD SYSOUT=*                 
//SYSUDUMP DD SYSOUT=*                           
/*'''


class SubmittedJob:
    def __init__(self, message=None, **kwargs):
        self.message = message
        self.kwargs = kwargs

    def check(self):
        if self.kwargs['rc'] != '0000':
            logger.error(
                f' Job {self.kwargs["jobid"]} failed with {self.kwargs["rc"]} code for {self.kwargs["dataset"]} ')
        elif self.message and self.kwargs["rc"] == '0000':
            logger.info(self.message)

# REMOVE ALL ARCHIVE GDG FILES ####################################
def remove_all_gdg(rte_):
    gdg_ds = [data + '.*' for data in zsmf.list_ds(ds_mask=f'ITM.PARM.ARCH.{rte_.upper()}.*') if
              data == re.findall(r'\w+.\w+.\w+.\w+.\w+', data)[0]]
    vsam_ds = [data for data in zsmf.list_ds(ds_mask=f'ITM.PARM.ARCH.{rte_.upper()}.*.VSAM')]
    for ds in gdg_ds + vsam_ds:
        res = jes_adapter.submit_jcl(text=gdg_delete.replace('#OUTDS#', ds))
        SubmittedJob(rc=res.rc, jobid=res.jobid, dataset=ds).check()

# CREATE GDG DATASETS AND DATASETS FOR VSAM ####################################
def create_gdg(rte_):
    rte_ds = [f"ITM.PARM.ARCH.{rte_.upper()}." + re.findall(rf'\.{rte_.upper()}\.(\S+)(?=$)', dataset)[0]
              for dataset in
              list(zsmf.list_ds(ds_mask=f'{rtes[rte_]["rte_hlq"]}.R*') + zsmf.list_ds(
                  ds_mask=f'{rtes[rte_]["rte_hlq"]}.W*'))]
    shared_ds = [f"ITM.PARM.ARCH.{rte_.upper()}." + re.findall(rf'\.BASE\.(\S+)(?=$)', ds)[0]
                 for ds in list(zsmf.list_ds(ds_mask=f'{rtes[rte_]["shared_ds"]}.R*'))
                 if rtes[rte_]['type'] == RteType.SHARED]
    vsam_ds = [rte_ds.pop(rte_ds.index(dataset) - 1) + '.VSAM' for dataset in
               rte_ds if re.findall(r'(?<=[\w+].)\w+', dataset)[-1] == 'DATA']
    all_datasets = [ds for ds in rte_ds + vsam_ds + shared_ds if
                    re.search(rf'\.{rte_.upper()}\.\w+($|.VSAM)' or ds == re.findall(r'\w+.\w+.\w+.\w+.\w+', ds)[0],
                              ds)]
    for ds in all_datasets:
        if not zsmf.list_ds(ds):
            res = jes_adapter.submit_jcl(text=gdg_define.replace('#NEWDS#', ds))
            SubmittedJob(rc=res.rc, jobid=res.jobid, dataset=ds).check()


# COPY GDG DATASETS ####################################
def copy_gdg(rte_):
    datasets = list(
        zsmf.list_ds(ds_mask=f'{rtes[rte_]["rte_hlq"]}.R*') + zsmf.list_ds(ds_mask=f'{rtes[rte_]["rte_hlq"]}.W*'))
    # create ds for shared rte
    shared_ds = [(dataset, f'ITM.PARM.ARCH.{rte_.upper()}.' + re.findall(r'(?<=[\w+].)\w+', dataset)[-1]) for
                 dataset in list(zsmf.list_ds(ds_mask=f'{rtes[rte_]["rte_hlq"][:-4]}BASE.R*'))
                 if rtes[rte_]['type'] == RteType.SHARED]
    # delete vsam ds, because don't need to make copy for them
    for dataset in datasets:
        if re.search(r'\w+.\w+.\w+.\w+.DATA', dataset):
            datasets.pop(datasets.index(dataset) - 1)
    # create archive ds for rte
    base_ds = [(dataset, f"ITM.PARM.ARCH.{rte_.upper()}." + re.findall(r'(?<=[\w+].)\w+', dataset)[-1]) for dataset in
               datasets if
               dataset == re.findall(r'\w+.\w+.\w+.\w+', dataset)[0]]
    backup_datasets = base_ds + shared_ds
    for new, old in backup_datasets:
        try:
            jcl = jes_adapter.submit_jcl(
                text=gdg.replace('#OUTDS#', old).replace('#INDS#', new))
            SubmittedJob(message=f'Copied gdg datasets from {new} in {old}', rc=jcl.rc, jobid=jcl.jobid,
                         dataset=new).check()
        except TypeError:
            print(f'JCL error for {new}')


if __name__ == '__main__':
    # will switch to True if need to remove all archive datasets
    remove_gdg = False
    for rte in rtes_:
        if remove_gdg:
            remove_all_gdg(rte)
        create_gdg(rte)
        copy_gdg(rte)

import os
import string
from os import listdir
import random
from typing import Tuple
import time
import logging
from taf.af_support_tools import TAFConfig
from taf.zos.jes import JESAdapter
from taf.zos.zosmflib import zOSMFConnector
from taf.zos.py3270 import keys
from typing import List, Union
from taf.zos.zftplib import ZFTP
# from libs.ds import Dataset_ext
import re

root = TAFConfig().testpack_root
logger = logging.getLogger(__name__)

logger = logging.getLogger()
stop_start = """
//IVTAUTXX JOB (ACCOUNT),'',CLASS=A,
//         MSGCLASS=X,REGION=0M   
//*                                              
//STRTCOL  EXEC PGM=SDSF                         
//ISFOUT   DD  SYSOUT=*                          
//ISFIN    DD *                                  
ST                                               
*                                
/#CMD# #JOB#                               
/*
"""


def is_job_active(d):
    active = filter(lambda x: x['status'] == 'ACTIVE', d.values())
    return True if len(list(active)) > 0 else False


def wait_job_to_finish(hostname, username, password, job):
    z = zOSMFConnector(hostname, username, password)
    maxtries = 10
    tries = 1

    while is_job_active(z.list_jobs(prefix=job, owner='*')) and tries < maxtries:
        time.sleep(30)
        tries += 1

    assert tries < maxtries, f'{job} did not stop'


def upload_files_to_pds(con, src, dst):
    for file_name in listdir(src):
        result = con.upload_ds_member(os.path.join(src, file_name), dst + f'({file_name})', recfm='FB', dsorg='PS')


def set_security(hostname, username, password, rte_hlq, rte_name, omegamon, members_dir,
                 jobs_to_submit: Tuple,
                 stc_job: str = None, delay=30):
    # stop the server
    z1 = JESAdapter(hostname, username, password)
    if stc_job is not None:
        z1.submit_jcl(text=stop_start.replace('#CMD#', 'P').replace('#JOB#', stc_job))

    z = zOSMFConnector(hostname, username, password)
    source_dir = os.path.join(root, 'resources', 'members', rte_name, members_dir, omegamon)
    dest_hlq = rte_hlq

    for dir_name in listdir(source_dir):
        dir_path = os.path.join(source_dir, dir_name)
        if os.path.isdir(dir_path):
            for member in listdir(dir_path):
                member_in_dataset = open(os.path.join(dir_path, member), 'r')
                text_in_member = member_in_dataset.read()
                proclib = 'ROCKET.USER.PROCLIB'
                clist = 'ITM.ITE.QA.CLIST'
                if dir_name.upper() == 'PROCLIB':
                    print(f'uploading to {proclib}({member})')
                    z.write_ds(dataset=f'{proclib}({member})', data=text_in_member)
                elif dir_name.upper() == 'CLIST':
                    print(f'uploading to {clist}({member})')
                    z.write_ds(dataset=f'{clist}({member})', data=text_in_member)
                else:
                    print(f'uploading to {dest_hlq}.{dir_name}({member})')
                    z.write_ds(dataset=f'{dest_hlq}.{dir_name}({member})', data=text_in_member)
                member_in_dataset.close()

    for job in jobs_to_submit:
        z1.submit_jcl(f'{dest_hlq}.RKANSAMU({job})')

    if stc_job is not None:
        wait_job_to_finish(hostname, username, password, stc_job)
        z1.submit_jcl(text=stop_start.replace('#CMD#', 'S').replace('#JOB#', stc_job))
        time.sleep(delay)

def upload_member_in_ds(hostname, username, password, datasets: List, data: str=''):
    z = zOSMFConnector(hostname, username, password)
    for dataset in datasets:
        try:
            z.read_ds(dataset)
        except:
            z.write_ds(data=data, dataset=dataset)

def update_stcs(hostname, username, password, src: str, dst: str = 'ITM.ITE.DEV.PROCLIB', member_mask: str = None,
                members: str = Union[str, List[str]],
                libraries: Union[str, List[str]] = None):
    """
    Load developers libraries in jobs from proclib.
    :param hostname: FTP host name
    :param username:  userid
    :param password:  password
    :param src: source library
    :param dst: destination library
    :param member_mask: pattern for jobs from the src lib to update
    :param members: list of members or string of member to update
    :param libraries: list of libraries or string of library to add
    :return: nothing
    """
    z = zOSMFConnector(hostname, username, password)
    zftp = ZFTP(hostname, username, password)
    if member_mask is not None:
        list_job = z.list(src, member_pattern=member_mask)
    elif isinstance(members, str):
        list_job = [members]
    else:
        list_job = members
    if isinstance(libraries, str):
        libs = [libraries]
    else:
        libs = libraries
    for job in list_job:
        data = z.read_ds(f'{src}({job})')
        for library in libs:
            if library not in data:
                name_lib = re.findall(r'(?<=\.\w)(\w+)(?!\.)', library)[-1]
                if data.find('&BASEHLEV.'+name_lib):
                    if 'APF' in job:
                        entries = re.findall(rf'//\s+DSNAME=&BASEHLEV.{name_lib},', data)
                        start=0
                        for entry in entries:
                            index_start = re.search(entry, data[start:]).start() + start
                            data = data[:index_start] + f'//    DSNAME={library},SMS\n//  SETPROG APF,ADD,\n' + data[index_start:]
                            start=re.search(entry, data).end()
                    else:
                        entries = re.findall(rf'//\s+DSN=&BASEHLEV.{name_lib}\s', data)
                        start=0
                        for entry in entries:
                            index_start = re.search(entry, data[start:]).start() + start
                            data = data[:index_start] + f'//          DSN={library}\n//          DD DISP=SHR,\n' + data[index_start:]
                            start = re.search(entry, data).end()
        count = 0
        for library in libs:
            if library in data:
                count += 1
                logger.info(f"{library} added to {job}")
        if count == 0:
            logger.info(f"{job} doesn't have libraries")
        elif count > 0:
            logger.info(f"Writing {dst}({job})")
            zftp.upload_ds(text=data, dest=f'{dst}({job})')


def delete_libs(hostname, username, password, src: str, dst: str = 'ITM.ITE.DEV.PROCLIB', member_mask: str = None,
                members: str = Union[str, List[str]],
                libraries: Union[str, List[str]] = None):
    """
    Delete developers libraries from jobs in proclib.
    :param hostname: FTP host name
    :param username:  userid
    :param password:  password
    :param src: main proclib
    :param dst: developers itm proclib
    :param member_mask: pattern for jobs from the proclib
    :param members: list of members or string of member
    :param libraries: list of libraries or string of library
    :return: nothing
    """
    z = zOSMFConnector(hostname, username, password)
    if member_mask is not None:
        list_job = z.list(src, member_pattern=member_mask)
    elif isinstance(members, str):
        list_job = [members]
    else:
        list_job = members
    if isinstance(libraries, str):
        libs = [libraries]
    else:
        libs = libraries
    for job in list_job:
        data = z.read_ds(f'{dst}({job})')
        count = 0
        for library in libs:
            if library in data:
                if 'APF' not in job:
                    new_data = data.replace(f'//          DSN={library}\n//          DD DISP=SHR,\n', '')
                    data = new_data
                    count += 1
                else:
                    new_data = data.replace(f'//  SETPROG APF,ADD,\n//    DSNAME={library},SMS\n', '')
                    data = new_data
                    count += 1
        if count > 0:
            z.write_ds(f'{dst}({job})', data)


def back_to_ZMENU(d):
    while not d.find('ZMENU    VTM'):
        d('', key=keys.PF3, timeout=30)
        if d.find('===> Enter: LOGON'):
            break


def get_random_alpha_numeric(k: int, uppercase: bool = True) -> str:
    """
    return random string with chars and digits
    :param k: len of string
    :param uppercase: use uppercase, else lowercase, true/false
    :return:
    """
    if uppercase:
        res = ''.join(random.choices(string.ascii_uppercase + string.digits, k=k))
    else:
        res = ''.join(random.choices(string.ascii_lowercase + string.digits, k=k))
    return res

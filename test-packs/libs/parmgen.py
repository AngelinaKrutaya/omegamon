import random
import time
import re
import datetime
import logging
from abc import ABC
from accessify import private

from typing import Dict, List, Union
from taf.zos.py3270 import ISPF
from taf.zos.py3270 import keys
from taf.zos.py3270 import Emulator
from taf.zos.py3270.display import LABEL_RIGHT
from taf.zos.zosmflib import zOSMFConnector
from libs.rte import RteType
from libs.ivtenv import rtes

from libs.e3270utils import get_text_position

logger = logging.getLogger(__name__)


class ParmException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'Parmgen Exception, {0} '.format(self.message)
        else:
            return 'Parmgen Exception has been raised'


class ParmBase(ABC):
    exec_host = 'rsd2'
    VARS_MODELS = ['$MDLHFV', '$MDLRSBV']
    COMPRESS_JCL = '''
//IVTCOMPR JOB (ACCOUNT),'',CLASS=A,                
//         MSGCLASS=X,MSGLEVEL=(1,1),               
//         REGION=0M                                
//COMPRESS    EXEC    PGM=IEBCOPY                   
//SYSPRINT DD  SYSOUT=A                             
//A    DD  DSNAME=#DS#,DISP=OLD
//B    DD  DSNAME=#DS#,DISP=OLD
//SYSIN DD *                                        
       COPY OUTDD=B,INDD=A                          
/*                                                  '''
    REALLOC_JCL = '''
//IVTREAL  JOB (ACCOUNT),'',CLASS=A,                
//         MSGCLASS=X,MSGLEVEL=(1,1),               
//         REGION=0M                                
//REALLOC  EXEC PGM=IKJEFT1A,PARM=KCIRJGRA  
//SYSTSPRT DD SYSOUT=*                      
//SYSEXEC  DD DISP=SHR,                     
//  DSN={hlq}.TKCIINST                    
//SYSTSIN  DD DUMMY                         
//SYSPRINT DD SYSOUT=*                      
//SYSUT3   DD DISP=(NEW),                   
//            UNIT=SYSALLDA,                
//            SPACE=(TRK,(50,50,132))       
//SYSUT4   DD DISP=(NEW),                   
//            UNIT=SYSALLDA,                
//            SPACE=(TRK,(50,50,132))       
//SYSIN    DD DUMMY                         
//LIBS     DD *
{libs}                             
/*                                                  '''
    BASE_LIBS = {
        'RKANCLI',
        'RKANCMD',
        'RKANDATR',
        'RKANEXEC',
        'RKANHENU',
        'RKANISP',
        'RKANMOD',
        'RKANMODL',
        'RKANMODP',
        'RKANMODR',
        'RKANOSRC',
        'RKANPAR',
        'RKANPENU',
        'RKANSAM',
        'RKANSAMF',
        'RKANSAMV',
        'RKANSQL',
        'RKANWENU',
        'RKEPHELP',
        'RKNSLOCL',
        'RKOBDATF',
        'RKOBHELP',
        'RKOCHELP',
        'RKOCPROC',
        'RKOIHELP',
        'RKOIPROC',
        'RKOMHELP',
        'RKOMPROC',
        'RKO2DATA',
        'RKO2DBRM',
        'RKO2EXEC',
        'RKO2HELP',
        'RKO2MENU',
        'RKO2PENU',
        'RKO2PROC',
        'RKO2SAMP',
        'RKO2SLIB',
        'RKO2TENU',
    }
    LIBS_FOR_RELOCATE = {
        'RKANDATR': 'SPACE(100 50) DIR(440)',
        'RKANPENU': 'SPACE(1300 100) DIR(440)',
        'RKANSAM': 'SPACE(900 100) DIR(440)',
        'RKANSAMU': 'SPACE(250 200) DIR(440)',
        'RKANSQL': 'SPACE(50 10) DIR(440)',
        'RKNSLOCL': 'SPACE(100 50) DIR(440)',
        'RKANWENU': 'SPACE(800 100) DIR(440)',
        'RKOCPROC': 'SPACE(200 50) DIR(440)',
        'RKO2PROC': 'SPACE(300 50) DIR(440)',
        'RKOIHELP': 'SPACE(80 50) DIR(440)',
        'RKANPAR': 'SPACE(200 50) DIR(440)',
        'RKANMOD': 'SPACE(4500 500) DIR(1800)',
        'RKANMODL': 'SPACE(4500 500) DIR(1800)',
        'RKANHENU': 'SPACE(800 100) DIR(800)',
        'RKO2PENU': 'SPACE(400 100) DIR(800)',
        'RKOIPROC': 'SPACE(250 50) DIR(800)',
        'RKO2SAMP': 'SPACE(250 50) DIR(800)',
        'RKANEXEC': 'SPACE(150 50) DIR(800)',
        'RKANCMD': 'SPACE(50 10) DIR(800)',
        'RKANMODP': 'SPACE(400 50) DIR(800)',
        'RKOMHELP': 'SPACE(150 20) DIR(800)',
        'RKANMODU': 'SPACE(700 100) DIR(20)',
        'RKOMPROC': 'SPACE(200 50) DIR(20)',
    }

    @staticmethod
    def change_parameters_in_dataset(z: zOSMFConnector, dataset: str, params: Dict[str, str],
                                     removed_params: List[str] = None,
                                     masks_params: List[str] = None):
        """
        :param z: zOSMFConnector
        :param dataset: dataset
        :param params: key=value pair to update in dataset
        :param removed_params: list to remove of dataset
        :param masks_params: all params from masks to remove of dataset
        :return:
        """
        # we have a problem with zosmf time to time, so we try to repeat
        n = 0
        n_max = 5
        while n < n_max:
            try:
                config_file = z.read_ds(dataset)
                break
            except Exception as e:
                print(e)
                n += 1
                time.sleep(2)
        else:
            raise ParmException(f'{dataset} cannot be read')
        '''
        in PARMGEN.JCL(<rte>) we have a symbol ® which gives an error when we try to save it back to z/os
        so we replace it with space
        '''
        reg = '®'
        config_file = config_file.replace(reg, ' ')
        if params:
            parameter = list(params.keys())
            for parm_name in parameter:
                try:
                    start = re.search(r'^' + parm_name + r'\s+', config_file, re.MULTILINE).end()
                    end = config_file.find('\n', start + 1)
                    config_file = config_file[:start] + f'{params[parm_name]}' + config_file[end:]
                except:
                    params.pop(parm_name)
                    logging.error(f'{parm_name} is not found in the config file {dataset}')
        else:
            for mask in masks_params:
                removed_params += re.findall(r'^' + mask + r'\S+\s', config_file, re.MULTILINE)
            for parm_name in removed_params:
                try:
                    start = re.search(r'^' + parm_name + r'\s*', config_file, re.MULTILINE).start()
                    end = config_file.find('\n', start + 1)
                    config_file = config_file[:start] + config_file[end:]
                except:
                    logging.error(f'{parm_name} is not found in the config file {dataset}')
        z.write_ds(dataset, config_file)

    @staticmethod
    def append_lines_into_dataset(z: zOSMFConnector, dataset: str,
                                  lines: Union[str, List[str]], start_line: str = None):
        """
        :param z: zOSMFConnector
        :param dataset: dataset
        :param lines: lines to add into dataset
        :param start_line: after which line we need to add params or to the end
        :return:
        """
        config_file = z.read_ds(dataset)
        config_file_list = config_file.splitlines()
        if isinstance(lines, str):
            lines = lines.splitlines()
        if start_line:
            start = 0
            for i, line in enumerate(config_file_list):
                if line.startswith(start_line):
                    start = i
                    break
            start += 1
            config_file_list[start:start] = lines
        else:
            config_file_list.extend(lines)
        z.write_ds(dataset, '\n'.join(config_file_list))

    @staticmethod
    def verify_values_in_datasets(results, zsmf, rte) -> bool:
        for member, values in results.items():
            member = member.replace('{rte}', rte)
            member_text = zsmf.read_ds(f"{rtes[rte]['rte_hlq']}.{member}")
            if isinstance(values, str):
                values = [values]
            for value in values:
                if not re.search(value, member_text):
                    return False
            return True


class Parmgen(ParmBase):

    def __init__(self, username: str, password: str, hlq: str, rte: str, is_new: bool = False, rte_model: str = '',
                 rte_products: List[str] = None, rte_type: int = None):
        """
        :param username: TSO username
        :param password: TSO password
        :param hlq: hlq of the csi, e.g. itm.itd
        :param rte: rte name
        :param is_new: new or old
        """
        self.username = username.upper()
        self.password = password
        self.hlq = hlq.upper()
        self.rte = rte.upper()
        self.step_results = {}
        self.is_new = is_new
        self.original_config = ''
        self.variables_config = ''
        self.rte_type = rte_type if not None else rtes[rte]['type']
        self.time = datetime.datetime.now().strftime('%Y/%m/%d')
        self.z = zOSMFConnector(self.exec_host, username, password)
        self.jobname = None
        self.step_results: Dict[str: Dict[str: int]] = {}
        self.ispf = None
        self.d = None
        self.all_jobs = set()
        self.changed_parameters = []
        self.rte_model = rte_model
        self.middle_hlq = self.hlq.split('.')[1]
        if rte_products is None:
            self.rte_products = []
        else:
            self.rte_products = rte_products

        self.CONFIG_FOR_PRODUCTS = {
            'KC5': self.update_config_for_kc5,
            'KDS': self.update_config_for_kds,
            'KD5': self.update_config_for_kd5,
            'KGW': self.update_config_for_kgw,
            'KI5': self.update_config_for_ki5,
            'KJJ': self.update_config_for_kjj,
            'KMQ': self.update_config_for_kmq,
            'KM5': self.update_config_for_km5,
            'KN3': self.update_config_for_kn3,
            'KOB': self.update_config_for_kob,
            'KQI': self.update_config_for_kqi,
            'KS3': self.update_config_for_ks3,
        }

    def relocate_libs(self):
        """
        Relocate some libs to make space bigger and prevent E37-04
        :return:
        """
        libs = []
        for lib in self.LIBS_FOR_RELOCATE.keys():
            if self.rte_type == RteType.SHARED and lib in self.BASE_LIBS:
                add_lib = f"{self.hlq}.BASE.{lib}\n     {self.LIBS_FOR_RELOCATE[lib]}"
                libs.append(add_lib)
            else:
                add_lib = f"{self.hlq}.{self.rte}.{lib}\n     {self.LIBS_FOR_RELOCATE[lib]}"
            libs.append(add_lib)
        libs = '\n'.join(libs)
        job = self.z.submit(self.REALLOC_JCL.replace('{hlq}', self.hlq).replace('{libs}', libs))

    def check_on_screen(self, text, exception_text):
        if not self.d.find(text):
            raise ParmException(exception_text)

    def delete_another_rte(self, rte_to_delete: str) -> bool:
        """
        Make sure, we do it after "logon".
        We go 1 screen back, use ? to list all RTEs, use D to start deletion.
        Then we add wait step to the job, submit it and, exit from pargen, check results.
        Wait is needed to have time for exit, otherwise RKANSAMU lib is locked by us.
        :param rte_to_delete:
        :return:
        """
        rte_to_delete = rte_to_delete.upper()
        if self.rte == rte_to_delete:
            raise ParmException('You are trying to delete current RTE, this is impossible!')
        d = self.d
        self.check_on_screen('KCIPQPGB', 'Incorrect panel')
        d(key=keys.PF3)
        self.check_on_screen('KCIPQPGA', 'Incorrect panel')
        d.find_by_label('RTE_NAME:')('', keys.ERASEEOF)('?').enter()
        d.find_by_label(rte_to_delete, label_pos=LABEL_RIGHT)('d').enter()
        self.check_on_screen('WARNING! WARNING!', 'No expected message')
        d.enter()
        # parially created RTE is deleted right away, w/o job
        if d.find('KCIR@DEL: Function:    Delete an RTE.'):
            d.enter()
            d(key=keys.PF3)
            d(key=keys.PF3)
            return True

        wait_step = [
            "//WAITXMIN   EXEC PGM=BPXBATCH,REGION=0M,",
            "//  PARM='sh sleep 15s'",
            "//STDIN    DD DUMMY",
            "//STDOUT   DD SYSOUT=*",
            "//STDERR   DD SYSOUT=*",
            "/*",
        ]
        # we replace comments with this additional step
        start_row_chars = '000020 //*'
        # by any reason, maybe we already updated this job
        if d.find(start_row_chars):
            y1, x1 = get_text_position(start_row_chars, d=d)
            x1 = x1 + len(start_row_chars) - 3
            for row in range(0, len(wait_step)):
                d.cursor = y1 + row, x1
                d('', keys.ERASEEOF)(wait_step[row])
        if not d.find('//WAITXMIN'):
            raise ParmException('Delete job is invalid')
        # get current jobname
        self.jobname = d.find(regex=r'(?<=//)\w+(?= JOB)').visible_only
        exist_list_jobs = self.z.list_jobs(prefix=self.jobname, owner=self.username)

        d.find_by_label('===>')('sub').enter()
        if not d.find(regex=rf'JOB\s+\w+\(\w+\)\s+SUBMITTED'):
            logger.info(d)
            raise ParmException('Submit error')
        d.enter()
        d.find_by_label('===>')('cancel').enter()
        if d.find('Data set has been changed'):
            d.enter()
        # exiting from parmgen
        d(key=keys.PF3)
        d(key=keys.PF3)
        d(key=keys.PF3)

        self.set_step_results('delete_rte', exist_list_jobs, 0)
        d.find_by_label('===>').enter()
        self.check_on_screen('MAXCC=0000', 'Job fails')
        d.enter()

    def update_config_for_rte(self):
        params = {'RTE_X_STC_INAPF_INCLUDE_FLAG': 'Y'}
        if self.rte_model in self.VARS_MODELS:
            params['RTE_XKAN_HILEV'] = f'{self.hlq}.{self.rte}.&SYSPLEX.'
        else:
            params['RTE_XKAN_HILEV'] = f'{self.hlq}.{self.rte}.RSPLEXL4'
        self.change_parameters(params)

        # update variables
        if self.rte_model in self.VARS_MODELS:
            self.change_parameters_in_dataset(self.z, f'{self.hlq}.PARMGEN.JCL({self.rte})',
                                              {'RTE_USS_RTEDIR': f'/proj/omivt/{self.middle_hlq.lower()}'})
        # update $GBL$USR
        glbusr = f'''GBL_DSN_SYS1_PARMLIB         ITM.{self.middle_hlq}.ROCKET.PARMLIB  
GBL_DSN_SYS1_SAXREXEC        ITM.{self.middle_hlq}.ROCKET.SAXREXEC 
GBL_DSN_SYS1_PROCLIB         ITM.{self.middle_hlq}.ROCKET.PROCLIB  
GBL_DSN_SYS1_VTAMLIB         ITM.{self.middle_hlq}.ROCKET.VTAMLIB  
GBL_DSN_SYS1_VTAMLST         ITM.{self.middle_hlq}.ROCKET.VTAMLST  
GBL_USS_TKANJAR_PATH "/proj/omivt/{self.middle_hlq.lower()}/usr/lpp/kan/bin/IBM"
GBL_HFS_JAVA_DIR1 "/rsusr/java/IBM/J7.1"  
GBL_DSN_DB2_LOADLIB_V11      "RSRTE.DSN.VB10.SDSNLOAD"   
GBL_DSN_DB2_LOADLIB_V12      "RSRTE.DSN.VC10.SDSNLOAD"   
GBL_DSN_DB2_RUNLIB_V11       "RSRTE.DSN.VB10.RUNLIB.LOAD" 
GBL_DSN_DB2_RUNLIB_V12       "RSRTE.DSN.VC10.RUNLIB.LOAD" 
GBL_DSN_DB2_DSNEXIT          "IDS4.SDSNEXIT"              
'''
        self.append_lines_into_dataset(self.z, f'{self.hlq}.{self.rte}.WCONFIG($GBL$USR)', glbusr)

    def update_config_for_kc5(self):
        pass

    def update_config_for_kds(self):
        pass

    def update_config_for_kd5(self):
        params = {'KD2_DB01_DB2_VER': '12'}
        self.change_parameters(params)

    def update_config_for_kgw(self):
        pass

    def update_config_for_ki5(self):
        lines = f'''KI2_I1                            BEGIN          
KI2_I101_ROW                      01             
KI2_I101_CLASSIC_IMSID            IFK1
KI2_I101_CLASSIC_MPREFIX          M0  
KI2_I101_CLASSIC_GLOBAL           00  
KI2_I101_CLASSIC_STC        {self.rte}OI0 
KI2_I101_CLASSIC_VTAM_NODE  {self.rte}OI0N             
KI2_I101_CLASSIC_VTAM_APPL_LOGON  {self.rte}OI0        
KI2_I101_CLASSIC_IMS_RESLIB IMS.IFK1.SDFSRESL    
KI2_I101_CLASSIC_LROWS            999            
KI2_I101_CLASSIC_USER_PROFILE     /C             
KI2_I101_CLASSIC_CTRL_UNIT_ADDR   XXXX           
KI2_I102_ROW                      02             
KI2_I102_CLASSIC_IMSID            IEK1
KI2_I102_CLASSIC_MPREFIX          M1  
KI2_I102_CLASSIC_GLOBAL           00  
KI2_I102_CLASSIC_STC        {self.rte}OI1 
KI2_I102_CLASSIC_VTAM_NODE  {self.rte}OI1N             
KI2_I102_CLASSIC_VTAM_APPL_LOGON  {self.rte}OI1        
KI2_I102_CLASSIC_IMS_RESLIB IMS.IEK1.SDFSRESL    
KI2_I102_CLASSIC_LROWS            999            
KI2_I102_CLASSIC_USER_PROFILE     /C             
KI2_I102_CLASSIC_CTRL_UNIT_ADDR   XXXX           
KI2_I1                            END            '''
        self.append_parameters(lines, '**KI2_I1                            END')

    def update_config_for_kjj(self):
        pass

    def update_config_for_kmq(self):
        pass

    def update_config_for_km5(self):
        params = {'GBL_SYSPLEX_NAME_XCFPLEXGROUP': f'{self.rte}RSD4'}
        if self.rte_model in self.VARS_MODELS:
            params['KM5_PDS_RKM5PLX_PLEXDATA_HILEV'] = f'{self.hlq}.{self.rte}.&SYSPLEX.'
        else:
            params['KM5_PDS_RKM5PLX_PLEXDATA_HILEV'] = f'{self.hlq}.{self.rte}.RSPLEXL4'
        self.change_parameters(params)

    def update_config_for_kn3(self):
        params = {
            'KN3_TCPX01_SYS_NAME': '$$$$ ',
            'KN3_TCPX01_TCP_STC': '$$$$$$$$',
            'KN3_TCPX01_OVRD_ZERT': 'Y',
        }
        self.change_parameters(params)

    def update_config_for_kob(self):
        pass

    def update_config_for_kqi(self):
        params = {
            'KQI_XML_XIMBNAME_MON_BRKR_NAME': 'Q191BRK',
            'KQI_XML_XIMBDIR1': '/u/ibstc/q191brk',
            'KQI_HFS_HFSROOT_DIR1': f'/proj/omivt/{self.middle_hlq.lower()}',
        }
        self.change_parameters(params)

    def update_config_for_ks3(self):
        params = {
            'KS3_AS_LISTENER_ADDR': '"192.168.54.121"',
            'KS3_NODEJS_HOME': '/rsusr/cnj/IBM/node-v6.14.4-os390-s390x',
        }
        self.change_parameters(params)

    def logon(self):
        if self.ispf is None:
            emulator = Emulator(self.exec_host, model=2, oversize=(62, 160))
            try:
                self.ispf = ISPF(emulator=emulator, target=self.exec_host, model=2, username=self.username,
                                 password=self.password)
                display = self.ispf.em.display
            except:
                emulator.close()
                raise ParmException('LOGON problem')
            display.wait(10, 'ISPF Primary Option Menu')
            display.find_by_label('===>')('3.4').enter()
            gbl_hlq = ''
            try:
                gbl_hlq = rtes[self.rte.lower()]['gbl_hlq']
            except:
                gbl_hlq = self.hlq
            tkancus = f'{gbl_hlq}.TKANCUS'.upper()
            display.find_by_label('Dsname Level . . .')('', keys.ERASEEOF)(tkancus).enter()
            display.find(f'        {tkancus}')('ex').enter()
            display.find_by_label('===>')('3').enter()
            if display.find('KCIP@TLV'):
                display.find_by_label('GBL_TARGET_HILEV:')('', keys.ERASEEOF)(gbl_hlq).enter()
            # there are 2 3270 fields for GBL_USER_JCL (no idea why), so find_by_label doesn't work
            display.find('GBL_USER_JCL:')('')
            display.cursor = display.cursor[0], display.cursor[1] + 16
            display('', keys.ERASEEOF)(f'{self.hlq}.PARMGEN.JCL')
            display.find_by_label('RTE_PLIB_HILEV:')('', keys.ERASEEOF)(self.hlq)
            display.find_by_label('RTE_NAME:')('', keys.ERASEEOF)(self.rte).enter()

            if self.is_new:
                # if not display.find('You have asked to configure a new RTE profile.'):
                #   raise ParmException('Incorrect panel')
                display('').enter()
            if not display.find('KCIPQPGB'):
                raise ParmException('Incorrect panel')
            else:
                self.d = display

    def logoff(self):
        logger.info(f'{self.rte}: {self.step_results}')
        if self.ispf is not None:
            self.ispf.logoff()
            self.ispf = None
            self.d = None

    def before(self):
        if not self.is_new:
            self.z.del_ds(f'{self.hlq}.{self.rte}.WCONFIG(KOB$PENV)')

    def get_step_result(self):
        return self.step_results

    def set_step_results(self, func, exist_list_jobs, rc):
        list_jobs = self.z.list_jobs(prefix=self.jobname, owner=self.username)
        for job in exist_list_jobs:
            list_jobs.pop(job, None)
        while any(job['status'] != 'OUTPUT' for job in list_jobs.values()):
            time.sleep(5)
            list_jobs = self.z.list_jobs(prefix=self.jobname, owner=self.username)
            for job in exist_list_jobs:
                list_jobs.pop(job, None)
        current_jobs = set(list_jobs.keys()) - self.all_jobs
        self.all_jobs = set(list_jobs.keys())
        for job in current_jobs:
            rc_code = re.search(r'\d+', list_jobs[job]['retcode'])[0]
            if int(rc_code) <= rc:
                self.step_results[func] = {job: list_jobs[job]['retcode'] for job in current_jobs}
            elif 'step_4_7' in func and rc_code == '0256':
                self.step_results[func] = {job: list_jobs[job]['retcode'] for job in current_jobs}
            else:
                raise ParmException(f'RC code {rc_code} in {job}')

    def submit_and_check(self, func, rc: int):
        """
        :param func: step name
        :param rc: max rc
        :return:
        """
        d = self.d
        if self.jobname is None:
            self.jobname = d.find(regex=r'(?<=//)\w+(?= JOB)').visible_only
        exist_list_jobs = self.z.list_jobs(prefix=self.jobname, owner=self.username)
        d.find_by_label('===>')('sub').enter()
        # wait some time to make sure, job is really submitted
        time.sleep(15)
        if not d.find(regex=rf'JOB\s+{self.jobname}\(\w+\)\s+SUBMITTED'):
            logger.info(d)
            raise ParmException('Submit error')
        self.set_step_results(func, exist_list_jobs, rc)
        d.enter()
        d.enter()
        d(key=keys.PF3)
        self.check_on_screen('KCIP@PGP', 'Incorrect panel')

    def step_1_set_up(self):
        self.jobname = f"KCIJ{random.randint(1, 9999):04d}"
        self.before()
        d = self.d
        d.find_by_label('===>')('1').enter()
        if d.find('KCIP@MSG'):
            d.enter()
        self.check_on_screen('KCIPQPG1', 'Incorrect panel')
        if self.is_new:
            d.find_by_label('==>')('?')
            d.enter()
            self.check_on_screen('KCIPQMDL', 'Incorrect panel')
            d.find_by_label(self.rte_model, label_pos=LABEL_RIGHT)('s').enter()
        else:
            # clear path to config
            d.find_by_label('==>')('', keys.ERASEEOF)(f'{self.hlq}.{self.rte}.WCONFIG({self.rte})')
        if d.find('==> _______\n==> _______'):
            # jobcard is empty, press enter to fill it in
            d.enter()
        d.find_all_by_label('==>')[1](f'//{self.jobname}').enter()
        self.check_on_screen('KCIP@PG2', 'Incorrect panel')
        d.enter()
        self.check_on_screen('KCIP@PG3', 'Incorrect panel')
        if self.is_new:
            if self.rte_type == RteType.SHARED:
                d.find_by_label('RTE_X_HILEV_SHARING:')('', keys.ERASEEOF)(self.hlq)
                d.find_by_label('RTE_SHARE:')('', keys.ERASEEOF)('BASE')
            d.find_by_label('RTE_X_SECURITY_EXIT_LIB:')('', keys.ERASEEOF)(f'{self.hlq}.{self.rte}.RKANSAMU')
            d.find_by_label('RTE_VTAM_APPLID_PREFIX:')('', keys.ERASEEOF)(f'{self.rte}')
            d.find_by_label('RTE_STC_PREFIX:')('', keys.ERASEEOF)(f'{self.rte}')
        d.enter()
        self.check_on_screen('KCIP@PGI', 'Incorrect panel')
        if self.is_new:
            # clear products selection
            y1, _ = get_text_position('Kpp  Component', d=d)
            y2, x2 = get_text_position('End of data', d=d)
            for y in range(y1 + 2, y2):
                d.cursor = y, x2
                d(' ')
            # choose products
            for product in self.rte_products:
                d.find_by_label(product, label_pos=LABEL_RIGHT)('/')
        d.enter()
        d('Y').enter()
        if d.find('KCIP@BAK IMPORTANT - REFRESH THE LPAR RTE USER AND IBM PROFILES'):
            d.find_by_label('==>')(self.rte).enter()
        self.submit_and_check('step_1_set_up', rc=0)
        d(key=keys.PF3)
        self.check_on_screen('KCIPQPGB', 'Incorrect panel')
        if d.find(regex=r'KCIJPCFG\s+RC=(\s+)0{5}(\s+)' + self.time):
            self.step_results['step_1_set_up']['result'] = True
        else:
            self.step_results['step_1_set_up']['result'] = False
        if 'KS3' in self.rte_products:
            self.CONFIG_FOR_PRODUCTS['KS3']()

    def submit_step(self, steps, workspace, jobname, rc):
        d = self.d
        func = f'step_{steps[0]}_{steps[1]}'
        for step in steps:
            d.find_by_label('===>')(str(step)).enter()
        if d.find('KCIP@PGP'):
            d.enter()
        if d.find('KCIP@SEC'):
            d(key=keys.PF3)
        self.submit_and_check(func, rc)
        d(key=keys.PF3)
        self.check_on_screen(workspace, 'Incorrect panel')
        if jobname in ['KCIJPW1R', 'KCIJPW2R']:
            # need to zoom to get details for this step
            d('12').enter()
        if (str(steps[0]) + '_' + str(steps[1]) != '3_1' and self.rte_model in self.VARS_MODELS) \
                or self.rte_model not in self.VARS_MODELS:
            self.find_step_result(steps, jobname, rc)

    @private
    def find_step_result(self, steps, jobname, rc):
        d = self.d
        func = f'step_{steps[0]}_{steps[1]}'
        try:
            time.sleep(10)
            rc_code = d.find(regex=r'(?<=' + jobname.replace('$', '\\$') + r').*?(?=' + self.time + r')').visible_only
            rc_code = re.search(r'\d+', rc_code)[0]
            if int(rc_code) <= rc:
                self.step_results[func]['result'] = True
            else:
                self.step_results[func]['result'] = False
        except:
            logger.info(d)
            raise ParmException('Job result is not found')
        finally:
            if jobname in ['KCIJPW1R', 'KCIJPW2R']:
                d(key=keys.PF3)
            if (jobname != '$PARSEDV' and self.rte_model in self.VARS_MODELS) or self.rte_model not in self.VARS_MODELS:
                d(key=keys.PF3)

    def change_parameters(self, params: Dict[str, str], variables: Dict[str, str] = None, dataset: str = None):
        """
        :param params: key=value pair to update in wconfig(<rte>)
        :param variables: key=value pair to update in variables config
        :param dataset: variables config
        :return:
        """
        if variables:
            self.change_parameters_in_dataset(self.z, dataset, variables)
        self.change_parameters_in_dataset(self.z, f'{self.hlq}.{self.rte}.WCONFIG({self.rte})', params)

    def remove_parameters(self, removed_params: Dict[str, List[str]], dataset: str = None):
        """
        :param removed_params: dict of two keys - list: 'parameters' and 'masks_params', and values: all parameters
         to remove of wconfig(<rte>)
        :param dataset: variables config
        :return:
        """
        self.change_parameters_in_dataset(self.z, dataset=f'{self.hlq}.{self.rte}.WCONFIG({self.rte})', params={},
                                          removed_params=removed_params['parameters'],
                                          masks_params=removed_params['masks_params'])

    def append_parameters(self, params: Union[str, List[str]], start_line: str = None):
        """
        :param params: List of lines to add into  wconfig(<rte>)
        :param start_line: after which line we need to add params or to the end
        :return:
        """
        self.append_lines_into_dataset(self.z, f'{self.hlq}.{self.rte}.WCONFIG({self.rte})', params, start_line)

    @private
    def go_to_params_clone_panel(self, product_code, section, base_section_id, target_section_id):
        d = self.d
        d(key=keys.PF16)
        d.find('KCIP@PM2')
        d.find_by_label('Repeating section (sc) =')(section)
        d.find_by_label('Base section ID   (ID) =')(base_section_id)
        d.find_by_label('Target section ID (ID) =')(target_section_id)
        d.find_by_label('Include comments       =')('Y')
        d.find_by_label('Product code      (pp) =')(product_code).enter()

    def save_config(self, dataset: str = None):
        if dataset:
            self.variables_config = self.z.read_ds(dataset)
        self.original_config = self.z.read_ds(f'{self.hlq}.{self.rte}.WCONFIG({self.rte})')
        return self.original_config, self.variables_config

    def restore_config(self, dataset: str = None):
        if dataset:
            self.z.write_ds(dataset, self.original_config)
        self.z.write_ds(f'{self.hlq}.{self.rte}.WCONFIG({self.rte})', self.original_config)
        return self.original_config, self.variables_config

    def get_config(self, dataset: str = None):
        if dataset:
            config_file = self.z.read_ds(dataset)
        else:
            config_file = self.z.read_ds(f'{self.hlq}.{self.rte}.WCONFIG({self.rte})')
        return config_file

    def include_parameters(self, product_code, section, base_section_id: str = '01', target_section_id: str = '02'):
        click_count = 0
        if not self.d:
            self.logon()
        else:
            while not self.d.find('KCIPQPGB') and click_count < 10:
                self.d(key=keys.PF3)
                click_count += 1
        d = self.d
        if d.find('KCIPQPGB'):
            d.find_by_label('===>')('2').enter()
            d.find_by_label('===>')('1').enter()
            d.enter()
            self.go_to_params_clone_panel(product_code, section, base_section_id, target_section_id)
            if not d.find(product_code + '_' + section + target_section_id + '_'):
                raise ParmException('Parameters did not included in config')
            d(key=keys.PF3)
            d(key=keys.PF3)
        else:
            raise ParmException('Could not logon to primary panel')

    def step_2_customize(self):
        d = self.d
        d.find_by_label('===>')('2').enter()
        d.find_by_label('===>')('1').enter()
        d.enter()
        d(key=keys.PF3)
        d(key=keys.PF3)
        # if new, we need to update several configs
        if self.is_new:
            self.update_config_for_rte()
            for product in self.rte_products:
                self.CONFIG_FOR_PRODUCTS[product]()

    def step_3_1_parse(self):
        self.submit_step(steps=(3, 1), workspace='KCIP@PR1', jobname='$PARSE', rc=4)

    def step_3_parse_with_variables(self):
        self.submit_step(steps=(3, 1), workspace='KCIP@PR1', jobname='$PARSESV', rc=4)
        self.submit_step(steps=(3, 2), workspace='KCIP@PR1', jobname='$PARSEDV', rc=4)
        self.find_step_result(steps=(3, 1), jobname='$PARSESV', rc=4)

    def step_4_1_composite_sub(self):
        self.submit_step(steps=(4, 1), workspace='KCIP@SUB', jobname='KCIJPSUB', rc=0)

    def step_4_2_allocate_ds(self):
        self.submit_step(steps=(4, 2), workspace='KCIP@SUB', jobname='KCIJPALO', rc=2)

    def step_4_3_copy_smpe_members(self):
        self.relocate_libs()
        self.submit_step(steps=(4, 3), workspace='KCIP@SUB', jobname='KCIJPLOD', rc=4)

    def step_4_4_run_product(self):
        # compress RKANMODU library first
        self.z.submit(self.COMPRESS_JCL.replace('#DS#', f'{self.hlq}.{self.rte}.RKANMODU'))
        self.submit_step(steps=(4, 4), workspace='KCIP@SUB', jobname='KCIJPSEC', rc=0)

    def step_4_5_update_var_name(self):
        self.submit_step(steps=(4, 5), workspace='KCIP@SUB', jobname='KCIJPUPV', rc=4)

    def step_4_6_create_uss(self):
        self.submit_step(steps=(4, 6), workspace='KCIP@SUB', jobname='KCIJPUSP', rc=0)

    def step_4_7_copy_uss(self):
        self.submit_step(steps=(4, 7), workspace='KCIP@SUB', jobname='KCIJPUSS', rc=0)

    def step_4_8_copy_runtime_members_to_sys1(self):
        self.submit_step(steps=(4, 8), workspace='KCIP@SUB', jobname='KCIJPSYS', rc=0)

    def step_4_9_run_post_smpe(self):
        self.submit_step(steps=(4, 9), workspace='KCIP@SUB', jobname='KCIJPLNK', rc=0)

    def step_4_10_verify_jobs(self):
        # this job can abend because of B37 on TEMP datasets but we can't control them, so set rc=20 as acceptable
        self.submit_step(steps=(4, 10), workspace='KCIP@SUB', jobname='KCIJPIVP', rc=20)

    def step_4_11_backup_rk_libs(self):
        self.submit_step(steps=(4, 11), workspace='KCIP@SUB', jobname='KCIJPCPR', rc=0)

    def step_4_12_copy_replace_files_from_wk(self):
        self.submit_step(steps=(4, 12, 1), workspace='KCIP@SUB', jobname='KCIJPW2R', rc=0)

    def step_4_12_empty_rk_ds_and_copy(self):
        self.submit_step(steps=(4, 12, 2), workspace='KCIP@SUB', jobname='KCIJPW1R', rc=0)

    def full_update(self, change_params: bool = False):
        logger.info(f'Full update of {self.rte}')
        if not change_params:
            self.step_1_set_up()
        if self.is_new:
            self.step_2_customize()
        if self.rte_model in self.VARS_MODELS:
            self.step_3_parse_with_variables()
        else:
            self.step_3_1_parse()
        self.step_4_2_allocate_ds()
        self.step_4_3_copy_smpe_members()
        self.step_4_4_run_product()
        if self.rte_model in self.VARS_MODELS:
            self.step_4_5_update_var_name()
        self.step_4_6_create_uss()
        self.step_4_7_copy_uss()
        self.step_4_8_copy_runtime_members_to_sys1()
        self.step_4_9_run_post_smpe()
        self.step_4_10_verify_jobs()
        self.step_4_11_backup_rk_libs()
        self.step_4_12_copy_replace_files_from_wk()
        self.step_4_12_empty_rk_ds_and_copy()
        return self.result()

    def partial_update(self) -> bool:
        logger.info(f'Partial update of {self.rte}')
        self.step_1_set_up()
        self.step_3_1_parse()
        self.step_4_2_allocate_ds()
        self.step_4_4_run_product()
        self.step_4_6_create_uss()
        self.step_4_7_copy_uss()
        self.step_4_8_copy_runtime_members_to_sys1()
        self.step_4_9_run_post_smpe()
        self.step_4_11_backup_rk_libs()
        return self.result()

    def result(self) -> bool:
        return all(v['result'] for v in self.step_results.values())

# if __name__ == '__main__':
#     from libs.creds import *
#     from libs.ivtenv import rtes
#     import os
#
#     rte = os.environ.get('rte', 'itp1')
#     hlq = rtes[rte]['rte_hlq']
#
#     username = os.environ.get('mf_user', username)
#     password = os.environ.get('mf_password', password)
#
#     rte1 = Parmgen(username, password, hlq[0:hlq.rfind('.')], rte)
#     try:
#         rte1.logon()
#         rte1.step_1_set_up()
#         rte1.step_3_1_parse()
#         print(rte1.step_results)
#     finally:
#         rte1.logoff()

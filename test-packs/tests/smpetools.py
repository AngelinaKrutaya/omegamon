import re
from taf.zos.jes import JESAdapter
from libs.creds import *


username = username[:-1]
target_system = 'rsd1'
target_csi = 'ITM.ITE.CSI'


fmids = {
    'HAAD71C': ['rsb1', 'RSQA.HAAD71C.*.PTF'],
    'HAAD710': ['rsb1', 'RSQA.HAAD710.*.PTF'],
    'HKYN710': ['rsb1', 'RSQA.HKYN710.*.PTF'],
    'HPMZ540': ['rsb1', 'RSQA.HPMZ540.*.PTF'],
    'HIZD310': ['rsb1', 'RSQA.HIZD310.*.PTF'],
    'HKC5550': ['rsb1', 'RSQA.HKC5550.*.PTF'],
    # 'HKDB54X': ['rs27', 'RSQA.???HAAD71C.*.PTF'],
    'HKDB540': ['rs27', 'RSQA.SRV540.*.PTF'],
    'HKGW550': ['rsb1', 'RSQA.HKGW550.*.PTF'],
    'HKI5550': ['rsb1', 'RSQA.HKI5550.*.PTF'],
    'HKJJ550': ['rsb1', 'RSQA.HKJJ550.*.PTF'],
    # 'HKJJ540': ['rsb1', 'RSQA.HKJJ540.*.PTF'],
    'HKMQ750': ['rsb1', 'RSQA.HKMQ750.*.PTF'],
    'HKQI750': ['rsb1', 'RSQA.HKQI750.*.PTF'],
    'HKSB750': ['rs27', 'RSQA.KSB750.*.PTF'],
    'HKS3550': ['rs27', 'RSQA.KS3550.*.PTF'],
    'HKOB750': ['rsb1', 'RSQA.HKOB750.*.PTF'],
    'HKCI310': ['rsb1', 'RSQA.HKCI310.*.PTF'],
    'HRKN560': ['rsb1', 'RSQA.HRKN560.*.PTF'],
    'HRKZ560': ['rsb1', 'RSQA.HRKZ560.*.PTF'],
    'HKLV630': ['rsb1', 'RSQA.HKLV630.*.PTF'],
    'HKDS630': ['rsb1', 'RSQA.HKDS630.*.PTF'],
}


ftp_jcl_start = '''\
//TS5813S JOB (ACCT#),'FTP',CLASS=A,           
//        MSGCLASS=X,REGION=0M NOTIFY=&SYSUID RESTART=FTP     
//FTP      EXEC PGM=FTP,PARM='(EXIT',COND=(04,LT)             
//SYSPRINT DD SYSOUT=*                                        
//OUTPUT   DD SYSOUT=*                                        
//INPUT    DD *                                               
{target}                                                          
{username}                                                        
{password}                                                      
MODE B                                                        
LOCSITE FWFRIENDLY                                            
SITE DATACLAS=EFCOMP5                                         
EBCDIC                                                        
'''

ftp_jcl_end = '''

QUIT                                                          
/*                                                            
//*'''


smpe_jcl_header = '''\
//TS5813SM JOB ,'CSI',CLASS=A,MSGCLASS=X, 
//         MSGLEVEL=(1,1),REGION=0M,NOTIFY=&SYSUID  
//S1       EXEC PGM=GIMSMP,                         
//         PARM='PROCESS=WAIT',                     
//         DYNAMNBR=120                             
//SMPCSI   DD DISP=SHR,DSN={csi}              
//*                                                 
'''


smpe_ptfs_jcl = smpe_jcl_header.replace(',NOTIFY=&SYSUID', '') + '''
//SMPCNTL  DD *                                     
  SET     BOUNDARY ( KDSTRG ).                      
       LIST SYSMODS PTFS .                          
/*                                                  
//S2       EXEC PGM=GIMSMP,                         
//         PARM='PROCESS=WAIT',                     
//         DYNAMNBR=120                             
//*                                                 
//SMPCSI   DD DISP=SHR,DSN={csi}              
//*                                                 
//SMPCNTL  DD *                                     
  SET     BOUNDARY ( KDSTRG ).                      
       LIST SUP.                                    
/*'''


def get_zosmf_jes(source, zosmf_cache=dict()):
    if source in zosmf_cache:
        zds = zosmf_cache.get(source)
    else:
        zds = JESAdapter(f'{source}.rocketsoftware.com', username, password)
        zosmf_cache[source] = zds
    return zds


def get_zosmf(source):
    return get_zosmf_jes(source).zo


def sync_fmid(fmid, target):
    jcl = ftp_jcl_start.replace('{target}', target) \
        .replace('{username}', username).replace('{password}', password)
    source = fmids[fmid][0]
    s_list = get_zosmf(source).list_ds(fmids[fmid][1])
    t_list = set(get_zosmf(target).list_ds(fmids[fmid][1], retrieve_all=True))
    needed_ptfs = []
    for ptf in s_list:
        if ptf not in t_list and len(ptf.split('.')) == 4:
            needed_ptfs.append(f"MVSPUT '{ptf}'")
    if needed_ptfs:
        jcl = jcl + '\n'.join(needed_ptfs) + ftp_jcl_end
        print(needed_ptfs)
        job = get_zosmf_jes(source).submit_jcl(text=jcl, wait=True)
        if int(job.get_rc()) == 0:
            print(f'Finished for {fmid}')
        else:
            print(f'FTP job failed for {fmid}, rc = {job.get_rc()}')
    else:
        print(f'Nothing to sync for {fmid}')


def get_available_ptfs(fmid, target):
    t_list = list(filter(lambda x: len(x.split('.')) == 4, get_zosmf(target).list_ds(fmids[fmid][1], retrieve_all=True)))
    return t_list


def gen_receive_job(fmids_, existing: set, target=target_system, csi=target_csi, write_to_member=None):
    """
    This function GETS available PTFs on target system and compare it with provided 'existing' set
    :param csi:
    :param fmids_:
    :param existing:
    :param target:
    :param write_to_member:
    :return:
    """
    if isinstance(fmids_, str):
        fmids_ = [fmids_]
    dds = []
    for fm in fmids_:
        available_ptfs = get_available_ptfs(fm, target)
        for ptf in available_ptfs:
            if ptf.split('.')[2] not in existing:
                dds.append(f'// DD DISP=SHR,DSN={ptf}')
    dds[0] = dds[0].replace('// DD ', '//SMPPTFIN DD ')
    ptfs = [ptf.split('.')[2] for ptf in dds]
    res = '\n'.join(dds) + '\n//SMPCNTL  DD *\n SET BDY(GLOBAL) .\nRECEIVE SYSMODS .'
    res = smpe_jcl_header.replace('{csi}', csi) + res
    print('-' * 20)
    print(res)
    if write_to_member:
        get_zosmf(target).write_ds(write_to_member, data=res)
    return ptfs


def gen_apply_job(ptfs: set, target=target_system, csi=target_csi, write_to_member=None):
    """
    This function just create APPLY statements based on provided 'ptfs' set
    :param csi:
    :param ptfs:
    :param target:
    :param write_to_member:
    :return:
    """
    if isinstance(ptfs, str):
        ptfs = [ptfs]

    res = '//SMPCNTL  DD *\nSET BOUNDARY (KDSTRG).\nAPPLY\nCHECK\nSELECT   (\n'
    res += '\n'.join(ptfs) + '\n)\nNOJCLINREPORT\nCOMPRESS(ALL)\nRETRY     (YES)\nBYPASS(HOLDSYS).'
    res = smpe_jcl_header.replace('{csi}', csi) + res
    print('-'*20)
    print(res)
    if write_to_member:
        get_zosmf(target).write_ds(write_to_member, data=res)
    return ptfs


def gen_accept_job(ptfs: set, target=target_system, csi=target_csi, write_to_member=None):
    """
    This function just create APPLY statements based on provided 'ptfs' set
    :param csi:
    :param ptfs:
    :param target:
    :param write_to_member:
    :return:
    """
    if isinstance(ptfs, str):
        ptfs = [ptfs]

    res = '//SMPHOLD  DD  DUMMY\n//SMPCNTL  DD  *\nSET BDY(KDSDLB).\nACCEPT\nCHECK\nSELECT(\n'
    res += '\n'.join(ptfs) + '\n)\nCOMPRESS(ALL)\nBYPASS(HOLDSYS,HOLDUSER,\nHOLDCLASS(UCLREL,ERREL)).'
    res = smpe_jcl_header.replace('{csi}', csi) + res
    print('-'*20)
    print(res)
    if write_to_member:
        get_zosmf(target).write_ds(write_to_member, data=res)
    return ptfs


def itcam_dddef_gen(folder_):
    """
    put this after
    //SMPCNTL  DD  *
    """
    FOLDER = folder_
    dddefs_s = f'''
SET BDY(KDSTRG) .                                                        
UCLIN .                                                                  
ADD DDDEF(SCYNZTMN)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/toolkit/msg/zh_CN/IBM/').   
ADD DDDEF(SCYNZTMP)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/toolkit/msg/pt_BR/IBM/').   
ADD DDDEF(SCYNZTMK)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/toolkit/msg/ko/IBM/').      
ADD DDDEF(SCYNZTMJ)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/toolkit/msg/ja/IBM/').      
ADD DDDEF(SCYNZTMI)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/toolkit/msg/it/IBM/').      
ADD DDDEF(SCYNZTMF)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/toolkit/msg/fr/IBM/').      
ADD DDDEF(SCYNZTME)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/toolkit/msg/es/IBM/').      
ADD DDDEF(SCYNZTMD)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/toolkit/msg/de/IBM/').      
ADD DDDEF(SCYNZTMC)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/toolkit/msg/C/IBM/').       
ADD DDDEF(SCYNZTLE)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/toolkit/lib/ext/IBM/').     
ADD DDDEF(SCYNZTLB)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/toolkit/lib/IBM/').        
ADD DDDEF(SCYNZTET)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/toolkit/etc/IBM/').        
ADD DDDEF(SCYNZTCO)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/toolkit/codeset/IBM/').     
ADD DDDEF(SCYNZLW6)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/lib/ext/was/was6/').   
ADD DDDEF(SCYNZLW)                                                     
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/lib/ext/was/IBM/').   
ADD DDDEF(SCYNZLAX)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/lib/ext/axis/IBM/').   
ADD DDDEF(SCYNZLBE)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/lib/ext/IBM/').    
ADD DDDEF(SCYNZILB)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/lib/IBM/').        
ADD DDDEF(SCYNZWPS)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/etc/was/wps/IBM/').   
ADD DDDEF(SCYNZEW8)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/etc/was/was8/IBM/').   
ADD DDDEF(SCYNZE70)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/etc/was/was70/IBM/').   
ADD DDDEF(SCYNZEW7)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/etc/was/was7/IBM/').   
ADD DDDEF(SCYNZW61)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/etc/was/was61/IBM/').   
ADD DDDEF(SCYNZW60)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/etc/was/was60/IBM/').        
ADD DDDEF(SCYNZW6)                                                     
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/etc/was/was6/IBM/').        
ADD DDDEF(SCYNZW51)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/etc/was/was51/IBM/').        
ADD DDDEF(SCYNZW5)                                                     
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/etc/was/was5/IBM/').        
ADD DDDEF(SCYNZPRS)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/etc/was/prs/IBM/').        
ADD DDDEF(SCYNZESB)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/etc/was/esb/IBM/').        
ADD DDDEF(SCYNZWAS)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/etc/was/IBM/').        
ADD DDDEF(SCYNZBIN)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/bin/IBM/').                
ADD DDDEF(SCYNZETC)                                                    
PATH('/proj/omivty/{FOLDER}/usr/lpp/itcam/WAS/DC/itcamdc/etc/IBM/').        
ENDUCL .'''

    dddefs_t = []
    for ddef in dddefs_s.split('\n'):
        ddef = ddef.strip()
        if len(ddef) > 72:
            dddefs_t.append(ddef[:72])
            dddefs_t.append(ddef[72:])
        else:
            dddefs_t.append(ddef)
    print('\n'.join(dddefs_t))


def get_ptfs_from_smppts(smppts: str, target):
    if smppts.upper().endswith('.CSI'):
        smppts = smppts[0:smppts.rfind('.')] + '.SMPPTS'
    return get_zosmf(target).list(smppts)


def get_ptfs_from_smpe(csi=target_csi, target=target_system) -> set:
    csi = csi.upper()
    jcl = smpe_ptfs_jcl.replace('{csi}', csi)
    job = get_zosmf_jes(target).submit_jcl(text=jcl, wait=True)
    output = job.spool(ddname='SMPLIST')
    values = set()
    # find all write_time and check that we have differences, means we have more than 1 history period
    for m in re.finditer(r'(?P<value>[0-9A-Z]+)   TYPE            = (PTF|SUPERSEDED)', output):
        values.add(m.group('value'))
    return values


"""
################## HOW TO USE   ######################################

Copy this file with another name and do all modification there.

Update global variables to use defaults later on:

target_system = 'rsd1'
target_csi = 'ITM.ITE.CSI'


First of all, copy all available PTFs to target system

# for fmid in fmids:
#     sync_fmid(fmid, target_system)

IF you want to update everything, use "fmids" dict, if no, create your own set, for example:

# fms = {'HKCI310', 'HKDS630', 'HKLV630'}

If you create a new CSI and need to receive additional PTFs to what you already have in SMPPTS, use:

# gen_receive_job(fms, get_ptfs_from_smppts(target_csi, target_system), write_to_member='TS5813.TMP5(REC)')

If you update existing CSI, use:

# pt_l = gen_receive_job(fms, get_ptfs_from_smpe(target_csi, target_system), write_to_member='TS5813.TMP5(REC)')

Then use pt_l list of received PTFs to generate APPLY-CHECK and ACCEPT-CHECK jobs:

# gen_apply_job(pt_l, write_to_member='TS5813.TMP5(APP)')
# gen_accept_job(pt_l, write_to_member='TS5813.TMP5(ACC)')


Special function is created to generate DDDEF statements for ITCAM, as there is a limitation in 71 length

# itcam_dddef_gen('IZM')

"""

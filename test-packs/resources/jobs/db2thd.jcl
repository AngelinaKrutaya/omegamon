//{job}  JOB (ACCT#),' PG V540 ',CLASS=A,MSGCLASS=X,      
//         REGION=0M NOTIFY=&SYSUID TYPRUN=SCAN             
//*******************************************************   
//JOBLIB   DD DSN=RSRTE.DSN.VC10.RUNLIB.LOAD,DISP=SHR       
//         DD DSN=RSRTE.DSN.VC10.SDSNLOAD,DISP=SHR          
//DSNTEP2  EXEC PGM=IKJEFT01,DYNAMNBR=20                    
//SYSTSPRT DD SYSOUT=*                                      
//SYSPRINT DD SYSOUT=*                                      
//SYSUDUMP DD SYSOUT=*                                      
//SYSTSIN  DD *                                             
 DSN SYSTEM({ssid})                                           
 RUN  PROGRAM(DSNTEP2) PLAN(DSNTEP2)  PARMS('/ALIGN(MID)')  
 END                                                        
//SYSIN    DD *                                             
  SELECT COUNT(*) FROM SYSIBM.SYSCOLUMNS,                   
         SYSIBM.SYSCOLUMNS,                                 
         SYSIBM.SYSCOLUMNS ;                                

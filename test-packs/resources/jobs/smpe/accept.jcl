//${mf_user}AC JOB ,'OMPE SMP ACCC',CLASS=A,MSGCLASS=X,              
//       MSGLEVEL=(1,1) NOTIFY=&SYSUID                           
//*************************************************************  
//*        INVOKE SMP/E                                          
//*************************************************************  
//SMP1    EXEC PGM=GIMSMP,PARM='DATE=U',REGION=0M                
//SMPCSI   DD  DISP=SHR,DSN=${CSI}                          
//*                                                              
//SMPHOLD  DD  DUMMY                                             
//SMPCNTL  DD  *                                                 
    SET BDY(KDSDLB).                /* SET TO DISTRIBUTION ZONE*/
    ACCEPT SELECT(                  /* APPLY FOR THIS FMID     */
              ${APAR}                                            
                  )                                              
    COMPRESS(ALL)                                                
    BYPASS(HOLDSYS,HOLDUSER,        /* BYPASS OPTIONS          */
    HOLDCLASS(UCLREL,ERREL)).                                    
/*                                                               
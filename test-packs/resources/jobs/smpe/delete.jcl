//${mf_user}DL JOB (ACCT#),' RS52 V540 RTEBAS ',CLASS=A,         
//        MSGCLASS=X,REGION=0M NOTIFY=&SYSUID RESTART=FTP    
//*                                                          
//* -------------------------------------------------------- 
//* delete
//* -------------------------------------------------------- 
//*                                                          
//BR14      EXEC PGM=IEFBR14                                 
//SYSPRINT  DD SYSOUT=*                                      
//TRSOUT    DD DSN=${APARDS},                  
//             DISP=(MOD,DELETE),SPACE=(TRK,(1,1)),UNIT=SYSDA
//*                                                          
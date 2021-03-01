//${mf_user}S2 JOB (ACCOUNT),'V540 SMPAPPC  ',CLASS=A,                     
//         MSGCLASS=X,REGION=0M NOTIFY=&SYSUID                         
//*                                                                    
//*                                                                    
//*********************************************************************
//*                                                                    
//* FILE TAILORING MEMBER NAMES = GIMISCGA, GIMISCGB, GIMISCGE,        
//*                     GIMISCGG, GIMISCGM, GIMISCGS, GIMISCGZ         
//* JCL TAILORED BY FUNCTION = GIMISCG                                 
//* JCL DESCRIPTION = PERFORM APPLY CHECK, APPLY, ACCEPT CHECK OR      
//*                     ACCEPT PROCESSING                              
//*                                                                    
//*********************************************************************
//S1       EXEC PGM=GIMSMP,                                            
//         PARM='PROCESS=WAIT',                                        
//         DYNAMNBR=120                                                
//*                                                                    
//* NOTE:      SMP ZONE-RELATED FILES ARE DYNAMICALLY ALLOCATED,       
//*            THIS INCLUDES THE SMPPTS, SMPLOG, AND SMPTLIB DATA SETS.
//*                                                                    
//* SMP FILES                                                          
//*                                                                    
//SMPCSI   DD DISP=SHR,DSN=${CSI}                                 
//*                                                                    
//*                                                                    
//SMPCNTL  DD *                                                        
  SET     BOUNDARY ( KDSTRG )                                          
          .                                                            
  APPLY                                                                
   CHECK                                                               
          SELECT   (                                                   
                   ${APAR}                                             
                     )                                                 
          /*  REDO  */                                                 
          NOJCLINREPORT                                                
          COMPRESS(ALL)                                                
          RETRY     (YES)                                              
          BYPASS(HOLDSYS)
          .                                                            
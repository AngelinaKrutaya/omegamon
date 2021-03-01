//${mf_user}S1 JOB (ACCOUNT),'V540 SMPREC  ',CLASS=A,                      
//         MSGCLASS=X,REGION=0M NOTIFY=&SYSUID                         
//*                                                                    
//*                                                                    
//*********************************************************************
//* R E C E I V E   S Y S M O D S                                      
//*********************************************************************
//S2       EXEC PGM=GIMSMP,                                            
//         PARM='PROCESS=WAIT',                                        
//         DYNAMNBR=120                                                
//*                                                                    
//* NOTE:      SMP ZONE-RELATED FILES ARE DYNAMICALLY ALLOCATED,       
//*            THIS INCLUDES THE SMPPTS, SMPLOG, AND SMPTLIB DATA SETS.
//*                                                                    
//* SMP FILES                                                          
//*                                                                    
//SMPCSI   DD DISP=SHR,DSN=${CSI} 
//SMPPTFIN DD DISP=SHR,DSN=${APARDS}
//SMPCNTL  DD *                                                        
 SET    BOUNDARY ( GLOBAL )   .                                        
 RECEIVE                                                               
         SELECT(                                                       
                ${APAR}                                                
                 )                                                     
         SYSMODS                                                       
                .                                                      

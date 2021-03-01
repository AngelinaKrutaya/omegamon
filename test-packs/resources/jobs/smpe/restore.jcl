//${mf_user}RT JOB ,'OMPE APAR REJ',CLASS=A,MSGCLASS=X,
//         MSGLEVEL=(1,1),REGION=0M 
//*                                                
//*                                                
//S1       EXEC PGM=GIMSMP,                        
//         PARM='PROCESS=WAIT',                    
//         DYNAMNBR=120                            
//*                                                
//SMPCSI   DD DISP=SHR,DSN=${CSI}             
//*                                                
//SMPCNTL  DD *                                    
  SET     BOUNDARY ( KDSTRG )                      
          .                                        
  RESTORE                                          
          SELECT   (                               
                     ${APAR}                       
                     )                             
          COMPRESS(ALL)                            
          RETRY     (YES)                          
      /*  BYPASS(HOLDSYSTEM)  */                   
          .                                        
/*                                           
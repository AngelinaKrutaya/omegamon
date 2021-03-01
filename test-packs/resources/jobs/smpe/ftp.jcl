//${mf_user}FT JOB (ACCOUNT),'FTP  ',CLASS=A,                      
//         MSGCLASS=X,REGION=0M NOTIFY=&SYSUID                         
//*                                                         
//* --------------------------------------------------------
//*                                                         
//* --------------------------------------------------------
//*                                                         
//FTP      EXEC PGM=FTP,PARM='(EXIT',COND=(04,LT)           
//SYSPRINT DD SYSOUT=*                                      
//OUTPUT   DD SYSOUT=*                                      
//INPUT    DD *                                             
${target_system}                                                        
${mf_user}                                                      
${mf_password}                                                    
MODE B                                                      
LOCSITE FWFRIENDLY                                          
SITE DATACLAS=EFCOMP5                                       
EBCDIC                                                      
MVSPUT '${APARDS}'                        
                                                            
QUIT                                                        
/*                                                          
//*                                                         
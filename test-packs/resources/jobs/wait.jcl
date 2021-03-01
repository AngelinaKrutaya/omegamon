//{job} JOB (ACCT#),' PG V540 ',CLASS=A,MSGCLASS=X,
//         REGION=0M NOTIFY=&SYSUID TYPRUN=SCAN       
//WAITXMIN   EXEC PGM=BPXBATCH,REGION=0M,             
//  PARM='sh sleep {seconds}s'                                
//STDIN    DD DUMMY                                   
//STDOUT   DD SYSOUT=*                                
//STDERR   DD SYSOUT=*                                
/*                                                    
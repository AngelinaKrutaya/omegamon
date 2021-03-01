This semi-automated process can be used to drive workload in your ITM environment by constantly submitting CT_Get SOAP requests that retrieve data from the managed systems.  The first step is to build CT_Get requests for the current managed systems.  The second step is to run the program that submits the requests at a fixed intervals.  The process does not notify you automatically of any anomaly during the process; however, it provides log files for you to diagnose and detect the errors easily.    

The batch files and PERL programs were written to run on Windows, but you can modify them to run on Linux/UNIX.  The PERL programs expect the same file/directory structure as they are contained in the zip file.  You may change the file/directory structure provided that you also change the variables referring to those files/directories in the PERL program 'BuildCT_Get.pl'.  

Before using the process, install the current versions of PERL and CURL, and include them in the PATH variable of the system, and make sure that the ITM HUB can be reached via a SOAP connection. Review the following README files in this sequence:

1. SOAP/input/product_attr_README.txt 
 
   It explains how to add your product tables to SOAP/input/product_attr.txt.

2. SOAP/BuildCT_Get_README.txt

   It shows how to run the program to build the CT_Get SOAP requests.

3. SOAP/xxxxxx/LoopSOAP_README.txt
  
   The xxxxxx directory is created/modified by SOAP/BuildCT_Get.pl.
   The README file is copied from SOAP/input.     
   It describes how to start sending CT_Get SOAP requests to ITM and view the results.  

  
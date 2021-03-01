1. Do not delete the 'input' subdirectory.  It contains essential files to support the 'BuildCT_Get' program.

2. Update 'BuildCT_Get.bat' to have the correct input argument values for HUB_Host_Name HUB_SOAP_Port UserID Password.

3. Run 'BuildCT_Get.bat'.  

4. A file 'BuildCT_Get_OUTPUT.log' is generated to record mostly diagnostic information.

5. The 'BuildCT_Get' program issues a SOAP request to the Hub to retrieve all the online nodes, uses the files in the 'input' subdirectory, and builds a subdirectory that is named after the Hub's hostname.  The subdirectory contains CT_GET requests, a program that submits the requests repeatedly to the Hub, and a program that summarizes the responses.  After 'BuildCT_Get' ends, you may move the subdirectory to another location on the same system or on another system. When you are ready to submit the CT_GET requests, drill into that directory and follow the instructions in 'LoopSOAP_README.txt'.       






  
1. The 'product_attr.txt' file defines the attribute tables to be targeted by CT_GET requests for each product code.    

2. Each entry in 'product_attr.txt' has three fields: 

   Product_Code -   ITM product code. 

   Unique_Name -    Since CT_GET requests can retrieve data only from the subnodes for some product, this field is used mainly to filter in 
                    the managed system name to be processed.  However, you can exclude the managed system name that contains this Unique Name, 
					specify '-' before the Unique Name.  

   table_name -     Will be specified in the CT_GET object segment.    


3. Many tables can be specified for the same product code.  


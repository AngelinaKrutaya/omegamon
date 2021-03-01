The perl script 'extractAttrGroup.pl' creates a file containing all the attribute tables for an agent type. 
You can then select some or all the attributes table for this agent type to be processed by "BuildCT_Get.bat" 
and generate CT_Get requests, one per attribute table, for the agent type.  

1. Place an agent's attribute file, e.g km5.atr from a z/OS RKANDATV(km5atr) member, in the same directory.

2. Edit the two lines, as below, in extractAttrGroup.pl, specifying the proper values.

    my $product = "M5";         #Agent's product code
    my $filter  = "MVSSYS";     #Look it up in product_attr_backup.txt

3. Issue '.../perl extractAttrGroup.pl'  in a Windows command prompt.

4. Incorporate the content of the output file (e.g. m5_attr.txt) into product_attr.txt, before running BuildCT_Get.bat.  
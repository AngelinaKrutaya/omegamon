:: Use to get list of all attributes: -c 30m
::   tacmd histlistattributegroups -t IP -c 30m

:: Use to get all active collections -c 30m
::   tacmd histlistcollections -t IP -c 30m

:: Connect server -c 30m
::tacmd tepslogin -s waldevompeivt02.dev.rocketsoftware.com -u sysadmin -p '' -c 30m
:: Create collection -c 30m
::                                                                                                                      remove (-l TEMS) to use TEMA as collection location -c 30m
tacmd histcreatecollection -t IP -o "Address Spaces"        -a "Address Spaces"         -c 30m
tacmd histcreatecollection -t IP -o "Balancing Groups"        -a "Balancing Groups"         -c 30m
tacmd histcreatecollection -t IP -o "Buffer Pool Statistics"      -a "Buffer Pool Statistics"       -c 30m
tacmd histcreatecollection -t IP -o "CF Group Name"        -a "CF Group Name"          -c 30m
tacmd histcreatecollection -t IP -o "DASD Logging"         -a "DASD Logging"          -c 30m
tacmd histcreatecollection -t IP -o "Data Entry Databases"       -a "Data Entry Databases"        -c 30m
tacmd histcreatecollection -t IP -o "DBCTL Thread Calls"       -a "DBCTL Thread Calls"        -c 30m
tacmd histcreatecollection -t IP -o "DBCTL Thread Details"       -a "DBCTL Thread Details"        -c 30m
tacmd histcreatecollection -t IP -o "DBCTL Thread Indoubts"      -a "DBCTL Thread Indoubts"        -c 30m
tacmd histcreatecollection -t IP -o "DBCTL Thread Summaries"      -a "DBCTL Thread Summaries"       -c 30m
tacmd histcreatecollection -t IP -o "Dependent Regions"       -a "Dependent Regions"         -c 30m
tacmd histcreatecollection -t IP -o "Dependent Regions Statistics"     -a "Dependent Regions Statistics"      -c 30m
tacmd histcreatecollection -t IP -o "Extended Recovery Facility"     -a "Extended Recovery Facility"      -c 30m
tacmd histcreatecollection -t IP -o "External Subsystems"       -a "External Subsystems"        -c 30m
tacmd histcreatecollection -t IP -o "Fast Path Regions"       -a "Fast Path Regions"         -c 30m
tacmd histcreatecollection -t IP -o "Fast Path System"        -a "Fast Path System"         -c 30m
tacmd histcreatecollection -t IP -o "HALDB Database Summary"      -a "HALDB Database Summary"       -c 30m
tacmd histcreatecollection -t IP -o "HALDB Partition Detail"      -a "HALDB Partition Detail"       -c 30m
tacmd histcreatecollection -t IP -o "I/O Devices"         -a "I/O Devices"          -c 30m
tacmd histcreatecollection -t IP -o "IMS All RTA Interval Summary"     -a "IMS All RTA Interval Summary"      -c 30m
tacmd histcreatecollection -t IP -o "IMS All RTA Slot Summary"      -a "IMS All RTA Slot Summary"       -c 30m
tacmd histcreatecollection -t IP -o "IMS Bottleneck Analysis Detail"    -a "IMS Bottleneck Analysis Detail"     -c 30m
tacmd histcreatecollection -t IP -o "IMS Bottleneck Analysis Summary"    -a "IMS Bottleneck Analysis Summary"     -c 30m
tacmd histcreatecollection -t IP -o "IMS Databases"        -a "IMS Databases"          -c 30m
tacmd histcreatecollection -t IP -o "IMS Health"         -a "IMS Health"          -c 30m
tacmd histcreatecollection -t IP -o "IMS I/O"          -a "IMS I/O"           -c 30m
tacmd histcreatecollection -t IP -o "IMS Local Lock Conflicts"      -a "IMS Local Lock Conflicts"       -c 30m
tacmd histcreatecollection -t IP -o "IMS Local MSC Performance Statistics"   -a "IMS Local MSC Performance Statistics"    -c 30m
tacmd histcreatecollection -t IP -o "IMS Lock Conflicts"       -a "IMS Lock Conflicts"        -c 30m
tacmd histcreatecollection -t IP -o "IMS RTA Exceptions"       -a "IMS RTA Exceptions"        -c 30m
tacmd histcreatecollection -t IP -o "IMS RTA Group Items Slots"     -a "IMS RTA Group Items Slots"       -c 30m
tacmd histcreatecollection -t IP -o "IMS RTA Groups Slots"       -a "IMS RTA Groups Slots"        -c 30m
tacmd histcreatecollection -t IP -o "IMS RTA Highest Resp Times LTERMs"   -a "IMS RTA Highest Resp Times LTERMs"     -c 30m
tacmd histcreatecollection -t IP -o "IMS RTA Highest Resp Times Trans"    -a "IMS RTA Highest Resp Times Trans"     -c 30m
tacmd histcreatecollection -t IP -o "IMS RTA Interval Summary"      -a "IMS RTA Interval Summary"       -c 30m
tacmd histcreatecollection -t IP -o "IMS RTA Slot Summary"       -a "IMS RTA Slot Summary"        -c 30m
tacmd histcreatecollection -t IP -o "IMS STATUS"         -a "IMS STATUS"          -c 30m
tacmd histcreatecollection -t IP -o "IMS System"         -a "IMS System"          -c 30m
tacmd histcreatecollection -t IP -o "IMS VSAM Databases"       -a "IMS VSAM Databases"        -c 30m
tacmd histcreatecollection -t IP -o "IMSPLEX DBCTL Thread Summary"     -a "IMSPLEX DBCTL Thread Summary"      -c 30m
tacmd histcreatecollection -t IP -o "IMSPLEX Health"        -a "IMSPLEX Health"         -c 30m
tacmd histcreatecollection -t IP -o "Internal Resource Lock Manager"    -a "Internal Resource Lock Manager"     -c 30m
tacmd histcreatecollection -t IP -o "Local CF IMS Data Sharing"     -a "Local CF IMS Data Sharing"       -c 30m
tacmd histcreatecollection -t IP -o "Local CF IMS DS OSAM"       -a "Local CF IMS DS OSAM"        -c 30m
tacmd histcreatecollection -t IP -o "Local IMS Startup Parameters"     -a "Local IMS Startup Parameters"      -c 30m
tacmd histcreatecollection -t IP -o "Local IMSCTL ACKNAK Detail"     -a "Local IMSCTL ACKNAK Detail"      -c 30m
tacmd histcreatecollection -t IP -o "Local IMSCTL Exception Events"    -a "Local IMSCTL Exception Events"      -c 30m
tacmd histcreatecollection -t IP -o "Local IMSCTL Resume Detail"     -a "Local IMSCTL Resume Detail"      -c 30m
tacmd histcreatecollection -t IP -o "Local IMSCTL TCPIP Usage Detail"    -a "Local IMSCTL TCPIP Usage Detail"     -c 30m
tacmd histcreatecollection -t IP -o "Local IMSCTL Transit Client"     -a "Local IMSCTL Transit Client"      -c 30m
tacmd histcreatecollection -t IP -o "Local IMSCTL Transit Detail"     -a "Local IMSCTL Transit Detail"      -c 30m
tacmd histcreatecollection -t IP -o "Local IMSCTL Transit Port"     -a "Local IMSCTL Transit Port"       -c 30m
tacmd histcreatecollection -t IP -o "Local IMSCTL Transit TDatastore"    -a "Local IMSCTL Transit TDatastore"     -c 30m
tacmd histcreatecollection -t IP -o "Local IMSCTL Transit Trancode"    -a "Local IMSCTL Transit Trancode"      -c 30m
tacmd histcreatecollection -t IP -o "Local IMSCTL Transit User"     -a "Local IMSCTL Transit User"       -c 30m
tacmd histcreatecollection -t IP -o "Local KIP MQ Statistics"      -a "Local KIP MQ Statistics"       -c 30m
tacmd histcreatecollection -t IP -o "Local MSC Logical Links"      -a "Local MSC Logical Links"       -c 30m
tacmd histcreatecollection -t IP -o "Local MSC Physical Links"      -a "Local MSC Physical Links"       -c 30m
tacmd histcreatecollection -t IP -o "Local RTA GNT"        -a "Local RTA GNT"          -c 30m
tacmd histcreatecollection -t IP -o "Local RTA INT"        -a "Local RTA INT"          -c 30m
tacmd histcreatecollection -t IP -o "Logical Terminals"       -a "Logical Terminals"         -c 30m
tacmd histcreatecollection -t IP -o "Main Storage Databases"      -a "Main Storage Databases"       -c 30m
tacmd histcreatecollection -t IP -o "MSDB Fields"         -a "MSDB Fields"          -c 30m
tacmd histcreatecollection -t IP -o "Omegamon XE Messages"       -a "Omegamon XE Messages"        -c 30m
tacmd histcreatecollection -t IP -o "Online Logging Datasets"      -a "Online Logging Datasets"       -c 30m
tacmd histcreatecollection -t IP -o "OSAM Subpools"        -a "OSAM Subpools"          -c 30m
tacmd histcreatecollection -t IP -o "OTMA Group"         -a "OTMA Group"          -c 30m
tacmd histcreatecollection -t IP -o "OTMA Status"         -a "OTMA Status"          -c 30m
tacmd histcreatecollection -t IP -o "OTMA TMember"         -a "OTMA TMember"          -c 30m
tacmd histcreatecollection -t IP -o "OTMA TPipe"         -a "OTMA TPipe"          -c 30m
tacmd histcreatecollection -t IP -o "Pool Buffer Statistics"      -a "Pool Buffer Statistics"       -c 30m
tacmd histcreatecollection -t IP -o "Pool Utilization"        -a "Pool Utilization"         -c 30m
tacmd histcreatecollection -t IP -o "Program Scheduling Blocks"     -a "Program Scheduling Blocks"       -c 30m
tacmd histcreatecollection -t IP -o "RECON Datasets"        -a "RECON Datasets"         -c 30m
tacmd histcreatecollection -t IP -o "SharedQueues APPC LUname Summary"    -a "SharedQueues APPC LUname Summary"     -c 30m
tacmd histcreatecollection -t IP -o "SharedQueues APPC TPname Summary"    -a "SharedQueues APPC TPname Summary"     -c 30m
tacmd histcreatecollection -t IP -o "SharedQueues Cold QueueName Summary"   -a "SharedQueues Cold QueueName Summary"    -c 30m
tacmd histcreatecollection -t IP -o "SharedQueues Cold QueueType Summary"   -a "SharedQueues Cold QueueType Summary"    -c 30m
tacmd histcreatecollection -t IP -o "SharedQueues FP Program Summary"    -a "SharedQueues FP Program Summary"     -c 30m
tacmd histcreatecollection -t IP -o "SharedQueues LTERM Summary"     -a "SharedQueues LTERM Summary"      -c 30m
tacmd histcreatecollection -t IP -o "SharedQueues OTMA Tmember Summary"   -a "SharedQueues OTMA Tmember Summary"     -c 30m
tacmd histcreatecollection -t IP -o "SharedQueues OTMA Tpipe Summary"    -a "SharedQueues OTMA Tpipe Summary"     -c 30m
tacmd histcreatecollection -t IP -o "SharedQueues Transaction Summary"    -a "SharedQueues Transaction Summary"     -c 30m
tacmd histcreatecollection -t IP -o "Sub Pool Statistics"       -a "Sub Pool Statistics"        -c 30m
tacmd histcreatecollection -t IP -o "Subsystem Connections"      -a "Subsystem Connections"        -c 30m
tacmd histcreatecollection -t IP -o "TCBCPU Utilization"       -a "TCBCPU Utilization"        -c 30m
tacmd histcreatecollection -t IP -o "Transaction Summary"       -a "Transaction Summary"        -c 30m
tacmd histcreatecollection -t IP -o "Transactions"         -a "Transactions"          -c 30m
tacmd histcreatecollection -t IP -o "Virtual Storage Option Dataspace Areas"  -a "Virtual Storage Option Dataspace Areas"   -c 30m
tacmd histcreatecollection -t IP -o "Virtual Storage Option Dataspaces"   -a "Virtual Storage Option Dataspaces"     -c 30m
tacmd histcreatecollection -t IP -o "VSAM/OSAM Databases"       -a "VSAM/OSAM Databases"        -c 30m
tacmd histcreatecollection -t IP -o "VSAM Subpools"        -a "VSAM Subpools"           -c 30m

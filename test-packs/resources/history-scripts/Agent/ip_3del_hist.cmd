:: Use to get list of all attributes:
::   tacmd histlistattributegroups -t IP

:: Use to get all active collections
::   tacmd histlistcollections -t IP

:: Connect server
::tacmd tepslogin -s waldevompeqa06.dev.rocketsoftware.com -u sysadmin -p ''
:: Stop collections
::                                                                                 use (-m "IEK1:RS27:IMS" "IFK3:RS27:IMS") instead of (-n ...) if collection's location is TEMA
:: Delete collections
tacmd histdeletecollection -a "Address Spaces"
tacmd histdeletecollection -a "Balancing Groups"
tacmd histdeletecollection -a "Buffer Pool Statistics"
tacmd histdeletecollection -a "CF Group Name"
tacmd histdeletecollection -a "DASD Logging"
tacmd histdeletecollection -a "Data Entry Databases"
tacmd histdeletecollection -a "DBCTL Thread Calls"
tacmd histdeletecollection -a "DBCTL Thread Details"
tacmd histdeletecollection -a "DBCTL Thread Indoubts"
tacmd histdeletecollection -a "DBCTL Thread Summaries"
tacmd histdeletecollection -a "Dependent Regions"
tacmd histdeletecollection -a "Dependent Regions Statistics"
tacmd histdeletecollection -a "Extended Recovery Facility"
tacmd histdeletecollection -a "External Subsystems"
tacmd histdeletecollection -a "Fast Path Regions"
tacmd histdeletecollection -a "Fast Path System"
tacmd histdeletecollection -a "HALDB Database Summary"
tacmd histdeletecollection -a "HALDB Partition Detail"
tacmd histdeletecollection -a "I/O Devices"
tacmd histdeletecollection -a "IMS All RTA Interval Summary"
tacmd histdeletecollection -a "IMS All RTA Slot Summary"
tacmd histdeletecollection -a "IMS Bottleneck Analysis Detail"
tacmd histdeletecollection -a "IMS Bottleneck Analysis Summary"
tacmd histdeletecollection -a "IMS Databases"
tacmd histdeletecollection -a "IMS Health"
tacmd histdeletecollection -a "IMS I/O"
tacmd histdeletecollection -a "IMS Local Lock Conflicts"
tacmd histdeletecollection -a "IMS Local MSC Performance Statistics"
tacmd histdeletecollection -a "IMS Lock Conflicts"
tacmd histdeletecollection -a "IMS RTA Exceptions"
tacmd histdeletecollection -a "IMS RTA Group Items Slots"
tacmd histdeletecollection -a "IMS RTA Groups Slots"
tacmd histdeletecollection -a "IMS RTA Highest Resp Times LTERMs"
tacmd histdeletecollection -a "IMS RTA Highest Resp Times Trans"
tacmd histdeletecollection -a "IMS RTA Interval Summary"
tacmd histdeletecollection -a "IMS RTA Slot Summary"
tacmd histdeletecollection -a "IMS STATUS"
tacmd histdeletecollection -a "IMS System"
tacmd histdeletecollection -a "IMS VSAM Databases"
tacmd histdeletecollection -a "IMSPLEX DBCTL Thread Summary"
tacmd histdeletecollection -a "IMSPLEX Health"
tacmd histdeletecollection -a "Internal Resource Lock Manager"
tacmd histdeletecollection -a "Local CF IMS Data Sharing"
tacmd histdeletecollection -a "Local CF IMS DS OSAM"
tacmd histdeletecollection -a "Local IMS Startup Parameters"
tacmd histdeletecollection -a "Local IMSCTL ACKNAK Detail"
tacmd histdeletecollection -a "Local IMSCTL Exception Events"
tacmd histdeletecollection -a "Local IMSCTL Resume Detail"
tacmd histdeletecollection -a "Local IMSCTL TCPIP Usage Detail"
tacmd histdeletecollection -a "Local IMSCTL Transit Client"
tacmd histdeletecollection -a "Local IMSCTL Transit Detail"
tacmd histdeletecollection -a "Local IMSCTL Transit Port"
tacmd histdeletecollection -a "Local IMSCTL Transit TDatastore"
tacmd histdeletecollection -a "Local IMSCTL Transit Trancode"
tacmd histdeletecollection -a "Local IMSCTL Transit User"
tacmd histdeletecollection -a "Local KIP MQ Statistics"
tacmd histdeletecollection -a "Local MSC Logical Links"
tacmd histdeletecollection -a "Local MSC Physical Links"
tacmd histdeletecollection -a "Local RTA GNT"
tacmd histdeletecollection -a "Local RTA INT"
tacmd histdeletecollection -a "Logical Terminals"
tacmd histdeletecollection -a "Main Storage Databases"
tacmd histdeletecollection -a "MSDB Fields"
tacmd histdeletecollection -a "Omegamon XE Messages"
tacmd histdeletecollection -a "Online Logging Datasets"
tacmd histdeletecollection -a "OSAM Subpools"
tacmd histdeletecollection -a "OTMA Group"
tacmd histdeletecollection -a "OTMA Status"
tacmd histdeletecollection -a "OTMA TMember"
tacmd histdeletecollection -a "OTMA TPipe"
tacmd histdeletecollection -a "Pool Buffer Statistics"
tacmd histdeletecollection -a "Pool Utilization"
tacmd histdeletecollection -a "Program Scheduling Blocks"
tacmd histdeletecollection -a "RECON Datasets"
tacmd histdeletecollection -a "SharedQueues APPC LUname Summary"
tacmd histdeletecollection -a "SharedQueues APPC TPname Summary"
tacmd histdeletecollection -a "SharedQueues Cold QueueName Summary"
tacmd histdeletecollection -a "SharedQueues Cold QueueType Summary"
tacmd histdeletecollection -a "SharedQueues FP Program Summary"
tacmd histdeletecollection -a "SharedQueues LTERM Summary"
tacmd histdeletecollection -a "SharedQueues OTMA Tmember Summary"
tacmd histdeletecollection -a "SharedQueues OTMA Tpipe Summary"
tacmd histdeletecollection -a "SharedQueues Transaction Summary"
tacmd histdeletecollection -a "Sub Pool Statistics"
tacmd histdeletecollection -a "Subsystem Connections"
tacmd histdeletecollection -a "TCBCPU Utilization"
tacmd histdeletecollection -a "Transaction Summary"
tacmd histdeletecollection -a "Transactions"
tacmd histdeletecollection -a "Virtual Storage Option Dataspace Areas"
tacmd histdeletecollection -a "Virtual Storage Option Dataspaces"
tacmd histdeletecollection -a "VSAM/OSAM Databases"
tacmd histdeletecollection -a "VSAM Subpools"

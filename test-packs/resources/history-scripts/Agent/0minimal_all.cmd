:::CICS
tacmd histcreatecollection -t OMCICS -o "CICSplex DB2 Summary                       " -a "CICSplex DB2 Summary                       "  -c 30m
tacmd histcreatecollection -t OMCICS -o "CICSplex Transaction Analysis              " -a "CICSplex Transaction Analysis              "  -c 30m
tacmd histstartcollection -a "CICSplex DB2 Summary                       " -m "*MVS_CICS" 
tacmd histstartcollection -a "CICSplex Transaction Analysis              " -m "*MVS_CICS" 

:::DB2
tacmd histcreatecollection -t DP -o "ALL THREADS" -a "ALL THREADS" -c 30m
tacmd histcreatecollection -t DP -o "Storage Consumption" -a "Storage Consumption" -c 30m
tacmd histcreatecollection -t DP -o "DB2 System States" -a "DB2 System States"             -c 30m
tacmd histcreatecollection -t DP -o "DB2 SRM Subsystem" -a "DB2 SRM Subsystem"             -c 30m
tacmd histstartcollection -a "DB2 SRM Subsystem" -m "*MVS_DB2"           
tacmd histstartcollection -a "DB2 System States" -m "*MVS_DB2"           
tacmd histstartcollection -a "ALL THREADS" -m "*MVS_DB2"  
tacmd histstartcollection -a "Storage Consumption" -m "*MVS_DB2"         

:::IMS
tacmd histcreatecollection -t IP -o "Address Spaces" -a "Address Spaces" -c 30m
tacmd histcreatecollection -t IP -o "IMS Health" -a "IMS Health" -c 30m
tacmd histstartcollection -a "Address Spaces" -m "*MVS_IMSPLEX"
tacmd histstartcollection -a "IMS Health"  -m "*MVS_IMSPLEX"

::JVM
tacmd histcreatecollection -t jj -o "JVM Address Space" -a "JVM Address Space" -c 30m
tacmd histcreatecollection -t jj -o "JVM CPU" -a "JVM CPU" -c 30m
tacmd histstartcollection -a "JVM Address Space" -m "*JVM_Monitor"
tacmd histstartcollection -a "JVM CPU" -m "*JVM_Monitor"

:::MFN
tacmd histcreatecollection -t KN3 -o "TCPIP Address Space" -a "TCPIP Address Space" -c 30m
tacmd histcreatecollection -t KN3 -o "TCPIP Applications" -a "TCPIP Applications" -c 30m
tacmd histstartcollection -a "TCPIP Address Space" -m "*OMEGAMONXE_MAINFRAME_NTWK_TCP"
tacmd histstartcollection -a "TCPIP Applications" -m "*OMEGAMONXE_MAINFRAME_NTWK_TCP"

:::MQ
tacmd histcreatecollection -t mq -o "Application Long-Term History" -a "Application Long-Term History" -c 30m
tacmd histcreatecollection -t mq -o "Buffer Manager Long-Term History" -a "Buffer Manager Long-Term History" -c 30m
tacmd histstartcollection -a "Application Long-Term History" -m "*MVS_MQM"
tacmd histstartcollection -a "Buffer Manager Long-Term History" -m "*MVS_MQM"

:::MQQI
tacmd histcreatecollection -t qi -o "Components" -a "Components" -c 30m
tacmd histcreatecollection -t qi -o "Broker Status" -a "Broker Status" -c 30m
tacmd histstartcollection -a "Broker Status" -m "*MQSI_BROKER_V7"
tacmd histstartcollection -a "Components" -m "*MQSI_AGENT"

:::MVS
tacmd histcreatecollection -t KM5 -o "Address Space Summary" -a "Address Space Summary" -c 30m
tacmd histcreatecollection -t KM5 -o "Common Storage" -a "Common Storage" -c 30m
tacmd histstartcollection -a "Address Space Summary" -m "*MVS_SYSTEM"
tacmd histstartcollection -a "Common Storage" -m "*MVS_SYSTEM"

:::Storage
tacmd histcreatecollection -t S3 -o "S3 Application Monitoring" -a "S3 Application Monitoring" -c 30m
tacmd histcreatecollection -t S3 -o "S3 Channel Path" -a "S3 Channel Path" -c 30m
tacmd histstartcollection -a "S3 Application Monitoring" -m "*OMEGAMONXE_SMS"
tacmd histstartcollection -a "S3 Channel Path" -m "*OMEGAMONXE_SMS"

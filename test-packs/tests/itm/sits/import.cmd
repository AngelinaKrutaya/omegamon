:::Import
tacmd login -s rsd4:21020 -u ts5813 -p xxx
tacmd bulkImportSit -p . -f -d


:::Associations
tacmd tepslogin -s waldevitmzqa03:1920 -u ts5813 -p xxx
tacmd createSitAssociation -i IVT_DP_Always_False -a "Enterprise/z//OS Systems/RSPLEXL4:MVS:SYSPLEX/RSD4/DB2/IB1D:RSD4:DB2" -f
tacmd createSitAssociation -i IVT_DP_Always_True -a "Enterprise/z//OS Systems/RSPLEXL4:MVS:SYSPLEX/RSD4/DB2/IB1D:RSD4:DB2" -f

tacmd createSitAssociation -i IVT_M5_Can_Be_True -a "Enterprise/z//OS Systems/RSPLEXL4:MVS:SYSPLEX/RSD4/MVS Operating System/RSPLEXL4:RSD4:MVSSYS" -f
tacmd createSitAssociation -i IVT_M5_SOAP_UTF8 -a "Enterprise/z//OS Systems/RSPLEXL4:MVS:SYSPLEX/RSD4/MVS Operating System/RSPLEXL4:RSD4:MVSSYS/Health Checks" -f




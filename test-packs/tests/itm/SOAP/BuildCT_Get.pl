#!/usr/bin/perl   
my $outfile="BuildCT_Get_OUTPUT.log";    # this script's log 
open(MYOUTFILE, ">$outfile");
my $numArgs = $#ARGV + 1;
if ($numArgs < 2) {
   print MYOUTFILE "Missing input argument(s) - BuildCT_Get.pl Hub_Host_Name Hub_Soap_Portuserid password\n";
   exit;
}

my $hostname; # "itmmt745.rtp.raleigh.ibm.com"
my $soapport; # 1920
my $userid;   # "sysadmin"
my $password; # "il0veitm"

my $work;

$hostname = $ARGV[0];

$work = $ARGV[1];
if ($work =~ /^-?\D/ ) {
    print STDOUT "Invalid Soap Port.  \n";
    exit;
} else {
    $soapport = $work; 
} 

$userid = $ARGV[2];
$password = $ARGV[3];


my $shortname = $hostname;
if ($shortname =~ /\./) {
    $shortname = substr($shortname, 0, index($shortname, ".") );
}

my $attrfile="input\\product_attr.txt";  # product attribute file.  
my $reqdir = $shortname;                # directory containing files to loop thru requests
my $reqsubdir = "request";               # subdirectory containing SOAP request files
my $execfile= "loopSOAP.bat";            # batch program to start SOAP request loop

my $temsurl;
my $req;
my $allnodes;

if ($port =~ "3661") {
   $temsurl = "https://$hostname:$soapport///cms/soap";
} else {
   $temsurl = "http://$hostname:$soapport///cms/soap";
}

$req="<CT_Get><userid>$userid</userid><password>$password</password><object>ManagedSystem</object><target>ManagedSystemName</target></CT_Get>";
print MYOUTFILE "Issuing curl -k -X POST -d \"$req\" $temsurl \r\n";
$allnodes = qx(curl -k -s -X POST -d \"$req\" $temsurl);
print MYOUTFILE "$allnodes\r\n";
if (!$allnodes) {
   print MYOUTFILE "No SOAP connection!!!   Failed to issue the command \r\n\r\n\tcurl -k -X POST -d \"$req\" $temsurl \r\n\r\n.  The SOAP connection problem must be resolved before this script is useful. \r\n";
exit 8
}

#system("rd /s /q \"$reqdir\"");
system("mkdir $reqdir");
system("mkdir $reqdir\\$reqsubdir");
my $loc;
my $line;
my @prodtype;
my @prodkey;
my @prodattr;
my @prodexclude;
my $prodtype;
my $prodkey;
my $prodexclude;
my $prodattr;

open(MYATTRFILE, $attrfile) || die("Could not open $attrfile"); 
while(<MYATTRFILE>) {
   $line = $_;
   chomp($line);
   if ($line eq "") {
      next;
   }
   $prodtype = substr($line,0,2);
   $line = trim(substr($line,3));
   $loc = index($line, " ");
   $prodkey = substr($line,0,$loc);
   if (substr($prodkey, 0, 1) eq "-")  {
      $prodkey = substr($prodkey,1);
      $prodexclude = 1;
   } else {
      $prodexclude = 0;
   }
 
   $prodattr = trim(substr($line,$loc + 1));
   #print STDOUT "$prodtype $prodkey $prodattr \r\n";
   push(@prodtype, $prodtype);
   push(@prodkey, $prodkey);
   push(@prodexclude, $prodexclude);
   push(@prodattr, $prodattr);
}

close(MYATTRFILE);
#print MYOUTFILE "close MYATTRFILE \r\n";


my $i = 0;
my $numprod = @prodtype;

my $nodename;
my $nodestatus;
my $nodetype;
my $nodecount;
my $begloc;
my $endloc;

my $soapobject;
my $numreq = 0;
my $filename;
my $target;
my $tobuild;
my $key1;
my $key2;

my $nextnode = 1;

while ($nextnode) {

   $begloc=index($allnodes, "<Name>");
   if ($begloc < 0) {
       $nextnode = 0;
       last;
   }
   $endloc= index($allnodes,"</Name>");
   $nodename = substr($allnodes, $begloc + length("<Name>"), $endloc - $begloc - length("<Name>") );
   $allnodes = substr($allnodes, $endloc + length("</Name>") );
   #print "$nodename \r\n";
   
   $begloc=index($allnodes, "<Status>");
   $endloc= index($allnodes,"</Status>");
   $nodestatus = substr($allnodes, $begloc + length("<Status>"), $endloc - $begloc - length("<Status>") );
   $allnodes = substr($allnodes, $endloc + length("</Status>") );
   if ($nodestatus ne "*ONLINE" )   {
      next;
   }

   $begloc=index($allnodes, "<Product>");
   $endloc= index($allnodes,"</Product>");
   $nodetype = substr($allnodes, $begloc + length("<Product>"), $endloc - $begloc - length("<Product>") );
   $allnodes = substr($allnodes, $endloc + length("</Product>") );
   $count++;
   #print "$nodename $nodestatus $nodetype \r\n";
   print MYOUTFILE "\'$nodename\' \'$nodetype\' \r\n";

   #  Find the Attribute Group for the node type 

   $soapobject = " ";
  
   for ($i=0; $i < $numprod; $i++) {
      if ($nodetype ne @prodtype[$i]) {
          next;
      }
      $key1 = $prodkey[$i];
      $tobuild = 0;
      $loc = index($key1,"&");
      if ( $loc > 0) {
          $key2 = trim(substr($key1, $loc + 1)); 
          $key1 = trim(substr($key1, 0, $loc));
          if ( index($nodename,$key1) >= 0 && index($nodename,$key2) >= 0  ) {
            $tobuild = 1;  
          }

      } else {
         if ( ($nodename =~ /$key1/ && !$prodexclude[$i] ) ||
              ($nodename !~ /$key1/ &&  $prodexclude[$i] ) )  {
            $tobuild = 1;


#         if ( (index($nodename,$key1) >= 0 && !$prodexclude[$i] ) ||
#              (index($nodename,$key1) < 0  &&  $prodexclude[$i] ) )  {
            $tobuild = 1;
         }
      }

#  Build a soap request
      if ($tobuild) {
         $soapobject = $prodattr[$i];
         $numreq++;
         $filename = $nodename;
         $filename =~ tr/\:/_/;   
         $filename =~ tr/ /_/;    
         $filename =~ tr/\./_/;   
         $filename = $nodetype . "_" . $filename . "_" . sprintf("%03d", $numreq) . "_req"; 
        
         $target = $nodename;
         if ($nodetype eq "EM") {
            $target = "ManagedSystemName";
         }
         $line = "<CT_Get><userid>$userid</userid><password>$password</password><object>$soapobject</object><target>$target</target></CT_Get>";
  
         open(MYREQFILE, ">$filename");
         print MYREQFILE $line;
         close(MYREQFILE);  
         $line = "    system(\"c:\\\\ibm\\\\itm\\\\cms\\\\kshsoap ..\\\\request\\\\" . $filename . " soap_url.txt >>\$outfile\");  sleep(1);";
         print MYSOAPFILE "$line \r\n";
      }
   }   
   if ($soapobject eq " ") {
      print MYOUTFILE "$nodetype $nodename     --> no match \r\n";
   }

}  #end of while loop

close(MYSOAPFILE);
close(MYOUTFILE);

open(MYEXECFILE, ">>$execfile");
print MYEXECFILE "\nrem  LoopSOAP.pl Beginning_Wait_Seconds Loop_Wait_Seconds Hub_Host_Name Hub_Soap_Port ITM_User_Name ITM_User_Password CURL_path SOAP_Request_Dir SOAP_Requst_File_Suffix \n";
print MYEXECFILE "\nperl LoopSOAP.pl 0 1 $hostname $soapport $userid $password C:\\curl\\bin C:\\SOAP\\$reqdir\\$reqsubdir req \n";
close(MYEXECFILE);

system("move *_req $reqdir\\$reqsubdir");
system("move $execfile $reqdir");
system("copy input\\Summarize_SOAP_output* $reqdir");
system("copy input\\*LoopSOAP* $reqdir");
#system("7z a newreq.zip $reqdir");


exit;



sub trim($)
{
	my $string = shift;
	$string =~ s/^\s+//;
	$string =~ s/\s+$//;
	return $string;
}


 
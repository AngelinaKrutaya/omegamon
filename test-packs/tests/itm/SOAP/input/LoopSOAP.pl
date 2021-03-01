#!/usr/bin/perl use Socket; use Sys::Hostname; 

my $begwait = 0;
my $loopwait = 15;
my $hostname; 
my $port; 
my $curldir;
my $reqdir;
my $reqsuffix; 

my $numArgs = $#ARGV + 1;
if ($numArgs < 7) {
   print STDOUT "Missing input argument(s) - LoopSOAP.pl Beginning_Wait_Seconds Loop_Wait_Seconds Hub_Host_Name Hub_Soap_Port ITM_User_Name ITM_User_Password CURL_path SOAP_Request_Dir SOAP_Requst_File_Suffix  \n";
   exit;
}

my $work;
my $temsurl;

$work = $ARGV[0];
if ($work =~ /^-?\D/ ) {
    print STDOUT "Beginning wait time contains non-digit(s).  Use default value $begwait.  \n";
} else {
    $begwait = $work; 
} 

$work = $ARGV[1];
if ($work =~ /^-?\D/ ) {
    print STDOUT "Loop Wait Time contains non-digit(s).  Use default value $loopwait. \n";
} else {
   $loopwait = $work; 
} 


$hostname = $ARGV[2];

$work = $ARGV[3];
if ($work =~ /^-?\D/ ) {
    print STDOUT "Invalid Soap Port.  \n";
    exit;
} else {
    $port = $work; 
} 

$curldir = $ARGV[6];
$reqdir = $ARGV[7];
$reqsuffix = $ARGV[8];


my $outfile = "SOAP_OUTPUT";
my $logtimefile = "logtime";

sleep($begwait + 1);
my $sec; 
my $min;
my $hour;
my $mday;
my $mon;
my $year;
my $wday;
my $yday;
my $isdst;
my $currenttime;
my @abbr = qw( 01 02 03 04 05 06 07 08 09 10 11 12 );
($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst)=localtime(time);
$currenttime=@abbr[$mon] . sprintf("%02d%02d%02d%02d", $mday, $hour, $min, $sec);
$outfile= $outfile . "_$currenttime.txt";
$logtimefile= $logtimefile . "_$currenttime.txt";
open(MYOUTFILE, ">>./$outfile");
open(LOGTIMEFILE, ">./$logtimefile");

if ($port =~ "3661") {
   $temsurl = "https://$hostname:$port///cms/soap";
} else {
   $temsurl = "http://$hostname:$port///cms/soap";
}
print MYOUTFILE "Issuing SOAP requests to $temsurl \r\n";
print STDOUT "Issuing Soap requests to $temsurl \r\n";

my $reqfile;
my $loc;
my $rsp;

#while (1)
#{   
    ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst)=localtime(time);
    $currenttime=@abbr[$mon] . "/" . sprintf("%02d %02d:%02d:%02d", $mday, $hour, $min	, $sec);
    print MYOUTFILE "************************************************ \r\n";
    print MYOUTFILE "*** Request Time: $currenttime ***************** \r\n";
    print MYOUTFILE "************************************************ \r\n"; 
    print STDOUT "$currenttime Start Requests\r\n";

    $reqfile = $reqdir . "\\*$reqsuffix";
#    $reqfile = "$reqdir\\*.$reqsuffix";
    print STDOUT "$reqfile\r\n";

    system("dir $reqfile >temp.txt");
    open(MYWORKFILE, "./temp.txt") || die("Could not open temp.txt");
    while (<MYWORKFILE>) {
      $line = $_;
      chomp($line);
      $loc = rindex($line, $reqsuffix);
      if ($loc == length($line) - length($reqsuffix) ) {
         $loc = rindex($line, " "); 
         $reqfile = $reqdir . "\\" . substr($line,$loc + 1);
         
         $rsp = qx(type $reqfile);
         print MYOUTFILE "$rsp \r\n";
         
         $reqfile = "@" .$reqfile;

        ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst)=localtime(time);
        $currenttime=@abbr[$mon] . "/" . sprintf("%02d %02d:%02d:%02d", $mday, $hour, $min	, $sec);
        print LOGTIMEFILE "$currenttime $reqfile\r\n";

         $rsp = qx($curldir\\curl -k -s -X POST -d $reqfile $temsurl);
         print MYOUTFILE "$rsp \r\n"; 
         sleep(1);
      }
    }
    close(MYWORKFILE);
    system("del temp.txt");


    ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst)=localtime(time);
    $currenttime=@abbr[$mon] . "/" . sprintf("%02d %02d:%02d:%02d", $mday, $hour, $min	, $sec);
     print STDOUT "$currenttime Stop Requests\r\n";
#    sleep($loopwait + 1);	
#}
close(MYOUTFILE);
close(LOGTIMEFILE);
exit;











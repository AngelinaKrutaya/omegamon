#!/usr/bin/perl   
use Sys::Hostname;

my $timestamp = "";
my $prefix = "SOAP_OUTPUT";

system("del $prefix*Summary.txt");
my $loc;
my $line;
my $found = 0;

if ($timestamp eq "") {
   system("dir $prefix* >abc.txt");
   open(MYWORKFILE, "./abc.txt") || die("Could not open abc.txt");
   while (<MYWORKFILE>) {
      $line = $_;
      chomp($line);
      $loc = index($line, $prefix);
      if ($loc >=0 ) {
         $found = 1;
         last;
      }
   }
   close(MYWORKFILE);
   system("del abc.txt");
   
   if ($found) {
      $timestamp = substr($line, $loc + length($prefix) + 1, 10);
      print STDOUT "timestamp=$timestamp \r\n";
   } else {
      print STDOUT "Cannot find any file with prefix \'$prefix\' \r\n";
      exit;
   }
}



my $infile =  $prefix . "_" . $timestamp . ".txt";
my $outfile = $prefix . "_" . $timestamp . "_Summary.txt"; 
my $numArgs = $#ARGV + 1;
if ($numArgs > 0) {
   $infile = $ARGV[0];
}


print STDOUT "Analyzing Soap Responses in $infile. \n";   

open(MYINFILE, $infile) || die("Could not open $infile");
open(MYOUTFILE, ">$outfile");
my $numreq = 0;
my $work;
my $object; 
my $target;
my $row = 0;
my $result;
my $complete=1;

my $pass_count = 0;
my $fail_count = 0;

while(<MYINFILE>) {

   $line = $_;
   chomp($line);
   $loc = index($line, "Request Time:");
   if ($loc >= 0) {
      $work = trim(substr($line, $loc + 13));
      $loc = index($work, "*");
      $timestamp = trim(substr($work, 0, $loc - 1));
      print STDOUT "timestamp=$timestamp \r\n";
   }

   if (index($line, "<CT_Get>") >= 0) {
      if ($complete != 1) {
         print MYOUTFILE "$timestamp $object $target $row n/a \r\n";
         $row = 0;
      }
      $loc = index($line,"<object>");
      $work = substr($line, $loc + 8 );
      $loc = index($work, "</object>");
      $object = substr($work,0, $loc);
      $work = substr($work,$loc + 9);
      $loc = index($work, "<target>");
      $work = substr($work,$loc + 8);
      $loc = index($work, "</target>");
      $target = substr($work, 0, $loc);
      $complete = 0; 
      #print STDOUT "object=$object target=$target \r\n";
   }

   if (index($line, "</SOAP-ENV:Envelope>") >= 0) {
      if (index($line, "Success") >= 0) {
          $pass_count = $pass_count + 1;
          if ($row > 0) {
             $result = "Pass";
          } else {
             $result = "Pass   ?????????????????????????????????????????????";
          }
      } else {
          $result = "Fail  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";
          $fail_count = $fail_count + 1;
      }
      print MYOUTFILE "$timestamp  $object $target $row $result \r\n";
      $row = 0;
      $complete = 1; 
   }

   if (index($line, "</ROW>") >= 0) {
      $row ++;
   }

}

print MYOUTFILE "Total PASS: $pass_count\r\n";
print MYOUTFILE "Total FAIL: $fail_count\r\n";


close(MYINFILE);
close(MYOUTFILE);

exit;

sub trim($)
{
	my $string = shift;
	$string =~ s/^\s+//;
	$string =~ s/\s+$//;
	return $string;
}
 
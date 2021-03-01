my $product = "QI";

#my $filter = "NT";
#my $filter = ":KUX";
#my $filter = ":LZ";
#my $filter = "SY";

my $infile = "K" . $product . "atr";
my $outfile = $product . "_attr.txt";


open(MYINFILE, $infile) || die("Could not open $infile");
open(MYOUTFILE, ">>$outfile");
my $line;
my $begin;
my $end;
my $name;
my $table;
my $period;


while (<MYINFILE>) 
{
   $line = $_;
   $begin = index($line, "name");
   $end = index($line, "tabl");

   if ($begin == 0) {
      $name = $line;
   }
   if ($end == 0) {
      $period = index($name, ".");
	  #printf "before $name \r\n";
	  $name = substr($name, 5, $period - 5);
          #printf "after $name \r\n";
	  print MYOUTFILE "$product $filter $name \n";
      
   }             
}
close(MYINFILE);
close(MYOUTFILE);
exit 0;



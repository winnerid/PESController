#!/usr/bin/perl
#
# File name: PESConfigSetting.pl
#
# Function: Set parameter value inside /etc/pes/config.xml
#
# Usage:
#      perl PESConfigSetting.pl
#      perl PESConfigSetting.pl -h
#      perl PESConfigSetting.pl -v   <== vi /etc/pes/config.xml
#      perl PESConfigSetting.pl -r   <== service pes restart
#      perl PESConfigSetting.pl 2711 <== means AES + iiff + false + fixed
#
# Author: William You
#
# Created date: 2016-07-11

use Getopt::Std;

getopts('rhv');
&usage() if($opt_h);
do{system("service pes restart"); exit(2)} if($opt_r);
do{system("vi /etc/pes/config.xml"); exit(2)} if($opt_v);
if(@ARGV < 1)
{
	print <<'END';
    - scramalgorithm:    1: DVB, 2:AES, 3:AES_Basic, 4:CISSA, 0:no change
    - indexfilecreation: 1:false, 2:true, 3:sidx, 4:nidx, 5:sidxnidx, 6:sidz, 7:iiff,
                         8:sidxiiff, 9:nidxiiff, a:sidxnidxiiff, b:sidziiff, 0:no change
    - separateECM:       1:false, 2:true, 0:no change
    - mode:              1:fixed, 2:video, 3:rai, 0:no change
    
    Input digits with RETURN:
END
  $|++;
  chomp($ARGV[0] = <STDIN>);
}
($algorithm, $indexfile, $separateECM, $mode) = split //, "".$ARGV[0];

%akv = ("1"=>"DVB", "2"=>"AES", "3"=>"AES_Basic", "4"=>"CISSA");
%ikv = ("1"=>"false", "2"=>"true", "3"=>"sidx", "4"=>"nidx", "5"=>"sidxnidx", "6"=>"sidz", "7"=>"iiff", "8"=>"sidxiiff", "9"=>"nidxiiff", "a"=>"sidxnidxiiff", "b"=>"sidziiff");
%skv = ("1"=>"false", "2"=>"true");
%mkv = ("1"=>"fixed", "2"=>"video", "3"=>"rai");

$input = "/etc/pes/config.xml";
open I,     $input     or die "Can't open input!";
open O, ">".$input."~" or die "Can't open output!";
print "---------------------BEGIN-------------------\n";

while(<I>)
{
  if(/scramalgorithm/ && defined $akv{$algorithm})
  {
    s/\".*\"/"$akv{$algorithm}"/;
    print;
  }
  if(/indexfilecreation/ && defined $ikv{$indexfile})
  {
    s/\".*\"/"$ikv{$indexfile}"/;
    print;
  }
  if(/separateECM/ && defined $skv{$separateECM})
  {
    s/\".*\"/"$skv{$separateECM}"/;
    print;
  }
  if(/mode/ && defined $mkv{$mode})
  {
    s/\".*\"/"$mkv{$mode}"/;
    print;
  }
  print O $_;
}
print "---------------------END---------------------\n\n";
close I;
close O;
unlink $input && rename($input."~", $input)||die "Cannot rename file.";
system("service pes restart");

sub usage
{
	print <<'END';
  ==========================================================================================
  This tool is to set value of 'scramalgorithm', 'indexfilecreation', 'separateECM', 'mode'
  according to the digit you give.
  ==========================================================================================
  Digit meaning:
    - scramalgorithm:    1: DVB, 2:AES, 3:AES_Basic, 4:CISSA, 0:no change
    
    - indexfilecreation: 1:false, 2:true, 3:sidx, 4:nidx, 5:sidxnidx, 6:sidz, 7:iiff,
                         8:sidxiiff, 9:nidxiiff, a:sidxnidxiiff, b:sidziiff, 0:no change
                         
    - separateECM:       1:false, 2:true, 0:no change
    
    - mode:              1:fixed, 2:video, 3:rai, 0:no change
	
  Usage example:
      perl PESConfigSetting.pl
      perl PESConfigSetting.pl -h
      perl PESConfigSetting.pl -v   <== vi /etc/pes/config.xml
      perl PESConfigSetting.pl -r   <== service pes restart
      perl PESConfigSetting.pl 2711 <== means AES + iiff + false + fixed
END
	exit(1);
}

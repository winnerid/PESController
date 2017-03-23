#!/usr/bin/perl
# 
# File name: PESConfigSetting.pl
#
# Function: This script sets value of 'ip_address', 'port', 'super_CAS_ID' against stPESConfigInfo.txt.
#
# Usage:
#      perl PESConfigSetting.pl -h
#
# Author: William You
#
# Created date: 2016-07-19

use Getopt::Std;
#use XML::Simple;  # No such module installed on PES

getopts('h');
&usage() if($opt_h);

use FindBin qw($Bin);

$config = "$Bin/stPESConfigInfo.xml";
$input  = "/etc/pes/config.xml";

#$xml    = XMLin($config, ForceArray => 1);
#$kms_ip = $xml->{"KMS_Info"}[0]->{'IP'}[0];  
#$port   = $xml->{"KMS_Info"}[0]->{'port'}[0];  
#$CAS_ID = $xml->{"KMS_Info"}[0]->{'CAS_ID'}[0];  

open C,     $config    or die "Can't open input!";
open I,     $input     or die "Can't open input!";
open O, ">".$input."~" or die "Can't open output!";

while(<C>)
{
  if(/\<IP\>(.*)\<\/IP\>/)
  {
	$kms_ip = $1;
  }
  if(/\<port\>(.*)\<\/port\>/)
  {
	$port = $1;
  }

  if(/\<CAS_ID\>(.*)\<\/CAS_ID\>/)
  {
	$CAS_ID = $1;
  }
}

#chomp $kms_ip; # remove RETURN
#chomp $port;
#chomp $CAS_ID;

print "---------------------BEGIN-------------------\n";
while(<I>)
{
  if(/ip_address=/ && !/member ip_address/)
  {
    s/\".*\"/"$kms_ip"/;
    print;
  }
  if(/port=/ && !/mwport=/)
  {
    s/\".*\"/"$port"/;
    print;
  }
  if(/super_CAS_ID=/)
  {
    s/\".*\"/"$CAS_ID"/;
    print;
  }
  print O $_;
}
print "---------------------END---------------------\n\n";

close C;
close I;
close O;
unlink $input && rename($input."~", $input)||die "Cannot rename file.";
system("service pes restart");

sub usage
{
	print <<'END';
  ============================================================================================
  This script sets value of 'ip_address', 'port', 'super_CAS_ID' against ./stPESConfigInfo.txt.
  ============================================================================================
END
	exit(1);
}

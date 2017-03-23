#!/bin/bash
###################################################################################################
#   This script aims to prepare the PES environment, then PES automation test remotely. 
#
#   Function:
#   1. Uninstall PES
#   2. Install PES
#   3. Update /etc/snmp/snmpd.conf & /etc/snmp/pesManager.conf
#   4. perl to set ip/port/CAS_ID in config.xml
#
#   Usage:
#	    ./stPESPreparation.sh pes-3.10.2-8.el5.i386.rpm
#
#   Author: William You 
#
#   Created date: 2016-07-18
##################################################################################################

# Add network info, otherwise 'No Scrambler available'
#ip=`ifconfig|grep "inet addr"|grep "Bcast"|awk '{print substr($2,6,20);}'|awk -F. '{print $1,".",$2,".",$3}'|sed 's/ //g'`
ip=`ifconfig|grep "inet addr"|grep "Bcast"|sed 's/^.*addr:\(.*\..*\..*\.\).*Bcast:.*$/\10/g'`

sed -i '/^\s*com2sec/d' /etc/snmp/snmpd.conf
sed -i '$a\com2sec local     localhost           scrambler' /etc/snmp/snmpd.conf
sed -i '$a\com2sec mynetwork '$ip'/24      scrambler' /etc/snmp/snmpd.conf

sed -i '/^\s*com2sec/d' /etc/snmp/pesManager.conf
sed -i '$a\com2sec local     localhost           scrambler' /etc/snmp/pesManager.conf
sed -i '$a\com2sec mynetwork '$ip'/24      scrambler' /etc/snmp/pesManager.conf


if [ $# -lt 1 ]
then
	echo
	echo "    Need identify PES .rpm to be installed. e.g."
	echo "         ./stPESPreparation.sh pes-3.10.2-8.el5.i386.rpm"
	echo
    exit 1
fi

# Uninstall if installed
current_ver=`rpm -qa | grep "^pes.*el"` # add re to avoid other rpm matched pes
if [ "$?" -eq 0 ]
then
	echo
	echo "(((((((( The existing PES version is: $current_ver ))))))))"
	echo
	#service pes stop
	rpm -e $current_ver
fi

# Install new one
path=$(cd "$(dirname "$0")"; pwd)
rpm -ivh --nodeps $path'/'$1
new_ver=`rpm -qa | grep "^pes.*el"`
echo
echo "(((((((( The new PES version is: $new_ver ))))))))"
echo
service pes start

rm /var/run/pes/todo -f
#mv /etc/pes/config.xml.rpmsave /etc/pes/config.xml -f

echo ""
echo "Setting ip_address, port, super_CAS_ID in config.xml ..."
echo ""
#echo $path'/'sss.pl
rm -f /etc/pes/config.xml
cp $path'/'config.bak.xml /etc/pes/config.xml  # The one installed by pes has no separateECM item.
perl $path'/'stPESConfigSettingPhase1.pl
service  vsftpd start
# Del .ts file, also can del them on interface tool one by one
rm -rf  /assets/DVB%2fTS
rm -rf  /reencryptassets/DVB%2fTS







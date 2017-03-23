"""
    This script works as PES automation controller - control PES remotely.

    Function:
		1. Upload automation files onto PES
		2. Uninstall PES
		3. Install PES
		4. Update /etc/snmp/snmpd.conf & /etc/snmp/pesManager.conf
		5. perl to set ip/port/CAS_ID in config.xml
		6. Set parameter value inside /etc/pes/config.xml
	
	Precondition:
		InstallPythonModule.bat - ssh/sftp, since PES linux without telnet
 
    Work flow:
		1. run InstallPythonModule.bat to install paramiko module if not install
		2. Edit KMS/PES infomation in stPESConfigInfo.xml
		3. python stPESController.py <PES rpm file name> [digit]
 
	Author: William You 
 
    Created date: 2016-07-19
"""

import sys
import paramiko
import time
import xml.etree.ElementTree as ET

#fileList   = ['stPESConfigInfo.xml', uploadDir + 'stPESConfigSetting.pl', uploadDir + 'stPESConfigSettingPhase1.pl', uploadDir + 'stPESPreparation.sh', uploadDir + 'config.bak.xml']
fileList   = ['stPESConfigInfo.xml', 'stPESConfigSetting.pl', 'stPESConfigSettingPhase1.pl', 'stPESPreparation.sh', 'config.bak.xml']
remoteDir  = '/var/william/'

class PESController:

	def __init__(self):
		self.__parseXML()
		self.ssh = paramiko.SSHClient()
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		self.ssh.connect(self.PES_IP, 22, self.PES_USER, self.PES_PWD)
		
	def __parseXML(self):
		root = ET.parse("stPESConfigInfo.xml")  
		try:
			self.PES_IP   = root.find("PES_Info/PES_IP").text 
			self.PES_USER = root.find("PES_Info/USER").text  
			self.PES_PWD  = root.find("PES_Info/PWD").text  
		except:
			print "There is error in stPESConfigInfo.xml, please check it or contact with William You."
			sys.exit(100)

	def __communicate(self, input, expected, timeout):
		stdin, stdout, stderr = self.ssh.exec_command(input)
		stdout.flush()
		print stdout.read()


	def __uploadFilesToPES(self, rpmfile):
		self.__communicate("rm -rf " + remoteDir, "williamYou", 3000)
		self.__communicate("mkdir " + remoteDir, "williamYou", 3000)
		scp = paramiko.Transport(self.PES_IP, 22)
		scp.connect(username = self.PES_USER, password = self.PES_PWD)
		sftp = paramiko.SFTPClient.from_transport(scp)

		# sftp.get('/var/william/a.sh', 'c:\\a.sh')
		sftp.put(fileList[0], remoteDir + fileList[0])  # .xml upload
		sftp.put(rpmfile,     remoteDir + rpmfile)       # .rpm upload
		uploadDir = sys.path[0] + "\\upload\\"
		for file in fileList[1:]:
			sftp.put(uploadDir + file, remoteDir + file)  # .pl/.sh/.txt upload
		scp.close()
		
	# Uninstall/install PES, update IP somewhere
	def preparePESEnvironment(self, rpmfile):
		self.__uploadFilesToPES(rpmfile)
		self.__communicate("chmod +x /var/william/stPESPreparation.sh", "williamYou", 3000)
		self.__communicate("/var/william/stPESPreparation.sh " + rpmfile, "williamYou", 3000)
		
	def setConfigXmlDigit(self, digit):
		pes.__communicate("perl /var/william/stPESConfigSetting.pl " + digit, "williamYou", 3000)


def usage():
	print ""
	print "  =================================================================================================="
	print "   USAGE: "
	print "       python stPESController.py <rpm filename> [digit] "
	print "            param 1: PES rpm to upload/install."
	print "            param 2 (OPTIONAL): Used by stPESConfigSetting.pl, default is 1111."
	print "   Example: "
	print "       python stPESController.py pes-3.10.2-8.el5.i386.rpm 2621"
	print ""
	print "   Digit meaning:"
	print "      - scramalgorithm:    1: DVB, 2:AES, 3:AES_Basic, 4:CISSA, 0:no change"
	print ""
	print "      - indexfilecreation: 1:false, 2:true, 3:sidx, 4:nidx, 5:sidxnidx, 6:sidz, 7:iiff,"
	print "                           8:sidxiiff, 9:nidxiiff, a:sidxnidxiiff, b:sidziiff, 0:no change"
	print "                         "
	print "      - separateECM:       1:false, 2:true, 0:no change"
	print ""    
	print "      - mode:              1:fixed, 2:video, 3:rai, 0:no change"
	print ""
	print "   PES automation work flow:"
	print "	  1. run InstallPythonModule.bat to install paramiko module if not install"
	print "	  2. Edit KMS/PES infomation in stPESConfigInfo.xml"
	print "	  3. python stPESController.py <PES rpm file name>"
	print "  =================================================================================================="
	sys.exit(3)


if __name__ == '__main__':
	if len(sys.argv) < 2 or sys.argv[1] == '-h' or sys.argv[1] == '/h':
		usage()
		
	try:
		digit = sys.argv[2]
	except:
		digit = '1111'

	print "PESController is working ..."
	pes = PESController()
	pes.preparePESEnvironment(sys.argv[1]) #upload .pl.sh.rpm/unintall/install/change IP...
	# Test Case
	pes.setConfigXmlDigit(digit)
	#pes.__communicate("perl /var/william/stPESConfigSetting.pl " + digit, "williamYou", 3000)
	print "Done!"

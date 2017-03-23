"""
    This script makes PES test automation - generate asset(s) automatically. 
	
	                               Version 2.0

    Function:
		1. Upload automation files onto PES
		2. Uninstall PES
		3. Install PES
		4. Update /etc/snmp/snmpd.conf & /etc/snmp/pesManager.conf
		5. perl to set ip/port/CAS_ID in config.xml
		6. Set parameter value inside /etc/pes/config.xml
		7. Generate scramble asset(s) against stPESConfigInfo.xml [version 2 added]
		8. Generate reencrypt asset(s) against stPESConfigInfo.xml [version 2 added]
	
	Precondition:
		Run InstallPythonModule.bat - ssh/sself.ftp, since PES linux without telnet
 
    Work flow:
		1. Run InstallPythonModule.bat to install paramiko & logging & pywinauto module if not install
		2. Edit KMS/PES/Asset infomation in stPESConfigInfo.xml
		3. python stPESController.py
		
	Notice:
		Need set NO time out limitation on ftp server, otherwise may cause ftp operation failed because of connection time out.
 
	Author: William You 
 
    Created date: 2016-07-19
	Modified date: 2017-01-05 [version 2]
"""

import sys
import os
import paramiko #sself.ftp
import time
import xml.etree.ElementTree as ET
from pywinauto.application import Application
from ftplib import FTP
import logging

fileList   = ['stPESConfigInfo.xml', 'stPESConfigSetting.pl', 'stPESConfigSettingPhase1.pl', 'stPESPreparation.sh', 'config.bak.xml']
#fileList   = ['stPESConfigInfo.xml', uploadDir + 'stPESConfigSetting.pl', uploadDir + 'stPESConfigSettingPhase1.pl', uploadDir + 'stPESPreparation.sh', uploadDir + 'config.bak.xml']
#remoteDir  = '/var/william/'
#
#InterfaceToolPath = r'D:\8. SCOT\PES Interface Tool 3.9.exe'
#clearTsLocation = "ftp://10.86.10.6/h264.ts"
#ftpForScrambled = "ftp://10.86.10.6/scrambled"
#ftpForReEncrypt = "ftp://10.86.10.6/reencrypt"
#assetName = "wewewe.ts"
#extensionNames = ['', '.cdx', '.idx']
#
#venderID = "0626"
#NID = "5000"
#TID = "0001"
#sector = "00"
#Products = "0003"
#serviceID = "0001" # Don't need give, hst show 0x1 for any value setting here

class PESController:
	def __init__(self):
		# prepare logging file
		if not os.path.exists("./log"):
			os.mkdir("./log")
		fileName = time.strftime('%Y%m%d_%H%M%S',time.localtime(time.time())) + ".txt"
		fh = logging.FileHandler("./log/" + fileName)
		self.logger = logging.getLogger("PESController")
		formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
		fh.setFormatter(formatter)
		self.logger.addHandler(fh)

		self._parseXML()
		self.ssh = paramiko.SSHClient()
		self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		self.ssh.connect(self.PES_IP, 22, self.PES_USER, self.PES_PWD)

	def _parseXML(self):
		root = ET.parse("stPESConfigInfo.xml")  
		try:
			self.PES_IP         = root.find("PES_Info/PES_IP").text.strip()
			self.PES_USER = root.find("PES_Info/USER").text.strip()
			self.PES_PWD   = root.find("PES_Info/PWD").text.strip()
			# ftp info
			self.InterfaceToolPath = root.find("InterfaceTool_Setting/Path").text.strip()
			self.ftpUrl                      = root.find("InterfaceTool_Setting/FTP").text.strip()
			self.clearTsLocation    = self.ftpUrl + "/" + root.find("InterfaceTool_Setting/clearTs").text.strip()
			self.ftpForScrambled  = self.ftpUrl + "/scrambled"
			self.ftpForReEncrypt  = self.ftpUrl + "/reencrypt"
			# Interface tool para
			self.venderID  = root.find("InterfaceTool_Setting/systemID").text.strip()
			self.NID           = root.find("InterfaceTool_Setting/NetworkID").text.strip()
			self.TID            = root.find("InterfaceTool_Setting/TransportID").text.strip()
			self.sector       = root.find("InterfaceTool_Setting/SectorNo").text.strip()
			self.serviceID = root.find("InterfaceTool_Setting/serviceID").text.strip()
			# vod product ID
			self.AssetVodPID  = root.find("PES_Algrithm_Combination/AssetVodPID").text.strip()
			self.BasicVodPID  = root.find("PES_Algrithm_Combination/BasicVodPID").text.strip()
			self.SubscriptionVodPID  = root.find("PES_Algrithm_Combination/SubscriptionVodPID").text.strip()
			# algrithm combination
			self.AssetVodAlgList  = []
			self.BasicVodAlgList  = []
			self.SubscriptionVodAlgList  = []
			
			if root.find("PES_Algrithm_Combination/AssetVod").text != None:
				self.AssetVodAlgList  = root.find("PES_Algrithm_Combination/AssetVod").text.split(",")
			if root.find("PES_Algrithm_Combination/BasicVod").text != None:
				self.BasicVodAlgList  = root.find("PES_Algrithm_Combination/BasicVod").text.split(",")
			if root.find("PES_Algrithm_Combination/SubscriptionVod").text != None:
				self.SubscriptionVodAlgList  = root.find("PES_Algrithm_Combination/SubscriptionVod").text.split(",")
			
			# common
			self.rpm  = root.find("Common/rpm").text.strip()
			self.remoteDir  = root.find("Common/remoteDir").text.strip()
			
			self.extensionNames = ['', '.cdx', '.idx']
		except:
			print "There is error in stPESConfigInfo.xml - other part, please check it or contact with William You."
			sys.exit(100)

	def _communicate(self, input, expected, timeout):
		stdin, stdout, stderr = self.ssh.exec_command(input)
		stdout.flush()
		print stdout.read()

	def _uploadFilesToPES(self, rpmfile):
		self._communicate("rm -rf " + self.remoteDir, "williamYou", 3000)
		self._communicate("mkdir " + self.remoteDir, "williamYou", 3000)
		scp = paramiko.Transport(self.PES_IP, 22)
		scp.connect(username = self.PES_USER, password = self.PES_PWD)
		sftp = paramiko.SFTPClient.from_transport(scp)

		# sftp.get('/var/william/a.sh', 'c:\\a.sh')
		sftp.put(fileList[0], self.remoteDir + fileList[0])  # .xml upload
		sftp.put(rpmfile,     self.remoteDir + rpmfile)       # .rpm upload
		uploadDir = sys.path[0] + "\\upload\\"
		for file in fileList[1:]:
			sftp.put(uploadDir + file, self.remoteDir + file)  # .pl/.sh/.txt upload
		scp.close()
		
	# Uninstall/install PES, update IP somewhere
	def _preparePESEnvironment(self, rpmfile):
		self._uploadFilesToPES(rpmfile)
		self._communicate("chmod +x /var/william/stPESPreparation.sh", "williamYou", 3000)
		self._communicate("/var/william/stPESPreparation.sh " + rpmfile, "williamYou", 3000)
		self._communicate("rm -f /assets/DVB%2fTS/*", "williamYou", 3000)
		self._communicate("rm -f /reencryptassets/DVB%2fTS/*", "williamYou", 3000)
		
	def _createResource(self):		
		self.ftp = FTP()
		self.ftp.connect(self.ftpUrl.split("//")[1], 21)
		self.ftp.login("anonymous", "anonymous@william.com")
		#self.ftp.sendcmd("prompt off")  # .xml upload
		#self.ftp.cwd("/") 
		dirL = []
		self.ftp.dir(dirL.append)
		if ''.join(dirL).find("scrambled") == -1:
			self.ftp.mkd("/scrambled") 
		if ''.join(dirL).find("reencrypt") == -1:
			self.ftp.mkd("/reencrypt") 
			
		os.system("taskkill /im \"pes interface tool*\"")
		#self.superclass = PESController()
		#self.p = PESController()
		#self._parseXML()
		#print "============="
		#print self.ftpUrl.split("//")[1]
		#time.sleep(3) # give time for pes uninstall/install, then pes running
		#self._communicate("")
		self.app = Application().Start(self.InterfaceToolPath)
		
	def _setConfigXmlDigit(self, digit):
		#print "\nSetting digit: " + digit + "\n"
		self.logger.info(" Setting algorithm digits: " + digit + " on PES server.")
		self._communicate("perl /var/william/stPESConfigSetting.pl " + digit, "williamYou", 3000)

	def _newAsset(self, assetName):
		#os.system("taskkill /im \"pes interface tool*\"")
		#self.superclass = PESController()
		#self.p = PESController()
		#self._parseXML()
		#print "============="
		#print self.ftpUrl.split("//")[1]
		time.sleep(2) # give time for pes uninstall/install, then pes running
		#self._communicate("")
		#self.app = Application().Start(self.InterfaceToolPath)

		#time.sleep(2)
		self._communicate("rm -f /assets/DVB%2fTS/" + assetName, "williamYou", 3000)
		self.app[u'PES Interface Tool 3.9'][u'Edit5'].SetText(self.PES_IP) # ip
		self.app[u'PES Interface Tool 3.9'][u'Connect'].Click() 
		
		time.sleep(2)			
		self.app[u'PES Interface Tool 3.9'][u'RadioButton6'].Click()  # new asset
		self.app[u'PES Interface Tool 3.9'][u'Clear Output'].Click() 
		self.app[u'PES Interface Tool 3.9'][u'Edit1'].SetText(assetName) 
		self.app[u'PES Interface Tool 3.9'][u'Edit4'].SetText(self.clearTsLocation)   #  ftp://10.86.10.6/h264.ts
		
		#self._communicate("rm /var/run/pes/todo -f", "williamYou", 3000)

		self.app[u'PES Interface Tool 3.9'][u'RadioButton9'].Click()  # change status
		self.app[u'PES Interface Tool 3.9'][u'Edit7'].SetText("SCRAMBLED") 
		self.app[u'PES Interface Tool 3.9'][u'Change Status'].Click() 
		#self._communicate("service pes restart", "williamYou", 3000)
		
		print "New asset <" + assetName + "> .",
		self.app[u'PES Interface Tool 3.9'][u'RadioButton6'].Click()  # new asset
		self.app[u'PES Interface Tool 3.9'][u'Clear Output'].Click() 
		#time.sleep(1)
		self.app[u'PES Interface Tool 3.9'][u'New Asset'].Click() 
		
		if self._checkOutput('Status="NEW"'):
			#print "\nNew asset successfully!\n"
			print "\n"
			self.logger.info(" New asset " + assetName + " done!")

	def _scrambleAsset(self, Products, assetName):
		self.ftp.cwd("/scrambled") 
		for ext in self.extensionNames:
			try:
				self.ftp.delete(assetName + ext)
			except:
				pass
				
		print "\nScramble asset <" + assetName + "> .",
		self.app[u'PES Interface Tool 3.9'][u'Clear Output'].Click() 
		self.app[u'PES Interface Tool 3.9'][u'RadioButton8'].Click()  # scramble asset
		self.app[u'PES Interface Tool 3.9'][u'Edit2'].SetText(self.venderID) 
		self.app[u'PES Interface Tool 3.9'][u'Edit8'].SetText(self.NID) 
		self.app[u'PES Interface Tool 3.9'][u'Edit9'].SetText(self.TID) 
		self.app[u'PES Interface Tool 3.9'][u'Edit12'].SetText(self.sector) 
		self.app[u'PES Interface Tool 3.9'][u'Edit10'].SetText(self.serviceID) 
		self.app[u'PES Interface Tool 3.9'][u'Edit11'].SetText(Products) 
		self.app[u'PES Interface Tool 3.9'][u'Clear'].Click() 
		
		self.app[u'PES Interface Tool 3.9'][u'CheckBox1'].Check()  # Delete after scrambling
		self.app[u'PES Interface Tool 3.9'][u'CheckBox2'].Check()  # Auto upload
		self.app[u'PES Interface Tool 3.9'][u'Edit13'].SetText(self.ftpForScrambled) 
		self.app[u'PES Interface Tool 3.9'][u'Scramble Asset'].Click() 
		
		if self._checkOutput('Status="SCRAMBLED"'):
			#print "\nScramble asset successfully!"
			print "\n"
			self.logger.info(" Scramble asset " + assetName + " with product " + Products + " done!")
			#print "\n"

	def _newReEncrypt(self, assetName):
		#os.system("taskkill /im \"pes interface tool*\"")
		time.sleep(2) # give time for pes uninstall/install, then pes running
		#self.app = Application().Start(self.InterfaceToolPath)

		#self._communicate("rm -f /reencryptassets/DVB%2fTS/*", "williamYou", 3000)
		#self.app[u'PES Interface Tool 3.9'][u'RadioButton9'].Click()  # change status
		#self.app[u'PES Interface Tool 3.9'][u'Edit7'].SetText("SCRAMBLED") 
		#self.app[u'PES Interface Tool 3.9'][u'Change Status'].Click() 
		
		self._communicate("rm -f /reencryptassets/DVB%2fTS/" + assetName, "williamYou", 3000)
		print "New ReEncrypt <" + assetName + "> .",
		self.app[u'PES Interface Tool 3.9'][u'Edit5'].SetText(self.PES_IP) # ip
		self.app[u'PES Interface Tool 3.9'][u'Connect'].Click() 
		
		time.sleep(2)			
		self.app[u'PES Interface Tool 3.9'][u'Clear Output'].Click() 
		self.app[u'PES Interface Tool 3.9'][u'RadioButton13'].Click()  # new ReEncrypt radio
		self.app[u'PES Interface Tool 3.9'][u'Edit1'].SetText(assetName)  # name same as new asset
		self.app[u'PES Interface Tool 3.9'][u'Edit4'].SetText(self.ftpForScrambled + '/' + assetName)   #  "self.ftp://10.86.10.6/scrambled/auto.ts"

		self.app[u'PES Interface Tool 3.9'][u'New ReEncrypt '].Click() 
			
		if self._checkOutput('Status="NEW"'):
			#print "\nNew ReEncrypt successfully!\n"
			print "\n"
			self.logger.info(" New ReEncrypt " + assetName + " done!")
			#print "\n"
			return True
		else:
				#if self._checkOutput('cannot get file"'):
					#print "\nCannot find scrambled file: " + self.ftpForScrambled + '/' + assetName + " for new ReEncrypt, skip this!\n"
			return False

	def _ReEncryptAsset(self, Products, assetName):
		self.ftp.cwd("/reencrypt") 
		for ext in self.extensionNames:
			try:
				self.ftp.delete(assetName + ext)
			except:
				pass
		# copy .ts from /scrambled to /reencrypt, if reen only generate .ts, it will overwrite the copied one
		#time.sleep(14)
		self.ftp.cwd("/scrambled")
		tmphandle = open(assetName,"wb").write
		self.ftp.retrbinary("RETR " + assetName, tmphandle, 10240)
		self.ftp.cwd("/reencrypt")
		tmphandle = open(assetName,"rb")
		self.ftp.storbinary("STOR " + assetName, tmphandle, 10240)
		tmphandle.close()
		#self.ftp.quit()
		os.remove(assetName)
		#time.sleep(10)  usage: During 10s replaced copied one with 0k one, and then overwritten by pes server ftp upload
		print "ReEncrypt asset <" + assetName + "> .",
		self.app[u'PES Interface Tool 3.9'][u'Clear Output'].Click() 
		self.app[u'PES Interface Tool 3.9'][u'RadioButton8'].Click()  # scramble asset
		self.app[u'PES Interface Tool 3.9'][u'Edit2'].SetText(self.venderID) 
		self.app[u'PES Interface Tool 3.9'][u'Edit8'].SetText(self.NID) 
		self.app[u'PES Interface Tool 3.9'][u'Edit9'].SetText(self.TID) 
		self.app[u'PES Interface Tool 3.9'][u'Edit12'].SetText(self.sector) 
		self.app[u'PES Interface Tool 3.9'][u'Edit10'].SetText(self.serviceID) 
		self.app[u'PES Interface Tool 3.9'][u'Edit11'].SetText(Products) 
		
		# For asset vod, unselect below
		#if assetName[0] == 'a':
		if self.vodType == 'a':
			self.app[u'PES Interface Tool 3.9'][u'CheckBox4'].UnCheck()  # ReEncrypt with ACs
		else:
			self.app[u'PES Interface Tool 3.9'][u'CheckBox4'].Check() 
			
		self.app[u'PES Interface Tool 3.9'][u'Clear'].Click() 	
		self.app[u'PES Interface Tool 3.9'][u'Clear Output'].Click() 
		
		self.app[u'PES Interface Tool 3.9'][u'RadioButton12'].Click()  # ReEncrypt asset radio
		self.app[u'PES Interface Tool 3.9'][u'CheckBox1'].Check()  # Delete after scrambling
		self.app[u'PES Interface Tool 3.9'][u'CheckBox2'].Check()  # Auto upload
		self.app[u'PES Interface Tool 3.9'][u'Edit13'].SetText(self.ftpForReEncrypt) 
		self.app[u'PES Interface Tool 3.9'][u'ReEncrypt Asset'].Click() 
		
		if self._checkOutput('Status="SCRAMBLED"'):
			#print "\nReEncrypt asset successfully!"
			print "\n"
			self.logger.info(" ReEncrypt asset " + assetName + " done!")
			#print "\n"

	def _checkOutput(self, kw):
		counter = 0
		#print "    detecting output ..."
		while True:
			if counter == 300:
				break
			print ".",
			time.sleep(2)
			counter += 1
			output = str(self.app[u'PES Interface Tool 3.9'][u'ListBox'].texts())

			if output.find("asset already in todolist") != -1:
				#print "[error] asset already in todolist!\n"
				print "\n"
				self.logger.error("asset already in todolist!")
				return False
				#break
				
			if output.find(kw) != -1:
				return True
				#break
		#print "\n[error] cannot find expected result in output!"	
		print "\n"
		self.logger.error("cannot find \"" + kw + "\" in output: [[[" + output + "]]]")		
		return False
		
	def autoRun(self, type):	
		self._preparePESEnvironment(self.rpm) 
		self._createResource()
		# scramble asset
		if type == 1 or type == 3:
			# asset vod
			for a in self.AssetVodAlgList:
				self._setConfigXmlDigit(a.strip())
				#time.sleep(15)
				self._newAsset('a' + a.strip() + ".ts")
				self._scrambleAsset(self.AssetVodPID, 'a' + a.strip() + ".ts")
			# basic vod
			for b in self.BasicVodAlgList:
				self._setConfigXmlDigit(b.strip())
				#time.sleep(15)
				self._newAsset('b' + b.strip() + ".ts")
				self._scrambleAsset(self.BasicVodPID, 'b' + b.strip() + ".ts")
			# subscription vod
			for s in self.SubscriptionVodAlgList:
				self._setConfigXmlDigit(s.strip())
				#time.sleep(15)
				self._newAsset('s' + s.strip() + ".ts")
				self._scrambleAsset(self.SubscriptionVodPID, 's' + s.strip() + ".ts")		
		# reEncrypt asset
		if type == 2 or type == 3: 
			# asset vod
			for a in self.AssetVodAlgList:
				self.vodType = 'a'
				self._setConfigXmlDigit(a.strip())
				#time.sleep(15)
				if self._newReEncrypt('a' + a.strip() + ".ts"): # if not scramble before, will not do ReEncryptAsset
					self._ReEncryptAsset(self.AssetVodPID, 'a' + a.strip() + ".ts")
			# basic vod
			for b in self.BasicVodAlgList:
				self.vodType = 'b'
				self._setConfigXmlDigit(b.strip())
				#time.sleep(15)
				self._newReEncrypt('b' + b.strip() + ".ts")
				self._ReEncryptAsset(self.BasicVodPID, 'b' + b.strip() + ".ts")
			# subscription vod
			for s in self.SubscriptionVodAlgList:
				self.vodType = 's'
				self._setConfigXmlDigit(s.strip())
				#time.sleep(15)
				self._newReEncrypt('s' + s.strip() + ".ts")
				self._ReEncryptAsset(self.SubscriptionVodPID, 's' + s.strip() + ".ts")		
		
def usage():
	print ""
	print "  ========================================================================="
	print "   Usage: "
	print "       python stPESController.py"
	print ""
	print "   You should give number after prompt:"
	print "            1: normal scramble; "
	print "            2: ReEncryption; "
	print "            3: normal scrambled & ReEncryption"
	print ""
	print "   What to do:"
	print "	  1. Install new PES rpm."
	print "	  2. Scramble asset with algorithm identified in stPESConfigInfo.xml."
	print "	  3. ReEncrypt asset with algorithm identified in stPESConfigInfo.xml."
	print "	  4. Point 2,3 covers asset/basic/subscription vod product type."
	print ""
	print "  Notice:"
	print "	   The newly generated .ts file will overwrite the file with same name on ftp, backup by yourself if needed!"
	print ""
	print "  ========================================================================="
	sys.exit(3)


if __name__ == '__main__':
	try:
		if sys.argv[1] == '-h' or sys.argv[1] == '/h':
			print usage()
            sys.exit(0)
	except:
		pass
		
	try:
		type = int(raw_input('  Choose operation:\n    1: Normal scramble\n    2: ReEncryption\n    3: Normal scrambled & ReEncryption\n'))
	except:
		print " Please input a digit!"
		sys.exit(2)
		
	if type != 1 and type != 2 and type != 3:
		print "The digit you given is invalid, exiting! "
		sys.exit(2)
		
	result = raw_input('  [Notice] The same name .ts file on ftp will be overwritten, go on? (y or n)\n')
	if result.lower() == "y" or result == "yes":
		print "PESController is working ...\n"
		pes = PESController()
		pes.autoRun(type)
		print "\n     All done!"		
	else:
		sys.exit(7)

	


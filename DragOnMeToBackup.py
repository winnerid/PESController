# -*- coding:utf-8 -*-  
# Author: William You
# Time: 2016-01-21 15:49:29
# Function: 把拖拽来的文件（夹）在本.py文件所在的目录下生成备份文件（夹）。格式为：原名_日期-时间

# 【注】让.py接受文件拖拽，把下面保存为.reg，导入即可
# Windows Registry Editor Version 5.00  
  
# [HKEY_CLASSES_ROOT\Python.File\shellex\DropHandler]  
# @="{60254CA5-953B-11CF-8C96-00AA00B8708C}" 
 
import os
import sys
import shutil
import time

strTime = time.strftime('%Y%m%d_%H%M%S',time.localtime(time.time())) #20160121_154838
newName = os.path.split(os.path.realpath(__file__))[0] + "\\" + sys.argv[1].split("\\")[-1] + "-" + strTime
#print newName

if os.path.isdir(sys.argv[1]): # folder copy
	print sys.argv[1] 
	shutil.copytree(sys.argv[1], newName)
else:                           # file copy
	shutil.copy(sys.argv[1], newName)

# input("ddd")
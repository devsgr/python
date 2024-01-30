# This is a working code to automate readerbaord
# Version 2.0 with auto update flag from ThingSpeak
# Must have a thingspeak account.Replace API Key from that 
import subprocess 
from time import sleep
from datetime import datetime, time, timedelta
import requests
import os
import json
#Change the following parameters to match your settings
Unit = 2  #The Kiosk number
Baseurl = "https://www.webpages.uidaho.edu/iac/BEL336/" #Web site url where index.html is colated
BaseFolder = "/home/pi/www/" #Path to base foler. This folder must exist
Channel = "123456789" #Thigspeak Channel
ReadAPI =  "READAPI123456789" # API Key to read
WriteAPI = "WRITEAPI12345678" # API Key to write
UpdateInterval = 15 #Look for update every this many minutes
#######################################################################################
def ReadField1():
#read field1
    url = "https://api.thingspeak.com/channels/"+Channel+"/fields/1.json?api_key="+ReadAPI+"&results=2"
    r = requests.get(url) #Reads the contnt of url in r
    
    if (r.headers['Status'] == '200 OK'):
        j = json.loads(r.text)["feeds"][1]['field1'] #converts r.text into json, then extracts "feeds" field, which is a list. From the list extract entry 1 which is again json and from that extarxts 'field1
    else:
        j = 'X'
    
    return j


def WriteField1(msg):
#Write back


    url = "https://api.thingspeak.com/update?api_key="+WriteAPI+"&field1=" + msg
    r = requests.get(url)
    if (r.headers['Status'] == '200 OK'):
         return True
    else:
        return False


def ValueIs2(v):
    
    
    # if v at Unit is 2 update else do nothing
    if (v == '-1'):
        return False
    elif(v[Unit]=="2"):
        return True
    else:
        return False
    
    
def isNewIndex():
    r = requests.get(Baseurl + 'index.html')
    rL = r.headers['Content-Length']
    print(r.headers)
    local = os.path.getsize(BaseFolder + "index.html")
    print(local) 
    if (local == rL):
        return False
    else:
        return True
                             


        
def update(Unit, Baseurl,BaseFolder):

    # read and Copy index.html
    FileName = 'index.html'
    r = requests.get(Baseurl + FileName)
    WritePath = BaseFolder + FileName
    
    with open(WritePath,'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk) 
    
    f.close()
   
    #f.write(r.text)
    #os.setxattr(WritePath,'Copied',r.headers['Last-Modified'])
    #print(os.getxattr(WritePath,'Copied'))
    x = 0

    # Now reading from index file, copy all image and video files
    while (x >= 0):
        x1 = r.text.find("Slides/",x+1) #returns -1 if not found
        x2 = r.text.find("Videos/",x+1) #returns -1 if not found
        if (x1 >=0 & x2 >=0): # There are more slides or video get the first one
            x = min(x1,x2)
        else: #There is eitehr not Videos or no Slides returning -1 for that
            x = max(x1,x2)
        #print(x)
        if (x >= 0):

            y = r.text.find('.', x+1)
            FileName = r.text[x:y+4]
            downloadurl = Baseurl + FileName
            WritePath = BaseFolder + FileName.replace('/','\\')
            # Videos should be downloaded only if length don't match or file does not exit

            if (r.text[x:x+6]=='Videos' and os.path.exists(WritePath)):

                req = requests.head(downloadurl)
                url_Size = req.headers['Content-Length']
                file_Size = os.path.getsize(WritePath)
                if (url_Size != file_Size):
                    req = requests.get(downloadurl)
                    with open(WritePath,'wb') as f: #wb stands for write in bytes
                        for chunk in req.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
            else:
                req = requests.get(downloadurl)
                #print(req.headers)
                with open(WritePath,'wb') as f:
                    for chunk in req.iter_content(chunk_size=8192):
                        if chunk:
                                f.write(chunk) 
                f.close()

update(Unit, Baseurl,BaseFolder)
Reload = True
while True:
    # Run the index file from local
    if(Reload):
        pid = subprocess.Popen('chromium-browser --kiosk ~/www/index.html &', shell = True)
    Reload = False
    Now = datetime.now()
    NextRun = Now + timedelta(minutes=UpdateInterval)
    SleepSec = (NextRun - Now).total_seconds()
    sleep(SleepSec)
    # 1. Check Thingspeak field 1
    
    v = ReadField1()
    #Check if 2
    if(ValueIs2(v)):
        # Switch to updating message
        pid = subprocess.Popen('chromium-browser --kiosk ~/www/CssJs/Updating.html &', shell = True)
        update(Unit, Baseurl,BaseFolder) 
        Reload = True
    # Write is active
    
    if (v[Unit] != "0"):
        msg = v[:Unit] + "0" + v[Unit+1:]
        while (not WriteField1(msg)):
            sleep(15)


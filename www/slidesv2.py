# This is a working code to automate the readerboard
# Version 2.0 with an auto-update flag from ThingSpeak
# Must have a thingspeak account. Replace the API Keys below from Thingspeak Channel, Filed1 (Uese only field1)
import subprocess 
from time import sleep
from datetime import datetime, time, timedelta
import requests
import os
import json
#Change the following parameters to match your settings
Unit = 2  #The Kiosk number
Baseurl = "https://www.webpages.uidaho.edu/iac/BEL336/" #Web site URL where index.html is located
BaseFolder = "/home/pi/www/" #Path to the base folder. Create this folder in pi. This folder must exist
Channel = "123456789" # Thing Speak Channel ID
ReadAPI =  "READAPI123456789" # API Key to read
WriteAPI = "WRITEAPI12345678" # API Key to write
UpdateInterval = 15 #Look for an update every this many minutes
#######################################################################################
def ReadField1():
#read field1
    url = "https://api.thingspeak.com/channels/"+Channel+"/fields/1.json?api_key="+ReadAPI+"&results=2"
    r = requests.get(url) #Reads the content of the url in r
    
    if (r.headers['Status'] == '200 OK'):
        j = json.loads(r.text)["feeds"][1]['field1'] #converts r.text into json, then extracts the "feeds" field, which is a list. From the list extract entry 1 which is again JSON and from that extracts 'field1
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
# If v at Unit is 2, return true else return false 
    if (v <=  '-1'):   # Thing speak returns -1? if there is a reading error
        return False
    elif(v[Unit-1]=="2"):
        return True
    else:
        return False
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
    #os.setxattr(WritePath,'Copied',r.headers['Last-Modified']) Trying to use attribute to copy file length did not work 
    #print(os.getxattr(WritePath,'Copied'))
    x = 0

    # Now reading from the index file, copy all image and video files
    while (x >= 0):
        x1 = r.text.find("Slides/",x+1) #returns -1 if not found
        x2 = r.text.find("Videos/",x+1) #returns -1 if not found
        if (x1 >=0 and x2 >=0): # There are more slides or video get the first one
            x = min(x1,x2)
        else: #There is either no Videos or no Slides returning -1 for that
            x = max(x1,x2)
        #print(x)
        if (x >= 0):

            y = r.text.find('.', x+1)
            FileName = r.text[x:y+4]
            downloadurl = Baseurl + FileName
            WritePath = BaseFolder + FileName # add .replace('/','\\') for windows
            # Videos should be downloaded only if the length doesn't match or the file does not exist

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
                
pid = subprocess.Popen('chromium-browser --kiosk ~/www/CssJs/Updating.html &', shell = True)
sleep(10) # Give about 10 seconds to complete starting chromium for the first time. If not given this time, the reading from the web was not successful and got stuck on the next line
update(Unit, Baseurl,BaseFolder)
pid.terminate()
Reload = True
while True:
    # Run the index file from the local www path
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
    # Make sure in Thingspeak that the length of v is greater than the unit value
    if(ValueIs2(v)):
        # Switch to updating message
        pid.terminate()
        pid = subprocess.Popen('chromium-browser --kiosk ~/www/CssJs/Updating.html &', shell = True)
        update(Unit, Baseurl,BaseFolder)
        pid.terminate()
        Reload = True
    # Write is active
    
    if (v[Unit-1] != "0"): # Write 0 only if the value is not already 0 (Avoids unnecessary writing as ThingSpeak has 15 seconds writing limit
        msg = v[:Unit-1] + "0" + v[Unit:] # In Python index starts at 0 and in thing speak, the first number belongs to Unit 1
        while (not WriteField1(msg)):
            sleep(16) #Thing Speak has 15 seconds interval limit. Try again after 16 seconds (1 second buffer)

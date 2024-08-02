# Last Update: 2024-08-02
# Added restart at 3:00 am, 
# Check web connection before trying to load to to 10 times and reload old page if fails.
# Added random senconds to write to thinngspeak if conflict.

# This is a working code to automate the readerboard
# Version 2.0 with an auto-update flag from ThingSpeak
# Must have a thingspeak account. Replace the API Keys below from Thingspeak Channel, Filed1 (Uese only field1)
import subprocess 
from time import sleep
from datetime import datetime, time, timedelta
import requests
import random
import os
import json
#Change the following parameters to match your settings
Unit = 2  #The Kiosk number
RebootTime = 3 #(3 AM)
Baseurl = "https://www.webpages.uidaho.edu/iac/BEL336/" #Web site URL where index.html is located
BaseFolder = "/home/pi/www/" #Path to the base folder. Create this folder in pi. This folder must exist
Channel = "123456789" # Thing Speak Channel ID
ReadAPI =  "READAPI123456789" # API Key to read
WriteAPI = "WRITEAPI12345678" # API Key to write
UpdateInterval = 15 #Look for an update every this many minutes
#######################################################################################
# ReadField1 reads the field 1 from Thinkspeak channel. This returns the value in varaible r. Converst to json and reads the "feeds.field1" tag value
def ReadField1():
#read field1
    url = "https://api.thingspeak.com/channels/"+Channel+"/fields/1.json?api_key="+ReadAPI+"&results=2"
    r = requests.get(url) #Reads the content of the url in r
    
    if (r.headers['Status'] == '200 OK'):
        j = json.loads(r.text)["feeds"][1]['field1'] #converts r.text into json, then extracts the "feeds" field, which is a list. From the list extract entry 1 which is again JSON and from that extracts 'field1
    else:
        j = 'X'
    return j

# WriteField1 Writes the field 1 to Thinkspeak channel. 
def WriteField1(msg):
#Write back
    url = "https://api.thingspeak.com/update?api_key="+WriteAPI+"&field1=" + msg
    r = requests.get(url)
    if (r.headers['Status'] == '200 OK'):
         return True
    else:
        return False

# ValueIs2 is a simple function to see if value is 2 for this kiosk to upadate
def ValueIs2(v):
# If v at Unit is 2, return true else return false 
    if (v <=  '-1'):   # Thing speak returns -1? if there is a reading error
        return False
    elif(v[Unit-1]=="2"):
        return True
    else:
        return False

def is_Online(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an exception if the status code is not 2xx
        return True
    except requests.RequestException:
        return False

# upadate is the main function that
# 1. Reads and save the index.html to local folder 
# 2. Parse the index file to get all the linked image and video fiels
# 3. Download and save all image and video files to local folder

def update(Baseurl,BaseFolder):

    # Open and write the update time to Log.txt
    fl = open(BaseFolder +'Log.txt','a') #Cant write temp.txt but Temp.txt is fine
    now = datetime.now()
    fl.write( now.strftime("%m/%d%Y, %H:%M:%S") +'\n' ) 
    
    # read and Copy index.html
    FileName = 'index.html'
    r = requests.get(Baseurl + FileName)
    WritePath = BaseFolder + FileName
    
    with open(WritePath,'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk) 
    
    f.close()
    # fl.write( 'Copied: '  + WritePath +'\n') # Optional to write copied file to log file
    # f.write(r.text)
    # os.setxattr(WritePath,'Copied',r.headers['Last-Modified']) Trying to use attribute to copy file length did not work 
    # print(os.getxattr(WritePath,'Copied'))
    x = 0

    # Now reading from the index file, copy all image and video files
    while (x >= 0):
        x1 = r.text.find("Slides/",x+1) #returns -1 if not found
        x2 = r.text.find("Videos/",x+1) #returns -1 if not found
        if (x1 >=0 and x2 >=0): # There are more slides or video get the first one, returns -1 when EOF
            x = min(x1,x2)
        else: #There is either no Videos or no Slides returning -1 for that
            x = max(x1,x2)
        # print(x)
        if (x >= 0):
            
            # Parse text to find the video or image file    
            y = r.text.find('.', x+1)
            FileName = r.text[x:y+4]
            downloadurl = Baseurl + FileName
            WritePath = BaseFolder + FileName

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
                #fl.write( 'Copied: '  + downloadurl +'\n')
    now = datetime.now()
    fl.write( "Updaetd successfully" +'\n')           
    fl.close()                

# Check to see if internet is connected

NextReboot = (datetime.now() + timedelta(days=1)).replace(hour = RebootTime, minute=0, second=0, microsecond=0)
pid = subprocess.Popen('chromium-browser --kiosk ~/www/CssJs/Updating.html &', shell = True)

# Try and wait 10 seconds up to 10 times to come the unit online, if fails load old page
TryCount = 0
while (not is_Online(Baseurl) and TryCount<10):
    sleep(10)
    TryCount += 1

if (TryCount < 10):
    update(Baseurl,BaseFolder)

Reload = True  
pid.terminate()
#print("pid terminated")

while True:
    # Run the index file from the local www path
    if(Reload):
        pid = subprocess.Popen('chromium-browser --kiosk ~/www/index.html &', shell = True)
    Reload = False
    Now = datetime.now()
    if(Now >= NextReboot):
        os.system('sudo reboot')

    NextRun = Now + timedelta(minutes=UpdateInterval)
    
    SleepSec = (NextRun - Now).total_seconds()
    sleep(SleepSec)
    # 1. Check Thingspeak field 1
    
    v = ReadField1()
    #Check if 2
    # Make sure in Thingspeak that the length of v is greater than the unit value
    if(ValueIs2(v)):
        # Switch to updating message
        pid = subprocess.Popen('chromium-browser --kiosk ~/www/CssJs/Updating.html &', shell = True)
        update(Baseurl,BaseFolder) 
        Reload = True
    # Write is active
    
    if (v[Unit-1] != "0"): # Write 0 only if the value is not already 0 (Avoids unnecessary writing as ThingSpeak has 15 seconds writing limit
        msg = v[:Unit-1] + "0" + v[Unit:] # In Python index starts at 0 and in thing speak, the first number belongs to Unit 1
        while (not WriteField1(msg)):
            random_number = random.randint(1, 100)
            sleep(16+random_number) #Thing Speak has 15 seconds interval limit. Try again after 16+ random seconds (1 second buffer)

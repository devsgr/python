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
def WriteLog(msg):
    fl = open(BaseFolder +'Log.txt','a') # Can't write temp.txt but Temp.txt is fine
    now = datetime.now()
    fl.write( now.strftime("%m/%d%Y, %H:%M:%S") +'\n' ) 
    fl.write( msg +'\n')           
    fl.close()  

def ReadField1(Channel,ReadAPI):
#read field1
    url = f"https://api.thingspeak.com/channels/"+{Channel}+"/fields/1.json?api_key="+{ReadAPI}+"&results=2"
    try:
        r = requests.get(url) #Reads the content of the url in r
        r.raise_for_status() # Raises HTTPError for bad responses
        data = r.json()
        return data["feeds"][1]["field1"]
    except (requests.RequestException, ValueError, KeyError) as e:
        WriteLog(f"Error reading field 1: {e}")
        return None # Return none on error // None is python key word it is not true, false, it is just None
    

# WriteField1 Writes the field 1 to Thinkspeak channel. 
def WriteField1(WriteAPI,msg):
#Write back
    url = "https://api.thingspeak.com/update?api_key="+WriteAPI+"&field1=" + msg
    r = requests.get(url)
    if r.status_code == 200:
         WriteLog("Successfully written to ThingSpeak")
         return True
    else:
        WriteLog("Error Writing to ThingSpeak")
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
 
    # 1 Read and Copy index.html
    FileName = 'index.html'
    try:
        r = requests.get(Baseurl + FileName)
        r.raise_for_status() # Raises HTTPError for bad responses
        WritePath = BaseFolder + FileName
        with open(WritePath,'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk) 
        
        f.close()
        
        

        # Now reading from the index file, copy all image and video files
        x = 0
        while (x >= 0):
            #Look for keyword 'Slides/' or 'Videos/'
            x1 = r.text.find("Slides/",x+1) #returns -1 if not found
            x2 = r.text.find("Videos/",x+1) #returns -1 if not found
            if (x1 >=0 and x2 >=0): # There are more slides or video get the first one, returns -1 when EOF
                x = min(x1,x2)
            else: #There is either no Videos or no Slides returning -1 for that
                x = max(x1,x2)
            # print(x)
            if (x >= 0):
                
                # Parse text to find the video or image file   
                # Parsing of structured text do not modify 
                y = r.text.find('.', x+1)
                FileName = r.text[x:y+4]
                downloadurl = Baseurl + FileName
                WritePath = BaseFolder + FileName

                # Videos should be downloaded only if the length doesn't match or the file does not exist
                # Download images regardless
                if (r.text[x:x+6]=='Videos' and os.path.exists(WritePath)):
                    #This is a video, next check file size 
                    req = requests.head(downloadurl)
                    req.raise_for_status() # Raises HTTPError for bad responses
                    url_Size = req.headers['Content-Length']
                    file_Size = os.path.getsize(WritePath)
                    if (url_Size != file_Size):
                        #File sizes don't match downlaod and save it
                        req = requests.get(downloadurl)
                        req.raise_for_status() # Raises HTTPError for bad responses
                        with open(WritePath,'wb') as f: #wb stands for write in bytes
                            for chunk in req.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                else:
                    #This is an image, downlaod and save it
                    req = requests.get(downloadurl)
                    req.raise_for_status() # Raises HTTPError for bad responses
                    with open(WritePath,'wb') as f:
                        for chunk in req.iter_content(chunk_size=8192):
                            if chunk:
                                    f.write(chunk) 
                    f.close()
                    
                    #MsgFile = open(BaseFolder +'CssJs/Message.txt','a') #Cant write temp.txt but Temp.txt is fine
                    #MsgFile.write('Copied: ' + FileName + '<br>')
                    #MsgFile.close()
        # Open and write the update time to Log.txt
        ToLog = "Update Successful"      
    except:
        ToLog = "Update Unsuccessful \n" + req.text
    
    WriteLog(ToLog)
    

NextReboot = (datetime.now() + timedelta(days=1)).replace(hour = RebootTime, minute=0, second=0, microsecond=0)
MsgFile = open(BaseFolder +'CssJs/Message.txt','w') #Cant write temp.txt but Temp.txt is fine
Msg = 'Updating...'
MsgFile.write(Msg)
MsgFile.close()

pid = subprocess.Popen('chromium-browser --kiosk ~/www/CssJs/Updating.html &', shell = True)
# Check to see if internet is connected
# Try and wait 10 seconds up to 10 times to come the unit online, if fails load old page
TryCount = 0
while (not is_Online(Baseurl) and TryCount<10):
    TryCount += 1
    MsgFile = open(BaseFolder +'CssJs/Message.txt','w') #Cant write temp.txt but Temp.txt is fine
    Msg = 'Updating... <br>'
    Msg += "Connecting to internet try " + TryCount + "of 10. <br>'"
    Msg += "Will try again in 10 S."
    MsgFile.write(Msg)
    MsgFile.close()
    WriteLog(Msg)
    pid.terminate()
    pid = subprocess.Popen('chromium-browser --kiosk ~/www/CssJs/Updating.html &', shell = True)
    sleep(10) #Try again in 10s



if (TryCount < 10):
    update(Baseurl,BaseFolder)
else:
    MsgFile = open(BaseFolder +'CssJs/Message.txt','w') #Cant write temp.txt but Temp.txt is fine
    Msg = 'Updating... <br>'
    Msg += "Could not connect to internet. Loading old files..."
    MsgFile.write(Msg)
    MsgFile.close()
    WriteLog(Msg)
    pid.terminate()
    pid = subprocess.Popen('chromium-browser --kiosk ~/www/CssJs/Updating.html &', shell = True)
    sleep(10)

Reload = True  


while True:
    # Run the index file from the local www path
    if(Reload):
        pid.terminate()
        pid = subprocess.Popen('chromium-browser --kiosk ~/www/index.html &', shell = True)
    Reload = False
    Now = datetime.now()
    if(Now >= NextReboot):
        os.system('sudo reboot')

    NextRun = Now + timedelta(minutes=UpdateInterval)
    
    SleepSec = (NextRun - Now).total_seconds()
    sleep(SleepSec)
    # 1. Check Thingspeak field 1
    
    v = ReadField1(Channel,ReadAPI)

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
        TryCount =0
        while (not WriteField1(WriteAPI,msg) and TryCount<10 ):
            random_number = random.randint(1, 100)
            sleep(20+random_number) #Thing Speak has 15 seconds interval limit. Try again after 20+ random seconds (5 second buffer)
            TryCount += 1


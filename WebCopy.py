import requests
import os
Baseurl = "https://www.webpages.uidaho.edu/iac/BEL336/"
BaseFolder = "D:\\Temp\\"
FileName = 'index.html'
r = requests.get(Baseurl + FileName)
x = 0
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
                with open(WritePath,'wb') as f:
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

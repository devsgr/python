import os
from subprocess import run
from time import sleep
from datetime import datetime, time, timedelta
cmd = "/usr/bin/chromium-browser --start-fullscreen shrestha.best/ep"
os.system(cmd)
On_Time = time(7,30,0)
Off_Time = time(17,0,0)


while True:
    Now = datetime.now()
    #https://www.programiz.com/python-programming/datetime/strftime
    current_day=int(Now.strftime('%w'))
    #current_day =0 for sunday 6 for saturday
    IsWeedDay = current_day > 0 and current_day < 6
    if Now.time() < On_Time:
        DisplayOn = False
        NextRun = datetime(Now.year,Now.month,Now.day,On_Time.hour,On_Time.minute,2)
    elif Now.time() >= On_Time  and   Now.time() <= Off_Time:
        DisplayOn = IsWeedDay
        NextRun = datetime(Now.year,Now.month,Now.day,Off_Time.hour,Off_Time.minute,2)
    else:
        DisplayOn = False
        t1 = Now + timedelta(days=1)
        NextRun = datetime(t1.year,t1.month,t1.day,On_Time.hour,On_Time.minute,2)
    
    # Check if it is weekday
    if DisplayOn:
        run('vcgencmd display_power 1',shell = True)
    else :
        run('vcgencmd display_power 0',shell = True)
    
    SleepSec = (NextRun - Now).total_seconds()
    print("Next Run =",NextRun)
    #print("Delay =", SleepSec)
    #print("Current Day =", Now.day)
    #print("Current Hour =", Now.hour)
    sleep(SleepSec)
    






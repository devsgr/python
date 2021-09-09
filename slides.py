from subprocess import run
from time import sleep
from datetime import datetime, time, timedelta
run('chromium-browser --kiosk webpages.uidaho.edu/~devs/slides/ &', shell = True)
On_Time = time(7,00,0)  #Screen on at 7 AM
Off_Time = time(18,0,0) #Screen off at 6 PM
WeekendOff = True

while True:
    Now = datetime.now()
    current_day=int(Now.strftime('%w'))
    #current_day =0 for sunday 6 for saturday
    if WeekendOff:
      IsWeedDay = current_day > 0 and current_day < 6
    else:
      IsWeedDay = True

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
    
    if DisplayOn:
        run('vcgencmd display_power 1',shell = True)
    else :
        run('vcgencmd display_power 0',shell = True)
    
    SleepSec = (NextRun - Now).total_seconds()
    print("Next Run =",NextRun)
    sleep(SleepSec)
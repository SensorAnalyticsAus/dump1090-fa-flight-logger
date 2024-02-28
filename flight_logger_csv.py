#!/usr/bin/python

FWIN = 900  # ignore same filght within FWIN secs of last seen
SWIN = 10   # wait secs before checking /var/dump1090-fa/aircraft.json again 

from datetime import datetime
from datetime import date
from time import time as tm
from time import sleep as sleep
import requests
import os
import csv
import json
import sys, signal
import csv

def getMh(ent):
 if ent.get('mach') is not None: 
     mh=ent['mach']
 else: mh='-'
 return mh
def getSq(ent):
 if ent.get('squawk') is not None: 
     sq=ent['squawk']
 else: sq='-'
 return sq
def getAl(ent):
 if ent.get('alt_baro') is not None: 
     al=ent['alt_baro']
 elif ent.get('alt_geom') is not None: 
     al=ent['alt_geom']
 elif ent.get('nav_altitude_mcp') is not None: 
     al=ent['nav_altitude_mcp']
 elif ent.get('nav_altitude_fms') is not None: 
     al=ent['nav_altitude_fms']
 else: al='-'
 return al
def cUpdt(hval,fval,dt,ti,at,sq,mh,stat):
 with open(filepath, 'a', newline='') as file:
     writer = csv.writer(file)
     fieldnames = ['hex','flight','date','time','alt','sq','mh','s']
     writer = csv.DictWriter(file, fieldnames=fieldnames)
     writer.writerow(
      {'hex':hval,'flight':fval,'date':dt,'time':ti,'alt':at,
       'sq':sq,'mh':mh,'s':stat})
def getJ():
 with open('/run/dump1090-fa/aircraft.json', 'r') as aircraft:
     file_contents = aircraft.read()
     return json.loads(file_contents)
def TSdate(timestamp):
 return datetime.fromtimestamp(timestamp)
def getTS(filepathcsv,key):
 result = []
 res = []
 with open(filepathcsv) as csvfile: #relies on dump1090-fa aircraft.json format
     reader = csv.reader(csvfile, delimiter=',', quotechar='|')
     for row in reader:
         if row[1].strip() == key:
             result.append(row[2].strip())
             result.append(row[3].strip())
             res.append(result[0]+' '+result[1])
             result.clear()
 if len(res) == 0:
     ts=tm() #time now
 else:
     pt = datetime.strptime(res[len(res)-1],'%Y-%m-%d %H:%M:%S') #take last
     ts=pt.timestamp()
 return(ts)
def signal_handler(signal, frame):
 print('\ngotta go...')
 sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print('flight logger started...')
print('ctrl-C to exit')

while True:
 today = date.today()
 month = datetime.now().strftime('%B')
 year = datetime.now().strftime('%Y')
 time = datetime.now().strftime('%H:%M:%S')

 # file setup
 filename = '{}.csv'.format(today)
 rootFolder = '/mnt/32G/flights/'
 subFolder = '{}-{}/'.format(month, year)
 filepath = rootFolder + subFolder + filename
 cf     = filepath #shorten it

 # create root folder and sub folder
 if not os.path.isdir(rootFolder):
     os.mkdir(rootFolder)

 if not os.path.isdir(rootFolder + subFolder):
     os.mkdir(rootFolder + subFolder)

 # check if files exists
 file_exists = os.path.isfile(filepath)

 # get all flights tracked to check against for duplicates
 flights = ''
 if file_exists:
     with open(filepath, 'r') as fp:
         flights = fp.read()

 # get json data
 json_dump=getJ()

 # write unique flights for the day to csv file
 with open(filepath, 'a', newline='') as file:
     writer = csv.writer(file)
     fieldnames = ['ICAO','flight','date', 'time','altitude', 
                   'squawk','mach','status']
     writer = csv.DictWriter(file, fieldnames=fieldnames)
     # create headers if first time writing to file
     if not file_exists: writer.writeheader()

# Flight specified and flight is not in csv (new entry)
 for entry in json_dump['aircraft']:
     if('flight' in entry and 
         ('{},{}'.format(entry['flight'].strip(), today) not in flights)
         ):
         hv=entry['hex'].strip()
         fv=entry['flight'].strip()
         al=getAl(entry)
         sq=getSq(entry)
         mh=getMh(entry)
         cUpdt(hv,fv,today,time,al,sq,mh,'N')
         print('N:',hv,fv,sq,'at:',al,mh,today,time)
# Flight n/a but ICAO hex code specified, code is not in csv (new entry)
     elif('hex' in entry and 
         '{},{},{}'.format(entry['hex'].strip(),'-',today) not in flights
         ):
         hv=entry['hex'].strip()
         al=getAl(entry)
         sq=getSq(entry)
         mh=getMh(entry)
         cUpdt(hv,'-',today,time,al,sq,mh,'N')
         print('N:',hv,'-',sq,'at:',al,mh,today,time)
# This flight is in csv but it is outside  FWIN window (Return flight)
     elif 'flight' in entry and (tm()-getTS(cf,entry['flight'].strip())) > FWIN:
         hv=entry['hex'].strip()
         fv=entry['flight'].strip()
         otime=getTS(cf,fv) #note original ts before csv is updated
         al=getAl(entry)
         sq=getSq(entry)
         mh=getMh(entry)
         cUpdt(hv,fv,today,time,al,sq,mh,'R')
         print('R:',hv,fv,sq,'at',al,mh,TSdate(otime),TSdate(tm()))
# This flight only has a ICAO code in csv and it is outside FWIN (Return flight)
     elif 'hex' in entry and (tm()-getTS(cf,entry['hex'].strip())) > FWIN:
         hv=entry['hex'].strip()
         otime=getTS(cf,hv) #note original ts before csv is updated
         al=getAl(entry)
         sq=getSq(entry)
         mh=getMh(entry)
         cUpdt(hv,'-',today,time,al,sq,mh,'R')
         print('R:',hv,'-',sq,'at',al,mh,TSdate(otime),TSdate(tm()))
 sleep(SWIN) # sleep SWIN secs before starting next while iter 

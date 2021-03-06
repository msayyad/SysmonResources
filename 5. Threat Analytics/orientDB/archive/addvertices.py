import pyorient
import sys
import os.path
import codecs
import json
import re

uid = "root" # don't do this in production
pwd = "Password1234"

#sys.argv += 'pc.txt'.split() # for testing only

if len(sys.argv) == 1:
    print('please provide path to winevent log file from collected by Nxlog!')
    exit

if  not os.path.exists(sys.argv[1]):
    print('please provide path to winevent log file from collected by Nxlog!')
    exit

# setup OrientDB connection
client = pyorient.OrientDB("localhost", 2424)
session_id = client.connect(uid, pwd)
client.db_open("DataFusion", uid, pwd)

eventIdLookup = {1:'ProcessCreate', 2:'FileCreateTime', 3:'NetworkConnect', \
                 4:'SysmonStatus', 5:'ProcessTerminate',6:'DriverLoad', \
                 7:'ImageLoad', 8:'CreateRemoteThread', 9:'RawAccessRead', \
                 10:'ProcessAccess', 11:'FileCreate', 12:'RegistryEvent', \
                 13:'RegistryEvent', 14:'RegistryEvent', 15:'FileCreateStreamHash', \
                 16:'ConfigChanged', 17:'PipeCreated', 18:'PipeConnected', \
                 19:'WmiEvent', 20:'WmiEvent', 21:'WmiEvent', 255:'Error' }

lines = codecs.open(sys.argv[1], 'r', encoding='utf-8').readlines()
for event in lines:
    e = json.loads(event)

    # if not Sysmon or DataFusion event, insert into WinEvent class
    classname = 'WinEvent' 

    # Sysmon events
    if '"SourceName":"Microsoft-Windows-Sysmon"' in event:
        if 'Keywords' in e: #negative no. is too big, so cast to string
            e['Keywords'] = str(e['Keywords']) 
        # ProcessID is Sysmon servie PID, Nxlog doesn't extract the one we need
        e['SysmonProcessId'] = e['ProcessID']
        del e['ProcessID']
        # extract ProcessId from Message field
        processId = re.search("ProcessId: (\d+)", event)
        e['ProcessId'] = processId.group(1)
        classname = eventIdLookup[e['EventID']]
        
    # DataFusion events
    if '"SourceName":"DataFuseUserActions"' in event:
        del e['ProcessID'] # deleted because there's a ProcessId field in Message        
        uat = json.loads(e['Message'])
        for k,v in uat.items():
            e[k] = v
        classname = 'UserActionTracking' # e['Action']
    print("insert into " + classname + " content " + json.dumps(e))
    r = client.command("insert into " + classname + " content " + json.dumps(e))
    
    print(r[0]._rid)
    
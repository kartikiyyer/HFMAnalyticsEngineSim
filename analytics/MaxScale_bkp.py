
__author__ = 'glally'
'''
making the change for initializing the values and restarting the traffic
'''
#!/usr/bin/python

import socket, IN               # Import socket module
import analytics_pb2
import subprocess, signal
import threading, thread
import random
import datetime
#from datetime import datetime
#from time import mktime
import array
import time,sys,struct, os, getopt
import errno                # getting error number
from struct import pack
from google.protobuf import message
from google.protobuf.internal import wire_format
from socket import error
import decimal
import os
import fcntl
latency_SampleRate=5000         #in millisecond
traffic_SampleRate=25              #seconds


class Lock:
    
    def __init__(self, filename):
        self.filename = filename
        # This will create it if it does not exist already
        self.handle = open(filename, 'w')
    
    # Bitwise OR fcntl.LOCK_NB if you need a non-blocking lock 
    def acquire(self):

        fcntl.flock(self.handle, fcntl.LOCK_EX| fcntl.LOCK_NB)
        
    def release(self):
        fcntl.flock(self.handle, fcntl.LOCK_UN)
        
    def __del__(self):
        self.handle.close()


lock = Lock("/tmp/lock_name.tmp")


def timeStamp():
    dt = datetime.datetime.now()
    sec_since_epoch = time.mktime(dt.timetuple())+dt.microsecond/1000000.0
    epochTime=int(sec_since_epoch * 1000000)
    #epochTime=int(time.time())*1000000
    return epochTime

def random_incremental():
    pass

def trueInterfaces(argv):
    #interfaceList=[90,91,92,93,94,95,96,97,8,9,10,12,37,39,40,41,43,46,47,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,]
    interfaceList= range(1, 101)
    if str(argv[2])=="analytics-qfx5100-01":
        interfaceList=[90,91,92,93,94,95,96,97,8,9,10,12,37,39,40,41,43,46,47,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,]
    elif  str(argv[2])=="analytics-qfx5100-02":
        interfaceList=[84,84,96,97,98,99,8,9,10,12,18,19,20,21,22,23,24,25,26,27,28,29,30,31,33,34,36,37,38,39,40,42,43,44,45,46,47,]
    elif  str(argv[2])=="analytics-demo-02":
        interfaceList=[1,2,3,4,5,6,7,9,10,11,12,13,14,15,16,17,18,19,20,21,22]

    return interfaceList



def random_Traffic():
    random_T=int(random.randrange(100000, 1000000000000, 100000))
    return random_T

def random_QueueDepth(interfaceNumber):
    random_QD=int(random.randrange(10000, 22345, 1000))
    if interfaceNumber % 10==0:
        random_QD=int(random.randrange(3234567, 5234567, 123456))
    elif interfaceNumber % 5==0:
        random_QD=int(random.randrange(1234567, 2234567, 123456))
    elif interfaceNumber % 6==0:
        random_QD=int(random.randrange(523456, 923456, 12345))
    elif interfaceNumber % 3==0:
        random_QD=int(random.randrange(123456, 723456, 100000))
    elif interfaceNumber % 2==0:
        random_QD=int(random.randrange(72345, 102345, 12345))
    return random_QD

def random_delay():
    random_Delay=random.randrange()
    return random_Delay

def average_Traffic(last_traffic):
    Traffic = (last_traffic+10000)
    return Traffic

def socketStart(argv):
    host=argv[3]
    print "opening connection....for %s"% argv[1],
    port=50005
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


    print "host:"+str(host)
    s.connect((host, port))
    print "Connected from ",s.getsockname()
    print "Connected to  ", s.getpeername()
    print "done"
    return s

def deviceInfo(s, deviceName, deviceSeriaNumber, model, argv):
    delay=1
    print "sending device info"
    packet= analytics_pb2.AnRecord()
    packet.system.name= argv[1]
    #packet.timestamp=timeStamp()
    info=packet.system.information
    info.boot_time=1398358901
    info.model_info= model
    info.serial_no= deviceSeriaNumber

    interfaceList=[]
    for interfaceNumber in trueInterfaces(argv):
        interfaceList.append("xe-0/0/"+str(interfaceNumber))

    packet.system.information.interface_list.extend(interfaceList)
    info.max_ports= 104
    status=packet.system.status
    status.queue_status.status=1
    status.queue_status.poll_interval=latency_SampleRate
    status.queue_status.lt_high=10000000
    status.queue_status.lt_low=100000
    status.traffic_status.status=1
    status.traffic_status.poll_interval=traffic_SampleRate

    sendPacket(s, packet, packet.system.name, argv)
    time.sleep(delay)
    print "sending data for interfaces"
    index=1
    for interface in interfaceList:
        interfaceInfo(s, deviceName, interface, index, model, argv)
	index=index+1



def interfaceInfo(s, deviceName, interface,index, model, argv):
    portNumber=interface.split('/')
    packet= analytics_pb2.AnRecord()
    #packet.timestamp=timeStamp()
    infoInterface=packet.interface.add()
    infoInterface.name= argv[1]+":"+str(interface)
    '''for name in packet.interface:
        print name'''
    info=infoInterface.information
    info.snmp_index=500+index
    info.index=644+index
    info.slot=0
    info.port=int(portNumber[-1])
    info.media_type=2
    info.capability=43072
    info.porttype=184
    pStatus=infoInterface.status.link
    pStatus.speed= 10000000000
    pStatus.duplex=2
    pStatus.mtu =1514
    pStatus.state=True
    pStatus.auto_negotiation=True
    sendPacket(s, packet, packet.system.name, argv)
    #print packet.interface.information


def queueStats(s, deviceInterface, numberOfTimesTransmit,argv):
    filename="./logs/"+argv[1]+".log"
    file= open(filename, "w+")
    delay=decimal.Decimal(latency_SampleRate)/decimal.Decimal(1000)
    sustainedPorts=int(sys.argv[4])
    print "delay:"+str(delay)
    start_time =time.time()
    print "sending Queue",
    print "for device %s " % argv[1]
    #for i in range (0,numberOfTimesTransmit):
    g=timeStamp()
    while(1):


        elapsed_time  =time.time() - start_time
        if elapsed_time >= 300:
            print "sending Burst for %s at %s\n\n\n" %( argv[1],  datetime.datetime.now())
            packet= analytics_pb2.AnRecord()
            packet.timestamp=timeStamp()
            for interfaceNumber in trueInterfaces(argv):
                interfaceName=deviceInterface+str(interfaceNumber)
                #print interfaceName
                interfaceX=packet.interface.add()
                interfaceX.name=interfaceName
                interfaceX.stats.queue_stats.queue_depth=random_QueueDepth(interfaceNumber)
            start_time =time.time() #set time to current for next 15 mins
            #print "Queue send= %s" % packet.timestamp

        else :

            T1= timeStamp()
            #sending only for one interface every 10 milliseconds
            packet= analytics_pb2.AnRecord()
            packet.timestamp=timeStamp()
            for interfaceNumber in range(startInterface, sustainedPorts):
                random_interfaceNumber=interfaceNumber#int(random.randrange(startInterface, numberOfInterfaces) )
                interfaceName=deviceInterface+str(random_interfaceNumber)
                interfaceX=packet.interface.add()
                interfaceX.name=interfaceName
                interfaceX.stats.queue_stats.queue_depth=random_QueueDepth(random_interfaceNumber)

        s=sendPacket(s, packet, interfaceX.name, argv)
        T2= int(timeStamp() )
        timeTaken= int((T2-T1) /1000 )
        diff=int((T2-g)/1000)
        g=T2
        time.sleep(delay)
        file.write("current packet sending at= %s, Last packet send %s milliseconds ago for interface= %s total time taken to build packet %s \n" % (T2, diff, interfaceName,timeTaken ))



def trafficStats(s, deviceInterface, numberOfTimeTransmit,  argv):
    time.sleep(30)# this sleep is for setting the delay between the queue process so that device info could be send in advance
    delay=traffic_SampleRate
    last_traffic = 100000000
    print "sending Traffic",
    print "for device %s " % argv[1]
    #for i in range (0,numberOfTimesTransmit):
    while(1):
        packet= analytics_pb2.AnRecord()
        traffic=average_Traffic(last_traffic)
        last_traffic=traffic
        if last_traffic>=100000000000:
            last_traffic= 1000000

        #for interfaceNumber in range(startInterface,numberOfInterfaces):
        for interfaceNumber in trueInterfaces(argv):
            trafficInterface= packet.interface.add()
            interfaceName=deviceInterface+str(interfaceNumber)
            trafficInterface.name=interfaceName
            #time Stamp
	        #print packet.timestamp
            packet.timestamp=timeStamp()

            Traffic_Stats=trafficInterface.stats.traffic_stats

            Traffic_Stats.rxpkt= int(random.randrange(3000000, 621286497, 1000000))
            Traffic_Stats.rxucpkt=Traffic_Stats.rxpkt
            Traffic_Stats.rxpps=int(random.randrange(5,200 ,5 ))
            #Traffic_Stats.rxmcpkt=traffic
            #Traffic_Stats.rxbcpkt=
            Traffic_Stats.rxbyte=int(random.randrange(50000000000, 99000000000, 1234567891))
            Traffic_Stats.rxbps=int(random.randrange(11264, 35000, 5345))
            Traffic_Stats.rxcrcerr=int(random.randrange(40, 345, 9))
            Traffic_Stats.rxdroppkt=int(random.randrange(3400000, 4999999, 100000))
            Traffic_Stats.txpkt=int(random.randrange(2000000,3392364 ,19236 ))
            Traffic_Stats.txucpkt=Traffic_Stats.txpkt
            #Traffic_Stats.txmcpkt=traffic
            #Traffic_Stats.txbcpkt=traffic
            Traffic_Stats.txpps=int(random.randrange(5,200 ,5 ))
            Traffic_Stats.txbyte=int(random.randrange(50000000000, 59000000000, 1234567891))
            Traffic_Stats.txbps=int(random.randrange(11264, 350000, 9345))
            #Traffic_Stats.txcrcerr=traffic
            Traffic_Stats.txdroppkt=int(random.randrange(40000000, 55263947, 100000))
        print "traffic send %s" % interfaceName
        s=sendPacket(s,   packet, trafficInterface.name, argv)
        '''sendTraffic=True
        while (sendTraffic):
            try:
                lock.acquire()
                #print "send traffic"
                s=sendPacket(s,   packet, trafficInterface.name, argv)
                sendTraffic=False
                lock.release()

            except IOError:
                print "socket used for sending queue data"
                time.sleep(0.6)'''

        time.sleep(delay)


def sendPacket(s, packet, interface, argv):
    recordLength = packet.ByteSize()
    #print packet
    #if int(timeStamp()) % 41 ==0:
	#print "Transmitting from ",s.getsockname(),
	#print "for device %s " % argv[1],
	#print "Transmitting to  " , s.getpeername()
    '''creating header , for more to read look into wire_format'''
    buffer= (struct.pack('<II',recordLength,1))
    sp=packet.SerializeToString()
    '''sending package'''
    try:
	s.sendall(buffer+sp)

    except error as sError:
	if sError.errno != errno.ECONNREFUSED:
                print " connection refused  ", s.getsockname()
                print str(datetime.datetime.now())
                s.close()
		s=socketStart(argv)
	else:
                raise sError
            	# connection refused
    return s




def simulate_traffic( device_Name_Interface,deviceSerialNum, model, argv):
    children=[]
    time_dic_device={}




    for process in range(0,2):
        child = os.fork()
        if child:
            children.append(child)
        else:
            #if process==0:
                #s = socketStart(argv)
                #print "connected to %s for  device %s"% (s.getpeername(), argv[1])
                #deviceInfoTransmission= deviceInfo(s,device_Name_Interface, deviceSerialNum,model, argv)
                #queueTransmission=queueStats(s,device_Name_Interface, numberOfTimesTransmit, argv)
                #os._exit(0)
            if process==1:
                s = socketStart(argv)
                trafficTransmission=trafficStats(s, device_Name_Interface, numberOfTimesTransmit, argv)


            #os._exit(0)
    #for child in enumerate(children):
        #os.waitpid(int(child), 0)

def main(argv):
    ts = time.time()
    time_dic={}

    delayBetweenMessages=2
    device_Name=argv[1]         #"analytics-qfx5100-02"
    deviceSerialNum=argv[2]     #"VB3714010001"
    host=argv[3]
    model="QFX5100"
    #host_name= socket.gethostname() # Get local machine name
    #host = socket.gethostbyname(host_name) #Get local IP address
    port = 50005
    print "Transitting for device %s=%s:xe-0/0/" % (device_Name,  deviceSerialNum)
    simulate_traffic( "%s:xe-0/0/"% device_Name, deviceSerialNum, model, argv)




if __name__ == '__main__':

    numberOfTimesTransmit=1
    print sys.argv
    startInterface=1
    Flag=False
    numberOfInterfaces=int(sys.argv[5])
    sustainedPorts=int(sys.argv[4])
    sys.argv.append(False)
    main(sys.argv)



'''
rm -rf /var/lib/cassandra/commitlog/
rm -rf /var/lib/cassandra/saved_caches/
rm -rf /var/lib/cassandra/commitlog/
rm -rf /var/lib/cassandra/data/kairosdb/
rm -rf /var/log/ae.log
rm -rf /tmp/analytics-engine.pid
'''





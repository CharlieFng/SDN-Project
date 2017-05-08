import random
import os
import json
import numpy as np
import re
import urllib
import urllib2
import time
import datetime
from sklearn.cluster import KMeans
from sklearn import svm
from sklearn.preprocessing import scale
from matplotlib.mlab import PCA as mlabPCA
from matplotlib import pyplot as plt

#  feature:install odl-restconf odl-l2switch-switch odl-mdsal-apidocs odl-dlux-all odl-tsdr-hsqldb-all

class TSDRDataService:

    getIntervalURL = 'http://118.138.235.213:8181/restconf/config/tsdr-openflow-statistics-collector:TSDROSCConfig'
    setIntervalURL = 'http://118.138.235.213:8181/restconf/operations/tsdr-openflow-statistics-collector:setPollingInterval'
    TSDRDataURL = 'http://118.138.235.213:8181/tsdr/metrics/query?'

    __dataPollingInterval = 1500

    __username = 'admin'
    __password = 'admin'


    def __init__(self, dataPollingInterval):
        self.__dataPollingInterval = dataPollingInterval
        if dataPollingInterval != 1500:
            self.setInterval(dataPollingInterval)
    

    def getUsername(self):
        return self.__username

    def setUsername(self, username):
        self.__username = username

    def getPassword(self):
        return self.__password

    def setPassword(self, password):
        self.__password = password


    def getGetIntervalURL(self):
        return self.getIntervalURL

    def setGetIntervalURL(self, getIntervalURL):
        self.getIntervalURL = getIntervalURL


    def getSetIntervalURL(self):
        return self.setIntervalURL

    def setSetIntervalURL(self, setIntervalURL):
        self.setIntervalURL = setIntervalURL

    def getTSDRDataURL(self):
        return self.TSDRDataURL

    def setTSDRDataURL(self, TSDRDataURL):
        self.TSDRDataURL = TSDRDataURL


    @classmethod
    def getInterval(cls):

        p = urllib2.HTTPPasswordMgrWithDefaultRealm()
        p.add_password(None, cls.getIntervalURL, cls.__username, cls.__password)
        handler = urllib2.HTTPBasicAuthHandler(p)
        opener = urllib2.build_opener(handler)
        urllib2.install_opener(opener)
        interval = urllib2.urlopen(cls.getIntervalURL).read()
        return interval

    @classmethod
    def setInterval(cls, interval = 1500):

        params = { "input": { "interval": str(interval) } }
        req = urllib2.Request(cls.setIntervalURL)
        req.add_header('Content-Type', 'application/json')
        p = urllib2.HTTPPasswordMgrWithDefaultRealm()
        p.add_password(None, cls.setIntervalURL, cls.__username, cls.__password)
        auth_handler = urllib2.HTTPBasicAuthHandler(p)
        opener = urllib2.build_opener(auth_handler)
        urllib2.install_opener(opener)
        content = urllib2.urlopen(req, json.dumps(params))


    def collectData(self, nodeid='', dataCategory='PORTSTATS', metricName='', recordKey='', timeInMinutes=1, write = True ):

        categories = ['FLOWSTATS','FLOWTABLESTATS','PORTSTATS']

        if dataCategory == "ALL" :
            for c in categories:
                self.collectData(dataCategory=c)
            return 

        now = datetime.datetime.now()
        past = now - datetime.timedelta(minutes=timeInMinutes)

        NOW = int(time.mktime(now.timetuple()))
        PAST = int(time.mktime(past.timetuple()))

        values = {'tsdrkey':'[NID='+nodeid+'][DC='+dataCategory+'][MN='+metricName+ '][RK='+ recordKey + ']', 'from':PAST, 'until':NOW}

        params = urllib.urlencode(values)
        p = urllib2.HTTPPasswordMgrWithDefaultRealm()

        p.add_password(None, self.TSDRDataURL, self.__username, self.__password)

        handler = urllib2.HTTPBasicAuthHandler(p)
        opener = urllib2.build_opener(handler)
        urllib2.install_opener(opener)

        try:
            response = urllib2.urlopen(self.TSDRDataURL+params)
            contents = response.read()
        except urllib2.HTTPError, error:
            contents = error.read()

        print contents
        if write :
            outputfile = open(dataCategory +'.txt','w')
            outputfile.write(contents)
            outputfile.close()


    def portStatsProcess(self, write=True):

        with open('PORTSTATS.txt') as data_file:
            data = json.load(data_file)

        orginList = filter( lambda x: re.match( r'^openflow:[0-9]:[0-9]$', x['recordKeys'][1]['keyValue'] ) ,data["metricRecords"])
        timestamps = sorted(set( map(lambda x: x['timeStamp'], orginList) ))
        ports = sorted(set(map (lambda x:x['recordKeys'][1]['keyValue'], orginList)))

        print ports
        statsByTime = [ [ y for y in orginList if y['timeStamp']==x ] for x in timestamps]

        statsByPort = [ [ [ z for z in x if z['recordKeys'][1]['keyValue'] == y ] for y in ports ] for x in statsByTime ]

        dataPointsGroup = [ [ self.__portStatsCleanUp(y) for y in x] for x in statsByPort]
      

        dataPoints = [item for sublist in dataPointsGroup for item in sublist]


        dataPointsClean = filter(lambda x : x != None , dataPoints)
        if dataPoints != dataPointsClean :
            print "ccccccccccccccccccccccccccccccccccccccccccccccccccccc"

        arr = np.asarray(dataPointsClean)
        print('Number of data points:', len(arr))

        columsName = ['Node','Port', 'TransmitDrops','ReceiveDrops','ReceiveCrcError','ReceiveFrameError','ReceiveOverRunError','TransmitErrors','CollisionCount','ReceiveErrors','TransmittedBytes','ReceivedBytes','TransmittedPackets','ReceivedPackets' ]

        if write == True :
            self.__writeIntoFile('portStatsPoints.csv', columsName, arr)



    def flowStatsProcess(self, wirte=True):
        with open('FLOWSTATS.txt') as data_file:
            data = json.load(data_file)

        orginList = data['metricRecords']
        timestamps = sorted( set( map(lambda x: x['timeStamp'], orginList) ) )

        print("different time number:", len(timestamps), "time stamps:", timestamps, "\n")

        flows = sorted(set(map(lambda x: x['recordKeys'][2]['keyValue'], orginList)))

        print("different flow number:", len(flows), "flows:", flows)

        statsByTime = [ [ y for y in orginList if y['timeStamp'] == x ]for x in timestamps]
        statsByFlow = [ [ [z for z in x if z['recordKeys'][2]['keyValue'] == y ]for y in flows]for x in statsByTime] 


        dataPointsGroup = [ [ self.__flowStatsCleanUp(y) for y in x] for x in statsByFlow] 

        dataPoints = [item for sublist in dataPointsGroup for item in sublist]

        dataPointsClean = filter(lambda x : x != None , dataPoints)
        if dataPoints != dataPointsClean :
            print "ccccccccccccccccccccccccccccccccccccccccccccccccccccc"

        arr = np.asarray(dataPointsClean)

        columsName = ['Table', 'Flow', ' Node', 'ByteCount', 'PacketCount']

        if write == True :
            self.__writeIntoFile('flowStatsPoints.csv', columsName, arr)



    def flowTableStatsProcess(self, write = True):
        with open('FLOWTABLESTATS.txt') as data_file:
            data = json.load(data_file)

        orginList = data['metricRecords']
        timestamps = sorted( set( map(lambda x: x['timeStamp'], orginList) ) )

        print("different time number:", len(timestamps), "time stamps:", timestamps, "\n")

        tables = sorted(set(map(lambda x: x['recordKeys'][1]['keyValue'], orginList)))

        print("different table number:", len(tables), "table:", tables)

        statsByTime = [ [ y for y in orginList if y['timeStamp'] == x ]for x in timestamps]
        statsByTable = [ [ [z for z in x if z['recordKeys'][1]['keyValue'] == y ]for y in tables]for x in statsByTime] 


        dataPointsGroup = [ [ self.__flowTableStatsCleanUp(y) for y in x] for x in statsByTable] 
        dataPoints = [item for sublist in dataPointsGroup for item in sublist]

        dataPointsClean = filter(lambda x : x != None , dataPoints)
        if dataPoints != dataPointsClean :
            print "ccccccccccccccccccccccccccccccccccccccccccccccccccccc"

        arr = np.asarray(dataPointsClean)

        columsName = ['Table','Node','ActiveFlows', 'PacketMatch', 'PacketLookup']

        if write == True :
            self.__writeIntoFile('flowTableStatsPoints.csv', columsName, arr)
     


    def __writeIntoFile(self, fileName, columsName, data):

        with open(fileName, 'w') as f:
            for index, col in enumerate(columsName):
                if index < len(columsName) -1:
                    f.write('%s,' % col)
                else:
                    f.write('%s\n' % col)
            #arr = np.asarray(data)
            print data
            np.savetxt(f, data, fmt='%.0f' ,delimiter=',')




    def __portStatsCleanUp(self,lst):
        if lst == []: return
        res = [0] * 14
        tmp = map(int, re.findall(r'\d+', lst[0]['recordKeys'][1]['keyValue']))
        print('Lenght of tmp:', len(tmp))
        res[0] = tmp[0]
        res[1] = tmp[1]
        for obj in lst:
            if obj['metricName'] == 'TransmitDrops':
                res[2] = obj['metricValue']
            elif obj['metricName'] == 'ReceiveDrops':
                res[3] = obj['metricValue']
            elif obj['metricName'] == 'ReceiveCrcError':
                res[4] = obj['metricValue']
            elif obj['metricName'] == 'ReceiveFrameError':
                res[5] = obj['metricValue']
            elif obj['metricName'] == 'ReceiveOverRunError':
                res[6] = obj['metricValue']
            elif obj['metricName'] == 'TransmitErrors':
                res[7] = obj['metricValue']
            elif obj['metricName'] == 'CollisionCount':
                res[8] = obj['metricValue']
            elif obj['metricName'] == 'ReceiveErrors':
                res[9] = obj['metricValue']
            elif obj['metricName'] == 'TransmittedBytes':
                res[10] = obj['metricValue']
            elif obj['metricName'] == 'ReceivedBytes':
                res[11] = obj['metricValue']
            elif obj['metricName'] == 'TransmittedPackets':
                res[12] = obj['metricValue']
            elif obj['metricName'] == 'ReceivedPackets':
                res[13] = obj['metricValue']
        print res
        return res



    def __flowStatsCleanUp(self, lst):

        if lst == []: return
        res = [0] * 5
        tmp = map(int, re.findall(r'\d+', lst[0]['recordKeys'][2]['keyValue']))
        res[2] = int(re.search(r'\d+',lst[0]['recordKeys'][0]['keyValue']).group())
        #print('Lenght of tmp:', len(tmp))
        res[0] = tmp[0]
        res[1] = tmp[1]

        for obj in lst:
            if obj['metricName'] == 'ByteCount':
                res[3] = obj['metricValue']
            elif obj['metricName'] == 'PacketCount':
                res[4] = obj['metricValue']

        return res


    def __flowTableStatsCleanUp(self, lst):

        if lst == []: return
        res = [0] * 5
        res[0] = int(lst[0]['recordKeys'][1]['keyValue'])
        res[1] = int(re.search(r'\d+',lst[0]['recordKeys'][0]['keyValue']).group())
        for obj in lst:
            if obj['metricName'] == 'ActiveFlows':
                res[2] = obj['metricValue']
            elif obj['metricName'] == 'PacketMatch':
                res[3] = obj['metricValue']
            elif obj['metricName'] == 'PacketLookup':
                res[4] = obj['metricValue']
        print res
        return res



    def KMeancluster(self, file):

        testData = np.loadtxt(file, dtype=int, delimiter=',', skiprows=1)
        print testData[:,2:]
        model = KMeans(n_clusters=2).fit(testData)

        labels = model.labels_ 
        cluster_centers = model.cluster_centers_

        print labels
        print cluster_centers


    def Classification(self, trainFile, testFile):

        trainData = np.loadtxt(trainFile, dtype=int, delimiter=',', skiprows=1)
        train_x = trainData[:,2:]

        temp = trainData[:, :2]
        train_y = np.array([ lst[0]*10 + lst[1]  for lst in temp])

        clf = svm.SVC(C=1.0, degree=3, kernel='rbf')
        clf.fit(train_x,train_y)

        testData = np.loadtxt(testFile, dtype=int, delimiter=',', skiprows=1)
        test_x = testData[:,2:]

        pred = clf.predict(test_x)

        print pred
        for index, item in enumerate(testData) :
            if item[0] * 10 + item[1] != pred[index]:
                print('Exception occurs in node %d with port %d' % (item[0], item[1]) )


def run():
    "Create a test for the module"

    tsdr = TSDRDataService(1500)
    print tsdr.getUsername()
    print tsdr.getGetIntervalURL()
    #print tsdr.getInterval()

    #tsdr.collectData(dataCategory="ALL")

    #tsdr.portStatsProcess()

    tsdr.Classification('portStatsPoints1.csv', 'portStatsPoints2.csv')

    #tsdr.Classification(portStatsPoints1.csv, portStatsPoints2.csv)
if __name__ == '__main__' :
    run()

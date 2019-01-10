__author__ = 'Konrad Połys, Krzysztof Grochla'


import copy, math, operator, random
#import numpy as np
import pyltes.devices as devices
import datetime
from operator import itemgetter

numberOfThreads = 3

class gatewayFinderIterations:
    def __init__(self, parent):
        self.parent = parent
        self.bsbuckets = None
        self.bsstate = None
        self.optHistory = []
        self.alreadyAssigned = False



    def addHistory(self):
        histLen = 10
        self.optHistory.append([len(self.parent.bs), self.returnNoReception()])
        if len(self.optHistory) > histLen:
            self.optHistory.remove(self.optHistory[0])

    def sameStateAgain(self):
        print(self.optHistory)
        if [len(self.parent.bs), self.returnNoReception()] in self.optHistory[0:len(self.optHistory)]:
            return True
        else:
            return False


    def saveState(self):
        self.bsstate = []
        self.bsstate.append([self.returnNoReception(),0])
        for BS in self.parent.bs:
            self.bsstate.append(BS.myNodeID)


    def restoreState(self):
        self.parent.bs = []
        self.cleanBSbuckets()
        for NodeID in range(len(self.parent.ue)):
            self.parent.ue[NodeID].iamBS = None
            self.parent.ue[NodeID].connectedToBS = None

        second = False
        for NodeID in self.bsstate:
            if second:
                if not self.addBaseStation(NodeID):
                    print("error")
            else:
                self.bsstate[0][1] += 1
                second = True
        self.makeassignment(2)


    def returnRestorationStatInSavedState(self):
        if self.bsstate is not None:
            return self.bsstate[0][1]
        else:
            return None

    def returnNoReceptInSavedState(self):
        if self.bsstate is not None:
            return self.bsstate[0][0]
        else:
            return None

    def returnBSnumberInSavedState(self):
        if self.bsstate is not None:
            return len(self.bsstate) - 1
        else:
            return None

    def cleanBSbuckets(self):
        x_bucket = self.parent.XsizeBuckets
        y_bucket = self.parent.YsizeBuckets
        self.bsbuckets = []
        for x in range(x_bucket):
            self.bsbuckets.append([])
            for y in range(y_bucket):
                self.bsbuckets[x].append([])

    def addToBSbucket(self, ID, x, y):
        if self.bsbuckets is None:
            self.cleanBSbuckets()

        resolution = self.parent.bucketResolution
        xx = int(x/resolution)
        yy = int(y/resolution)
        self.bsbuckets[xx][yy].append(ID)


    def returnNoReception(self):
        howBad = 0
        for ue in self.parent.ue:
            if ue.connectedToBS is None:
                howBad += 1
        return howBad

    def makeMatrix(self, x, y):
        m = [None] * x
        for a in range(x):
           m[a] = [None] * y
        return m

    def addBaseStation(self, NodeID):
        newBS = devices.LoRaBS()
        newBS.ID = len(self.parent.bs)
        newBS.turnedOn = True
        newBS.omnidirectionalAntenna = True
        newBS.Rc = 1500
        newBS.x = self.parent.ue[NodeID].x
        newBS.y = self.parent.ue[NodeID].y
        newBS.long = self.parent.ue[NodeID].long
        newBS.lat = self.parent.ue[NodeID].lat
        newBS.height = self.parent.ue[NodeID].height
        newBS.myNodeID = NodeID
        newBS.power = self.parent.bspower
        newBS.maxClients = newBS.returnMaxClientsPerGW(self.parent.deliveryProbability, self.parent.gatheringTime, 51, self.parent.sf)
        if self.parent.ue[NodeID].iamBS is None:
            self.parent.ue[NodeID].iamBS = newBS.ID
            self.parent.bs.append(newBS)
            self.addToBSbucket(newBS.ID, newBS.x, newBS.y)
            return True
        else:
            return False
        self.alreadyAssigned = False


    def addBaseStations(self, NodeIDlist):
        NodeIDlist = list(set(NodeIDlist))
        for NodeID in NodeIDlist:
            if not self.addBaseStation(NodeID):
                print("Error")

    def removeBaseStation(self, BSID):
        NodeID = self.parent.bs[BSID].myNodeID
        self.parent.ue[NodeID].iamBS = None
        self.parent.ue[NodeID].connectedToBS = None
        self.parent.bs.remove(self.parent.bs[BSID])
        self.cleanBSbuckets()
        for i in range(len(self.parent.bs)):
            NodeID = self.parent.bs[i].myNodeID
            self.parent.ue[NodeID].iamBS = i
            self.parent.ue[NodeID].connectedToBS = None
            self.parent.bs[i].ID = i
            self.addToBSbucket(i, self.parent.bs[i].x, self.parent.bs[i].y)
            assert self.parent.ue[NodeID].x == self.parent.bs[i].x and self.parent.ue[NodeID].y == self.parent.bs[i].y
        self.alreadyAssigned = False

    def removeBaseStations(self, BSIDlist):
        BSIDlist = list(set(BSIDlist))
        BSIDlist.sort(reverse=True)
        for BSID in BSIDlist:
            self.removeBaseStation(BSID)

    def returnDistance(self, x1, y1, x2, y2):
        return math.sqrt((x2-x1)**2 + (y2-y1)**2)


    def returnNodeIDat(self, x, y, me = None):
        nodeID = None
        bucketDistance = 2
        while nodeID is None:
            nodesToCheck = self.returnNodesToCheck(x, y, bucketDistance)
            distance = None
            for node in nodesToCheck:
                if self.parent.ue[node].iamBS is None or self.parent.ue[node].iamBS is me :
                    tmpdist = self.returnDistance(self.parent.ue[node].x, self.parent.ue[node].y, x, y)
                    if distance is None or distance > tmpdist:
                        distance = tmpdist
                        nodeID = node
            bucketDistance += 1
        return nodeID



    def returnNodeIDatOld(self, x, y, onlyNode=False, bucketDistance=1, different = None):
        nodeID = None
        while nodeID is None:
            nodesToCheck = self.returnNodesToCheck(x, y, bucketDistance)

            distance = None
            for node in nodesToCheck:
                tmpdist = self.returnDistance(self.parent.ue[node].x, self.parent.ue[node].y, x, y)
                if distance is None or distance > tmpdist:
                    if different is None or different != node:
                        if onlyNode:
                            if self.parent.ue[node].iamBS is None:
                                distance = tmpdist
                                nodeID = node
                        else:
                            distance = tmpdist
                            nodeID = node
            bucketDistance += 1
        return nodeID

    def returnNodesToCheck(self, x, y, bucketDistance):
        if x is not None and y is not None:

            x_bucket = int(x / self.parent.bucketResolution)
            y_bucket = int(y / self.parent.bucketResolution)

            x_min = x_bucket - bucketDistance
            x_max = x_bucket + bucketDistance
            y_min = y_bucket - bucketDistance
            y_max = y_bucket + bucketDistance

            if x_min < 0:
                x_min = 0
            if x_max > self.parent.XsizeBuckets - 1:
                x_max = self.parent.XsizeBuckets - 1
            if y_min < 0:
                y_min = 0
            if y_max > self.parent.YsizeBuckets - 1:
                y_max = self.parent.YsizeBuckets - 1

            coordsToCheck = []
            for x in range(x_min, x_max + 1):
                for y in range(y_min, y_max + 1):
                    coordsToCheck.append([x, y])

            nodesToCheck = []
            for x, y in coordsToCheck:
                for id in self.parent.buckets[x][y]:
                    nodesToCheck.append(id)
            return nodesToCheck
        else:
            return None

####################################
####################################
    def findGateways(self, mainLoopIterations, movefunctioniterations):

        allowednoconnected = int(self.parent.allowednoconnected / 100.0 * len(self.parent.ue))
        self.putgateways(stepDistance=self.parent.bucketResolution*1.0, bucketDistance=0)
        self.saveState()

        while self.returnNoReception() >= allowednoconnected and mainLoopIterations > 0:
            moveFunctionCounter = movefunctioniterations
            while self.returnNoReception() >= allowednoconnected and moveFunctionCounter > 0:
                self.fillListOfClients()
                self.moveBaseStation()
                if self.returnNoReception() < self.returnNoReceptInSavedState():
                    self.saveState()
                moveFunctionCounter -= 1

            if self.returnNoReception() > self.returnNoReceptInSavedState():
                self.restoreState()

            self.deleteOverlapping()
            self.addSomeNew()
            self.saveState()
            mainLoopIterations -= 1
        # self.showLoad()







####################################
    def addSomeNew(self):
        if self.returnNoReception() == 0:
            return
        minToAddGW = 1
        for xb in self.parent.buckets:
            for yb in xb:
                countNotConnected = 0
                minX = None
                maxX = None
                minY = None
                maxY = None
                for NodeID in yb:
                    if self.parent.ue[NodeID].connectedToBS is None:
                        countNotConnected += 1
                        if minX is None or minX > self.parent.ue[NodeID].x:
                            minX = self.parent.ue[NodeID].x
                        if minY is None or minY > self.parent.ue[NodeID].y:
                            minY = self.parent.ue[NodeID].y
                        if maxX is None or maxX < self.parent.ue[NodeID].x:
                            maxX = self.parent.ue[NodeID].x
                        if maxY is None or maxY < self.parent.ue[NodeID].y:
                            maxY = self.parent.ue[NodeID].y
                if countNotConnected >= minToAddGW:
                    randX = random.uniform(minX, maxX)
                    randY = random.uniform(minY, maxY)
                    newGW = self.returnNodeIDat(randX, randY)
                    self.addBaseStation(newGW)
                    self.makeassignment(2)

    def deleteOverlapping(self):
        if self.returnNoReception() == 0:
            return
        for bs in self.parent.bs:
            self.makeassignment(2)
            self.fillListOfClients()
            count = 0
            count_duplicates = 0
            for client in bs.clientList:
                count += 1
                if len(self.returnGWsInClientRange(client)) > 1:
                    count_duplicates += 1
            rand = random.uniform(0, bs.maxClients/5.0)
            if count_duplicates + rand >= count and len(bs.clientList) < bs.maxClients/2.0:
                self.removeBaseStation(bs.ID)
                self.makeassignment(2)
                self.fillListOfClients()


    def returnGWsInClientRange(self, NodeID):
        bucketDistance = 2
        ue_x_bucket = int(self.parent.ue[NodeID].x / self.parent.bucketResolution)
        ue_y_bucket = int(self.parent.ue[NodeID].y / self.parent.bucketResolution)

        x_min = ue_x_bucket - bucketDistance
        x_max = ue_x_bucket + bucketDistance
        y_min = ue_y_bucket - bucketDistance
        y_max = ue_y_bucket + bucketDistance

        if x_min < 0:
            x_min = 0
        if x_max > self.parent.XsizeBuckets - 1:
            x_max = self.parent.XsizeBuckets - 1
        if y_min < 0:
            y_min = 0
        if y_max > self.parent.YsizeBuckets - 1:
            y_max = self.parent.YsizeBuckets - 1

        coordsToCheck = []
        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                coordsToCheck.append([x, y])

        bsToCheck = []
        for x, y in coordsToCheck:
            for BSID in self.bsbuckets[x][y]:
                bsToCheck.append(BSID)

        output = []
        for BSID in bsToCheck:
            tmp = self.parent.getAttenuationForNetwork(NodeID, BSID, secondArgIsBS=True)
            if tmp is not None :
                output.append(BSID)
        return output

    def fillListOfClients(self):
        if not self.alreadyAssigned:
            self.makeassignment(bucketDistance=1)
        for bsid in range(len(self.parent.bs)):
            self.parent.bs[bsid].clientList = []
        for ue in self.parent.ue:
            if ue.connectedToBS is not None:
                self.parent.bs[ue.connectedToBS].clientList.append(ue.ID)

    def findNotConnectedInRangePlus(self, plusRangePercent, bs):
        range = self.parent.bucketResolution
        range += range * (plusRangePercent/100.0)
        bucketDistance = math.ceil(range / self.parent.bucketResolution)
        nodesToCheck = self.returnNodesToCheck(bs.x, bs.y, bucketDistance)
        nodesWOreception = []

        for nod in nodesToCheck:
            if self.parent.ue[nod].connectedToBS is None and self.returnDistance(bs.x, bs.y, self.parent.ue[nod].x, self.parent.ue[nod].y) <= range:
                nodesWOreception.append(nod)
        return nodesWOreception

    def moveBaseStation(self):
        toRemove = []
        toAdd = []
        for bs in self.parent.bs:
            notConnected = self.findNotConnectedInRangePlus(plusRangePercent = 50, bs = bs)
            if len(notConnected) > 0:
                averageLoc = [0,0] #x,y
                for ncID in notConnected:
                    averageLoc[0] += self.parent.ue[ncID].x
                    averageLoc[1] += self.parent.ue[ncID].y
                averageLoc[0] = averageLoc[0] / len(notConnected)
                averageLoc[1] = averageLoc[1] / len(notConnected)
                range10 = self.parent.bucketResolution / 10.0
                if averageLoc[0] > bs.x + range10 or averageLoc[0] < bs.x - range10 \
                    and averageLoc[1] > bs.y + range10 or averageLoc[1] < bs.y - range10:
                    vecX = averageLoc[0] - bs.x
                    vecY = averageLoc[1] - bs.y
                    maxRandom = 95
                    vecX *= (random.uniform(1, maxRandom) / 100.0)
                    vecY *= (random.uniform(1, maxRandom) / 100.0)
                    newX = bs.x + vecX
                    newY = bs.y + vecY

                    futureBS = self.returnNodeIDat(newX, newY, bs.ID)
                    if self.parent.ue[futureBS].iamBS is not bs.ID:
                        # if len(bs.clientList) < bs.maxClients:
                        toRemove.append(bs.ID)
                        toAdd.append(futureBS)
        self.removeBaseStations(toRemove)
        self.addBaseStations(toAdd)
        self.makeassignment(2)

    def putgateways(self, stepDistance, bucketDistance = 0):
        self.alreadyAssigned = False
        x = 0
        while x < self.parent.constraintAreaMaxX:
            y = 0
            while y < self.parent.constraintAreaMaxY:
                nodesToCheck = self.returnNodesToCheck(x, y, bucketDistance=bucketDistance)
                if len(nodesToCheck) > 0:
                    minX = None
                    minY = None
                    maxX = None
                    maxY = None
                    for NodeID in nodesToCheck:
                        if minX is None or self.parent.ue[NodeID].x < minX:
                            minX = self.parent.ue[NodeID].x
                        if minY is None or self.parent.ue[NodeID].y < minY:
                            minY = self.parent.ue[NodeID].y

                        if maxX is None or self.parent.ue[NodeID].x > maxX:
                            maxX = self.parent.ue[NodeID].x
                        if maxY is None or self.parent.ue[NodeID].y > maxY:
                            maxY = self.parent.ue[NodeID].y

                    midX = minX + ((maxX - minX) / 2)
                    midY = minY + ((maxY - minY) / 2)
                    NodeID = self.returnNodeIDat(midX, midY)
                    if not self.addBaseStation(NodeID):
                        print("error5")
                y += stepDistance
            x += stepDistance
        self.makeassignment(bucketDistance=1)

    def showLoad(self):
        self.fillListOfClients()
        for bs in self.parent.bs:
            print(bs.ID, len(bs.clientList))

    def addNewGateway(self):
        success = False
        blacklist = []
        while not success:
            noRecp = None
            cx = None
            cy = None
            x = 0
            while x < self.parent.constraintAreaMaxX:
                y = 0
                while y < self.parent.constraintAreaMaxY:
                    if [x, y] not in blacklist:
                        nodesToCheck = self.returnNodesToCheck(x, y, bucketDistance=0)
                        bucketNoRecp = 0
                        for NodeID in nodesToCheck:
                            if self.parent.ue[NodeID].connectedToBS is None:
                                bucketNoRecp += 1
                        if noRecp is None or noRecp < bucketNoRecp:
                            noRecp = bucketNoRecp
                            cx = x
                            cy = y
                    else:
                        print("blacklist", blacklist)
                    y += self.parent.bucketResolution
                x += self.parent.bucketResolution

            if noRecp is None or noRecp > 0:
                nodesToCheck = self.returnNodesToCheck(cx, cy, bucketDistance=0)
                minX = None
                minY = None
                maxX = None
                maxY = None
                avgX = 0
                avgY = 0
                for NodeID in nodesToCheck:
                    if self.parent.ue[NodeID].connectedToBS is None:
                        avgX += self.parent.ue[NodeID].x
                        avgY += self.parent.ue[NodeID].y

                        if minX is None or self.parent.ue[NodeID].x < minX:
                            minX = self.parent.ue[NodeID].x
                        if minY is None or self.parent.ue[NodeID].y < minY:
                            minY = self.parent.ue[NodeID].y

                        if maxX is None or self.parent.ue[NodeID].x > maxX:
                            maxX = self.parent.ue[NodeID].x
                        if maxY is None or self.parent.ue[NodeID].y > maxY:
                            maxY = self.parent.ue[NodeID].y
                avgX = avgX / len(nodesToCheck)
                avgY = avgY / len(nodesToCheck)
                midX = minX + ((maxX - minX) / 2)
                midY = minY + ((maxY - minY) / 2)
                NodeID = self.returnNodeIDat(midX, midY, bucketDistance=0)
                if self.addBaseStation(NodeID):
                    success = True
                else:
                    NodeID = self.returnNodeIDat(avgX, avgY, bucketDistance=0)
                    if self.addBaseStation(NodeID):
                        success = True
                    else:
                        blacklist.append([cx, cy])
            else:
                success = True


    def findGWtoMove(self, bucketDistance, movefunctioniterations):
        interruptCounter = movefunctioniterations
        internalBucketDistance = 1
        while self.returnNoReception() > 0 and interruptCounter > 0 and internalBucketDistance >= 0:
            noReceptOnEnter = self.returnNoReception()
            keepDistance = False
            toRemove = []
            toAdd = []

            lenbs = len(self.parent.bs)
            for BSID in range(lenbs):
                nodesToCheck = self.returnNodesToCheck(self.parent.bs[BSID].x, self.parent.bs[BSID].y, internalBucketDistance)

                nodesWOreception = []
                for nod in nodesToCheck:
                    if self.parent.ue[nod].connectedToBS is None:
                        nodesWOreception.append(nod)

                if len(nodesWOreception) > 0:
                    avgX = 0
                    avgY = 0
                    for nod in nodesWOreception:
                        avgX += self.parent.ue[nod].x
                        avgY += self.parent.ue[nod].y
                    avgX = int(avgX/len(nodesWOreception))
                    avgY = int(avgY/len(nodesWOreception))

                    moveMultiplier = 0.1
                    doWhile = True
                    while doWhile:
                        movX = abs(avgX - self.parent.bs[BSID].x) * moveMultiplier
                        movY = abs(avgY - self.parent.bs[BSID].y) * moveMultiplier
                        if avgX > self.parent.bs[BSID].x:
                            newX = self.parent.bs[BSID].x + movX
                        else:
                            newX = self.parent.bs[BSID].x - movX

                        if avgY > self.parent.bs[BSID].y:
                            newY = self.parent.bs[BSID].y + movY
                        else:
                            newY = self.parent.bs[BSID].y - movY
                        futureBSNodeID = self.returnNodeIDat(newX, newY, onlyNode=True)

                        if self.parent.ue[futureBSNodeID].iamBS is None:
                            doWhile = False
                            toAdd.append(futureBSNodeID)
                            toRemove.append(BSID)
                        else:
                            moveMultiplier += 0.1

                        if moveMultiplier > 0.5:
                            doWhile = False

                    keepDistance = True
                    if self.returnNoReceptInSavedState() is None or self.returnNoReceptInSavedState() > self.returnNoReception():
                        self.saveState()
                    break

            assert len(toAdd) == len(toRemove)
            self.removeBaseStations(toRemove)
            self.addBaseStations(toAdd)
            self.makeassignment(bucketDistance)

            if self.returnNoReception() == noReceptOnEnter and keepDistance is False:
                internalBucketDistance -= 1
            interruptCounter -= 1


    def makeassignment(self, bucketDistance):
        lenue = len(self.parent.ue)
        lenbs = len(self.parent.bs)
        for BSID in range(lenbs):
            self.parent.bs[BSID].clientList = []

        for NodeID in range(lenue):
            self.parent.ue[NodeID].connectedToBS = None
            if self.parent.ue[NodeID].iamBS is None:
                ue_x_bucket = int(self.parent.ue[NodeID].x / self.parent.bucketResolution)
                ue_y_bucket = int(self.parent.ue[NodeID].y / self.parent.bucketResolution)

                x_min = ue_x_bucket - bucketDistance
                x_max = ue_x_bucket + bucketDistance
                y_min = ue_y_bucket - bucketDistance
                y_max = ue_y_bucket + bucketDistance

                if x_min < 0:
                    x_min = 0
                if x_max > self.parent.XsizeBuckets - 1:
                    x_max = self.parent.XsizeBuckets - 1
                if y_min < 0:
                    y_min = 0
                if y_max > self.parent.YsizeBuckets - 1:
                    y_max = self.parent.YsizeBuckets - 1

                coordsToCheck = []
                for x in range(x_min, x_max + 1):
                    for y in range(y_min, y_max + 1):
                        coordsToCheck.append([x, y])

                bsToCheck = []
                for x, y in coordsToCheck:
                    for BSID in self.bsbuckets[x][y]:
                        bsToCheck.append(BSID)

                maxx = None
                for BSID in bsToCheck:
                    tmp = self.parent.getAttenuationForNetwork(NodeID, BSID, secondArgIsBS=True)
                    if tmp is not None and (maxx is None or maxx < tmp):
                        maxx = tmp
                        self.parent.ue[NodeID].connectedToBS = BSID
                        self.parent.bs[BSID].clientList.append(NodeID)
            else:
                self.parent.ue[NodeID].connectedToBS = self.parent.ue[NodeID].iamBS
                assert self.parent.ue[NodeID].x == self.parent.bs[self.parent.ue[NodeID].iamBS].x and self.parent.ue[NodeID].x == self.parent.bs[self.parent.ue[NodeID].iamBS].x

        for BSID in range(lenbs):
            clientsList = []
            for NodeID in range(lenue):
                if self.parent.ue[NodeID].connectedToBS == BSID:
                    tmp = self.parent.getAttenuationForNetwork(NodeID, BSID, secondArgIsBS=True)
                    clientsList.append([NodeID, tmp])
            clientsList = sorted(clientsList, key=itemgetter(1), reverse=True)
            if self.parent.bs[BSID].maxClients < len(clientsList):
                clientsList = clientsList[self.parent.bs[BSID].maxClients:]
                for cl in clientsList:
                    self.parent.ue[cl[0]].connectedToBS = None

        for NodeID in range(lenue):
            if self.parent.ue[NodeID].connectedToBS is None:
                newBSforNode = self.findBSwithFreeSlots(NodeID, bucketDistance)
                if newBSforNode is not None:
                    self.parent.ue[NodeID].connectedToBS = newBSforNode
                    self.parent.bs[newBSforNode].clientList.append(NodeID)


    def findBSwithFreeSlots(self, NodeID, bucketDistance):
        ue_x_bucket = int(self.parent.ue[NodeID].x / self.parent.bucketResolution)
        ue_y_bucket = int(self.parent.ue[NodeID].y / self.parent.bucketResolution)

        x_min = ue_x_bucket - bucketDistance
        x_max = ue_x_bucket + bucketDistance
        y_min = ue_y_bucket - bucketDistance
        y_max = ue_y_bucket + bucketDistance

        if x_min < 0:
            x_min = 0
        if x_max > self.parent.XsizeBuckets - 1:
            x_max = self.parent.XsizeBuckets - 1
        if y_min < 0:
            y_min = 0
        if y_max > self.parent.YsizeBuckets - 1:
            y_max = self.parent.YsizeBuckets - 1

        coordsToCheck = []
        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                coordsToCheck.append([x, y])

        bsToCheck = []
        for x, y in coordsToCheck:
            for BSID in self.bsbuckets[x][y]:
                bsToCheck.append(BSID)

        maxx = None
        outputBSID = None
        for BSID in bsToCheck:
            if len(self.parent.bs[BSID].clientList) <= self.parent.bs[BSID].maxClients :
                tmp = self.parent.getAttenuationForNetwork(NodeID, BSID, secondArgIsBS=True)
                if tmp is not None and (maxx is None or maxx < tmp):
                    maxx = tmp
                    outputBSID = BSID
        return outputBSID


    def findTooNearBSbyDistance(self, stepDistance):
        bucketDistance = 1
        bsToRemove = []
        bsToAdd = []
        for bs in range(len(self.parent.bs)):
            bs_x_bucket = int(self.parent.bs[bs].x / self.parent.bucketResolution)
            bs_y_bucket = int(self.parent.bs[bs].y / self.parent.bucketResolution)
            coordsToCheck = []


            x_min = bs_x_bucket - bucketDistance
            x_max = bs_x_bucket + bucketDistance
            y_min = bs_y_bucket - bucketDistance
            y_max = bs_y_bucket + bucketDistance

            if x_min < 0:
                x_min = 0
            if x_max > self.parent.XsizeBuckets - 1:
                x_max = self.parent.XsizeBuckets - 1
            if y_min < 0:
                y_min = 0
            if y_max > self.parent.YsizeBuckets - 1:
                y_max = self.parent.YsizeBuckets - 1

            for x in range(x_min, x_max + 1):
                for y in range(y_min, y_max + 1):
                    coordsToCheck.append([x, y])

            bsToCheck = []
            for x, y in coordsToCheck:
                for id in self.bsbuckets[x][y]:
                    if id is not bs:
                        bsToCheck.append(id)

            minID = None
            min = None
            for nod in bsToCheck:
                distance = math.sqrt(((self.parent.bs[bs].x - self.parent.bs[nod].x) ** 2) + ((self.parent.bs[bs].y - self.parent.bs[nod].y) ** 2))
                if distance < self.parent.bucketResolution:
                    if min is None or distance < min:
                        minID = nod
                        min = distance
            if minID is not None:
                bsToRemove.append(minID)
                bsToRemove.append(bs)
                newX = (self.parent.bs[bs].x + self.parent.bs[minID].x) / 2
                newY = (self.parent.bs[bs].y + self.parent.bs[minID].y) / 2
                bsToAdd.append(self.returnNodeIDat(newX, newY))


        self.removeBaseStations(bsToRemove)
        self.addBaseStations(bsToAdd)

    def findTooNearBS(self, stepDistance):
        bucketDistance = 1
        bsToRemove = []
        bsToAdd = []
        for bs in range(len(self.parent.bs)):
            clients = 0
            for u in self.parent.ue:
                if u.connectedToBS == bs:
                    clients += 1

            if clients < self.parent.bs[bs].maxClients*1.5:
                bs_x_bucket = int(self.parent.bs[bs].x / self.parent.bucketResolution)
                bs_y_bucket = int(self.parent.bs[bs].y / self.parent.bucketResolution)
                coordsToCheck = []


                x_min = bs_x_bucket - bucketDistance
                x_max = bs_x_bucket + bucketDistance
                y_min = bs_y_bucket - bucketDistance
                y_max = bs_y_bucket + bucketDistance

                if x_min < 0:
                    x_min = 0
                if x_max > self.parent.XsizeBuckets - 1:
                    x_max = self.parent.XsizeBuckets - 1
                if y_min < 0:
                    y_min = 0
                if y_max > self.parent.YsizeBuckets - 1:
                    y_max = self.parent.YsizeBuckets - 1

                for x in range(x_min, x_max + 1):
                    for y in range(y_min, y_max + 1):
                        coordsToCheck.append([x, y])

                bsToCheck = []
                for x, y in coordsToCheck:
                    for id in self.bsbuckets[x][y]:
                        if id is not bs:
                            bsToCheck.append(id)

                minID = None
                min = None
                for nod in bsToCheck:
                    distance = math.sqrt(((self.parent.bs[bs].x - self.parent.bs[nod].x) ** 2) + ((self.parent.bs[bs].y - self.parent.bs[nod].y) ** 2))
                    if distance < self.parent.bucketResolution:
                        if min is None or distance < min:
                            minID = nod
                            min = distance
                if minID is not None:
                    bsToRemove.append(minID)
                    bsToRemove.append(bs)
                    newX = (self.parent.bs[bs].x + self.parent.bs[minID].x) / 2
                    newY = (self.parent.bs[bs].y + self.parent.bs[minID].y) / 2
                    bsToAdd.append(self.returnNodeIDat(newX, newY))


        self.removeBaseStations(bsToRemove)
        self.addBaseStations(bsToAdd)




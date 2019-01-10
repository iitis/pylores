__author__ = 'Mariusz Slabicki, Konrad Polys, Anna Strzoda'

import math
import csv
import numpy as np

class NetworkDevice:
    """Network device, needed for inheritance"""
    def __init__(self, parent):
        self.x = 0
        self.y = 0
        self.parent = parent

class UE(NetworkDevice):
    """UE"""
    def __init__(self):
        self.ID = 0
        self.connectedToBS = 0
        self.inside = True

    def distanceToBS(self, BS):
        return math.sqrt((self.x-BS.x)**2+(self.y-BS.y)**2)

    def isSeenFromBS(self, BS):
        if BS.omnidirectionalAntenna == True:
            return True
        #returns true if angle allow signal receive, else False
        a_y = BS.y-self.y
        distance_bs_ue = self.distanceToBS(BS)
        if distance_bs_ue == 0 or BS.turnedOn == False:
            return False
        ue_angle_rad = math.acos(a_y/distance_bs_ue)
        ue_angle = math.degrees(ue_angle_rad)
        if self.x <= BS.x:
            ue_angle = 360 - ue_angle
        if BS.angle > ue_angle:
            alpha_diff = BS.angle - ue_angle
        else:
            alpha_diff = ue_angle - BS.angle
        if alpha_diff <= 60 or alpha_diff >= 300:
            return True
        else:
            return False

    def connectToNearestBS(self, BS_vector):
        closestDistance = -1
        foundBS = -1
        for bs in BS_vector:
            if self.isSeenFromBS(bs):
                currentDistance = self.distanceToBS(bs)
                if currentDistance < closestDistance or foundBS == -1:
                    closestDistance = currentDistance
                    foundBS = bs.ID
        self.connectedToBS = foundBS

    def connectToTheBestBS(self, BS_vector, obstacleVector = None):
        theBestSINR = -1000
        foundBS = -1
        for bs in BS_vector:
            if self.isSeenFromBS(bs):
                self.connectedToBS = bs.ID
                currentSINR = self.calculateSINR(BS_vector, obstacleVector)
                if theBestSINR < currentSINR or foundBS == -1:
                    theBestSINR = currentSINR
                    foundBS = bs.ID
        self.connectedToBS = foundBS

    def calculateWallLoss(self, BS_vector, obstacleVector):
        wallLoss = 0
        for obstacle in obstacleVector:
            s10_x = self.x - BS_vector[self.connectedToBS].x
            s10_y = self.y - BS_vector[self.connectedToBS].y
            s32_x = obstacle[2] - obstacle[0]
            s32_y = obstacle[3] - obstacle[1]

            denom = s10_x * s32_y - s32_x * s10_y

            if denom == 0 :
                continue

            denom_is_positive = denom > 0

            s02_x = BS_vector[self.connectedToBS].x - obstacle[0]
            s02_y = BS_vector[self.connectedToBS].y - obstacle[1]

            s_numer = s10_x * s02_y - s10_y * s02_x

            if (s_numer < 0) == denom_is_positive:
                continue

            t_numer = s32_x * s02_y - s32_y * s02_x

            if (t_numer < 0) == denom_is_positive:
                continue

            if (s_numer > denom) == denom_is_positive or (t_numer > denom) == denom_is_positive :
                continue


            wallLoss = wallLoss + obstacle[4]
        return wallLoss

    def calculateReceivedPower(self, pSend, distance):
        R = distance
        lambda_val = 0.142758313333
        a = 4.0
        b = 0.0065
        c = 17.1
        d = 10.8
        s = 15.8

        ht = 40
        hr = 1.5
        f = 2.1
        gamma = a - b*ht + c/ht
        Xf = 6 * math.log10( f/2 )
        Xh = -d * math.log10( hr/2 )

        R0 = 100.0
        R0p = R0 * pow(10.0,-( (Xf+Xh) / (10*gamma) ))

        if(R>R0p):
            alpha = 20 * math.log10( (4*math.pi*R0p) / lambda_val )
            PL = alpha + 10*gamma*math.log10( R/R0 ) + Xf + Xh + s
        else:
            PL = 20 * math.log10( (4*math.pi*R) / lambda_val ) + s

        pRec = pSend - PL
        if(pRec > pSend):
            pRec = pSend
        return pRec


    def calculateNoise(self, bandwidth=20):
        k = 1.3806488 * math.pow(10, -23)
        T = 293.0
        BW = bandwidth * 1000 * 1000
        N = 10*math.log10(k*T) + 10*math.log10(BW)
        return N

    def calculateSINRfor(self, where, BS_vector, obstacleVector = None):
        if (where not in ["in", "out"]):
            raise Exception("wrong argument")

        R = self.distanceToBS(BS_vector[self.connectedToBS])
        if (where=="in"):
            receivedPower_connectedBS=self.calculateReceivedPower(BS_vector[self.connectedToBS].insidePower, R)
        else: # where=="out"
            receivedPower_connectedBS=self.calculateReceivedPower(BS_vector[self.connectedToBS].outsidePower, R)

        a_x = 10
        a_y = 0
        b_x = self.x - BS_vector[self.connectedToBS].x
        b_y = self.y - BS_vector[self.connectedToBS].y
        aob = a_x * b_x + a_y * b_y
        cos_alpha = aob / (R * 10)
        ue_angle_rad = math.acos(cos_alpha)
        ue_angle = math.trunc(math.degrees(ue_angle_rad))

        if self.y - BS_vector[self.connectedToBS].y < 0:
            ue_angle = 359 - ue_angle

        if len(BS_vector[self.connectedToBS].characteristic) != 0:
            receivedPower_connectedBS += float(BS_vector[self.connectedToBS].characteristic[ue_angle])
        if obstacleVector != None:
            receivedPower_connectedBS -= self.calculateWallLoss(BS_vector, obstacleVector)

        myColor = BS_vector[self.connectedToBS].color
        receivedPower_otherBS_mw = 0
        for bs_other in BS_vector:
            if self.connectedToBS == bs_other.ID:
                continue
            if self.isSeenFromBS(bs_other) is False:
                continue

            if (where=="in" and BS_vector[self.connectedToBS].useSFR):
                sum_power_mw = 0
                for i in range(1,4):
                    if (myColor == i):
                        continue
                    if(bs_other.color == i):
                        bs_other_power = bs_other.outsidePower
                    else:
                        bs_other_power = bs_other.insidePower

                    sum_power_mw += math.pow(10, self.calculateReceivedPower(bs_other_power, self.distanceToBS(bs_other))/10)
                receivedPower_one = 10*math.log10(sum_power_mw/2.0)
            else: # where=="out"
                if(bs_other.color == myColor):
                    bs_other_power = bs_other.outsidePower
                else:
                    bs_other_power = bs_other.insidePower
                receivedPower_one = self.calculateReceivedPower(bs_other_power, self.distanceToBS(bs_other))

            if obstacleVector != None:
                receivedPower_one = receivedPower_one - self.calculateWallLoss(BS_vector, obstacleVector)
            receivedPower_otherBS_mw = receivedPower_otherBS_mw + math.pow(10, receivedPower_one/10)

        I_mw = receivedPower_otherBS_mw
        S_mw = math.pow(10, receivedPower_connectedBS/10)
        N_mw = math.pow(10, self.calculateNoise()/10)

        SINR_mw = S_mw/(I_mw+N_mw)
        SINR = 10*math.log10(SINR_mw)

        return SINR

    def calculateSINR(self, BS_vector, obstacleVector = None):
        if BS_vector[self.connectedToBS].useSFR:
            SINRin = self.calculateSINRfor("in", BS_vector, obstacleVector)
            if(SINRin > BS_vector[self.connectedToBS].mi):
                SINR=SINRin
                self.inside = True
            else:
                SINR=self.calculateSINRfor("out", BS_vector, obstacleVector)
                self.inside = False
        else:
            SINR=self.calculateSINRfor("out", BS_vector, obstacleVector)
            self.inside = False
        return SINR

    def calculateMaxThroughputOfTheNode(self, bs_vector, obstacles = None):
        r_i = 0.0
        M_i = 0.0
        sinr = self.calculateSINR(bs_vector, obstacles)
        if sinr < -5.45:
            r_i = 0
            M_i = 1
        elif -5.45 <= sinr < -3.63:
            r_i = 78/1024
            M_i = 4
        elif -3.63 <= sinr < -1.81:
            r_i = 120/1034
            M_i = 4
        elif -1.81 <= sinr < 0:
            r_i = 193/1024
            M_i = 4
        elif 0 <= sinr < 1.81:
            r_i = 308/1024
            M_i = 4
        elif 1.81 <= sinr < 3.63:
            r_i = 449/1024
            M_i = 4
        elif 3.63 <= sinr < 5.45:
            r_i = 602/1024
            M_i = 4
        elif 5.45 <= sinr < 7.27:
            r_i = 378/1024
            M_i = 16
        elif 7.27 <= sinr < 9.09:
            r_i = 490/1024
            M_i = 16
        elif 9.09 <= sinr < 10.90:
            r_i = 616/1024
            M_i = 16
        elif 10.90 <= sinr < 12.72:
            r_i = 466/1024
            M_i = 64
        elif 12.72 <= sinr < 14.54:
            r_i = 567/1024
            M_i = 64
        elif 14.54 <= sinr < 16.36:
            r_i = 666/1024
            M_i = 64
        elif 16.36 <= sinr < 18.18:
            r_i = 772/1024
            M_i = 64
        elif 18.18 <= sinr < 20:
            r_i = 873/1024
            M_i = 64
        elif 20 <= sinr:
            r_i = 948/1024
            M_i = 64

        if bs_vector[self.connectedToBS].useSFR == True:
            if self.inside:
                capacityForUE_ms = r_i * math.log2(M_i) * 12 * 7 * ((200*(2/3))/1)
                capacityForUE_s = capacityForUE_ms * 1000
            else:
                capacityForUE_ms = r_i * math.log2(M_i) * 12 * 7 * ((200*(1/3))/1)
                capacityForUE_s = capacityForUE_ms * 1000
        else:
            capacityForUE_ms = r_i * math.log2(M_i) * 12 * 7 * ((200)/1)
            capacityForUE_s = capacityForUE_ms * 1000
        return capacityForUE_s

class BS(NetworkDevice):
    """Base Station"""
    def __init__(self):
        self.ID = 0
        self.insidePower = 0
        self.outsidePower = 0
        self.mi = 0
        self.Rc = 1666.3793
        self.color = 1
        self.angle = 0
        self.turnedOn = False
        self.type = "MakroCell"
        self.omnidirectionalAntenna = False
        self.useSFR = False
        self.characteristic = []
        self.long = None
        self.lat = None

    def loadCharacteristic(self, filename):
        readCharacteristic = csv.reader(open(filename), delimiter=';', quotechar='|')
        for oneAngle in readCharacteristic:
            self.characteristic.append(float(oneAngle[1]))

class LoRaBS(NetworkDevice):
    """LoRa Base Station"""
    def __init__(self):
        self.ID = 0
        self.power = 0
        self.Rc = 1666.3793
        self.turnedOn = False
        self.type = "MakroCell"
        self.omnidirectionalAntenna = True
        self.characteristic = []
        self.channel = 1
        self.myNodeID = None
        self.long = None
        self.lat = None
        self.height = None
        self.maxClients = 262
        self.clientList = []
        self.deviceType = None
        # self.currClients = 0



    def transmissionTimeSec(self, parameter, sf):
        de = 0
        if sf is 11 or sf is 12:
            de = 1
        bandwidth = 125
        # appPaylodSize = 12
        loraHeaderSize = 13
        preambleSymbols = 8
        explicitHeader = 1
        codingRate = 5
        I18 = pow(2, sf) / (bandwidth * 1000) * 1000
        I19 = (preambleSymbols + 4.25) * I18
        roundUp = math.ceil(((8 * (parameter + loraHeaderSize) - 4 * sf + 28 + 16 - 20 * (1 - explicitHeader)) / (4 * (sf - 2 * de)))) * codingRate
        maximum = max(roundUp, 0)
        I20 = 8 + maximum
        I21 = I20 * I18
        formula = I19 + I21
        return formula/1000.0

    def returnMaxClientsPerGW(self, p, tw, payload, sf):
        t = self.transmissionTimeSec(payload, sf)
        nominator = math.log(p, 10)
        denominator = math.log((1 - ((2 * t) / tw)), 10)
        n = 1 + nominator / denominator
        return math.floor(n)#*8


class Node(UE):
    """LoRa Node"""
    def __init__(self, parent):
        self.parent = parent
        self.connectedToBS = None
        self.iamBS = None
        self.SF = 9
        self.channel = 1
        self.power = 0
        self.noise = -152.96139146871246
        self.long = None
        self.lat = None
        self.height = None

    def returnSpreadingFactor(self, SINR, minSINR):
        if SINR is None or SINR < minSINR:
            return None, None
        sf = 12
        w = 1.0
        for i in range(5):
            if SINR >= minSINR + i * 3 + 3:
                sf -= 1
                w /= 2.0
            else:
                break
        return sf, w

    def calculateSINR(self, BS_vector, obstacleVector = None):
        SINR=self.calculateSINRfor(BS_vector, obstacleVector)
        return SINR

    def calculateSINRfor(self, BS_vector, obstacleVector = None):

        R = self.distanceToBS(BS_vector[self.connectedToBS])
        receivedPower_connectedBS=self.calculateReceivedPower(BS_vector[self.connectedToBS].power, R)

        a_x = 10
        a_y = 0
        b_x = self.x - BS_vector[self.connectedToBS].x
        b_y = self.y - BS_vector[self.connectedToBS].y
        aob = a_x * b_x + a_y * b_y
        cos_alpha = aob / (R * 10)
        ue_angle_rad = math.acos(cos_alpha)
        ue_angle = math.trunc(math.degrees(ue_angle_rad))

        if self.y - BS_vector[self.connectedToBS].y < 0:
            ue_angle = 359 - ue_angle

        if len(BS_vector[self.connectedToBS].characteristic) != 0:
            receivedPower_connectedBS += float(BS_vector[self.connectedToBS].characteristic[ue_angle])
        if obstacleVector != None:
            receivedPower_connectedBS -= self.calculateWallLoss(BS_vector, obstacleVector)

        myChannel = BS_vector[self.connectedToBS].channel
        receivedPower_otherBS_mw = 0
        for bs_other in BS_vector:
            if self.connectedToBS == bs_other.ID:
                continue
            if self.isSeenFromBS(bs_other) is False:
                continue

            receivedPower_one = self.calculateReceivedPower(bs_other.power, self.distanceToBS(bs_other))

            if obstacleVector != None:
                receivedPower_one = receivedPower_one - self.calculateWallLoss(BS_vector, obstacleVector)
            receivedPower_otherBS_mw = receivedPower_otherBS_mw + math.pow(10, receivedPower_one/10)

        I_mw = receivedPower_otherBS_mw
        S_mw = math.pow(10, receivedPower_connectedBS/10)
        N_mw = math.pow(10, self.calculateNoise()/10)

        SINR_mw = S_mw/(I_mw+N_mw)
        SINR = 10*math.log10(SINR_mw)

        return SINR

    def calculateReceivedPower1(self, pSend, distance, height): #SUI
        R = distance
        if int(R) == 0:
            return  pSend
        lambda_val = 0.142758313333
        a = 4.0
        b = 0.0065
        c = 17.1
        d = 10.8
        s = 15.8

        ht = height #15
        hr = self.height #1.5
        f = 0.868
        gamma = a - b*ht + c/ht
        Xf = 6 * math.log10( f/2 )
        Xh = -d * math.log10( hr/2 )

        R0 = 100.0
        R0p = R0 * pow(10.0,-( (Xf+Xh) / (10*gamma) ))

        if(R>R0p):
            alpha = 20 * math.log10( (4*math.pi*R0p) / lambda_val )
            PL = alpha + 10*gamma*math.log10( R/R0 ) + Xf + Xh + s
        else:
            PL = 20 * math.log10( (4*math.pi*R) / lambda_val ) + s

        pRec = pSend - PL
        if(pRec > pSend):
            pRec = pSend
        return pRec

    def calculateReceivedPower2(self, pSend, distance): #LogNormal
        if int(distance) == 0:
            return  pSend

        gamma = 2.08
        sigma = 0 #3.57
        d0 = 40
        PL_d0_db = 127.41
        PL = PL_d0_db + 10 * gamma * math.log10( distance / d0) + np.random.normal(0.0,sigma)

        pRec = pSend - PL
        if(pRec > pSend):
            pRec = pSend
        return pRec

    def calculateReceivedPower3(self, pSend, distance, height):  #Okumura https://www.wiley.com/legacy/wileychi/molisch/supp2/appendices/c07_Appendices.pdf
        if int(distance) == 0:
            return  pSend

        ht = height #15
        hr = self.height #1.5

        ahm = (1.1*math.log10(868) - 0.7) * hr - (1.56*math.log10(868) - 0.8)
        A = 69.55 + 26.16*math.log10(868) - 13.82*math.log10(ht) - ahm
        B = 44.9 - 6.55*math.log10(ht)
        C = 0
        PL = A + B * math.log10( distance / 1000.0 ) + C

        pRec = pSend - PL
        if(pRec > pSend):
            pRec = pSend
        return pRec

    def calculateReceivedPower4(self, pSend, distance):  #Okumura lite
        if int(distance) == 0:
            return  pSend

        K1 = 127.5
        K2 = 35.2
        PL = K1 + K2 * math.log10( distance / 1000.0 )

        pRec = pSend - PL
        if(pRec > pSend):
            pRec = pSend

        return pRec


    def calculateReceivedPower(self, pSend, distance, height):
        if self.parent.propagationModel == "SUI":
            return self.calculateReceivedPower1(pSend, distance, height)
        elif self.parent.propagationModel == "Log-distance":
            return self.calculateReceivedPower2(pSend, distance)
        elif self.parent.propagationModel == "Okumura-Hata":
            return self.calculateReceivedPower3(pSend, distance, height)
        elif self.parent.propagationModel == "Okumura-Hata s.":
            return self.calculateReceivedPower4(pSend, distance)
        else:
            assert "Wrong propagation model"


    def calculateSINRforNode(self, Node, att, power=None, R=None,):
        if Node is not None:
            R = self.distanceToBS(Node)
            receivedPower_connectedBS = self.calculateReceivedPower(Node.power, R, Node.height)
            power = Node.power
        else:
            receivedPower_connectedBS = self.calculateReceivedPower(power, R, self.height)
        return receivedPower_connectedBS

    def calculateSINRforNode2(self, Node, att, power=None, R=None,):
        if Node is not None:
            R = self.distanceToBS(Node)
            receivedPower_connectedBS = self.calculateReceivedPower(Node.power, R)
            power = Node.power
        else:
            receivedPower_connectedBS = self.calculateReceivedPower(power, R)

        # antennasGain = 6
        # receivedPower_connectedBS += antennasGain

        S_mw = math.pow(10, receivedPower_connectedBS/10)
        # N_mw = math.pow(10, self.calculateNoise(0.125)/10)
        #self.noise = -72 - att
        self.noise = -37 - (power*2.5) - att


        Nnn = math.fabs(self.noise * (R*0.71)/2500.0) - math.fabs(self.noise)
        N_mw = math.pow(10, (self.noise + Nnn) / 10)

        SINR_mw = S_mw/(N_mw)
        SINR = 10*math.log10(SINR_mw)

        # if R>2500 and SINR>-20:
        #     print(R, SINR)

        return SINR
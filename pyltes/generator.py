__author__ = 'Mariusz Slabicki, Konrad Połys'

import math
import csv
import random
from pyltes import devices
from pyltes import network
from copy import deepcopy
from xml.dom.minidom import parseString
import random
import sys
import tkinter
from tkinter import messagebox
import datetime
currentDate = datetime.datetime.now()




class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Generator:
    """Class that generates network deployment"""
    def __init__(self, parent):
        self.parent = parent

    def create1BSnetwork(self, radius):

        H_hex = 2 * radius
        W_hex = radius * math.sqrt(3)
        self.parent.radius = radius
        self.parent.constraintAreaMaxX = 2 * W_hex
        self.parent.constraintAreaMaxY = H_hex + 1.5 * radius
        if type(self.parent) is network.LoRaNetwork:
            bs = devices.LoRaBS()
        else:
            bs = devices.BS()
        bs.ID = 0
        bs.turnedOn = True
        bs.x = self.parent.constraintAreaMaxX/2
        bs.y = self.parent.constraintAreaMaxY/2
        self.parent.bs.append(bs)

    def createHexagonalBSdeployment(self, radius, numberOfBS = 36, omnidirectionalAntennas = False, SFR = False):
        # print("Jestem w createHexagonalBSdeployment")
        d_x = math.sqrt(3)/2 * radius
        d_y = radius/2
        H_hex = 2 * radius
        W_hex = radius * math.sqrt(3)
        self.parent.radius = radius
        if numberOfBS == 36:
            self.parent.constraintAreaMaxX = 6.5 * W_hex
            self.parent.constraintAreaMaxY = 3 * H_hex + 3.5 * radius
        if numberOfBS == 75:
            self.parent.constraintAreaMaxX = 8 * W_hex
            self.parent.constraintAreaMaxY = 4 * H_hex + 7.5 * radius
        if numberOfBS == 90:
            self.parent.constraintAreaMaxX = 9.5 * W_hex
            self.parent.constraintAreaMaxY = 4 * H_hex + 7.5 * radius
        if numberOfBS == 108:
            self.parent.constraintAreaMaxX = 9.5 * W_hex
            self.parent.constraintAreaMaxY = 6 * H_hex + 6.5 * radius
        for i in range(0, numberOfBS):
            bs = devices.BS()
            bs.ID = i
            bs.turnedOn = True
            bs.omnidirectionalAntenna = omnidirectionalAntennas
            bs.useSFR = SFR
            self.parent.bs.append(bs)

        if numberOfBS == 36:
            numberOfRows = 3
            numberOfColumns = 4
            multiplier = 12
        if numberOfBS == 75:
            numberOfRows = 5
            numberOfColumns = 5
            multiplier = 15
        if numberOfBS == 90:
            numberOfRows = 5
            numberOfColumns = 6
            multiplier = 18
        if numberOfBS == 108:
            numberOfRows = 6
            numberOfColumns = 6
            multiplier = 18

        for row_number in range(0, numberOfRows):
            for column_number  in range(0, numberOfColumns):
                for sector_nb in range(0, 3):
                    self.parent.bs[multiplier*row_number + 3*column_number + sector_nb].x = (3*(column_number+1)-1) * d_x
                    self.parent.bs[multiplier*row_number + 3*column_number + sector_nb].y = (1 + row_number) * H_hex - d_y + row_number * radius
                    self.parent.bs[multiplier*row_number + 3*column_number + sector_nb].angle = sector_nb * 120
                    if column_number % 2 == 1:
                        self.parent.bs[multiplier*row_number + 3*column_number + sector_nb].x = (3*(column_number+1)-1) * d_x
                        self.parent.bs[multiplier*row_number + 3*column_number + sector_nb].y += d_y
                        self.parent.bs[multiplier*row_number + 3*column_number + sector_nb].angle += 60

    def createHoneycombBSdeployment(self, radius, numberOfBS = 36, omnidirectionalAntennas = False, SFR = False):
        """This function creates a honeycomb deployment with any number of BaseStations eg. 2 or 9
        In case of sector antennas the number will be increased to by multiply of 3 because it's
        assumed that there are 3 BaseStation at the spot with 120 degress antennas """
        # print("Jestem w createHoneycombBSdeployment")
        if not omnidirectionalAntennas:
            if numberOfBS % 3 == 1:
                print("Incorrect number of BaseStations for sector antennas. Increasing the number.")
            numberOfBS = math.ceil(numberOfBS / 3.0)

        x = int(math.ceil(math.sqrt(numberOfBS)))
        y = int(math.floor(math.sqrt(numberOfBS)))
        if x*y < numberOfBS:
            y += 1

        self.parent.constraintAreaMaxX = x * radius + 0.5 * radius
        self.parent.constraintAreaMaxY = y * radius
        self.parent.radius = radius

        xc = 0
        yc = 0
        xo = 1

        for i in range(0, numberOfBS):
            sectors = 1
            if not omnidirectionalAntennas:
                sectors = 3

            for j in range(sectors):
                bs = devices.BS()
                bs.ID = i*sectors + j
                bs.turnedOn = True
                bs.omnidirectionalAntenna = omnidirectionalAntennas
                bs.useSFR = SFR
                bs.Rc = radius
                bs.angle = 120 * j
                bs.x = (0.5 * radius) * (xc + 1) + (0.5 * radius) * xo
                bs.y = (0.5 * radius) * (yc + 1)
                self.parent.bs.append(bs)
            xc += 2
            if xc > 2*x-1:
                xc = 0
                yc +=2
                if (yc/2) % 2 == 1:
                    xo = 0
                else:
                    xo = 1

    def loadDeploymentFromFile(self, filename):
        # print("Jestem w loadDeploymentFromFile")
        self.parent.constraintAreaMaxX = 3000
        self.parent.constraintAreaMaxY = 5000
        network = csv.reader(open(filename), delimiter=';', quotechar='|')
        bs_number = 0
        for row in network:
            bs = devices.BS()
            bs.x = float(row[1])
            bs.y = float(row[2])
            bs.x = bs.x - 8500
            bs.y = bs.y - 11000
            bs.ID = bs_number
            bs_number +=1
            bs.angle = float(row[4])
            bs.turnedOn = True
            if (len(row)>12):
                bs.color = int(row[12])
            else:
                bs.color = 1
            self.parent.bs.append(bs)

    def loadNetworkAndObstaclesFromFile(self, filename):
        # print("Jestem w loadNetworkAndObstaclesFromFile")
        network = csv.reader(open(filename), delimiter=';', quotechar='|')
        for row in network:
            if row[0] == "x_size_real":
                self.parent.constraintAreaMaxX = float(row[1])
            if row[0] == "y_size_real":
                self.parent.constraintAreaMaxY = float(row[1])
            if row[0] == "x_size_map":
                x_size_map = float(row[1])
            if row[0] == "y_size_map":
                y_size_map = float(row[1])
            if row[0] == "wall":
                obstacle = []
                obstacle.append(float(row[1])/x_size_map*self.parent.constraintAreaMaxX)
                obstacle.append(self.parent.constraintAreaMaxY - float(row[2])/y_size_map*self.parent.constraintAreaMaxY)
                obstacle.append(float(row[3])/x_size_map*self.parent.constraintAreaMaxX)
                obstacle.append(self.parent.constraintAreaMaxY - float(row[4])/y_size_map*self.parent.constraintAreaMaxY)
                obstacle.append(float(row[5]))
                self.parent.obstacles.append(obstacle)
            if row[0] == "bs":
                bs = devices.BS()
                bs.x = float(float(row[1])/x_size_map*self.parent.constraintAreaMaxX)
                bs.y = float(self.parent.constraintAreaMaxY - float(row[2])/y_size_map*self.parent.constraintAreaMaxY)
                bs.ID = int(row[3])
                bs.turnedOn = True
                self.parent.bs.append(bs)

    def insertUEingrid(self, numberOfDevices):
        # print("Jestem w insertUEingrid")
        numberOfNodesInRow = math.ceil(math.sqrt(numberOfDevices))
        number = 0
        x_step = int(self.parent.constraintAreaMaxX)/numberOfNodesInRow
        y_step = int(self.parent.constraintAreaMaxY)/numberOfNodesInRow
        for x_pos in range(0, numberOfNodesInRow):
            for y_pos in range(0, numberOfNodesInRow):
                ue = devices.UE()
                ue.ID = number
                ue.x = 0.5*x_step + (x_pos*x_step)
                ue.y = 0.5*y_step + (y_pos*y_step)
                self.parent.ue.append(ue)
                number = number+1

    def insertUErandomly(self, numberOfDevices):
        # print("Jestem w insertUErandomly")
        number = 0
        for i in range(0, numberOfDevices):
            ue = devices.UE()
            ue.ID = number
            ue.x = random.uniform(0, self.parent.constraintAreaMaxX)
            ue.y = random.uniform(0, self.parent.constraintAreaMaxY)
            self.parent.ue.append(ue)
            number = number+1

    def loadNodesFromFile(self, filename):
        # print("Jestem w loadNodesFromFile")
        file = open(filename)
        file.readline()
        networkcsv = csv.reader(file, delimiter=';')
        lat_min = 999
        long_min = 999
        for row in networkcsv:
            if len(row) == 5:
                lat = float(row[1].replace(',','.'))
                long = float(row[2].replace(',','.'))
                if int(lat) == 0 or int(long) != 0:
                    if lat < lat_min: lat_min = lat
                    if long < long_min: long_min = long
        file.seek(0)
        file.readline()
        # print(lat_min, long_min)
        # print("min maks znaleziony")
        R = 6371e3
        number = 0
        max_x = 0
        max_y = 0
        for row in networkcsv:
            if len(row) == 5:
                lat = float(row[1].replace(',','.'))
                long = float(row[2].replace(',','.'))
                height = float(row[3].replace(',','.'))
                dtype = int(row[4])
                if int(lat) == 0 or int(long) != 0:
                    fi1 = math.radians(lat)
                    fi2 = math.radians(lat_min)
                    deltafi = math.radians(lat - lat_min)
                    deltalambda = math.radians(long - long_min)

                    a = math.sin(deltafi / 2.0) * math.sin(deltafi / 2.0) + math.cos(fi1) * math.cos(fi2) * math.sin(
                        deltalambda / 2.0) * math.sin(deltalambda / 2.0)
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                    d = R * c

                    fi1 = math.radians(lat)
                    fi2 = math.radians(lat_min)
                    deltafi = math.radians(lat - lat_min)
                    deltalambda = math.radians(long - long)

                    a = math.sin(deltafi / 2.0) * math.sin(deltafi / 2.0) + math.cos(fi1) * math.cos(fi2) * math.sin(
                        deltalambda / 2.0) * math.sin(deltalambda / 2.0)
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                    y = R * c

                    fi1 = math.radians(lat)
                    fi2 = math.radians(lat)
                    deltafi = math.radians(lat - lat_min)
                    deltalambda = math.radians(long - long_min)

                    a = math.sin(deltafi/2.0) * math.sin(deltafi/2.0) + math.cos(fi1) * math.cos(fi2) * math.sin(deltalambda/2.0) * math.sin(deltalambda/2.0)
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                    x = R * c

                    if type(self.parent) is network.LoRaNetwork:
                        ue = devices.Node(self.parent)
                    else:
                        ue = devices.UE(self.parent)

                    if max_x < x: max_x = x
                    if max_y < y: max_y = y

                    ue.x = x
                    ue.y = y
                    ue.lat = lat
                    ue.long = long
                    ue.height = height
                    ue.type = dtype
                    ue.ID = number
                    self.parent.ue.append(ue)
                    number = number + 1
        # print(len(self.parent.ue), "wspolrzednych dodane, teraz kubelki")
                # print("lat", lat, "long", long, "d", round(d,2), "x", round(x,2), "y", round(y,2))
        self.parent.constraintAreaMaxX = int(max_x + 0.05 * max_x)
        self.parent.constraintAreaMaxY = int(max_y + 0.05 * max_y)

        # print("X", self.parent.constraintAreaMaxX / 1000, "Y", self.parent.constraintAreaMaxY / 1000)
        for ue in self.parent.ue:
            # None
            self.addToBucket(ue.ID, ue.x, ue.y)
        # print("kubelki dodane")
        file.close()
        # print("lat min", lat_min, "long min", long_min)

    def removeBSs(self):
        self.parent.bs = []
        # print("Jestem w removeBSs")

class LoRaGenerator (Generator):
    """Class that generates network deployment"""
    def __init__(self,parent):
        self.parent = parent

    def createHoneycombBSdeployment(self, radius, numberOfBS = 2, omnidirectionalAntennas = True):
        # print("Jestem w createHoneycombBSdeployment")
        x = int(math.ceil(math.sqrt(numberOfBS)))
        y = int(math.floor(math.sqrt(numberOfBS)))
        if x*y < numberOfBS:
            y += 1

        self.parent.constraintAreaMaxX = x * radius + 0.5 * radius
        self.parent.constraintAreaMaxY = y * radius
        self.parent.radius = radius

        xc = 0
        yc = 0
        xo = 1

        for i in range(0, numberOfBS):
            sectors = 1
            if not omnidirectionalAntennas:
                sectors = 3

            for j in range(sectors):
                bs = devices.LoRaBS()
                bs.ID = i*sectors + j
                bs.turnedOn = True
                bs.omnidirectionalAntenna = omnidirectionalAntennas
                bs.Rc = radius
                bs.x = (0.5 * radius) * (xc + 1) + (0.5 * radius) * xo
                bs.y = (0.5 * radius) * (yc + 1)
                self.parent.bs.append(bs)
            xc += 2
            if xc > 2*x-1:
                xc = 0
                yc +=2
                if (yc/2) % 2 == 1:
                    xo = 0
                else:
                    xo = 1

    def addToBucket(self, ID, x, y):
        resolution = self.parent.bucketResolution

        if self.parent.buckets is None:

            x_bucket = math.ceil(self.parent.constraintAreaMaxX / resolution)
            y_bucket = math.ceil(self.parent.constraintAreaMaxY / resolution)
            #self.parent.buckets = [ [[]] * y_bucket ] * x_bucket

            self.parent.buckets = []
            for rx in range(x_bucket):
                self.parent.buckets.append([])
                for ry in range(y_bucket):
                    self.parent.buckets[rx].append([])
            self.parent.XsizeBuckets = x_bucket
            self.parent.YsizeBuckets = y_bucket

        xx = int(x/resolution)
        yy = int(y/resolution)
        # print("ID",ID, "xx,yy:", xx, yy, "\t\tres:", resolution, "x,y:", x, y)
        self.parent.buckets[xx][yy].append(ID)

    def insertUEingrid(self, numberOfDevices):

        numberOfNodesInRow = math.ceil(math.sqrt(numberOfDevices))
        number = 0
        x_step = int(self.parent.constraintAreaMaxX)/numberOfNodesInRow
        y_step = int(self.parent.constraintAreaMaxY)/numberOfNodesInRow
        for x_pos in range(0, numberOfNodesInRow):
            for y_pos in range(0, numberOfNodesInRow):
                ue = devices.Node(self.parent)
                ue.ID = number
                ue.height = 15
                ue.type = 0
                ue.x = 0.5*x_step + (x_pos*x_step)
                ue.y = 0.5*y_step + (y_pos*y_step)

                self.addToBucket(ue.ID, ue.x, ue.y)
                self.parent.ue.append(ue)
                number = number+1

    def insertUErandomly(self, numberOfDevices, seed = 131313):

        number = 0
        random.seed(seed)

        for i in range(0, numberOfDevices):
            ue = devices.Node(self.parent)
            ue.ID = number
            ue.height = 15
            ue.type = 0
            ue.x = random.uniform(0, self.parent.constraintAreaMaxX)
            ue.y = random.uniform(0, self.parent.constraintAreaMaxY)
            
            # print("uerandomly\tid:", ue.ID, "x,y:", ue.x, ue.y)
            self.addToBucket(ue.ID, ue.x, ue.y)
            self.parent.ue.append(ue)
            number = number+1

    def insertUErandomly_(self, numberOfDevices, seed = 131313):

        number = 0
        random.seed(seed)
        rows = 5
        xr = self.parent.constraintAreaMaxX / rows
        yr = self.parent.constraintAreaMaxY / rows

        for i in range(0, numberOfDevices):
            ue = devices.Node()
            ue.ID = number
            ue.x = random.uniform(0, self.parent.constraintAreaMaxX)
            ue.y = random.uniform(0, self.parent.constraintAreaMaxY)
            ey = int(ue.y / yr)
            if ey % 2 and ((ue.x < 0.5 * xr) or (ue.x > self.parent.constraintAreaMaxX - 0.5 * xr)):
                None
            else:
                self.parent.ue.append(ue)
                self.addToBucket(ue.ID, ue.x, ue.y)
                number = number+1

    def loadNodesFromKMLFile(self, filename, numberOfDevices):


            ppk = PointPolygonKML(self)
            xyp = ppk.generatePointsFromKML(filename, numberOfDevices)

            lat_min = 999
            long_min = 999

            for row in xyp:
                if row.x < long_min: long_min = row.x
                if row.y < lat_min: lat_min = row.y

            R = 6371e3
            number = 0
            max_x = 0
            max_y = 0

            for row in xyp:
                fi1 = math.radians(row.y)
                fi2 = math.radians(lat_min)
                deltafi = math.radians(row.y - lat_min)
                deltalambda = math.radians(row.x - long_min)

                a = math.sin(deltafi / 2.0) * math.sin(deltafi / 2.0) + math.cos(fi1) * math.cos(fi2) * math.sin(
                    deltalambda / 2.0) * math.sin(deltalambda / 2.0)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                d = R * c

                fi1 = math.radians(row.y)
                fi2 = math.radians(lat_min)
                deltafi = math.radians(row.y - lat_min)
                deltalambda = math.radians(row.x - row.x)

                a = math.sin(deltafi / 2.0) * math.sin(deltafi / 2.0) + math.cos(fi1) * math.cos(fi2) * math.sin(
                    deltalambda / 2.0) * math.sin(deltalambda / 2.0)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                y = R * c

                fi1 = math.radians(row.y)
                fi2 = math.radians(row.y)
                deltafi = math.radians(row.y - lat_min)
                deltalambda = math.radians(row.x - long_min)

                a = math.sin(deltafi / 2.0) * math.sin(deltafi / 2.0) + math.cos(fi1) * math.cos(fi2) * math.sin(
                    deltalambda / 2.0) * math.sin(deltalambda / 2.0)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                x = R * c

                if type(self.parent) is network.LoRaNetwork:
                    ue = devices.Node(self.parent)
                else:
                    ue = devices.UE(self.parent)

                if max_x < x: max_x = x
                if max_y < y: max_y = y
                print("gen", number, x, y, row.x, row.y)
                ue.x = x
                ue.y = y
                ue.lat = row.y
                ue.long = row.x
                ue.height = 15
                ue.ID = number
                self.parent.ue.append(ue)
                number = number + 1
            # print(len(self.parent.ue), "wspolrzednych dodane, teraz kubelki")
            # print("lat", lat, "long", long, "d", round(d,2), "x", round(x,2), "y", round(y,2))
            self.parent.constraintAreaMaxX = int(max_x + 0.05 * max_x)
            self.parent.constraintAreaMaxY = int(max_y + 0.05 * max_y)


            for ue in self.parent.ue:
                self.addToBucket(ue.ID, ue.x, ue.y)




class PointPolygonKML:


    def __init__(self,parent):
        self.parent = parent


    def generate_points(self, points, noofpoints):

        output_points = []
        added_points = 0

        if len(points) == 0:

            return output_points

        else:
            min_x = max_x = points[0].x
            min_y = max_y = points[0].y

            for p in points:
                if p.x < min_x:
                    min_x = p.x
                if p.x > max_x:
                    max_x = p.x
                if p.y < min_y:
                    min_y = p.y
                if p.y > max_y:
                    max_y = p.y

            while added_points < noofpoints:
                random_point = Point(0, 0)
                random_point.x = random.uniform(min_x, max_x)
                random_point.y = random.uniform(min_y, max_y)

                if_point_in_polygon = self.point_in_polygon(points, random_point)

                if if_point_in_polygon:
                    output_points.append(random_point)
                    added_points += 1

            return output_points


    def findPointGivenKML(self, location):

        points = []

        try:
            file = open(location, encoding="utf8")
            data = file.read()
            file.close()
            dom = parseString(data)
        except:
            print("[", str(currentDate), "] Error! Failure to open the file.")

        try:
            coordinates = dom.getElementsByTagName('coordinates')[0].firstChild.nodeValue
            word = coordinates.strip().split(' ')
        except:
            print("[", str(currentDate), "] Error! No coordinates in KML file.")
            return points


        for i in word:
            j = i.split(',')
            topPoints = Point(0, 0)
            topPoints.x = float(j[0])
            topPoints.y = float(j[1])
            print(topPoints.x, ', ', topPoints.y)
            points.append(topPoints)

        return points


    def point_in_polygon(self, points, rp):


        oddnodes = False
        j = len(points) - 1
        for i in range(0, len(points)):
            if (((points[i].y > rp.y) != (points[j].y > rp.y)) and
                    (rp.x < ((points[j].x - points[i].x) * (rp.y - points[i].y) / (points[j].y - points[i].y) +
                                points[i].x))):
                oddnodes = not oddnodes
            j = i
        return oddnodes


    def generatePointsFromKML(self, fileName, noofpoints):

        #location = 'C:/Users/Anna/Desktop/area.kml'
        pointsFromKMLFile = self.findPointGivenKML(fileName)
        drawPointsInPolygon = self.generate_points(pointsFromKMLFile, noofpoints)
        # print(len(drawPointsInPolygon))
        return drawPointsInPolygon

#        for k in drawPointsInPolygon:
#            print(k.x, ',', k.y)


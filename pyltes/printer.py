__author__ = 'Mariusz'

from pyltes import devices
from pyltes import network
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import math

class Printer:
    """Class that prints network deployment"""
    def __init__(self,parent):
        self.parent = parent

    def drawHistogramOfUEThroughput(self, filename):
        thr_vector = self.parent.returnRealUEThroughputVectorRR()
        thr_MBit = [x / (1024*1024) for x in thr_vector]
        plt.hist(thr_MBit)
        # plt.savefig(filename, format="pdf", dpi=300)
        plt.savefig(filename+".png", format="png", dpi=300)
        plt.clf()

    def drawHistogramOfSetPowers(self, filename):
        power_vector = []
        for bs in self.parent.bs:
            power_vector.append(bs.outsidePower)
        plt.hist(power_vector, bins=np.arange(self.parent.minFemtoTxPower, self.parent.maxTxPower + 1, 1))
        plt.xlim(0, 100)
        # plt.savefig(filename, format="pdf", dpi=300)
        plt.savefig(filename+".png", format="png", dpi=300)
        plt.clf()

    def drawNetwork(self, filename, BS=True, UE=True, links=True, obstacles=True, fillMethod="SINR", colorMap = None, drawLegend=True, tilesInLine = 100, figSize = (8, 8), colorMinValue = None, colorMaxValue = None, outputFileFormat = ["png"]):
        if len(self.parent.ue) == 0:
            return
        main_draw = plt.figure(1, figsize=figSize)
        ax = main_draw.add_subplot(111)
        if fillMethod == "SINR":
            if colorMap == None:
                cm = plt.cm.get_cmap("viridis")
            else:
                cm = plt.cm.get_cmap(colorMap)
            if type(self.parent) is network.LoRaNetwork:
                ue = devices.Node(self.parent)
            else:
                ue = devices.UE(self.parent)
            imageMatrix = np.zeros((tilesInLine, tilesInLine))
            d_x = round(self.parent.constraintAreaMaxX/tilesInLine)
            d_y = round(self.parent.constraintAreaMaxY/tilesInLine)
            for x in range(0, tilesInLine):
                for y in range(0, tilesInLine):
                    ue.x = x * d_x
                    ue.y = y * d_y
                    ue.connectToTheBestBS(self.parent.bs, self.parent.obstacles)
                    SINR = ue.calculateSINR(self.parent.bs, self.parent.obstacles)
                    imageMatrix[y][x] = SINR
            if colorMinValue != None:
                colorMin = colorMinValue
            else:
                colorMin = imageMatrix.min()
            if colorMaxValue != None:
                colorMax = colorMaxValue
            else:
                colorMax = imageMatrix.max()
            image = plt.imshow(imageMatrix, vmin=colorMin, vmax=colorMax, origin='lower', extent=[0, self.parent.constraintAreaMaxX, 0, self.parent.constraintAreaMaxY], interpolation='nearest', cmap=cm)
            if drawLegend == True:
                from mpl_toolkits.axes_grid1 import make_axes_locatable
                divider = make_axes_locatable(ax)
                cax1 = divider.append_axes("right", size="5%", pad=0.05)
                cbar = plt.colorbar(image, cax = cax1)
                #cbar.set_clim(-60, 50)
                #cbar.ax.set_yticklabels(['0','1','2','>3'])
                #cbar.set_label('# of contacts', rotation=270)

        elif fillMethod == "Sectors":
            if colorMap == None:
                cm = plt.cm.get_cmap("Paired")
            else:
                cm = plt.cm.get_cmap(colorMap)
            if type(self.parent) is network.LoRaNetwork:
                ue = devices.Node()
            else:
                ue = devices.UE()
            imageMatrix = np.zeros((tilesInLine, tilesInLine))
            d_x = round(self.parent.constraintAreaMaxX/tilesInLine)
            d_y = round(self.parent.constraintAreaMaxY/tilesInLine)
            for x in range(0, tilesInLine):
                for y in range(0, tilesInLine):
                    RSSI_best = -1000
                    BS_best = -1
                    for bs in self.parent.bs:
                        ue.x = x * d_x
                        ue.y = y * d_y
                        if ue.isSeenFromBS(bs) == False:
                            continue
                        ue.connectedToBS = bs.ID
                        temp_RSSI = ue.calculateSINR(self.parent.bs)
                        if temp_RSSI > RSSI_best:
                            RSSI_best = temp_RSSI
                            BS_best = bs.ID

                    imageMatrix[y][x] = BS_best
            plt.imshow(imageMatrix, origin='lower', extent=[0, self.parent.constraintAreaMaxX, 0, self.parent.constraintAreaMaxY], interpolation='nearest', cmap=cm)

        elif fillMethod == "Devices":
            if colorMap == None:
                cm = plt.cm.get_cmap("Paired")
            else:
                cm = plt.cm.get_cmap(colorMap)
            if type(self.parent) is network.LoRaNetwork:
                ue = devices.Node(self.parent)
            else:
                ue = devices.UE(self.parent)
            imageMatrix = np.zeros((tilesInLine, tilesInLine))
            # print(self.parent.constraintAreaMaxX, tilesInLine)
            d_x = round(self.parent.constraintAreaMaxX/tilesInLine)
            d_y = round(self.parent.constraintAreaMaxY/tilesInLine)
            plt.imshow(imageMatrix, origin='lower', extent=[0, self.parent.constraintAreaMaxX, 0, self.parent.constraintAreaMaxY], interpolation='nearest', cmap=cm)

        ax.text(10,15,str(int(self.parent.constraintAreaMaxX))+" x "+str(int(self.parent.constraintAreaMaxY)), fontsize=5, color="white")
        ax.text(10,255,"BS: " + str(len(self.parent.bs)) + ", NODE: " + str(len(self.parent.ue)), fontsize=5, color="white")

        if BS == True:
            # bs_x_locations = []
            # bs_y_locations = []
            for bs in self.parent.bs:
                # print("BS", round(bs.x), round(bs.y))
                # bs_x_locations.append(bs.x)
                # bs_y_locations.append(bs.y)
                ax.plot(bs.x, bs.y, 'r^', color="black", markersize=20)
                ax.text(bs.x, bs.y, str(bs.ID), fontsize=15, color="yellow")


                # ax.plot(bs_x_locations, bs_y_locations, 'r^', color="black", markersize=20)

        if UE == True:
            # ue_x_locations = []
            # ue_y_locations = []
            # for ue in self.parent.ue:
            #     ue_x_locations.append(ue.x)
            #     ue_y_locations.append(ue.y)
            # ax.plot(ue_x_locations, ue_y_locations, '.', color="white", markersize=10)
            for ue in self.parent.ue:
                ccolor = "white"
                if ue.connectedToBS is not None:
                    modres = ue.connectedToBS % 4
                    if modres == 0:
                        ccolor = "red"
                    elif modres == 1:
                        ccolor = "blue"
                    elif modres == 2:
                        ccolor = "green"
                    elif modres == 3:
                        ccolor = "orange"
                ax.plot(ue.x, ue.y, '.', color=ccolor, markersize=10)
                # if ue.ID == 0:
                #     ax.text(ue.x, ue.y, str(ue.ID), fontsize=15, color="yellow")
                #     print(ue.connectedToBS)




        if links == True:
            for ue in self.parent.ue:
                # print(ue.ID, ue.connectedToBS)
                if ue.connectedToBS is not None:
                    ccolor = "white"
                    if ue.connectedToBS is not None:
                        modres = ue.connectedToBS % 4
                        if modres == 0:
                            ccolor = "red"
                        elif modres == 1:
                            ccolor = "blue"
                        elif modres == 2:
                            ccolor = "green"
                        elif modres == 3:
                            ccolor = "orange"
                    # print(ue.connectedToBS)
                    ax.arrow(ue.x, ue.y, self.parent.bs[ue.connectedToBS].x - ue.x, self.parent.bs[ue.connectedToBS].y - ue.y, color=ccolor)

        if obstacles == True:
            for obstacle in self.parent.obstacles:
                ax.arrow(obstacle[0], obstacle[1], obstacle[2] - obstacle[0], obstacle[3] - obstacle[1])

        networkBorder = plt.Rectangle((0,0), self.parent.constraintAreaMaxX, self.parent.constraintAreaMaxY, color='black', fill=False)
        ax.add_patch(networkBorder)
        ax.axis('equal')
        ax.axis([0, self.parent.constraintAreaMaxX, 0, self.parent.constraintAreaMaxY])
        ax.axis('off')
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)
        for outputFormat in outputFileFormat:
            if outputFormat == "png":
                main_draw.savefig(filename+".tmp", format="png", dpi=300, bbox_inches='tight')

            if outputFormat == "pdf":
                main_draw.savefig(filename+".pdf", format="pdf", dpi=300, bbox_inches='tight')
        
        plt.clf()

    def drawNetworkToText(self, filename, BS=True, UE=True, links=True):
        filename = filename.replace(".csv", ".kml")
        f = open(filename, "w")
        f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<kml xmlns=\"http://www.opengis.net/kml/2.2\">\n\t<Document>\n")

        if BS == True:
            f.write("\t\t<Folder>\n\t\t\t<name>Gateways</name>\n")
            for bs in self.parent.bs:
                f.write("\t\t\t<Placemark>\n")
                f.write("\t\t\t\t<name>GW_" + str(bs.ID) + "</name>\n")
                f.write("\t\t\t\t<styleUrl> #globeIcon</styleUrl>\n")
                f.write("\t\t\t\t<Point>\n\t\t\t\t\t<coordinates>")
                f.write(str(bs.long) + "," + str(bs.lat) + ",0")
                f.write("</coordinates>\n\t\t\t\t</Point>\n")
                f.write("\t\t\t</Placemark>\n")
            f.write("\t\t</Folder>\n")

        if UE == True:
            f.write("\t\t<Folder>\n\t\t\t<name>Nodes</name>\n")
            for ue in self.parent.ue:
                f.write("\t\t\t<Placemark>\n")
                f.write("\t\t\t\t<name>GW_" + str(ue.ID) + "</name>\n")
                f.write("\t\t\t\t<Point>\n\t\t\t\t\t<coordinates>")
                f.write(str(ue.long) + "," + str(ue.lat) + ",0")
                f.write("</coordinates>\n\t\t\t\t</Point>\n")
                f.write("\t\t\t</Placemark>\n")
            f.write("\t\t</Folder>\n")

        if links == True:
            f.write("\t\t<Folder>\n\t\t\t<name>Links</name>\n")
            for ue in self.parent.ue:
                if ue.connectedToBS is not None:
                    f.write("\t\t\t<Placemark>\n")
                    f.write("\t\t\t\t<LineString>\n\t\t\t\t\t<tessellate>0</tessellate>\n\t\t\t\t\t<coordinates>\n\t\t\t\t\t\t")
                    f.write(str(ue.long) + "," + str(ue.lat) + ",0")
                    f.write("\n\t\t\t\t\t\t")
                    f.write(str(self.parent.bs[ue.connectedToBS].long) + "," + str(self.parent.bs[ue.connectedToBS].lat) + ",0")
                    f.write("\n\t\t\t\t\t</coordinates>\n\t\t\t\t</LineString>\n")
                    f.write("\t\t\t</Placemark>\n")
            f.write("\t\t</Folder>\n")

        f.write("\t</Document>\n</kml>")
        f.close()

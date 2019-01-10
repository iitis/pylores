#!/usr/bin/env python3
from pyltes.network import CellularNetwork, LoRaNetwork
from appJar import gui
import datetime
import sys
import threading
import subprocess
import os
import tkinter
from tkinter import messagebox

from PIL import Image

class workThread (threading.Thread):
    def __init__(self, mainloopiterations, movefunctioniterations, type, nodescount, bstx, areasize, gwfinderbucketsize, gwremover, devsensitivity, filename = None):
        threading.Thread.__init__(self)
        self.mainloopiterations = mainloopiterations
        self.movefunctioniterations = movefunctioniterations
        self.type = type
        self.nodescount = nodescount
        self.bstx = bstx
        self.devsensitivity = devsensitivity
        self.filename = filename
        self.areasize = areasize
        self.gwfinderstepDistance = gwfinderbucketsize
        self.gwremover = gwremover
        self.propagationModel = app.getOptionBox("Propagation model")
        self.network = LoRaNetwork(bstx, devsensitivity, self.propagationModel, int(app.getOptionBox("Spreading Factor")))
        self.payload = 51
        self.gatheringTime = None
        self.deliveryProbability = None
        self.algo = app.getRadioButton("iterorgraph")
        self.k = app.getEntry("Redundancy factor:")
        self.allowednoconnected = app.getEntry("Allowed % of nodes w/o connectin")


        #print("type", type, "nodescount", nodescount, "bstx", bstx, "nodetx", nodetx, "filename", filename)

    def run(self):
        self.network.gatheringTime = self.gatheringTime
        self.network.deliveryProbability = self.deliveryProbability
        self.network.allowednoconnected = self.allowednoconnected

        if self.type == "file":
            self.network.Generator.loadNodesFromFile(self.filename)
        elif self.type == "filekml":
            self.network.Generator.loadNodesFromKMLFile(self.filename, self.nodescount)

        elif self.type == "random":
            self.network.Generator.createHoneycombBSdeployment(self.areasize, 1)
            self.network.Generator.insertUErandomly(self.nodescount, seed=2121)
            # network.Generator.insertUEingrid(2000)
            self.network.Generator.removeBSs()
        elif self.type == "uniform":
            self.network.Generator.createHoneycombBSdeployment(self.areasize, 1)
            self.network.Generator.insertUEingrid(self.nodescount)
            self.network.Generator.removeBSs()
        self.network.setPowerInAllBS(self.bstx)
        self.network.setPowerInAllNodes(self.bstx)

        if self.algo == "Iteration solver":
            self.network.loadGatewayFinderIterations()
            self.network.gatewayFinder.findGateways(mainLoopIterations=self.mainloopiterations, movefunctioniterations=self.movefunctioniterations)
        elif self.algo == "Graph solver":
            self.network.loadGatewayFinderGraph()
            self.network.gatewayFinder.findGateways(self.k)

        # if False: #True -> Interation, False -> Graph
        #     self.network.loadGatewayFinderIterations()
        #     self.network.gatewayFinder.findGateways(mainLoopIterations=self.mainloopiterations, movefunctioniterations=self.movefunctioniterations)
        # else:
        #     self.network.loadGatewayFinderGraph()
        #     self.network.gatewayFinder.findGateways(k = 2)

    def nothreadrun(self):
        if app.getCheckBox("Create KML file"):
            print("[", str(datetime.datetime.now()), "] Printing KML in main thread...")
            self.network.Printer.drawNetworkToText(filename=self.filename, links=True)
        if app.getCheckBox("Create GIF file"):
            print("[", str(datetime.datetime.now()), "] Printing GIF in main thread...")
            self.network.Printer.drawNetwork(fillMethod="Devices", filename="res", links=True, figSize=(10, 10))
            im = Image.open('res.tmp')
            background = Image.new('RGBA', im.size, (255, 255, 255))
            background.paste(im, im)
            im = background.convert('RGB').convert('P', palette=Image.ADAPTIVE)
            im.save('Result.gif')
        print("[", str(datetime.datetime.now()), "] Done...\n")

    def status(self):
        if len(self.network.ue) == 0 or len(self.network.bs) == 0:
            output = "No nodes or gateways"
        else:
            output = ""
            output += "Gateways: " + str(len(self.network.bs)) + ", "
            output += "Nodes: " + str(len(self.network.ue)) + ", "
            output += "Range: " + str(self.network.bucketResolution) + "m, "
            output += "Max clients per GW: " + str(self.network.bs[0].maxClients) + ", "
            output += "W/O connection: " + str(self.network.gatewayFinder.returnNoReception())

        return output


def openImage():
    if sys.platform.startswith('darwin'):
        subprocess.call(('open', "Result.gif"))
    elif os.name == 'nt':
        os.startfile("Result.gif")
    elif os.name == 'posix':
        subprocess.call(('xdg-open', "Result.gif"))

def press(button):
    if button == "Exit":
        app.stop()

    if button == "Generate":
        val = app.getRadioButton("inputDataType")
        filename = app.getEntry("f1")
        mainloopiterations = int(app.getEntry("Number of iterations of main loop:"))
        movefunctioniterations = int(app.getEntry("Number of iterations of move function:"))
        nodescount = int(app.getEntry("How many nodes:"))
        bstx = int(app.getEntry("Tx Power [dBm]:"))
        devsensitivity = int(app.getEntry("Receiver sensitivity [dBm]:"))
        areasize = int(app.getEntry("Shorter side [m]:"))
        gwfinderbucketsize = int(app.getEntry("Step size for GW finder [m]:"))
        gwremover = int(app.getEntry("GW remover - no. of buckets to check:"))

        if val == "From file":
            csvOrKml = app.getRadioButton("inputFileType")
            if csvOrKml == "KML file":
                type = "filekml"
            elif csvOrKml == "CSV file":
                type = "file"



        elif val == "From generator":
            genval = app.getRadioButton("generatorType")
            if genval == "Random":
                type = "random"
            elif genval == "Uniform":
                type = "uniform"

        worker = workThread(type=type, mainloopiterations=mainloopiterations, movefunctioniterations=movefunctioniterations, nodescount=nodescount, bstx=bstx, devsensitivity=devsensitivity,  areasize=areasize, gwfinderbucketsize=gwfinderbucketsize,  gwremover=gwremover, filename=filename)
        worker.deliveryProbability = float(app.getEntry("Delivery probability (1-100)")) / 100.0
        worker.gatheringTime = int(app.getEntry("Gathering time [minutes]")) * 60
        if app.getCheckBox("Collision raport"):
            worker.network.raport = app.getEntry("Filename")
        else:
            worker.network.raport = None


        print("[", str(datetime.datetime.now()), "] Calculating...")
        worker.start()
        while worker.is_alive():
            worker.join(10)
            print("[", str(datetime.datetime.now()), "] Wait")
        print("[", str(datetime.datetime.now()), "] Calculating...")
        worker.nothreadrun()
        app.setEntry("Status:", worker.status())
        if len(worker.network.ue) != 0:
            if app.getCheckBox("Create GIF file"):
                try:
                    app.openFrame("Simple")
                    app.reloadImage("simple", "Result.gif")
                    app.shrinkImage("simple", 6)
                    app.stopFrame()
                except:
                    app.startFrame("Simple", 14, 0, colspan=2)
                    app.addImage("simple", "Result.gif")
                    app.shrinkImage("simple", 6)
                    app.setImageSubmitFunction("simple", openImage)
                    app.stopFrame()
        ###################################networkx
        # import matplotlib.pyplot as plt
        # import networkx as nx
        # nx.draw(worker.network.graph)
        # plt.show()
        ###################################

def inputDataTypeChange(radio):
    val = app.getRadioButton("inputDataType")

    # print(val)
    if val == "From file":

        app.enableRadioButton("inputFileType")
        app.enableEntry("f1")
        app.disableRadioButton("generatorType")
        app.disableEntry("Shorter side [m]:")
        app.enableCheckBox("Create KML file")

        valfile = app.getEntry("f1")
        if len(valfile) == 0:
            app.disableButton("Generate")
        else:
            app.enableButton("Generate")


        csvOrKml = app.getRadioButton("inputFileType")
        if csvOrKml == "KML file":
            app.enableEntry("How many nodes:")
        elif csvOrKml == "CSV file":
            app.disableEntry("How many nodes:")

    else:
        app.disableEntry("f1")
        app.enableRadioButton("generatorType")
        app.enableEntry("How many nodes:")
        app.enableEntry("Shorter side [m]:")
        app.enableButton("Generate")
        app.setCheckBox("Create KML file", False)
        app.disableCheckBox("Create KML file")
        app.disableRadioButton("inputFileType")



def genButEnable():
    valfile = app.getEntry("f1")
    valin = app.getRadioButton("inputDataType")
    if valin == "From file" and len(valfile) == 0:
        filebut = False
    else:
        filebut = True

    if app.getEntry("Number of iterations of main loop:") is not None and int(app.getEntry("Number of iterations of main loop:")) > 0:
        mainloopiterations = True
    else:
        mainloopiterations = False

    if app.getEntry("How many nodes:") is not None  and int(app.getEntry("How many nodes:")) > 0:
        nodescount = True
    else:
        nodescount = False

    if app.getEntry("Tx Power [dBm]:") is not None and int(app.getEntry("Tx Power [dBm]:")) > 0:
        bstx = True
    else:
        bstx = False

    if app.getEntry("Receiver sensitivity [dBm]:") is not None and int(app.getEntry("Receiver sensitivity [dBm]:")) > -200:
        nodetx = True
    else:
        nodetx = False

    if app.getEntry("Shorter side [m]:") is not None and int(app.getEntry("Shorter side [m]:")) > 0:
        areasize = True
    else:
        areasize = False

    if app.getEntry("Step size for GW finder [m]:") is not None and int(app.getEntry("Step size for GW finder [m]:")) > 0:
        gwfinderbucketsize = True
    else:
        gwfinderbucketsize = False

    if app.getEntry("Number of iterations of move function:") is not None and int(app.getEntry("Number of iterations of move function:")) > -1:
        movefunctioniterations = True
    else:
        movefunctioniterations = False

    if app.getEntry("GW remover - no. of buckets to check:") is not None and int(app.getEntry("GW remover - no. of buckets to check:")) > -2:
        gwremover = True
    else:
        gwremover = False

    if app.getEntry("Gathering time [minutes]") is not None and int(app.getEntry("Gathering time [minutes]")) > 0:
        gatheringtime = True
    else:
        gatheringtime = False

    if app.getEntry("Delivery probability (1-100)") is not None and float(app.getEntry("Delivery probability (1-100)")) > 0 and float(app.getEntry("Delivery probability (1-100)")) <= 100:
        deliveryprobability = True
    else:
        deliveryprobability = False

    # if filebut and mainloopiterations and nodescount and bstx and nodetx and areasize and gwfinderbucketsize  and gwremover:
    if filebut and mainloopiterations and nodescount and bstx and areasize and nodetx and movefunctioniterations and gatheringtime and deliveryprobability:
        app.enableButton("Generate")
    else:
        app.disableButton("Generate")


app = gui("PyLOREs", "1100x900")
app.setPadding([20,5])
app.setStretch("column")

app.addRadioButton("inputDataType", "From generator", row=0, column=1)
app.addRadioButton("inputDataType", "From file", row=0, column=0)

app.addCheckBox("Collision raport", row=5, column=2)
app.addEntry("Filename", row=6, column=2)
app.setEntry("Filename", "raport")
app.hideCheckBox("Collision raport")
app.hideEntry("Filename")

app.addFileEntry("f1", row=2, column=0, rowspan=3)
app.startFrame("ranoruni", row=1, column=1)
app.addRadioButton("generatorType", "Random",  row=0, column=0)
app.addRadioButton("generatorType", "Uniform", row=0, column=1)
app.stopFrame()

app.startFrame("csvkml", row=1, column=0)
app.addRadioButton("inputFileType", "KML file",  row=1, column=0)
app.addRadioButton("inputFileType", "CSV file", row=1, column=1)
app.stopFrame()

app.addLabelNumericEntry("Shorter side [m]:", row=2, column=1)
app.setEntry("Shorter side [m]:", 2150)

app.addLabelNumericEntry("How many nodes:", row=3, column=1)
app.setEntry("How many nodes:", 2000)

app.addLabel("  ", row=4, column=0)

# app.setPadding([20,50])
app.addLabelNumericEntry("Tx Power [dBm]:", row=5, column=0)
app.setEntry("Tx Power [dBm]:", 14)

app.addLabelNumericEntry("Receiver sensitivity [dBm]:", row=5, column=1)
app.setEntry("Receiver sensitivity [dBm]:", -133)
# app.setPadding([20,0])

app.addLabelNumericEntry("Step size for GW finder [m]:", row=6, column=0)
app.setEntry("Step size for GW finder [m]:", 0)

app.addLabelNumericEntry("Number of iterations of main loop:", row=7, column=0)
app.setEntry("Number of iterations of main loop:", 5)
app.addLabelNumericEntry("Number of iterations of move function:", row=7, column=1)
app.setEntry("Number of iterations of move function:", 50)

app.addLabelNumericEntry("GW remover - no. of buckets to check:", row=8, column=0)
app.setEntry("GW remover - no. of buckets to check:", -1)

app.startFrame("outopts", row=8, column=0)
app.addCheckBox("Create KML file", row=0, column=0)
app.addCheckBox("Create GIF file", row=0, column=1)
app.stopFrame()

app.addLabelNumericEntry("Allowed % of nodes w/o connectin", row=9, column=0)
app.setEntry("Allowed % of nodes w/o connectin", 0)

app.addLabelOptionBox("Propagation model", ["SUI", "Log-distance", "Okumura-Hata", "Okumura-Hata s."],  row=8, column=1)

app.addLabelNumericEntry("Delivery probability (1-100)", row=9, column=1)
app.setEntry("Delivery probability (1-100)", 60)


app.startFrame("itergraph", row=10, column=0)
app.addRadioButton("iterorgraph", "Iteration solver", row=0, column=0)
app.addRadioButton("iterorgraph", "Graph solver", row=0, column=1)
app.stopFrame()
app.hideFrame("itergraph")

app.addLabelNumericEntry("Gathering time [minutes]", row=10, column=1)
app.setEntry("Gathering time [minutes]", 60)

app.addLabelNumericEntry("Redundancy factor:", row=11, column=0)
app.setEntry("Redundancy factor:", 2)
app.hideLabel("Redundancy factor:")

app.addLabelOptionBox("Spreading Factor", [12, 11, 10, 9, 8, 7], row=11, column=1)


app.addButtons(["Generate", "Exit"], press, row=12, column=0, colspan=2)
app.addLabelEntry("Status:", row=13, column=0, colspan=2)
app.disableEntry("Status:")

# app.disableRadioButton("generatorType")
# app.disableButton("Generate")
# app.disableEntry("How many nodes:")
# app.disableEntry("Shorter side [m]:")
# app.hideEntry("Node Tx Power [dBm]:")
# app.hideEntry("Number of iterations of main loop:")
# app.hideEntry("Number of iterations of move function:")
app.hideEntry("Step size for GW finder [m]:")
app.hideEntry("GW remover - no. of buckets to check:")
app.setCheckBox("Create GIF file")
# app.disableEntry("Step size for GW finder [m]:")
inputDataTypeChange(True)
app.setRadioButtonChangeFunction("inputDataType", inputDataTypeChange)
app.setRadioButtonChangeFunction("inputFileType", inputDataTypeChange)
app.setEntryChangeFunction("f1", genButEnable)
app.setEntryChangeFunction("Shorter side [m]:", genButEnable)
app.setEntryChangeFunction("How many nodes:", genButEnable)
app.setEntryChangeFunction("Tx Power [dBm]:", genButEnable)
app.setEntryChangeFunction("Receiver sensitivity [dBm]:", genButEnable)
app.setEntryChangeFunction("Number of iterations of main loop:", genButEnable)
app.setEntryChangeFunction("Step size for GW finder [m]:", genButEnable)
app.setEntryChangeFunction("Number of iterations of move function:", genButEnable)
app.setEntryChangeFunction("GW remover - no. of buckets to check:", genButEnable)
app.setEntryChangeFunction("Delivery probability (1-100)", genButEnable)
app.setEntryChangeFunction("Gathering time [minutes]", genButEnable)

app.go()



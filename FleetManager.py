from appJar import gui
import json
import datetime
import sys
import os
from ws4py.client.threadedclient import WebSocketClient

class BorderConnectClient(WebSocketClient):
    
    def setSendMessage(self, message):
        self.sendMessage = message
    
    def opened(self):
        self.send('{"apiKey": "a-12698-3fac5f135b764570"}')
        
    def closed(self, code, reason=None):
        print("BorderConnectClient closed")
        self.close()
    
    def received_message(self, responce):
        #print(responce)
        content = json.loads(responce.data.decode("utf-8"))
        print(responce)
        if "status" in content.keys():
            if content["status"] == "OK":
                self.send(json.dumps(self.sendMessage))
            elif content["status"] == "QUEUED":
                pass
            else:
                print("ERROR: Unrecognized responce received:")
        self.close()

def press1(button):
    try:
        with open("ACEconfig.json", "r") as ACEconfigFile:
            ACE = json.load(ACEconfigFile)
        with open("ACIconfig.json", "r") as ACIconfigFile:
            ACI = json.load(ACIconfigFile)
            
        start = app.getDatePicker("startDP")
        end = app.getDatePicker("endDP")
        delta = (end - start).days + 1
        for i in range(0, delta): # For each day between the start and end dates
            day = datetime.date.fromordinal(start.toordinal() + i)
            YYYYMMDD = str(day).replace("-", "")
            if day.weekday() < 5: # If the day is not Saturday or Sunday
                SCAC = "SEIK" + YYYYMMDD + "DR"
                ACE["tripNumber"] = SCAC
                ACE["estimatedArrivalDateTime"] = str(day) + " 10:00:00"
                
                CCN = "726G" + YYYYMMDD + "DR"
                PARS = CCN + "02"
                ACI["tripNumber"] = CCN
                ACI["estimatedArrivalDateTime"] = str(day) + " 12:00:00"
                ACI["shipments"][0]["cargoControlNumber"] = PARS
                ACI["shipments"][0]["estimatedArrivalDate"] = str(day) + " 12:00:00"
                
                if app.getCheckBox("Save .json(s) to disk"):
                    path = "ACE-ACI Manifests" + os.sep + YYYYMMDD
                    if not os.path.exists("ACE-ACI Manifests"):
                        os.mkdir("ACE-ACI Manifests")
                    if not os.path.exists(path):
                        os.mkdir(path)
                    with open(path + os.sep + "ace-trip-" + SCAC + ".json", "w") as outFile:
                        json.dump(ACE, outFile)
                    with open(path + os.sep + "aci-trip-" + CCN + ".json", "w") as outFile:
                        json.dump(ACI, outFile)
                    
                if app.getCheckBox("Send .json(s) to BorderConnect"):
                    sendToBC(ACE)
                    sendToBC(ACI)
                    
                if app.getCheckBox("Request .pdf(s) from BorderConnect"):
                    ACERequest = {
                        "data": "PDF_REQUEST",
                        "companyKey": "c-9000-2bcd8ae5954e0c48",
                        "type": "ACE_STANDARD_DRIVERS_COPY",
                        "action": "EMAIL",
                        "tripNumber": SCAC,
                        "emailDetails": {
                            "address": "christopher@stallionexpress.ca",
                            "replyToAddress": "christopher@stallionexpress.ca",
                            "subject": "ACE eManifest Trip Number " + SCAC,
                            "body": str(day)
                            }
                        }
                    sendToBC(ACERequest)
                    ACIRequest = {
                        "data": "PDF_REQUEST",
                        "companyKey": "c-9000-2bcd8ae5954e0c48",
                        "type": "ACI_STANDARD_DRIVERS_COPY",
                        "action": "EMAIL",
                        "tripNumber": CCN,
                        "emailDetails": {
                            "address": "christopher@stallionexpress.ca",
                            "replyToAddress": "christopher@stallionexpress.ca",
                            "subject": "ACI eManifest Trip Number " + CCN,
                            "body": str(day)
                            }
                        }
                    sendToBC(ACIRequest)
                # TODO: Add ACI request
                # TODO: Look in to generating the PDF yourself (incl. barcode?)
    except:
        print(sys.exc_info())
        raise

def press2(button):
    if button == "Send to BC":
        with open("tripconfig.json", "r") as tripconfigFile:
            trip = json.load(tripconfigFile)
        today = str(datetime.datetime.now())[:10] #Produces string in the format YYYY-MM-DD
        YYYYMMDD = today.replace("-", "")
        PARS = "726G" + YYYYMMDD + "DR02" #String version of PARS number
        trip["cargoControlNumber"] = PARS
        trip["estimatedArrivalDate"] = getNextTime()
        total = 0
        for i in range(1, 6):
            if (app.getEntry("box" + str(i) + "Quantity") != "") and (app.getEntry("totalWeight") != ""):
                total += int(app.getEntry("box" + str(i) + "Quantity"))
        for i in range(1, 6):
            if (app.getOptionBox("box" + str(i)) != "None") and (app.getEntry("box" + str(i) + "Quantity") != "") and (app.getEntry("totalWeight") != ""):
                desc = app.getOptionBox("box" + str(i))
                quan = int(app.getEntry("box" + str(i) + "Quantity"))
                weight = round(quan / total * int(app.getEntry("totalWeight")))
                trip["commodities"].append({
                    "description": desc,
                    "quantity": quan,
                    "packagingUnit": "PCE",
                    "weight": str(weight),
                    "weightUnit": "LBR"
                    })
        # TEMP
        print(trip)
        path = "ACE-ACI Manifests" + os.sep + YYYYMMDD
        if not os.path.exists("ACE-ACI Manifests"):
            os.mkdir("ACE-ACI Manifests")
        if not os.path.exists(path):
            os.mkdir(path)
        with open(path + os.sep + "aci-shipment-" + PARS + ".json", "w") as outFile:
            json.dump(trip, outFile)
        sendToBC(trip)
        # TODO: Add drag'n'drop support to store Ford BoL
        # TODO: Autosend email to Buckland
        
def press3():
    # TODO: Generate Invoice
    # TODO: add drag'n'drop support to sort signed BoLs
    # TODO: Email to Timeline
    pass

def sendToBC(sendMessage):
    try:
        client = BorderConnectClient("wss://borderconnect.com/api/sockets/stallionexpress")
        client.setSendMessage(sendMessage)
        client.connect()
        client.run_forever()
    except KeyboardInterrupt:
        client.close()

def getNextTime(): # returns next available 15-minute arrival time
    now = datetime.datetime.now()
    day = now.strftime("%Y-%m-%d")
    hour = int(now.strftime("%H"))
    minute = int(now.strftime("%M"))
    minute = ((minute // 15) + 1) * 15
    if minute >= 60:
        minute = minute % 60
        hour = hour + 1
        if hour >= 24:
            hour = hour % 24
    return(day + " " + str(hour) + ":" + str(minute) + ":00")


options = [
    "None",
    "FA1B- R02526 AD REINF FRT BDY PLR RH",
    "FA1B- R02527 AD REINF FRT BDY PLR LH",
    "FT4B- R02526 AJ REINF FRT BDY PLR RH",
    "FT4B- R02527 AH REINF FRT BDY PLR LH",
    "FT4B- R279C38 AL REINF BDY SD PNL RR",
    "FT4B- R279C39 AL REINF BDY SD PNL RR",
    "KA1B- R279C38 AB REINF BDY SD PNL RR",
    "KA1B- R279C39 AB REINF BDY SD PNL RR"
    ]

app = gui()

app.startTabbedFrame("TabbedFrame")

# Tab 1
app.startTab("ACE/ACI Creation")

app.setSticky("w")
app.addLabel("label1", "Start Date:", 0, 0)
app.addDatePicker("startDP", 1, 0)
app.setDatePickerRange("startDP", 2019, 2037)
app.setDatePicker("startDP")

app.addLabel("label2", "End Date:", 0, 1)
app.addDatePicker("endDP", 1, 1)
app.setDatePickerRange("endDP", 2019, 2037)
app.setDatePicker("endDP")

app.addCheckBox("Save .json(s) to disk")
app.addCheckBox("Send .json(s) to BorderConnect")
app.addCheckBox("Request .pdf(s) from BorderConnect")
app.setCheckBox("Save .json(s) to disk")
app.setCheckBox("Send .json(s) to BorderConnect")
app.setCheckBox("Request .pdf(s) from BorderConnect")

app.setSticky("s")
app.addButton("Generate", press1)
app.stopTab()

# Tab 2
app.startTab("ACI Contents Entry")
app.addLabel("title1Label", "", 0, 0)
app.addLabel("title2Label", "Item:", 0, 1)
app.addLabel("title3Label", "Quantity:", 0, 2)

app.addLabel("box1Label", "Item 1: ", 1, 0)
app.addLabel("box2Label", "Item 2: ", 2, 0)
app.addLabel("box3Label", "Item 3: ", 3, 0)
app.addLabel("box4Label", "Item 4: ", 4, 0)
app.addLabel("box5Label", "Item 5: ", 5, 0)
app.addLabel("box6Label", "Item 6: ", 6, 0)
app.addLabel("totalWeightLabel", "Total Weight: ", 7, 0)

app.addOptionBox("box1", options, 1, 1)
app.addOptionBox("box2", options, 2, 1)
app.addOptionBox("box3", options, 3, 1)
app.addOptionBox("box4", options, 4, 1)
app.addOptionBox("box5", options, 5, 1)
app.addOptionBox("box6", options, 6, 1)
app.addEntry("totalWeight", 7, 1)

app.addEntry("box1Quantity", 1, 2)
app.addEntry("box2Quantity", 2, 2)
app.addEntry("box3Quantity", 3, 2)
app.addEntry("box4Quantity", 4, 2)
app.addEntry("box5Quantity", 5, 2)
app.addEntry("box6Quantity", 6, 2)

app.addButton("Send to BC", press2, 8, 1)
app.stopTab()

# Tab 3
app.startTab("Invoice Generation")
app.addLabel("label3", "Test post, please ignore")
app.stopTab()

app.stopTabbedFrame()

app.go()
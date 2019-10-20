from appJar import gui
import json
import datetime
from ws4py.client.threadedclient import WebSocketClient
from orca.scripts import self_voicing

class BorderConnectClient(WebSocketClient):
    
    def setMessage(self, message):
        self.message = message
    
    def opened(self):
        self.send('{"apiKey": "a-12698-3fac5f135b764570"}')
        
    def closed(self, code, reason=None):
        print("BorderConnectClient closed")
    
    def received_message(self, responce):
        #print(responce)
        content = json.loads(responce.data.decode("utf-8"))
        if "status" in content.keys():
            print("Status: " + content["status"])
            
            if content["status"] == "OK":
                print("Sending ACI shipment")
                self.send(json.dumps(self.message))
            elif content["status"] == "QUEUED":
                print("ACI shipment queued. Please check BorderConnect")
            else:
                print("ERROR: Unrecognized status received")
        self.close()

def press(button):
    if button == "Submit":
        today = str(datetime.datetime.now())[:10] #Produces string in the format YYYY-MM-DD
        PARS = "726G" + today.replace("-", "") + "DR02" #String version of PARS number
        out = {
            "data": "ACI_SHIPMENT",
            "companyKey": "c-9000-2bcd8ae5954e0c48",
            "operation": "UPDATE",
            "shipmentType": "PARS",
            "loadedOn": {
                "type": "TRAILER",
                "number": "9P1683"
            },
            "cargoControlNumber": PARS,
            "referenceOnlyShipment": False,
            "portOfEntry": "0427",
            "releaseOffice": "0427",
            "estimatedArrivalDate": today + " 12:30:00",
            "estimatedArrivalTimeZone": "EST",
            "cityOfLoading": {
                "cityName": "Buffalo",
                "stateProvince": "NY"
            },
            "consolidatedFreight": False,
            "shipper": {
                "name": "Ford Buffalo Stamping",
                "address": {
                    "addressLine": "3663 Lakeshore Road",
                    "city": "Buffalo",
                    "stateProvince": "NY",
                    "postalCode": "14219"
                }
            },
            "consignee": {
                "name": "Maple Stamping",
                "address": {
                    "addressLine": "401 Caldari Road",
                    "city": "Concord",
                    "stateProvince": "ON",
                    "postalCode": "L4K 5P1"
                }
            },
            "commodities": [],
            "autoSend": False
        }
        total = 0
        for i in range(1, 6):
            if (app.getEntry("box" + str(i) + "Quantity") != "") and (app.getEntry("totalWeight") != ""):
                total += int(app.getEntry("box" + str(i) + "Quantity"))
        for i in range(1, 6):
            if (app.getOptionBox("box" + str(i)) != "None") and (app.getEntry("box" + str(i) + "Quantity") != "") and (app.getEntry("totalWeight") != ""):
                desc = app.getOptionBox("box" + str(i))
                quan = int(app.getEntry("box" + str(i) + "Quantity"))
                weight = round(quan / total * int(app.getEntry("totalWeight")))
                out["commodities"].append({
                    "description": desc,
                    "quantity": quan,
                    "packagingUnit": "PCE",
                    "weight": str(weight),
                    "weightUnit": "LBR"
                    })
        # TEMP
        print(out)
        with open("aci-shipment-" + PARS + ".json", "w") as outFile:
            json.dump(out, outFile)
        # END TEMP
        try:
            client = BorderConnectClient("wss://borderconnect.com/api/sockets/stallionexpress", out)
            client.setMessage(out)
            client.connect()
            client.run_forever()
        except KeyboardInterrupt:
            client.close()

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

app.addButton("Submit", press, 8, 1)
app.go()

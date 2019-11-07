from appJar import gui
import json
import datetime
import sys
import os
import shutil
from ws4py.client.threadedclient import WebSocketClient
import email, smtplib, ssl
from decimal import *

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import barcode
from barcode.writer import ImageWriter
import PIL

from PyPDF2 import PdfFileReader, PdfFileWriter

pdfmetrics.registerFont(TTFont('Lucida', 'C:\Windows\Fonts\LTYPE.TTF'))
password = "SE7^email"

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
                
                if app.getCheckBox("Generate .pdf(s)"):
                    path = "ACE-ACI Manifests" + os.sep + YYYYMMDD
                    if not os.path.exists("ACE-ACI Manifests"):
                        os.mkdir("ACE-ACI Manifests")
                    if not os.path.exists(path):
                        os.mkdir(path)
                    CODE128 = barcode.get_barcode_class("code128")
                    
                    #ACE Manifest
                    text = []
                    text.append("ACE Manifest")
                    text.append(" ")
                    text.append("Company: Stallion Express Inc.")
                    text.append("Trip Number: " + SCAC)
                    text.append(" ")
                    text.append(" ") 
                    text.append(" ") # Empty room for barcodes
                    text.append(" ")
                    text.append(" ")
                    text.append(" ")
                    text.append(" ")
                    text.append(" ")
                    text.append(" *" + SCAC + "*")
                    text.append(" ")
                    text.append("Driver Name: " + ACE["drivers"][0]["firstName"] + " " + ACE["drivers"][0]["lastName"])
                    text.append("Truck License Plate: " + ACE["truck"]["licensePlates"][0]["number"] + " (" + ACE["truck"]["licensePlates"][0]["stateProvince"] + ", CA)")
                    text.append("Trailer License Plate: " + ACE["trailers"][0]["licensePlates"][0]["number"] + " (" + ACE["trailers"][0]["licensePlates"][0]["stateProvince"] + ", CA)")
                    
                    bar = CODE128(SCAC, writer = ImageWriter())
                    if os.path.exists(path + os.sep + SCAC):
                        os.remove(path + os.sep + SCAC)
                    file = bar.save(path + os.sep + SCAC)
                    
                    c = canvas.Canvas(path + os.sep + SCAC + ".pdf", bottomup = 0)
                    c.setFont("Lucida", 20)
                    c.drawImage(file, 20, 120, width=227, height=140, mask=None)
                    for i, line in enumerate(text):
                        c.drawString(20, 40 + (i * 22), line)
                    if os.path.exists(path + os.sep + SCAC + ".pdf"):
                        os.remove(path + os.sep + SCAC + ".pdf")
                    c.save()
                    
                    # ACI Manifest
                    text = []
                    text.append("ACI Manifest for Canada")
                    text.append(" ")
                    text.append("Company: Stallion Express Inc.")
                    text.append("Conveyance Reference Number: " + CCN)
                    text.append(" ")
                    text.append(" ") 
                    text.append(" ") # Empty room for barcodes
                    text.append(" ")
                    text.append(" ")
                    text.append(" ")
                    text.append(" ")
                    text.append(" ")
                    text.append(" *" + CCN + "*")
                    text.append(" ")
                    text.append("Port of Entry: 0427: Niagara Falls")
                    text.append("               - Queenston Lewiston Bridge") # TODO: un-hardcode this
                    text.append("Driver Name: " + ACI["drivers"][0]["firstName"] + " " + ACI["drivers"][0]["lastName"])
                    text.append("Truck License Plate: " + ACI["truck"]["licensePlate"]["number"] + " (" + ACI["truck"]["licensePlate"]["stateProvince"] + ", CA)")
                    text.append("Trailer License Plate: " + ACI["trailers"][0]["licensePlate"]["number"] + " (" + ACI["trailers"][0]["licensePlate"]["stateProvince"] + ", CA)")
                    text.append("Cargo Control Number(s): " + PARS)
                    text.append("                         Type: PARS")
                    
                    bar = CODE128(CCN, writer = ImageWriter())
                    if os.path.exists(path + os.sep + CCN):
                        os.remove(path + os.sep + CCN)
                    file = bar.save(path + os.sep + CCN)
                    
                    c = canvas.Canvas(path + os.sep + CCN + ".pdf", bottomup = 0)
                    c.setFont("Lucida", 20)
                    c.drawImage(file, 20, 120, width=227, height=140, mask=None)
                    for i, line in enumerate(text):
                        c.drawString(20, 40 + (i * 22), line)
                    if os.path.exists(path + os.sep + CCN + ".pdf"):
                        os.remove(path + os.sep + CCN + ".pdf")
                    c.save()
                if app.getCheckBox("Email .pdf(s) to Driver"):
                    path = "ACE-ACI Manifests" + os.sep + YYYYMMDD
                    if os.path.exists(path + os.sep + SCAC + ".pdf") and os.path.exists(path + os.sep + CCN + ".pdf"): # IF both necessary files are present, send an email
                        server = smtplib.SMTP(host = "smtp.gmail.com", port = 587)
                        server.starttls()
                        server.login("christopher@stallionexpress.ca", password)
                        
                        message = MIMEMultipart()
                        text = ""
                        message["From"] = "christopher@stallionexpress.ca"
                        message["To"] = "husnainzaheer@icloud.com"
                        message["Subject"] = "Paperwork for " + str(day)
                        
                        message.attach(MIMEText(text, "plain"))
                        
                        files = [path + os.sep + SCAC + ".pdf", path + os.sep + CCN + ".pdf"]
                        for f in files:
                            attachment = MIMEApplication(open(f, "rb").read())
                            attachment.add_header("Content-Disposition", "attachment", filename = f)
                            message.attach(attachment)
                            
                        server.send_message(message)
                        print("Email Sent")
                        del message
                    else:
                        print("Ford BoL or ACI not found")
                if app.getCheckBox("Backup to Google Drive"):
                    pass
                    # TODO: Backup to Google Drive?
    except:
        print(sys.exc_info())
        raise

def press2(button):
    password = "SE7^email"
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
            if (app.getEntry("box" + str(i) + "Quantity") != "") and (app.getEntry("Total Weight:") != ""):
                total += int(app.getEntry("box" + str(i) + "Quantity"))
        for i in range(1, 6):
            if (app.getOptionBox("Item " + str(i)) != "None") and (app.getEntry("box" + str(i) + "Quantity") != "") and (app.getEntry("Total Weight:") != ""):
                desc = app.getOptionBox("Item " + str(i))
                quan = int(app.getEntry("box" + str(i) + "Quantity"))
                weight = round(quan / total * int(app.getEntry("Total Weight:")))
                trip["commodities"].append({
                    "description": desc,
                    "quantity": quan,
                    "packagingUnit": "PCE",
                    "weight": str(weight),
                    "weightUnit": "LBR"
                    })
        path = "ACE-ACI Manifests" + os.sep + YYYYMMDD
        if not os.path.exists("ACE-ACI Manifests"):
            os.mkdir("ACE-ACI Manifests")
        if not os.path.exists(path):
            os.mkdir(path)
        with open(path + os.sep + "aci-shipment-" + PARS + ".json", "w") as outFile:
            json.dump(trip, outFile)
        if app.getCheckBox("Send contents to BC"):
            sendToBC(trip)
            print("Contents sent to BC")
        
        tripNumber = "726G" + YYYYMMDD + "DR"
        if os.path.exists(path + os.sep + tripNumber + ".pdf") and app.getEntry("contentsEntry") != "": # IF both necessary files are present, send an email
            server = smtplib.SMTP(host = "smtp.gmail.com", port = 587)
            server.starttls()
            server.login("christopher@stallionexpress.ca", password)
            
            message = MIMEMultipart()
            text = tripNumber
            message["From"] = "christopher@stallionexpress.ca"
            #message["To"] = "christopher@stallionexpress.ca"
            message["To"] = "opswo@buckland.com"
            message["Subject"] = tripNumber
            
            message.attach(MIMEText(text, "plain"))
            
            files = [app.getEntry("contentsEntry"), path + os.sep + tripNumber + ".pdf"]
            for f in files:
                attachment = MIMEApplication(open(f, "rb").read())
                attachment.add_header("Content-Disposition", "attachment", filename = f)
                message.attach(attachment)
            if app.getCheckBox("Send email to Buckland"):
                server.send_message(message)
                print("Email Sent")
            else:
                print("Email created but not sent")
            del message
        else:
            print("Ford BoL or ACI not found")
        
        
def press3():
    if app.getEntry("Invoice #:") != "" and app.getEntry("LDS #:") != "" and app.getEntry("CCEntry") != "":
        
        # 1.
        invoiceNumber = app.getEntry("Invoice #:")
        load = app.getEntry("LDS #:")
        filename = "Stallion Express Invoice #" + invoiceNumber + " - LDS" + load + ".pdf"
        
        # 2.
        date = str(app.getDatePicker("invoiceDatePicker"))
        today = str(datetime.date.today())
        path = "ACE-ACI Manifests" + os.sep + date.replace("-", "")
        #print(path)
        if not os.path.exists("ACE-ACI Manifests"):
            os.mkdir("ACE-ACI Manifests")
        if not os.path.exists(path):
            os.mkdir(path)
            
        text = []
        text.append("Stallion Express Invoice                                              Invoice  ")
        text.append("                                                                               ")
        text.append("Stallion Express Inc.                                          Invoice: #" + app.getEntry("Invoice #:"))
        text.append("7676 Woodbine Avenue, Unit 2                                 Date: " + today)
        text.append("Markham, ON, L3R 2N2, Canada                                                   ")
        text.append("Tel: (647)-557-3725                                                            ")
        text.append("Email: ar@stallionexpress.ca                                                   ")
        text.append("                                                                               ")
        text.append("BILL TO: TRAFFIC TECH INC.                                        LDS" + app.getEntry("LDS #:"))
        text.append("16711 TRANS-CANADA HIGHWAY                             PARS #726G" + date.replace("-", "") + "DR02")
        text.append("KIRKLAND, QC                                                                   ")
        text.append("H9H 3L1                                                                        ")
        text.append("                                                                               ")
        text.append("PICK-UP: " + date + "                     DELIVERY: " + date + "                   ")
        text.append("FORD BUFFALO STAMPING                   MAPLE STAMPING                         ")
        text.append("3663 LAKE SHORE ROAD                    401 CALDARI                            ")
        text.append("BUFFALO, NY                             CONCORD, ON                            ")
        text.append("14219                                   L4K 2X2                                ")
        text.append("                                                                               ")
        text.append("                       Tractor: 664077  Trailer: 9P1683                        ")
        text.append("                                                                               ")
        text.append("Activity                                                     Rate      Amount  ")
        text.append("-----------------------------------------------------------------------------  ")
        text.append("FTL - Buffalo Ford Rounder                                            $800.00  ")
        total = "800.00"
        if app.getSpinBox("Detention Charge:") == "0":
            total = "800.00"
            text.append("                                                                               ")
        else:
            length = app.getSpinBox("Detention Charge:")
            if length == "15": # Formatting numebrs sucks. Hard-coding out of laziness
                extra = " 12.50"
                total = "812.50"
            elif length == "30":
                extra = " 25.00"
                total = "825.00"
            elif length == "45":
                extra = " 37.50"
                total = "837.50"
            elif length == "60":
                extra = " 50.00"
                total = "850.00"
            elif length == "75":
                extra = " 62.50"
                total = "862.50"
            elif length == "90":
                extra = " 75.00"
                total = "875.00"
            elif length == "105":
                extra = " 87.50"
                total = "887.50"
            elif length == "120":
                extra = "100.00"
                total = "900.00"
            text.append("Detention charge - " + (length + " minutes").ljust(11) + "                                        $" + extra)
        text.append("-----------------------------------------------------------------------------  ")
        text.append("                                                            TOTAL     $" + total)
        text.append("                                                                               ")
        text.append("Make cheques payable to:                                                       ")
        text.append("Stallion Express Inc.                                                          ")
        text.append("7676 Woodbine Avenue, Unit 2, Markham, Ontario, L3R 2N2, Canada                ")
        
        c = canvas.Canvas(path + os.sep + "Invoice.pdf")
        c.setFont("Lucida", 12)
        c.drawImage("StallionExpress-Black-Logo.png", 20, 737, width = 255, height = 85, mask=None)
        for i, line in enumerate(text):
            c.drawString(20, 720 - (i * 14), line)
        if os.path.exists(path + os.sep + "Invoice.pdf"):
            os.remove(path + os.sep + "Invoice.pdf")
        c.save()
        
        today = str(datetime.date.today())
        loadSummary = "\t#" + invoiceNumber + "\tSENT\t" + today + "\t" + load + "\tTRAFFIC TECH\t$" + str(total) + "\t664077\t9P1683\tZAHEER\t" + date + "\tBUFFALO, NY\t" + date + "\tCONCORD, ON\tFTL, ROUNDER"
        print(loadSummary)
        app.topLevel.clipboard_append(loadSummary)
        
        if app.getCheckBox("Email Invoice"):
            mapleBoL = path + os.sep + "Maple BoL.pdf"
            fordBoL = path + os.sep + "Ford BoL.pdf"
            invoicePath = path + os.sep + "Invoice.pdf"
            #print(mapleBoL, fordBoL, invoicePath)
            if os.path.exists(mapleBoL) and os.path.exists(fordBoL) and os.path.exists(invoicePath):
                server = smtplib.SMTP(host = "smtp.gmail.com", port = 587)
                server.starttls()
                server.login("christopher@stallionexpress.ca", password)
                
                message = MIMEMultipart()
                text = "Please see attached:\n1. " + filename + "\n2. Maple BoL\n3. Ford BoL\n4. Carrier Confirmation"
                message["From"] = "christopher@stallionexpress.ca"
                #message["To"] = "christopher@stallionexpress.ca"
                message["To"] = "P@traffictech.com"
                message["Subject"] = filename
                
                message.attach(MIMEText(text, "plain"))
                
                inputStreams = []
                files = [invoicePath, mapleBoL, fordBoL, app.getEntry("CCEntry")]
                try:
                    for file in files:
                        inputStreams.append(open(file, "rb"))
                    writer = PdfFileWriter()
                    for reader in map(PdfFileReader, inputStreams):
                        for n in range (reader.getNumPages()):
                            writer.addPage(reader.getPage(n))
                    if os.path.exists(path + os.sep + filename):
                        os.remove(path + os.sep + filename)
                    writer.write(open(path + os.sep + filename, "wb"))
                finally:
                    for f in inputStreams:
                        f.close()

                attachment = MIMEApplication(open(path + os.sep + filename, "rb").read())
                attachment.add_header("Content-Disposition", "attachment", filename = filename)
                message.attach(attachment)

                server.send_message(message)
                #print("Email Sent")
                del message
            else:
                print("One of Maple BoL or Ford BoL not found")
                
def press4():
    date = app.getDatePicker("fileSorterDatePicker")
    folder = str(date).replace("-", "")
    if app.getRadioButton("file") != "ACE Manifest" and app.getRadioButton("file") != "ACI Manifest":
        filename = app.getRadioButton("file") + ".pdf"
        path = "ACE-ACI Manifests" + os.sep + folder
        if not os.path.exists("ACE-ACI Manifests"):
            os.mkdir("ACE-ACI Manifests")
        if not os.path.exists(path):
            os.mkdir(path)
        
        shutil.move(app.getEntry("fileEntry"), path + os.sep + filename)
    else:
        filename = app.getEntry("fileEntry").split("/")[-1]
        path = "ACE-ACI Manifests" + os.sep + folder
        if not os.path.exists("ACE-ACI Manifests"):
            os.mkdir("ACE-ACI Manifests")
        if not os.path.exists(path):
            os.mkdir(path)
        
        shutil.move(app.getEntry("fileEntry"), path + os.sep + "acei.manifest" + filename)

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

def changeDate(button):
    if button == "Previous":
        app.setDatePicker("fileSorterDatePicker", datetime.date.fromordinal(app.getDatePicker("fileSorterDatePicker").toordinal() - 1))
    if button == "Today":
        app.setDatePicker("fileSorterDatePicker", datetime.date.today())
    if button == "Next":
        app.setDatePicker("fileSorterDatePicker", datetime.date.fromordinal(app.getDatePicker("fileSorterDatePicker").toordinal() + 1))

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

padding = [5, 1]

app = gui()

app.startTabbedFrame("TabbedFrame")

# Tab 1
app.startTab("ACE/ACI Creation")
app.setInPadding(padding)

app.setSticky("nw")
app.setStretch("column")

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
app.addCheckBox("Generate .pdf(s)")
app.addCheckBox("Email .pdf(s) to Driver")
app.addCheckBox("Backup to Google Drive")

app.setCheckBox("Save .json(s) to disk")
app.setCheckBox("Send .json(s) to BorderConnect")
#app.setCheckBox("Request .pdf(s) from BorderConnect")
app.setCheckBox("Generate .pdf(s)")
app.setCheckBox("Email .pdf(s) to Driver")
app.setCheckBox("Backup to Google Drive")

app.setSticky("s")
app.addButton("Generate", press1)
app.stopTab()

# Tab 2
app.startTab("ACI Contents Entry")
app.setInPadding(padding)

app.addFileEntry("contentsEntry", 0, 0)
app.addLabel("title1Label", "Item:", 1, 0)
app.addLabel("title2Label", "Quantity:", 1, 1)

app.addLabelOptionBox("Item 1", options, 2, 0)
app.addLabelOptionBox("Item 2", options, 3, 0)
app.addLabelOptionBox("Item 3", options, 4, 0)
app.addLabelOptionBox("Item 4", options, 5, 0)
app.addLabelOptionBox("Item 5", options, 6, 0)
app.addLabelOptionBox("Item 6", options, 7, 0)
app.addLabelEntry("Total Weight:", 8, 0)

app.addEntry("box1Quantity", 2, 1)
app.addEntry("box2Quantity", 3, 1)
app.addEntry("box3Quantity", 4, 1)
app.addEntry("box4Quantity", 5, 1)
app.addEntry("box5Quantity", 6, 1)
app.addEntry("box6Quantity", 7, 1)

app.addCheckBox("Send contents to BC", 9, 0)
app.addCheckBox("Send email to Buckland", 10, 0)
app.setCheckBox("Send contents to BC")
app.setCheckBox("Send email to Buckland")

app.addButton("Send to BC", press2, 11, 0)
app.stopTab()

# Tab 3
app.startTab("Invoice Generation")
app.setInPadding(padding)

app.setSticky("nw")
app.setStretch("column")

app.addDatePicker("invoiceDatePicker", 0, 0, 1, 3)
app.setDatePickerRange("invoiceDatePicker", 2019, 2037)
app.setDatePicker("invoiceDatePicker")
app.setDatePicker("invoiceDatePicker", datetime.date.fromordinal(app.getDatePicker("invoiceDatePicker").toordinal() - 1))

app.addButton("Previous ", changeDate, 0, 1)
app.addButton("Today ", changeDate, 1, 1)
app.addButton("Next ", changeDate, 2, 1)

app.addFileEntry("CCEntry", 4, 0)
app.addLabelSpinBox("Detention Charge:", ["0","15","30","45","60","75","90","105","120"], 5, 0)
app.addLabelEntry("Invoice #:", 6, 0)
app.addLabelEntry("LDS #:", 7, 0)
app.addCheckBox("Create Invoice", 8, 0)
app.addCheckBox("Email Invoice", 9, 0)
app.setCheckBox("Create Invoice")
app.setCheckBox("Email Invoice")
app.setSticky("s")
app.addButton("Invoice", press3, 10, 0)
app.stopTab()

# Tab 4
app.startTab("Paperwork Sorter")
app.setInPadding(padding)

app.setSticky("nw")
app.setStretch("column")

app.addFileEntry("fileEntry", 0, 0, 2, 1)
app.addDatePicker("fileSorterDatePicker", 1, 0, 1, 3)
app.setDatePickerRange("fileSorterDatePicker", 2019, 2037)
app.setDatePicker("fileSorterDatePicker")

app.addButton("Previous", changeDate, 1, 1)
app.addButton("Today", changeDate, 2, 1)
app.addButton("Next", changeDate, 3, 1)

app.addRadioButton("file", "Carrier Confirmation", 4, 0)
app.addRadioButton("file", "ACE Manifest", 5, 0)
app.addRadioButton("file", "ACI Manifest", 6, 0)
app.addRadioButton("file", "Contents", 7, 0)
app.addRadioButton("file", "Maple BoL", 8, 0)
app.addRadioButton("file", "Ford BoL", 9, 0)
app.setSticky("s")
app.addButton("Sort", press4, 10, 0)
app.stopTab()

app.stopTabbedFrame()

app.go()
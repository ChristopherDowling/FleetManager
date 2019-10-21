import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

server = smtplib.SMTP(host = "smtp.gmail.com", port = 587)
server.starttls()
server.login("tiberiania@gmail.com", "")

message = MIMEMultipart()
text = "Test email, please ignore"
message["From"] = "tiberiania@gmail.com"
message["To"] = "tiberiania@gmail.com"
message["Subject"] = "Test email"

message.attach(MIMEText(text, "plain"))
server.send_message(message)
del message
print("completed")
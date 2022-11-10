import smtplib, os, json
from email.message import EmailMessage

def notification(message):
    try:
        message = json.loads(message)
        mp3_fid = message["mp3_id"]

        #Using Google SMTP to send the notification and download link to the user's email

        #Setting up the credientials
        sender_address = os.environ.get("GMAIL_ADDRESS")
        sender_password = os.environ.get("GMAIL_PASSWORD")
        receiver_address = message["username"]

        #Setting up the message to be sent
        msg = EmailMessage()
        msg.set_content(f"mp3 file_id: {mp3_fid} is now ready!")
        msg["Subject"] = "MP3 Download"
        msg["From"] = sender_address
        msg["To"] = receiver_address

        # start a session on GMail SMTP
        session = smtplib.SMTP("smtp.gmail.com", 587)
        # Sets the session into TLS (Transport Layer Security) Mode which makessure the transmission between our server
        # is encrypted
        session.starttls()
        session.login(sender_address, sender_password)
        session.send_message(msg, sender_address, receiver_address)
        session.quit()
        print("E-Mail has been sent")
    except Exception as err:
        print(err)
        return err

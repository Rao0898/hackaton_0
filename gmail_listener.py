import os
import time
import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from datetime import datetime

class GmailListener:
    def __init__(self, email_address, password, download_dir=r"D:\hackaton-0\AI_Employee_Vault\Pending_Approval"):
        self.email_address = email_address
        self.password = password
        self.download_dir = download_dir
        self.processed_emails = set()

        os.makedirs(self.download_dir, exist_ok=True)

    def connect_imap(self):
        """Reading ke liye connect karein"""
        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com')
            mail.login(self.email_address, self.password)
            return mail
        except Exception as e:
            print(f"IMAP Connection failed: {str(e)}")
            return None

    def send_reply(self, receiver_email, subject):
        """Reply bhejne ke liye SMTP function"""
        try:
            # SMTP Server connect karein
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_address, self.password)

            # Reply message taiyar karein
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = receiver_email
            msg['Subject'] = "Re: " + subject

            body = "Assalam-o-Alaikum!\n\nMain Zoro AI Assistant hoon Ahmed ka. Aapka email mil gaya hai, ahmed jb free hongy to apko reply karengy. 🤖"
            msg.attach(MIMEText(body, 'plain'))

            # Send Email
            server.send_message(msg)
            server.quit()
            print(f"🚀 SUCCESS: Auto-reply sent to {receiver_email}")
        except Exception as e:
            print(f"❌ Failed to send reply: {str(e)}")

    def clean_filename(self, filename):
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        return filename[:100]

    def get_email_body(self, msg):
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8')
                        break
                    except: continue
        else:
            try: body = msg.get_payload(decode=True).decode('utf-8')
            except: body = ""
        return body

    def check_new_emails(self):
        mail = self.connect_imap()
        if not mail: return []

        try:
            mail.select('inbox')
            status, messages = mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()

            new_emails = []

            for email_id in email_ids:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Get Sender details
                sender_raw = msg['From']
                subject = decode_header(msg['Subject'])[0][0]
                if isinstance(subject, bytes): subject = subject.decode('utf-8')

                # Extract only email address for replying
                sender_email = re.search(r"[\w\.-]+@[\w\.-]+", sender_raw).group(0)
                
                # Extract name for MD file
                sender_name = sender_raw.split('<')[0].strip().replace('"', '')

                date = msg['Date']
                body = self.get_email_body(msg)
                email_uid = f"{sender_email}_{subject}_{date}"

                if email_uid not in self.processed_emails:
                    # 1. Save locally
                    # self.save_email_as_md(sender_name, subject, body, date) # Optional
                    
                    # 2. Send Auto-Reply
                    print(f"🔔 New Email from {sender_email}. Sending reply...")
                    self.send_reply(sender_email, subject)
                    
                    self.processed_emails.add(email_uid)
                    new_emails.append((sender_name, subject))

            mail.close()
            mail.logout()
            return new_emails

        except Exception as e:
            print(f"Error checking emails: {str(e)}")
            return []

    def start_listening(self, interval=60):
        print(f"Zoro Gmail Assistant is Active (Checking every {interval}s)...")
        try:
            while True:
                new_emails = self.check_new_emails()
                if not new_emails:
                    print("Scanning inbox... No new emails.")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nStopped.")

def main():
    # Configuration
    EMAIL_ADDRESS = input("Enter your Gmail address: ")
    # Yad rahe: Regular password nahi, Gmail ka "APP PASSWORD" chahiye
    APP_PASSWORD = input("Enter your Gmail App Password: ")

    listener = GmailListener(EMAIL_ADDRESS, APP_PASSWORD)
    listener.start_listening()

if __name__ == "__main__":
    main()
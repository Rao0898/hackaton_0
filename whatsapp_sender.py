import time
import threading
import re
import pyperclip  # Emojis handle karne ke liye
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class AhmedZoroAssistant:
    def __init__(self):
        self.driver_lock = threading.Lock()
        self.processed_chats = {}
        self.setup_driver()

    def setup_driver(self):
        print("🛠️ Setting up Ahmed's AI Environment...")
        chrome_options = Options()
        chrome_options.add_argument("--user-data-dir=D:\\hackaton-0\\selenium_whatsapp_session")
        chrome_options.add_argument("--profile-directory=Default")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("🌐 Opening WhatsApp Web... Please wait.")
        self.driver.get("https://web.whatsapp.com")
        time.sleep(20)

    def send_reply(self, contact_name):
        with self.driver_lock:
            try:
                # 1. Search Box
                clean_name = re.sub(r'[^\w\s]', '', contact_name).strip()
                print(f"🔍 Ahmed's Zoro is Searching: {clean_name}")

                search_box = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true' and @data-tab='3']"))
                )
                search_box.click()
                search_box.send_keys(Keys.CONTROL + "a", Keys.BACKSPACE)
                time.sleep(1)
                search_box.send_keys(clean_name)
                time.sleep(2)

                # 2. Click Contact
                first_part = clean_name.split()[0]
                contact_xpath = f"//span[contains(@title, '{first_part}')]"
                contact_element = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, contact_xpath))
                )
                contact_element.click()
                print(f"✅ Chat opened for: {contact_name}")
                time.sleep(3)

                # 3. Message Box dhoondna
                try:
                    msg_box = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true' and @data-testid='compose-box-text']"))
                    )
                except:
                    msg_box = self.driver.find_element(By.XPATH, "//footer//div[@contenteditable='true']")
                
                msg_box.click()
                time.sleep(1)

                # 4. Emoji handling via Copy-Paste
                reply_text = "Assalam-o-Alaikum! Main Zoro AI Assistant hoon Ahmed ka. Aapka message mil gaya hai, ahmed jb free hongy to apko thori dair mein reply karengy ok. 🤖"
                
                # Text ko clipboard mein copy karna
                pyperclip.copy(reply_text)
                
                # Message box mein Paste karna (Ctrl + V)
                msg_box.send_keys(Keys.CONTROL + "v")
                time.sleep(1)
                msg_box.send_keys(Keys.ENTER)
                
                print(f"🚀 SUCCESS: Ahmed's reply sent to {contact_name}")
                
                # Search clear karna
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                
            except Exception as e:
                print(f"❌ Error: {e}")
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)

    def monitor_chats(self):
        print("🦅 Zoro is Scanning... Monitoring all incoming messages.")
        while True:
            try:
                unreads = self.driver.find_elements(By.XPATH, "//span[contains(@aria-label, 'unread')] | //span[contains(@class, 'l7jjieqr')]")
                
                for badge in unreads:
                    try:
                        chat_row = badge.find_element(By.XPATH, "./ancestor::div[@role='row']")
                        name_elem = chat_row.find_element(By.XPATH, ".//span[@title]")
                        full_name = name_elem.get_attribute("title")

                        now = time.time()
                        if full_name in self.processed_chats and (now - self.processed_chats[full_name] < 300):
                            continue

                        print(f"🔔 NEW MESSAGE: {full_name}")
                        self.processed_chats[full_name] = now
                        self.send_reply(full_name)
                    except: continue
                time.sleep(3) 
            except Exception as e:
                time.sleep(5)

if __name__ == "__main__":
    assistant = AhmedZoroAssistant()
    assistant.monitor_chats()
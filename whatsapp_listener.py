import os
import time
import random
import shutil
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

def create_md_file(chat_name, unread_count=1):
    """Creates a markdown file with the given content in the Needs_Action folder"""
    folder_path = os.path.join("AI_Employee_Vault", "Needs_Action")

    # Create folder if it doesn't exist
    os.makedirs(folder_path, exist_ok=True)

    # Generate a unique filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"whatsapp_message_{chat_name.replace(' ', '_')}_{timestamp}.md"
    file_path = os.path.join(folder_path, filename)

    # Write content to the file
    content = f"""Platform: WhatsApp
Status: Pending
Content: New message received from {chat_name}

WhatsApp Message Summary:
- Unread message detected from: {chat_name}
- Unread count: {unread_count}
- Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Please process this message appropriately."""

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

    print(f"Created file: {file_path}")
    return file_path

def setup_driver():
    """Sets up Chrome driver with user data directory for session persistence"""
    chrome_options = Options()
    chrome_options.add_argument("--user-data-dir=D:\\hackaton-0\\selenium_whatsapp_session")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Initialize the driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Turn off the automation indicator
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver

def send_message_to_contact(driver, contact_name, message):
    """Sends a message to the specified contact via WhatsApp Web"""
    try:
        print(f"Searching for contact: {contact_name}")

        # Wait for the search box to be available
        search_box = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@contenteditable='true'][@data-testid='search']"))
        )

        # Clear the search box and type the contact name
        search_box.clear()
        search_box.click()
        search_box.send_keys(contact_name)
        time.sleep(2)

        # Wait for the contact to appear in the search results
        contact_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, f"//span[@title='{contact_name}']"))
        )

        # Click on the contact to open the chat
        contact_element.click()
        print(f"Opened chat with {contact_name}")

        # Wait for the message input box to be available
        message_box = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@contenteditable='true'][@data-testid='compose-box-text']"))
        )

        # Clear the message box and type the message
        message_box.click()
        # Select all and delete any existing text
        message_box.send_keys(Keys.CONTROL + "a")
        message_box.send_keys(Keys.DELETE)
        message_box.send_keys(message)

        # Find and click the send button
        send_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-testid='compose-btn-send']"))
        )

        send_button.click()
        print(f"Message sent to {contact_name}: {message[:50]}...")

        return True

    except TimeoutException:
        print(f"Timeout: Could not find contact '{contact_name}' or send message")
        return False
    except NoSuchElementException:
        print(f"Element not found: Could not locate elements for contact '{contact_name}'")
        return False
    except Exception as e:
        print(f"Error sending message to {contact_name}: {str(e)}")
        return False


def extract_contact_and_response(file_path):
    """Extracts contact name and response from the markdown file"""
    contact_name = None
    response = ""

    # Extract contact name from the filename
    filename = os.path.basename(file_path)
    # Handle filenames like response_whatsapp_message_Learn_with_Dr_zain_20260217_145133.md
    if filename.startswith("response_whatsapp_message_"):
        # Extract the contact name part
        parts = filename[len("response_whatsapp_message_"):].split('_')
        # Take everything before the timestamp (last 2 parts: date and time)
        timestamp_parts = 2  # date and time parts
        if len(parts) > timestamp_parts:
            # Reconstruct contact name from remaining parts
            contact_name = ' '.join(parts[:-timestamp_parts]).replace('_', ' ')

    # If contact name wasn't extracted from filename, try from content
    if not contact_name:
        # Extract from original whatsapp_message files moved to General
        if "whatsapp_message_" in filename:
            # Extract from response_whatsapp_message_Contact_Name_Date_Time.md format
            match = re.search(r'response_whatsapp_message_(.+?)_\d{8}_\d{6}', filename)
            if match:
                contact_name = match.group(1).replace('_', ' ')

    # If still no contact name, try to extract from original pending file
    if not contact_name:
        # Try to get contact name from original pending file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for contact name in the original format
        original_match = re.search(r'Unread message detected from: (.+)', content)
        if original_match:
            contact_name = original_match.group(1).strip()

    # If still no contact name, try simpler format
    if not contact_name:
        # Handle simple format like response_ChatGPT.md
        if filename.startswith("response_") and filename.endswith(".md"):
            contact_name = filename[len("response_"):-3].replace('_', ' ')

    # Get the response content (the actual message to send)
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # The entire content (except for the separator) is the response
    lines = content.split('\n')
    response_lines = []
    for line in lines:
        if line.strip() == "--- Task Managed by Zoro ---":
            break
        response_lines.append(line)

    response = '\n'.join(response_lines).strip()

    return contact_name, response


def process_response_file(driver, file_path):
    """Process a response .md file by extracting contact and response, then sending via WhatsApp"""
    print(f"Processing response file: {file_path}")

    try:
        contact_name, response = extract_contact_and_response(file_path)

        if not contact_name:
            print(f"Could not extract contact name from {file_path}")
            return False

        if not response:
            print(f"No response content found in {file_path}")
            return False

        print(f"Extracted - Contact: {contact_name}, Response: {response[:50]}...")

        # Send the message
        success = send_message_to_contact(driver, contact_name, response)

        if success:
            # Move the file to Done folder
            destination_folder = os.path.join("AI_Employee_Vault", "Done")
            os.makedirs(destination_folder, exist_ok=True)

            destination_path = os.path.join(destination_folder, os.path.basename(file_path))
            shutil.move(file_path, destination_path)
            print(f"File moved to: {destination_path}")
            return True
        else:
            print(f"Failed to send message for {file_path}")
            return False

    except Exception as e:
        print(f"Error processing file {file_path}: {str(e)}")
        return False


class FileHandler(FileSystemEventHandler):
    def __init__(self, driver):
        self.driver = driver

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith('.md'):
            # Small delay to ensure file is completely written
            time.sleep(2)
            self.process_file(event.src_path)

    def on_moved(self, event):
        if not event.is_directory and event.dest_path.lower().endswith('.md'):
            # Small delay to ensure file is completely moved
            time.sleep(2)
            self.process_file(event.dest_path)

    def process_file(self, file_path):
        """Process the file if it's a new .md file"""
        if os.path.exists(file_path) and file_path.lower().endswith('.md'):
            # Verify it's actually a response file by checking if it contains response content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Check if it looks like a response file (doesn't start with Platform: WhatsApp)
                    if not content.strip().startswith('Platform: WhatsApp'):
                        print(f"Detected new response file: {file_path}")
                        # Process in a separate thread to avoid blocking the main monitoring loop
                        processing_thread = threading.Thread(target=process_response_file, args=(self.driver, file_path))
                        processing_thread.start()
            except Exception as e:
                print(f"Error reading file {file_path}: {str(e)}")


def main():
    print("Setting up WhatsApp listener...")

    # Setup Chrome driver
    driver = setup_driver()

    try:
        # Set up file watcher for the Needs_Action folder
        watch_folder = os.path.join("AI_Employee_Vault", "Needs_Action")
        os.makedirs(watch_folder, exist_ok=True)

        event_handler = FileHandler(driver)
        observer = Observer()
        observer.schedule(event_handler, watch_folder, recursive=False)
        observer.start()
        print(f"Monitoring folder: {watch_folder}")

        # Open WhatsApp Web
        print("Opening WhatsApp Web...")
        driver.get("https://web.whatsapp.com")

        # Wait for user to press Enter after scanning QR code
        input("Please scan the QR code if prompted, then press Enter to start monitoring...")
        print("Starting monitoring...")

        # Wait a bit for the page to load properly
        time.sleep(10)

        # Track previously seen unread chats with timestamps to avoid duplicate processing
        processed_unreads = {}

        print("Zoro is scanning...")

        while True:
            try:
                # Print scanning status
                print("Zoro is scanning...")

                # Full page scan for unread indicators using comprehensive XPaths
                # Look for elements that might indicate unread messages
                xpaths_to_try = [
                    # Look for any element with aria-label containing 'unread'
                    "//*[contains(@aria-label, 'unread') or contains(@aria-label, 'Unread')]",

                    # Look for elements with unread indicators anywhere on the page
                    "//div[contains(@class, 'unread')]",
                    "//span[contains(@class, 'unread')]",
                    "//div[contains(@class, 'l7jjieqr')]",  # Common unread badge class
                    "//div[contains(@class, '_1XkO3')]",     # Traditional unread indicator
                    "//div[contains(@class, '_1ZMSM')]",     # Another common unread badge class
                    "//div[contains(@class, '_2nYze')]",     # Additional unread indicator
                    "//div[contains(@class, '_2f-Rg')]",     # Unread count indicator
                    "//div[contains(@class, '_3j7s9')]",     # Alternative unread indicator

                    # Look for elements that might contain numbers (unread counts)
                    "//div[contains(text(), '1') or contains(text(), '2') or contains(text(), '3') or contains(text(), '4') or contains(text(), '5') or contains(text(), '6') or contains(text(), '7') or contains(text(), '8') or contains(text(), '9')]",

                    # Look for specific unread badge elements
                    "//span[@data-testid='default-group']",
                    "//span[@data-testid='muted-group']",
                    "//div[@data-icon='chat-unread']",
                    "//div[@data-testid='chat-unread-badge']",

                    # Look for chat items that might have unread indicators
                    "//div[@tabindex='0']//div[contains(@class, 'unread')]",
                    "//div[@tabindex='0']//span[contains(@class, 'unread')]",
                    "//div[@tabindex='0']//div[contains(@class, 'l7jjieqr')]",
                    "//div[@tabindex='0']//div[contains(@class, '_1XkO3')]",

                    # Comprehensive search for chat list items
                    "//div[contains(@class, 'zoWT4') or contains(@class, '_3q44f') or contains(@class, '_2FBdJ') or contains(@class, '_199zI') or contains(@class, '_357i8')]",
                ]

                # Count total elements found for debugging
                total_found = 0

                # Search through all XPaths
                for xpath in xpaths_to_try:
                    try:
                        elements = driver.find_elements(By.XPATH, xpath)
                        if elements:
                            total_found += len(elements)

                            # Check each element individually for unread characteristics
                            for element in elements:
                                try:
                                    # Get element attributes
                                    aria_label = element.get_attribute("aria-label") or ""
                                    text_content = element.text.strip()
                                    element_class = element.get_attribute("class") or ""

                                    # Check if element has characteristics of an unread indicator
                                    is_unread = (
                                        'unread' in aria_label.lower() or
                                        'unread' in element_class.lower() or
                                        text_content.isdigit() and len(text_content) <= 2 and int(text_content) > 0  # Small number indicating unread count
                                    )

                                    if is_unread:
                                        # Try to find the associated chat name
                                        chat_name = "Unknown Contact"

                                        # Look for parent chat container to get contact name
                                        parent = element
                                        for _ in range(5):  # Look up to 5 levels up
                                            try:
                                                # Try to find contact name in parent elements
                                                name_elements = parent.find_elements(By.XPATH, ".//div[@title] | .//span[@title] | .//div[contains(@class, '199zI')] | .//div[contains(@class, '_357i8')]")
                                                if name_elements:
                                                    for name_elem in name_elements:
                                                        if name_elem.text.strip():
                                                            chat_name = name_elem.text.strip()
                                                            break
                                                if chat_name != "Unknown Contact":
                                                    break

                                                # Move to parent element
                                                parent = parent.find_element(By.XPATH, "..")
                                            except:
                                                break

                                        # If we couldn't get the name from parents, try siblings
                                        if chat_name == "Unknown Contact":
                                            try:
                                                # Look for adjacent elements that might contain the name
                                                sibling_names = element.find_elements(By.XPATH, "./preceding-sibling::div[@title] | ./following-sibling::div[@title] | ./preceding-sibling::span[@title] | ./following-sibling::span[@title]")
                                                for name_elem in sibling_names:
                                                    if name_elem.text.strip():
                                                        chat_name = name_elem.text.strip()
                                                        break
                                            except:
                                                pass

                                        # Determine unread count
                                        unread_count = 1
                                        if text_content.isdigit():
                                            unread_count = int(text_content)

                                        # Check if this chat has been processed in the last 2 minutes
                                        current_time = time.time()
                                        if chat_name in processed_unreads:
                                            last_processed_time = processed_unreads[chat_name]
                                            if current_time - last_processed_time < 120:  # 2 minutes cooldown
                                                print(f"Skipping {chat_name} - cooldown active ({int(current_time - last_processed_time)}s remaining)")
                                                continue

                                        # Update the last processed time for this chat
                                        processed_unreads[chat_name] = current_time

                                        # Create markdown file for this unread message
                                        create_md_file(chat_name, unread_count)
                                        print(f"✅ Alert saved! Unread message from: {chat_name} (Count: {unread_count})")

                                except Exception as e:
                                    # Skip individual element if there's an error
                                    continue

                    except Exception as e:
                        # Continue if a particular XPath fails
                        continue

                # Also scan the chat list panel specifically
                try:
                    # Target the main chat list panel
                    chat_list_selectors = [
                        "div[aria-label='Chat list']",
                        "div[aria-label='Chats']",
                        "div[data-testid='chat-list']",
                        "div._3q44f",
                        "div._2FBdJ"
                    ]

                    chat_list_found = False
                    for selector in chat_list_selectors:
                        try:
                            chat_panels = driver.find_elements(By.CSS_SELECTOR, selector)
                            if chat_panels:
                                chat_list_found = True
                                for panel in chat_panels:
                                    # Find all chat items in the panel
                                    chat_items = panel.find_elements(By.XPATH, ".//div[@tabindex='0']")

                                    for chat_item in chat_items:
                                        try:
                                            # Check for unread indicators within each chat item
                                            unread_elements = chat_item.find_elements(By.XPATH,
                                                ".//div[contains(@class, 'l7jjieqr') or contains(@class, '_1XkO3') or contains(@class, '_1ZMSM') or contains(@class, '_2nYze') or contains(@class, '_2f-Rg') or contains(@class, '_3j7s9') or @data-testid='default-group' or @data-testid='muted-group']")

                                            if unread_elements:
                                                # Get the chat name from this item
                                                name_elements = chat_item.find_elements(By.XPATH,
                                                    ".//div[@title] | .//span[@title] | .//div[contains(@class, '199zI')] | .//div[contains(@class, '_357i8')]")

                                                chat_name = "Unknown Contact"
                                                for name_elem in name_elements:
                                                    if name_elem.text.strip():
                                                        chat_name = name_elem.text.strip()
                                                        break

                                                # Get unread count
                                                unread_count = 1
                                                for unread_elem in unread_elements:
                                                    elem_text = unread_elem.text.strip()
                                                    if elem_text.isdigit():
                                                        unread_count = int(elem_text)
                                                        break

                                                # Check if this chat has been processed in the last 2 minutes
                                                current_time = time.time()
                                                if chat_name in processed_unreads:
                                                    last_processed_time = processed_unreads[chat_name]
                                                    if current_time - last_processed_time < 120:  # 2 minutes cooldown
                                                        print(f"Skipping {chat_name} - cooldown active ({int(current_time - last_processed_time)}s remaining)")
                                                        continue

                                                # Update the last processed time for this chat
                                                processed_unreads[chat_name] = current_time

                                                create_md_file(chat_name, unread_count)
                                                print(f"✅ Alert saved! Unread message from: {chat_name} (Count: {unread_count})")

                                        except Exception:
                                            continue

                                break  # Stop after finding the first valid chat panel

                        except Exception:
                            continue

                except Exception:
                    pass  # Continue even if chat list scan fails

                # Clean up old entries from processed_unreads that are older than 2 minutes
                current_time = time.time()
                processed_unreads = {
                    chat: timestamp
                    for chat, timestamp in processed_unreads.items()
                    if current_time - timestamp < 120
                }

                # Debug output
                print(f"🔍 Debug: Found {total_found} potential elements during scan")
                print(f"📊 Active cooldowns: {len(processed_unreads)} contacts")

                # Wait 5-10 seconds before checking again
                sleep_time = 5 + random.randint(0, 5)  # Random wait between 5-10 seconds
                time.sleep(sleep_time)

            except Exception as e:
                print(f"An error occurred during monitoring: {str(e)}")
                time.sleep(10)  # Wait 10 seconds before retrying
                print("Zoro is scanning...")

    except KeyboardInterrupt:
        print("\nStopping WhatsApp listener...")
    finally:
        observer.stop()
        observer.join()
        driver.quit()

if __name__ == "__main__":
    main()
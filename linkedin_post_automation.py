import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_chrome_driver():
    """Setup Chrome driver with saved session data"""
    chrome_options = Options()

    # Add the user data directory for session persistence
    chrome_options.add_argument(f"--user-data-dir={os.path.abspath('linkedin_session')}")

    # Additional options for stability
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Install and setup ChromeDriver using webdriver_manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Execute script to remove webdriver property
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver

def wait_and_click(driver, xpath, timeout=10):
    """Helper function to wait for element and click it"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        element.click()
        return True
    except TimeoutException:
        logger.error(f"Element not found or clickable: {xpath}")
        return False

def wait_for_element(driver, xpath, timeout=10):
    """Helper function to wait for element to be present"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return element
    except TimeoutException:
        logger.error(f"Element not found: {xpath}")
        return None

def post_on_linkedin(image_path, caption_text):
    """Main function to post on LinkedIn with image and text"""

    # Validate image file exists
    if not os.path.exists(image_path):
        logger.error(f"Image file does not exist: {image_path}")
        return False

    driver = None
    try:
        # Setup Chrome driver
        logger.info("Setting up Chrome driver with saved session...")
        driver = setup_chrome_driver()

        # Navigate to LinkedIn feed
        logger.info("Navigating to LinkedIn feed...")
        driver.get("https://www.linkedin.com/feed/")

        # Wait for page to load
        time.sleep(3)

        # Step 1: Click on "Start a post" - multiple possible selectors
        logger.info("Looking for 'Start a post' button...")
        start_post_selectors = [
            "//button[contains(@class, 'share-box-feed-entry__trigger')]",
            "//button[contains(@aria-label, 'Start a post')]",
            "//button[contains(text(), 'Start a post')]",
            "//button[contains(@data-control-name, 'share_post')]",
            "//button[contains(@class, 'artdeco-button') and contains(@aria-label, 'Share')]"
        ]

        start_post_clicked = False
        for selector in start_post_selectors:
            if wait_and_click(driver, selector, timeout=5):
                logger.info(f"Clicked 'Start a post' using selector: {selector}")
                start_post_clicked = True
                break

        if not start_post_clicked:
            logger.error("Could not find 'Start a post' button")
            return False

        # Wait for the post composer to appear
        time.sleep(2)

        # Step 2: Find the file input element and send the image path
        logger.info("Looking for file input for image upload...")
        file_input_selectors = [
            "//input[@type='file' and contains(@accept, 'image')]",
            "//input[@type='file' and @accept='image/*']",
            "//input[@type='file' and contains(@class, 'file-input')]",
            "//input[@type='file' and contains(@id, 'file')]"
        ]

        file_input_found = False
        for selector in file_input_selectors:
            try:
                file_input = wait_for_element(driver, selector, timeout=5)
                if file_input:
                    logger.info(f"Found file input element, uploading image: {image_path}")
                    file_input.send_keys(os.path.abspath(image_path))
                    file_input_found = True
                    break
            except Exception as e:
                logger.warning(f"Could not use file input selector {selector}: {e}")
                continue

        if not file_input_found:
            logger.error("Could not find file input for image upload")
            return False

        # Wait for image to upload
        time.sleep(5)

        # Step 3: Click "Done" or "Next" button after image upload
        logger.info("Looking for 'Done' or 'Next' button after image upload...")
        done_next_selectors = [
            "//button[contains(text(), 'Done')]",
            "//button[contains(text(), 'Next')]",
            "//button[contains(@aria-label, 'Done')]",
            "//button[contains(@aria-label, 'Next') and contains(@class, 'artdeco-button')]",
            "//button[contains(@data-test-id, 'done')]"
        ]

        done_next_clicked = False
        for selector in done_next_selectors:
            if wait_and_click(driver, selector, timeout=5):
                logger.info(f"Clicked 'Done/Next' button using selector: {selector}")
                done_next_clicked = True
                break

        # Wait a bit more for the post editor to update
        time.sleep(3)

        # Step 4: Add caption text to the content area
        logger.info("Adding caption text...")
        caption_selectors = [
            "//div[@contenteditable='true' and contains(@class, 'mentions-texteditor__contenteditable')]",
            "//div[@contenteditable='true' and contains(@role, 'textbox')]",
            "//div[@contenteditable='true' and contains(@data-placeholder, 'Share your thoughts')]",
            "//div[@contenteditable='true' and contains(@aria-label, 'Share your thoughts')]",
            "//div[contains(@class, 'share-creation-state') and @contenteditable='true']"
        ]

        caption_added = False
        for selector in caption_selectors:
            try:
                caption_area = wait_for_element(driver, selector, timeout=5)
                if caption_area:
                    # Clear any existing content and add new text
                    driver.execute_script("arguments[0].innerHTML = arguments[1];", caption_area, "")
                    caption_area.send_keys(caption_text)
                    logger.info("Caption text added successfully")
                    caption_added = True
                    break
            except Exception as e:
                logger.warning(f"Could not add caption using selector {selector}: {e}")
                continue

        if not caption_added:
            logger.error("Could not find caption area to add text")
            return False

        # Wait a moment for the text to be processed
        time.sleep(2)

        # Step 5: Click the final "Post" button
        logger.info("Looking for final 'Post' button...")
        post_selectors = [
            "//button[contains(text(), 'Post') and contains(@class, 'share-actions__primary-action-btn')]",
            "//button[contains(text(), 'Post') and contains(@class, 'artdeco-button--primary')]",
            "//button[contains(text(), 'Post') and contains(@aria-label, 'Post')]",
            "//button[contains(@data-control-name, 'share.post') and contains(text(), 'Post')]",
            "//button[contains(@class, 'artdeco-button') and contains(@class, 'artdeco-button--primary') and contains(text(), 'Post')]"
        ]

        post_clicked = False
        for selector in post_selectors:
            if wait_and_click(driver, selector, timeout=5):
                logger.info(f"Clicked 'Post' button using selector: {selector}")
                post_clicked = True
                break

        if not post_clicked:
            logger.error("Could not find 'Post' button")
            return False

        # Wait for post to be submitted
        time.sleep(5)

        logger.info("LinkedIn post submitted successfully!")
        return True

    except Exception as e:
        logger.error(f"An error occurred during the posting process: {str(e)}")
        return False

    finally:
        # Close the driver
        if driver:
            logger.info("Closing browser...")
            driver.quit()

if __name__ == "__main__":
    # Define paths and text
    image_path = os.path.join("insta_Posts", "insta-post.jpeg")
    caption_text = "Zoro AI is officially automating LinkedIn! 🤖 #Hackathon2026 #AI"

    # Execute the post function
    success = post_on_linkedin(image_path, caption_text)

    if success:
        print("LinkedIn post created successfully!")
    else:
        print("Failed to create LinkedIn post. Please check the logs for details.")
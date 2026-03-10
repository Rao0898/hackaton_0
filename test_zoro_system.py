import os
import time
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_directory_structure():
    """Test that all required directories exist under AI_Employee_Vault"""
    required_dirs = [
        'AI_Employee_Vault/Needs_Action',
        'AI_Employee_Vault/Pending_Approval',
        'AI_Employee_Vault/Approved',
        'AI_Employee_Vault/Done'
    ]

    print("Testing directory structure...")
    all_exist = True

    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"[OK] {dir_name}/ directory exists")
        else:
            print(f"[ERROR] {dir_name}/ directory missing")
            all_exist = False

    return all_exist

def test_scripts_exist():
    """Test that required scripts exist"""
    required_scripts = ['zoro_orchestration.py', 'linkedin_post_automation.py', 'insta-post.py']

    print("\nTesting required scripts...")
    all_exist = True

    for script in required_scripts:
        if os.path.exists(script):
            print(f"[OK] {script} exists")
        else:
            print(f"[ERROR] {script} missing")
            all_exist = False

    return all_exist

def test_sample_files():
    """Test that sample files were created correctly"""
    print("\nTesting sample files...")

    # Check if sample WhatsApp message exists in the new location
    whatsapp_msg_path = Path("AI_Employee_Vault/Needs_Action") / "whatsapp_message_test.md"
    if whatsapp_msg_path.exists():
        print(f"[OK] Sample WhatsApp message exists: {whatsapp_msg_path}")
    else:
        print(f"[ERROR] Sample WhatsApp message missing: {whatsapp_msg_path}")

    # Check if sample LinkedIn task exists in the new location
    linkedin_task_path = Path("AI_Employee_Vault/Approved") / "sample_linkedin_task.md"
    if linkedin_task_path.exists():
        print(f"[OK] Sample LinkedIn task exists: {linkedin_task_path}")
    else:
        print(f"[ERROR] Sample LinkedIn task missing: {linkedin_task_path}")

    return whatsapp_msg_path.exists() and linkedin_task_path.exists()

def test_requirements():
    """Test that requirements file has all needed dependencies"""
    print("\nTesting requirements.txt...")

    with open('requirements.txt', 'r') as f:
        requirements = f.read()

    required_packages = ['selenium', 'webdriver-manager', 'Pillow', 'watchdog']
    all_present = True

    for package in required_packages:
        if package in requirements:
            print(f"[OK] {package} in requirements.txt")
        else:
            print(f"[ERROR] {package} missing from requirements.txt")
            all_present = False

    return all_present

def main():
    """Run all tests"""
    print("[INFO] Testing Zoro Orchestration System Setup\n")

    dir_test = test_directory_structure()
    script_test = test_scripts_exist()
    file_test = test_sample_files()
    req_test = test_requirements()

    print(f"\n[Test Results:]")
    print(f"Directory structure: {'PASS' if dir_test else 'FAIL'}")
    print(f"Required scripts: {'PASS' if script_test else 'FAIL'}")
    print(f"Sample files: {'PASS' if file_test else 'FAIL'}")
    print(f"Requirements: {'PASS' if req_test else 'FAIL'}")

    overall = all([dir_test, script_test, file_test, req_test])
    print(f"\nOverall: {'PASS' if overall else 'FAIL'}")

    if overall:
        print("\n[Zoro Orchestration System is properly set up!]")
        print("\nTo run the system:")
        print("  python zoro_orchestration.py")
        print("\nThe system will:")
        print("  - Monitor AI_Employee_Vault/Approved/ for new tasks")
        print("  - Process WhatsApp messages in AI_Employee_Vault/Needs_Action/")
        print("  - Execute LinkedIn/Instagram posts as requested")
        print("  - Move completed tasks to AI_Employee_Vault/Done/")
        print("  - Create post drafts in AI_Employee_Vault/Pending_Approval/")
    else:
        print("\n[Please fix the above issues before running the system]")

if __name__ == "__main__":
    main()
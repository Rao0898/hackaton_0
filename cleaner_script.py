import os
import time
from datetime import datetime, timedelta

def clean_duplicate_files():
    """
    Cleans duplicate WhatsApp message files based on contact name.
    Keeps the most recent file for each contact and removes older ones.
    """
    folder_path = r"D:\hackaton-0\AI_Employee_Vault\Pending_Approval"

    if not os.path.exists(folder_path):
        print(f"Folder does not exist: {folder_path}")
        return

    # Get all WhatsApp message files
    files = []
    for filename in os.listdir(folder_path):
        if filename.startswith("whatsapp_message_") and filename.endswith(".md"):
            filepath = os.path.join(folder_path, filename)
            creation_time = os.path.getctime(filepath)
            # Extract contact name from filename (part between 'whatsapp_message_' and first '_timestamp')
            parts = filename.replace('.md', '').split('_')
            if len(parts) >= 3:
                # Reconstruct the contact name (which might have underscores)
                contact_name = '_'.join(parts[2:-2]) if len(parts) > 4 else parts[2]
                files.append({
                    'filename': filename,
                    'filepath': filepath,
                    'contact': contact_name,
                    'time': creation_time
                })

    if not files:
        print("No WhatsApp message files found to clean.")
        return

    print(f"Found {len(files)} WhatsApp message files to process.")

    # Group files by contact name
    contacts = {}
    for file_info in files:
        contact = file_info['contact']
        if contact not in contacts:
            contacts[contact] = []
        contacts[contact].append(file_info)

    files_deleted = 0
    files_kept = 0

    # For each contact, keep only the most recent file
    for contact, contact_files in contacts.items():
        if len(contact_files) <= 1:
            # Only one file for this contact, keep it
            files_kept += len(contact_files)
            continue

        # Sort files by creation time (most recent first)
        contact_files.sort(key=lambda x: x['time'], reverse=True)

        # Keep the most recent file, delete the rest
        kept_file = contact_files[0]
        files_kept += 1

        for old_file in contact_files[1:]:
            try:
                os.remove(old_file['filepath'])
                print(f"Deleted duplicate: {old_file['filename']}")
                files_deleted += 1
            except Exception as e:
                print(f"Could not delete {old_file['filename']}: {str(e)}")

    print(f"\nCleanup complete!")
    print(f"Files deleted: {files_deleted}")
    print(f"Files kept: {files_kept}")

def clean_old_files(days_old=7):
    """
    Removes files older than specified days
    """
    folder_path = r"D:\hackaton-0\AI_Employee_Vault\Pending_Approval"

    if not os.path.exists(folder_path):
        print(f"Folder does not exist: {folder_path}")
        return

    cutoff_time = time.time() - (days_old * 24 * 60 * 60)
    files_deleted = 0

    for filename in os.listdir(folder_path):
        if filename.startswith("whatsapp_message_") and filename.endswith(".md"):
            filepath = os.path.join(folder_path, filename)
            file_time = os.path.getctime(filepath)

            if file_time < cutoff_time:
                try:
                    os.remove(filepath)
                    print(f"Deleted old file: {filename}")
                    files_deleted += 1
                except Exception as e:
                    print(f"Could not delete {filename}: {str(e)}")

    if files_deleted > 0:
        print(f"Removed {files_deleted} files older than {days_old} days.")
    else:
        print(f"No files older than {days_old} days found.")

if __name__ == "__main__":
    print("WhatsApp Message File Cleaner")
    print("=" * 40)

    print("\nStep 1: Removing duplicate files (keeping most recent for each contact)...")
    clean_duplicate_files()

    print("\nStep 2: Removing files older than 7 days...")
    clean_old_files(7)

    print("\nAll cleanup tasks completed!")
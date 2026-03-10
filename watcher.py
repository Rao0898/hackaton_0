import os
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class MarkdownFileHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        # Define source and destination folders
        self.source_folder = r"D:\hackaton-0\AI_Employee_Vault\Pending_Approval"
        self.dest_folder = r"D:\hackaton-0\AI_Employee_Vault\Needs_Action"

        # Define the Employee Rules file path
        self.employee_rules_path = r"D:\hackaton-0\AI_Employee_Vault\Employee_Rules.md"

        # Create destination folder if it doesn't exist
        os.makedirs(self.dest_folder, exist_ok=True)

        # Set to keep track of processed files to prevent double processing
        self.processed_files = set()

    def is_markdown_file(self, file_path):
        """Check if the file is a markdown file (ends with .md)"""
        _, ext = os.path.splitext(file_path)
        return ext.lower() == '.md'

    def process_markdown_file(self, file_path):
        """Process the markdown file: read content, execute claude command, move file"""
        file_name = os.path.basename(file_path)

        # Check if the filename is 'Untitled.md' and return if it is
        if file_name == 'Untitled.md':
            print(f"Skipping Untitled.md file: {file_path}")
            return

        # Check if file has already been processed recently
        if file_path in self.processed_files:
            print(f"File already processed recently, skipping: {file_name}")
            return

        # Add file to processed set to prevent double processing
        self.processed_files.add(file_path)

        # Sleep at the very beginning
        time.sleep(2)

        # Use absolute path to ensure path is correct for Windows
        abs_file_path = os.path.abspath(file_path)

        # Retry logic: try to find the file 5 times with 1-second delay
        found = False
        for attempt in range(5):
            print(f'Attempting to access: {abs_file_path}')

            if os.path.exists(abs_file_path):
                found = True
                break
            else:
                time.sleep(1)  # 1-second delay between tries

        # If file still doesn't exist after 5 attempts, give up
        if not found:
            print(f'Gave up on file: {file_name}')
            self.processed_files.discard(file_path)
            return

        content = None

        try:
            # Read the content of the file only if it exists
            if os.path.exists(abs_file_path):
                with open(abs_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()  # Move content reading to local variable immediately

                # Read the Employee Rules file if it exists
                rules_content = ""
                if os.path.exists(self.employee_rules_path):
                    try:
                        with open(self.employee_rules_path, 'r', encoding='utf-8') as f:
                            rules_content = f.read()
                        print(f"Employee rules loaded from: {self.employee_rules_path}")
                    except Exception as e:
                        print(f"Could not read employee rules file: {str(e)}, proceeding with user content only")
                        rules_content = ""
                else:
                    print(f"Employee rules file not found: {self.employee_rules_path}, proceeding with user content only")

                # Check if the content contains 'Platform: Gmail'
                if 'Platform: Gmail' in content:
                    # Emphasize that Claude should use the Gmail-specific professional format
                    combined_input = rules_content + "\n\nIMPORTANT: Since this message is from Gmail platform, please use the Gmail-specific professional format as mentioned in the rules: 'Dear Sender, I hope you are doing well. This is Zoro, Ahmed's Personal AI Assistant. Ahmed is currently participating in 'Hackathon' and is unavailable to check his emails personally at the moment. I have logged your request, and he will get back to you as soon as the event concludes. Best Regards, Zoro (AI Assistant).' Use this exact format for the response.\n\n" + content if rules_content else content
                else:
                    # Combine the rules and user content normally
                    combined_input = rules_content + "\n\n" + content if rules_content else content

                print(f"Processing file: {file_name}")
                print(f"File content length: {len(content)} characters")
                print(f"Combined input length (rules + user content): {len(combined_input)} characters")

                # Execute the claude command with the combined input as a prompt
                print("--- STARTING CLAUDE CALL ---")  # Clear message before subprocess
                result = subprocess.run(['ccr', 'code'], input=combined_input, capture_output=True, text=True, shell=True)  # Use input parameter for pipe

                if result.returncode == 0:
                    print(f"Claude command executed successfully for {file_name}")
                    print(f"Actual Claude output: {result.stdout}")  # Show the actual output from Claude

                    # Determine the appropriate subfolder based on the response content
                    response_content = result.stdout
                    if '```' in response_content:
                        # Contains code blocks, save to Coding folder
                        subfolder = os.path.join(self.dest_folder, "Coding")
                    elif len(response_content.split()) > 50:  # If it's longer text (writing)
                        # Likely contains longer writing, save to Writing folder
                        subfolder = os.path.join(self.dest_folder, "Writing")
                    else:
                        # Default to General folder
                        subfolder = os.path.join(self.dest_folder, "General")

                    # Create the subfolder if it doesn't exist
                    os.makedirs(subfolder, exist_ok=True)

                    # Save the stdout result to a response file in the appropriate subfolder
                    response_filename = f"response_{file_name}"
                    response_path = os.path.join(subfolder, response_filename)

                    try:
                        with open(response_path, 'w', encoding='utf-8') as f:
                            f.write(result.stdout)
                        print(f"Response saved to: {response_path}")

                        # Only after saving the response file, move/delete the original file
                        source_path = abs_file_path
                        if os.path.exists(source_path):
                            os.remove(source_path)  # Delete the original file
                            print(f"Original file {file_name} deleted after saving response")
                    except Exception as e:
                        print(f"Error saving response file or deleting original: {str(e)}")
                        # Don't remove from processed set if there was an error in post-processing
                        return
                else:
                    print(f"Error executing claude command for {file_name}: {result.stderr}")
                    # Don't move the file - leave it in place for debugging
                    # Remove from processed set since there was an error
                    self.processed_files.discard(file_path)
                    return

        except FileNotFoundError:
            print(f"File not found: {abs_file_path}")
            # Remove from processed set since we couldn't process it
            self.processed_files.discard(file_path)
            return
        except Exception as e:
            print(f"Error processing file {abs_file_path}: {str(e)}")
            # Remove from processed set since we couldn't process it
            self.processed_files.discard(file_path)
            return


    def on_created(self, event):
        # Print any event detected to see if the watcher is working
        print(f"Event detected: {event.event_type} - Path: {event.src_path}")

        # Check if the created file is a .md file
        if not event.is_directory and self.is_markdown_file(event.src_path):
            self.process_markdown_file(event.src_path)

    def on_modified(self, event):
        # Handle modified events as well, since Windows sometimes triggers this instead of 'created'
        print(f"Modified event detected: {event.event_type} - Path: {event.src_path}")

        # Check if the modified file is a .md file
        if not event.is_directory and self.is_markdown_file(event.src_path):
            self.process_markdown_file(event.src_path)


def watch_folder(folder_path):
    # Create event handler
    event_handler = MarkdownFileHandler()

    # Create observer
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=False)

    # Start the observer
    observer.start()
    print(f"Watching folder: {folder_path} for .md files...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopping file watcher...")

    observer.join()


if __name__ == "__main__":
    # Define the folder to watch
    folder_to_watch = r"D:\hackaton-0\AI_Employee_Vault\Pending_Approval"

    # Check if the folder exists
    if not os.path.exists(folder_to_watch):
        print(f"Error: Folder does not exist: {folder_to_watch}")
    else:
        watch_folder(folder_to_watch)
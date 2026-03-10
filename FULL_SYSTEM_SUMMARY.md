# AI Employee Zoro - Complete System Overview

## Project Structure

```
D:\hackaton-0\
├── AI_Employee_Vault/       # Main vault system
│   ├── Needs_Action/        # Raw WhatsApp messages and tasks needing attention
│   ├── Pending_Approval/    # Summarized content awaiting approval
│   ├── Approved/            # Approved tasks ready for execution
│   └── Done/                # Completed tasks
├── insta_Posts/             # Instagram post assets
├── linkedin_session/        # LinkedIn Chrome session data
├── selenium_whatsapp_session/ # WhatsApp session data
├── zoro_orchestration.py    # Main orchestration system
├── linkedin_post_automation.py # LinkedIn automation script
├── insta-post.py            # Instagram automation script (placeholder)
├── whatsapp_listener.py     # WhatsApp message listener
├── gmail_listener.py        # Gmail message listener
├── whatsapp_sender.py       # WhatsApp message sender
├── requirements.txt         # Dependencies
├── ORCHESTRATION_README.md  # Orchestration documentation
├── README.md               # Main project documentation
└── start_zoro.bat          # Startup script
```

## System Components

### 1. Listener Components (Already Built)
- **whatsapp_listener.py**: Monitors WhatsApp for incoming messages
- **gmail_listener.py**: Monitors Gmail for incoming messages

### 2. Execution Components (Already Built)
- **linkedin_post_automation.py**: Automates LinkedIn posts with image and text
- **insta-post.py**: Placeholder for Instagram post automation
- **whatsapp_sender.py**: Sends WhatsApp messages

### 3. Orchestration Component (Newly Built)
- **zoro_orchestration.py**: Main orchestration system that:
  - Monitors `AI_Employee_Vault/Approved/` folder for new tasks
  - Executes appropriate actions based on file content
  - Moves completed files to `AI_Employee_Vault/Done/` folder
  - Processes raw WhatsApp messages into post drafts
  - Places drafts in `AI_Employee_Vault/Pending_Approval/` for review

## How the System Works

### Task Execution Flow
1. User places a file in `AI_Employee_Vault/Approved/` folder
2. File content determines the action:
   - Contains "Action: LinkedIn" → Runs `linkedin_post_automation.py`
   - Contains "Action: Instagram" → Runs `insta-post.py`
3. After execution, file is moved to `AI_Employee_Vault/Done/` folder
4. All activities are logged

### Message Summarization Flow
1. Raw WhatsApp messages are placed in `AI_Employee_Vault/Needs_Action/` folder
2. Orchestration system periodically scans for new messages
3. Converts raw messages into clean post drafts
4. Places drafts in `AI_Employee_Vault/Pending_Approval/` folder
5. Original messages are archived

## Usage

### Running the System
```
python zoro_orchestration.py
```
Or use the batch file:
```
start_zoro.bat
```

### Creating Tasks
To trigger a LinkedIn post, create a file in `AI_Employee_Vault/Approved/` with content:
```
Action: LinkedIn
Post: New product launch announcement
```

To trigger an Instagram post, create a file in `AI_Employee_Vault/Approved/` with content:
```
Action: Instagram
Post: Weekly update with team photo
```

## Dependencies
- selenium: Web automation
- webdriver-manager: ChromeDriver management
- Pillow: Image handling
- watchdog: File system monitoring

## Error Handling
- Failed executions are logged but files are still moved to done directory
- Timeouts prevent hanging processes
- Graceful handling of missing files/scripts
- Comprehensive logging to both console and file

## Security Considerations
- Chrome sessions are persisted in dedicated directories
- All sensitive automation handled through established session data
- No credentials stored in plain text
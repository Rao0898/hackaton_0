# AI Employee Zoro - Orchestration System

This orchestration script manages the complete workflow for the AI Employee "Zoro", handling task execution and message summarization.

## Components

### Directory Structure
- `AI_Employee_Vault/Needs_Action/` - Raw WhatsApp messages and tasks needing attention
- `AI_Employee_Vault/Pending_Approval/` - Summarized content awaiting approval
- `AI_Employee_Vault/Approved/` - Approved tasks ready for execution
- `AI_Employee_Vault/Done/` - Completed tasks

### Core Functions

#### 1. Task Execution
- Monitors `AI_Employee_Vault/Approved/` directory for new files
- Reads file content to determine action:
  - `Action: LinkedIn` → Executes `linkedin_post_automation.py`
  - `Action: Instagram` → Executes `insta-post.py`
- Moves processed files to `AI_Employee_Vault/Done/` directory

#### 2. Message Summarization
- Periodically scans `AI_Employee_Vault/Needs_Action/` for WhatsApp messages
- Converts raw messages into clean post drafts
- Places drafts in `AI_Employee_Vault/Pending_Approval/` for review
- Archives processed messages to prevent duplicate processing

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure the following scripts exist:
   - `linkedin_post_automation.py` (for LinkedIn posts)
   - `insta-post.py` (for Instagram posts)

3. Create the required directory structure (script will create if missing).

## Usage

Run the orchestration system:
```bash
python zoro_orchestration.py
```

## Example Task File

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

## Logging

All activities are logged to both console and `zoro_orchestration.log` file.

## Error Handling

- Failed executions are logged but files are still moved to done directory
- Timeouts prevent hanging processes
- Graceful handling of missing files/scripts
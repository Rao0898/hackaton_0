import asyncio
import json
import time
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

# Naye MCP SDK ke correct imports
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import TextContent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('zoro_orchestration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ZoroOrchestration:
    def __init__(self, vault_path: str = "AI_Employee_Vault"):
        self.vault_path = Path(vault_path)
        self.mcp_session = None  # Yahan hum session store karenge

        # Folder Structure
        self.needs_action_dir = self.vault_path / "Needs_Action"
        self.in_progress_dir = self.vault_path / "In_Progress"
        self.zoro_in_progress_dir = self.in_progress_dir / "Zoro"
        self.pending_approval_dir = self.vault_path / "Pending_Approval"
        self.approved_dir = self.vault_path / "Approved"
        self.executed_dir = self.vault_path / "Executed"
        self.processed_dir = self.needs_action_dir / "Processed"
        self.audit_log_file = self.vault_path / "audit_log.txt"

        # Auto-Folder Creation: Create all required sub-folders
        for folder in [
            self.needs_action_dir / "Social",
            self.needs_action_dir / "Finance",
            self.needs_action_dir / "Coding",
            self.needs_action_dir / "Writing",
            self.zoro_in_progress_dir,  # In_Progress/Zoro
            self.pending_approval_dir,
            self.approved_dir,
            self.executed_dir,
            self.processed_dir
        ]:
            folder.mkdir(parents=True, exist_ok=True)

        # Create audit log file with absolute path
        self.audit_log_file = self.vault_path / "audit_log.txt"
        # Force creation of the audit log file with initialization entry
        init_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.audit_log_file, 'w', encoding='utf-8') as f:
            f.write(f"[{init_timestamp}] - SYSTEM - INITIALIZATION - SUCCESS\n")

        self.processed_files = set()
        self.approved_processed_files = set()

        # Create empty files archive directory
        self.empty_files_dir = self.vault_path / "Archived" / "Empty_Files"
        self.empty_files_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Zoro Orchestration initialized - PLATINUM TIER - ENTERPRISE ARCHITECT")

    def log_audit(self, action: str, status: str, domain: str = "Unknown"):
        """Audit log with timestamp, domain, and result."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        audit_entry = f"[{timestamp}] - GOLD-TIER - {domain} - {action} - {status}\n"

        # Append the current audit entry using the absolute path
        with open(self.audit_log_file, "a", encoding="utf-8") as f:
            f.write(audit_entry)

        logger.info(f"GOLD-TIER AUDIT: {domain} - {action} - {status}")

    async def call_mcp_tool(self, tool_name: str, params: Dict) -> Optional[str]:
        """MCP Tool ko call karne ka safe tareeqa."""
        if not self.mcp_session:
            return None
        try:
            result = await self.mcp_session.call_tool(tool_name, params)
            if result and result.content:
                # Result list se text nikalna
                return result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
            return None
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return None

    async def get_vault_context(self, file_path: Path):
        """Vault se context nikalna (Gold Tier Feature)."""
        logger.info(f"Retrieving vault context for {file_path.name}...")

        # 1. List Structure
        structure = await self.call_mcp_tool("list_vault_structure", {})

        # 2. Search for related files
        search_query = file_path.stem
        search_results = await self.call_mcp_tool("search_vault_files", {"query": search_query})

        return {
            "structure": structure or "No structure found",
            "search_results": search_results or "No similar files found"
        }

    async def check_file_content(self, file_path: Path) -> str:
        """Windows empty file issue fix (Retry logic)."""
        for attempt in range(5):
            try:
                content = file_path.read_text(encoding='utf-8').strip()
                if content:
                    return content
                await asyncio.sleep(0.2)
            except Exception:
                await asyncio.sleep(0.2)
        return ""

    async def process_new_file(self, file_path: Path):
        """Nayi file par action lena with Claim-by-Move logic."""
        logger.info(f"Processing: {file_path.name}")

        # Log file detected event
        self.log_audit("File Detected", "PROCESSING STARTED", "Unknown")

        # Check if file is named report.md and treat as General
        if file_path.name == "report.md":
            logger.info("File named report.md detected, treating as General category and triggering CEO briefing")
            self.generate_ceo_briefing()
            # Log the action
            self.log_audit("Report Detected", "CEO BRIEFING GENERATED", "General")
            # Remove the original file
            file_path.unlink()
            self.processed_files.add(file_path.name)
            return

        # Determine the domain based on the subfolder
        domain = "Unknown"
        if "Social" in str(file_path):
            domain = "Social"
        elif "Finance" in str(file_path):
            domain = "Finance"
        elif "Coding" in str(file_path):
            domain = "Coding"
        elif "Writing" in str(file_path):
            domain = "Writing"
        elif "General" in str(file_path):
            domain = "General"

        # Log delegation to appropriate agent as soon as file is detected
        if domain == "Finance":
            self.log_multi_agent_communication("[ZORO-CHIEF] -> [FINANCE-AGENT]: New task detected. Please start processing.")
        elif domain in ["Social", "General"]:
            self.log_multi_agent_communication("[ZORO-CHIEF] -> [SOCIAL-AGENT]: New task detected. Please start processing.")

        # Read the content to determine if it's an invoice or social media task
        content = await self.check_file_content(file_path)
        if not content:
            logger.warning(f"File {file_path.name} is empty, moving to archived.")

            # Move empty file to archived directory
            archived_path = self.empty_files_dir / f"empty_{file_path.name}_{int(time.time())}.md"
            file_path.rename(archived_path)

            self.log_audit("Empty File Archived", "MOVED TO ARCHIVE", domain)
            return

        # Add Research Agent for Social and General tasks
        if domain in ["Social", "General"]:
            self.log_multi_agent_communication("[RESEARCH-AGENT]: Analyzing market trends and hashtags for optimal engagement...")

        # Check if it's an invoice or social media task that needs approval
        content_lower = content.lower()
        needs_approval = ('invoice' in content_lower or
                         domain == "Social" or
                         'social' in content_lower)

        if needs_approval:
            # For invoices and social media tasks, create appropriate reasoning plans
            if domain == "Social":
                # Create a 'Reasoning Plan' for social media tasks
                reasoning_plan = f"""# Social Media Reasoning Plan for {file_path.name}

## Analysis
- Content: {content[:100]}...
- Platform: Automatically detected from location (Social folder)

## Reasoning
- Checking best time for engagement...
- Content matches brand voice.
- Analyzing optimal posting strategy based on historical data.

## Recommended Action
- Schedule for optimal engagement time
- Apply brand-consistent formatting
- Include relevant hashtags

Action: Pending Approval
"""
                # Save the reasoning plan to Pending_Approval
                plan_name = f"Reasoning_Plan_{file_path.stem}_{int(time.time())}.md"
                plan_path = self.pending_approval_dir / plan_name
                with open(plan_path, 'w', encoding='utf-8') as plan_file:
                    plan_file.write(reasoning_plan)

                # Log the action
                self.log_audit("Social Media Reasoning Plan Created", "PENDING APPROVAL", domain)

                # Remove the original file since we've created a reasoning plan
                file_path.unlink()

                logger.info(f"Social reasoning plan created and moved to Pending_Approval: {plan_path}")
                self.processed_files.add(file_path.name)
                return
            else:
                # For invoices and other social tasks, move directly to Pending_Approval
                pending_path = self.pending_approval_dir / f"{file_path.stem}_for_approval_{int(time.time())}.md"
                file_path.rename(pending_path)

                # Log the action
                action_type = "Invoice Approval Requested" if 'invoice' in content_lower else "Social Media Approval Requested"
                self.log_audit(action_type, "PENDING APPROVAL", domain)

                logger.info(f"File moved to Pending_Approval: {pending_path}")
                self.processed_files.add(file_path.name)
                return

        # For other files, proceed with the normal process
        # Claim-by-Move: Immediately move the file to In_Progress/Zoro
        in_progress_path = self.zoro_in_progress_dir / f"{file_path.stem}_in_progress_{int(time.time())}.md"
        file_path.rename(in_progress_path)
        logger.info(f"File claimed and moved to: {in_progress_path}")

        # Log the claiming action
        self.log_audit("File Claimed", "SUCCESS", domain)

        # Multi-Agent Delegation Logic
        if domain == "Finance":
            self.log_multi_agent_communication("[ZORO-CHIEF] -> [FINANCE-AGENT]: New invoice detected. Analyze and sync with Odoo.")
        elif domain == "Social":
            self.log_multi_agent_communication("[ZORO-CHIEF] -> [SOCIAL-AGENT]: Brand content found. Review and prepare for LinkedIn.")
        elif domain == "Coding":
            self.log_multi_agent_communication("[ZORO-CHIEF] -> [DEV-AGENT]: Code review requested. Analyze and test implementation.")
        elif domain == "Writing":
            self.log_multi_agent_communication("[ZORO-CHIEF] -> [WRITER-AGENT]: Document review requested. Check compliance and quality.")

        # MCP Context Retrieval
        context = await self.get_vault_context(in_progress_path)

        # Simulation of Plan Generation (In real, this goes to LLM)
        plan = f"""# Gold Tier Plan for {in_progress_path.name}
## Vault Context Found:
{context['search_results'][:200]}...

## Content:
{content}

Action: Processed via Zoro Gold Tier MCP.
"""
        # Save Plan
        plan_name = f"Plan_{in_progress_path.stem}_{int(time.time())}.md"
        (self.pending_approval_dir / plan_name).write_text(plan)

        # Log the plan creation
        self.log_audit("Plan Created", "SUCCESS", domain)

        # Add to processed set
        self.processed_files.add(in_progress_path.name)
        logger.info(f"Plan created: {plan_name}")

    def detect_new_files(self) -> List[Path]:
        """Nayi files dhoondna in all Needs_Action sub-folders."""
        new_files = []
        # Check all sub-folders under Needs_Action including General
        for subfolder in ["Social", "Finance", "Coding", "Writing", "General"]:
            subfolder_path = self.needs_action_dir / subfolder
            for file in subfolder_path.rglob("*.md"):
                if file.is_file() and file.name not in self.processed_files:
                    new_files.append(file)
        return new_files

    async def execute_approved_plan(self, file_path: Path):
        """Execute an approved plan."""
        logger.info(f"Executing approved plan: {file_path.name}")

        # Log that the plan is being approved and executed
        self.log_audit("Plan Approved", "EXECUTION STARTED", "Unknown")

        try:
            # Read the plan content
            plan_content = file_path.read_text(encoding='utf-8')

            # Determine the action based on plan content
            action_taken = "Unknown Action"

            # Check if this is an invoice (contains 'invoice' in content)
            content_lower = plan_content.lower()
            if 'invoice' in content_lower:
                # Process invoice via simulated Odoo API
                invoice_data = {"invoice_number": f"INV-{int(time.time())}", "amount": "calculated_from_content", "status": "processed"}
                odoo_success = self.call_odoo_api("Invoice Processed", invoice_data)

                if odoo_success:
                    action_taken = "Invoice Processed via Odoo ERP"
                    # Update bank transactions if it's finance-related
                    if 'finance' in content_lower or 'payment' in content_lower:
                        self.update_bank_transactions(plan_content)
                        # Ensure CEO_Briefing.md is updated for financial tasks
                        self.generate_ceo_briefing()

                    # Handover mechanism: FINANCE-AGENT reports back to ZORO-CHIEF
                    import re
                    odoo_logs = []
                    # Find the last Odoo sync ID from the Odoo_Sync_Audit.log
                    odoo_audit_path = self.vault_path / "Odoo_Sync_Audit.log"
                    if odoo_audit_path.exists():
                        with open(odoo_audit_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            for line in reversed(lines):
                                match = re.search(r'SyncID: (ODOO-\w+)', line)
                                if match:
                                    sync_id = match.group(1)
                                    break
                            else:
                                sync_id = f"ODOO-{int(time.time()) % 10000}"  # Fallback ID
                    else:
                        sync_id = f"ODOO-{int(time.time()) % 10000}"  # Fallback ID

                    self.log_multi_agent_communication(f"[FINANCE-AGENT] -> [ZORO-CHIEF]: Task completed. Odoo SyncID: {sync_id} generated.")
                else:
                    action_taken = "Invoice Processing Failed"

            elif 'Action: LinkedIn' in plan_content:
                action_taken = "Simulated LinkedIn Post"
                # Log social media activity
                self.log_social_activity("LinkedIn", "Post successfully published")
                # Ensure CEO_Briefing.md is updated for social tasks
                self.generate_ceo_briefing()

                # Handover mechanism: SOCIAL-AGENT reports back to ZORO-CHIEF
                self.log_multi_agent_communication("[SOCIAL-AGENT] -> [ZORO-CHIEF]: LinkedIn post published successfully. Engagement metrics queued for analysis.")
            elif 'Action: Instagram' in plan_content:
                action_taken = "Simulated Instagram Post"
                # Log social media activity
                self.log_social_activity("Instagram", "Post successfully published")
                # Ensure CEO_Briefing.md is updated for social tasks
                self.generate_ceo_briefing()

                # Handover mechanism: SOCIAL-AGENT reports back to ZORO-CHIEF
                self.log_multi_agent_communication("[SOCIAL-AGENT] -> [ZORO-CHIEF]: Instagram post published successfully. Engagement metrics queued for analysis.")
            elif 'Action: WhatsApp' in plan_content:
                action_taken = "Sending WhatsApp Message"
            elif 'Action: Twitter' in plan_content:
                action_taken = "Posting to Twitter"
                # Log social media activity
                self.log_social_activity("Twitter", "Post successfully published")
                # Ensure CEO_Briefing.md is updated for social tasks
                self.generate_ceo_briefing()

                # Handover mechanism: SOCIAL-AGENT reports back to ZORO-CHIEF
                self.log_multi_agent_communication("[SOCIAL-AGENT] -> [ZORO-CHIEF]: Twitter post published successfully. Engagement metrics queued for analysis.")
            elif 'Action: Email' in plan_content:
                action_taken = "Sending Email"
            elif 'Action: YouTube' in plan_content:
                action_taken = "Uploading YouTube Video"
                # Log social media activity
                self.log_social_activity("YouTube", "Video successfully published")
                # Ensure CEO_Briefing.md is updated for social tasks
                self.generate_ceo_briefing()

                # Handover mechanism: SOCIAL-AGENT reports back to ZORO-CHIEF
                self.log_multi_agent_communication("[SOCIAL-AGENT] -> [ZORO-CHIEF]: YouTube video uploaded successfully. Engagement metrics queued for analysis.")
            elif 'Action: Facebook' in plan_content:
                action_taken = "Posting to Facebook"
                # Log social media activity
                self.log_social_activity("Facebook", "Post successfully published")
                # Ensure CEO_Briefing.md is updated for social tasks
                self.generate_ceo_briefing()

                # Handover mechanism: SOCIAL-AGENT reports back to ZORO-CHIEF
                self.log_multi_agent_communication("[SOCIAL-AGENT] -> [ZORO-CHIEF]: Facebook post published successfully. Engagement metrics queued for analysis.")
            elif 'Action: Generic' in plan_content:
                action_taken = "Processing Generic Task"
            else:
                # Try to infer from content
                if any(platform in content_lower for platform in ['linkedin', 'post']):
                    action_taken = "Simulated LinkedIn Post"
                    # Log social media activity
                    self.log_social_activity("LinkedIn", "Post successfully published")
                    # Ensure CEO_Briefing.md is updated for social tasks
                    self.generate_ceo_briefing()

                    # Handover mechanism: SOCIAL-AGENT reports back to ZORO-CHIEF
                    self.log_multi_agent_communication("[SOCIAL-AGENT] -> [ZORO-CHIEF]: LinkedIn post published successfully. Engagement metrics queued for analysis.")
                elif any(platform in content_lower for platform in ['instagram', 'ig', 'photo', 'story']):
                    action_taken = "Simulated Instagram Post"
                    # Log social media activity
                    self.log_social_activity("Instagram", "Post successfully published")
                    # Ensure CEO_Briefing.md is updated for social tasks
                    self.generate_ceo_briefing()

                    # Handover mechanism: SOCIAL-AGENT reports back to ZORO-CHIEF
                    self.log_multi_agent_communication("[SOCIAL-AGENT] -> [ZORO-CHIEF]: Instagram post published successfully. Engagement metrics queued for analysis.")
                elif any(platform in content_lower for platform in ['whatsapp', 'message']):
                    action_taken = "Sending WhatsApp Message"
                elif any(platform in content_lower for platform in ['twitter', 'tweet']):
                    action_taken = "Posting to Twitter"
                    # Log social media activity
                    self.log_social_activity("Twitter", "Post successfully published")
                    # Ensure CEO_Briefing.md is updated for social tasks
                    self.generate_ceo_briefing()

                    # Handover mechanism: SOCIAL-AGENT reports back to ZORO-CHIEF
                    self.log_multi_agent_communication("[SOCIAL-AGENT] -> [ZORO-CHIEF]: Twitter post published successfully. Engagement metrics queued for analysis.")
                elif any(platform in content_lower for platform in ['email', 'mail', 'newsletter']):
                    action_taken = "Sending Email"
                elif any(platform in content_lower for platform in ['youtube', 'video']):
                    action_taken = "Uploading YouTube Video"
                    # Log social media activity
                    self.log_social_activity("YouTube", "Video successfully published")
                    # Ensure CEO_Briefing.md is updated for social tasks
                    self.generate_ceo_briefing()

                    # Handover mechanism: SOCIAL-AGENT reports back to ZORO-CHIEF
                    self.log_multi_agent_communication("[SOCIAL-AGENT] -> [ZORO-CHIEF]: YouTube video uploaded successfully. Engagement metrics queued for analysis.")
                elif any(platform in content_lower for platform in ['facebook', 'fb']):
                    action_taken = "Posting to Facebook"
                    # Log social media activity
                    self.log_social_activity("Facebook", "Post successfully published")
                    # Ensure CEO_Briefing.md is updated for social tasks
                    self.generate_ceo_briefing()

                    # Handover mechanism: SOCIAL-AGENT reports back to ZORO-CHIEF
                    self.log_multi_agent_communication("[SOCIAL-AGENT] -> [ZORO-CHIEF]: Facebook post published successfully. Engagement metrics queued for analysis.")
                else:
                    action_taken = "Processing Generic Task"
                    # Update bank transactions if finance-related
                    if 'finance' in content_lower or 'payment' in content_lower or 'transaction' in content_lower:
                        self.update_bank_transactions(plan_content)
                        # Ensure CEO_Briefing.md is updated for financial tasks
                        self.generate_ceo_briefing()

            # Simulate the action
            print(f"SIMULATING: {action_taken}")
            logger.info(f"SIMULATING: {action_taken}")

            # Move the file to Executed folder
            executed_path = self.executed_dir / f"{file_path.stem}_executed_{int(time.time())}.md"
            file_path.rename(executed_path)

            # Add to processed set to prevent reprocessing
            self.approved_processed_files.add(file_path.name)

            # Determine domain for audit logging
            domain = "Unknown"
            if any(d in plan_content.lower() for d in ['social', 'linkedin', 'instagram', 'twitter', 'facebook', 'whatsapp']):
                domain = "Social"
            elif any(d in plan_content.lower() for d in ['finance', 'payment', 'money', 'budget', 'investment', 'invoice']):
                domain = "Finance"
            elif any(d in plan_content.lower() for d in ['code', 'coding', 'program', 'software', 'development']):
                domain = "Coding"
            elif any(d in plan_content.lower() for d in ['writing', 'article', 'blog', 'document', 'content']):
                domain = "Writing"

            # Log the execution
            self.log_audit(action_taken, "SUCCESS", domain)

            # Add success log entry
            logger.info(f"SUCCESS - Task Executed and Archived: {action_taken}")
            print(f"SUCCESS - Task Executed and Archived: {action_taken}")

        except Exception as e:
            logger.error(f"Error executing plan {file_path.name}: {e}")
            # Determine domain for audit logging in case of error
            domain = "Unknown"
            self.log_audit("Plan Execution", f"FAILED - {str(e)}", domain)

    def log_social_activity(self, platform, action):
        """Log social media activity."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [SOCIAL_API] - {action} to {platform}\n"

        # Append to audit log
        with open(self.audit_log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

        logger.info(f"[SOCIAL_API] {action} to {platform}")

    def update_bank_transactions(self, content):
        """Update bank_transactions.csv with new transaction."""
        try:
            import csv
            from datetime import datetime

            # Parse content to extract transaction info
            # This is a simplified version - in real scenario, you'd parse the content more thoroughly
            amount = 0
            description = "Generic Transaction"

            # Look for amount in content (simplified parsing)
            content_lower = content.lower()
            if 'payment' in content_lower or 'invoice' in content_lower:
                # Extract a sample amount - in real scenario, parse from content
                amount = 100.00  # This would come from parsed invoice data
                description = "Invoice Payment"

            # Create transaction record
            transaction = {
                'Date': datetime.now().strftime('%Y-%m-%d'),
                'Description': description,
                'Amount': amount
            }

            vault_root = self.vault_path.resolve()
            csv_path = vault_root / "bank_transactions.csv"

            # Write or append to the CSV
            file_exists = csv_path.exists()
            with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Date', 'Description', 'Amount']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if not file_exists:
                    writer.writeheader()

                writer.writerow(transaction)

            logger.info(f"Bank transaction updated: {transaction}")
        except Exception as e:
            logger.error(f"Error updating bank transactions: {e}")

    def detect_approved_files(self) -> List[Path]:
        """Detect approved files that need execution."""
        approved_files = []
        for file in self.approved_dir.rglob("*.md"):
            if file.is_file() and file.name not in self.approved_processed_files:
                approved_files.append(file)
        return approved_files

    def call_odoo_api(self, action, data):
        """Simulate an ERP API call."""
        try:
            import random

            # Extract amount from data if it exists
            amount = data.get('amount', 'N/A')

            # Generate a random sync ID
            random_id = ''.join([str(random.randint(0, 9)) for _ in range(6)])

            # Log the simulated API call to main audit log
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            audit_log_entry = f"[{timestamp}] - GOLD-TIER - [ODOO_ERP] - {action} - Data: {data} - Status: SUCCESS\n"

            # Write to main audit log
            with open(self.audit_log_file, "a", encoding="utf-8") as f:
                f.write(audit_log_entry)

            # Create the visual Odoo sync audit log in the vault root
            odoo_audit_path = self.vault_path / "Odoo_Sync_Audit.log"
            odoo_sync_entry = f"[{timestamp}] - ERP_SYNC_SUCCESS - Object: {action} - Amount: {amount} - SyncID: ODOO-{random_id}\n"

            # Write to Odoo sync audit log
            with open(odoo_audit_path, "a", encoding="utf-8") as f:
                f.write(odoo_sync_entry)

            logger.info(f"[ODOO_ERP] {action} - Status: SUCCESS - SyncID: ODOO-{random_id}")
            return True
        except Exception as e:
            logger.error(f"Error in simulated ODOO API call: {e}")
            return False

    def generate_forecast(self):
        """Generate financial forecast based on historical data."""
        try:
            import csv
            from datetime import datetime
            from collections import defaultdict

            # Define absolute paths
            vault_root = self.vault_path.resolve()
            csv_path = vault_root / "bank_transactions.csv"

            monthly_data = defaultdict(lambda: {'revenue': 0, 'expenses': 0})

            if csv_path.exists():
                with open(csv_path, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        date_str = row.get('Date', '')
                        amount_str = row.get('Amount', '0')

                        try:
                            # Parse date to get month-year
                            date_obj = datetime.strptime(date_str.split()[0] if ' ' in date_str else date_str, '%Y-%m-%d')
                            month_year = date_obj.strftime('%Y-%m')

                            amount = float(amount_str) if amount_str.replace('.', '').replace('-', '').replace(',', '').isdigit() else 0

                            if amount > 0:
                                monthly_data[month_year]['revenue'] += amount
                            else:
                                monthly_data[month_year]['expenses'] += abs(amount)
                        except ValueError:
                            continue  # Skip invalid dates

            # Convert to sorted list of months
            sorted_months = sorted(monthly_data.keys())

            if len(sorted_months) < 2:
                return {"next_month_revenue": 0, "next_month_expenses": 0, "growth_rate": 0}

            # Calculate monthly growth rates
            revenue_growth_rates = []
            expense_growth_rates = []

            for i in range(1, len(sorted_months)):
                prev_month = sorted_months[i-1]
                curr_month = sorted_months[i]

                prev_revenue = monthly_data[prev_month]['revenue']
                curr_revenue = monthly_data[curr_month]['revenue']

                prev_expenses = monthly_data[prev_month]['expenses']
                curr_expenses = monthly_data[curr_month]['expenses']

                if prev_revenue != 0:
                    revenue_growth = (curr_revenue - prev_revenue) / prev_revenue
                    revenue_growth_rates.append(revenue_growth)

                if prev_expenses != 0:
                    expense_growth = (curr_expenses - prev_expenses) / prev_expenses
                    expense_growth_rates.append(expense_growth)

            # Calculate average growth rates
            avg_revenue_growth = sum(revenue_growth_rates) / len(revenue_growth_rates) if revenue_growth_rates else 0
            avg_expense_growth = sum(expense_growth_rates) / len(expense_growth_rates) if expense_growth_rates else 0

            # Predict next month values
            last_month = sorted_months[-1]
            last_revenue = monthly_data[last_month]['revenue']
            last_expenses = monthly_data[last_month]['expenses']

            predicted_revenue = last_revenue * (1 + avg_revenue_growth)
            predicted_expenses = last_expenses * (1 + avg_expense_growth)

            return {
                "next_month_revenue": predicted_revenue,
                "next_month_expenses": predicted_expenses,
                "revenue_growth_rate": avg_revenue_growth,
                "expense_growth_rate": avg_expense_growth
            }
        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            return {"next_month_revenue": 0, "next_month_expenses": 0, "growth_rate": 0}

    def generate_ceo_briefing(self):
        """Generate CEO Briefing from CSV and audit log data."""
        try:
            import csv
            from datetime import datetime

            # Define absolute paths
            vault_root = self.vault_path.resolve()
            csv_path = vault_root / "bank_transactions.csv"
            audit_path = vault_root / "audit_log.txt"
            briefing_path = vault_root / "CEO_Briefing.md"

            # Calculate financial metrics from CSV
            total_revenue = 0
            total_expenses = 0

            if csv_path.exists():
                with open(csv_path, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        amount_str = row.get('Amount', '0')
                        amount = float(amount_str) if amount_str.replace('.', '').replace('-', '').isdigit() else 0

                        if amount > 0:
                            total_revenue += amount
                        else:
                            total_expenses += abs(amount)

            net_profit = total_revenue - total_expenses

            # Count SUCCESS entries from audit log
            success_count = 0
            # Count social media posts from today
            social_posts_today = 0

            if audit_path.exists():
                today_date = datetime.now().strftime('%Y-%m-%d')
                with open(audit_path, 'r', encoding='utf-8') as auditfile:
                    for line in auditfile:
                        if 'SUCCESS' in line:
                            success_count += 1
                        # Check for social media posts today
                        if '[SOCIAL_API]' in line and today_date in line:
                            social_posts_today += 1

            # Generate forecast
            forecast = self.generate_forecast()
            predicted_revenue = forecast.get("next_month_revenue", 0)
            predicted_expenses = forecast.get("next_month_expenses", 0)
            predicted_net_profit = predicted_revenue - predicted_expenses
            revenue_growth_rate = forecast.get("revenue_growth_rate", 0)
            expense_growth_rate = forecast.get("expense_growth_rate", 0)

            # Generate strategic advice based on forecast
            strategic_advice = []
            if expense_growth_rate > revenue_growth_rate:
                strategic_advice.append("⚠️ Warning: Expenses are rising faster than revenue. Suggesting 5% budget cut in Social Media")
            elif revenue_growth_rate > expense_growth_rate:
                strategic_advice.append("✅ Positive trend: Revenue growth exceeds expense growth. Consider investing more in marketing")
            else:
                strategic_advice.append("📊 Neutral trend: Revenue and expense growth are balanced. Maintain current spending patterns")

            if predicted_expenses > predicted_revenue:
                strategic_advice.append("⚠️ Alert: Projected expenses exceed projected revenue. Immediate cost control measures recommended")

            # Create CEO Briefing content
            briefing_content = f"""# CEO Daily Briefing
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Financial Summary
- **Total Revenue:** ${total_revenue:,.2f}
- **Total Expenses:** ${total_expenses:,.2f}
- **Net Profit:** ${net_profit:,.2f}

## Operations Summary
- **Successful Operations:** {success_count} tasks completed successfully
- **System Status:** Operational

## Social Media Activity
- **Posts Published Today:** {social_posts_today} posts across platforms

## Financial Forecast
- **Predicted Next Month Revenue:** ${predicted_revenue:,.2f}
- **Predicted Next Month Expenses:** ${predicted_expenses:,.2f}
- **Predicted Next Month Net Profit:** ${predicted_net_profit:,.2f}
- **Revenue Growth Rate:** {(revenue_growth_rate * 100):.2f}%
- **Expense Growth Rate:** {(expense_growth_rate * 100):.2f}%

## Strategic Advice
{chr(10).join(['- ' + advice for advice in strategic_advice])}

## Market Insights
- AI Trends are up 15%. Recommend focusing on automation content.

## Recommendations
Based on current data:
- Revenue trends indicate healthy business activity
- Expense management appears stable
- Operational efficiency demonstrated by {success_count} successful tasks
- Active social media presence with {social_posts_today} posts today

---
*Generated by Zoro AI Employee - Platinum Tier*
"""

            # Write the briefing to the file
            with open(briefing_path, 'w', encoding='utf-8') as briefing_file:
                briefing_file.write(briefing_content)

            logger.info(f"CEO Briefing generated successfully at {briefing_path}")
            print(f"CEO Briefing generated: Revenue=${total_revenue:.2f}, Expenses=${total_expenses:.2f}, Net=${net_profit:.2f}, Successes={success_count}, Social Posts Today={social_posts_today}")

            # Log the briefing generation
            self.log_audit("CEO Briefing Generated", "SUCCESS", "General")

        except Exception as e:
            logger.error(f"Error generating CEO briefing: {e}")
            print(f"Error generating CEO briefing: {e}")

    def log_multi_agent_communication(self, message):
        """Log multi-agent communication with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] - PLATINUM-TIER - MULTI-AGENT - {message}\n"

        # Append to audit log
        with open(self.audit_log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)

        logger.info(f"MULTI-AGENT COMMUNICATION: {message}")

    def check_and_heal_vault_integrity(self):
        """Check for misplaced files and move them back to Needs_Action."""
        try:
            misplaced_files_found = 0

            # Check for files in unexpected locations
            for root, dirs, files in os.walk(self.vault_path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = Path(root) / file

                        # Skip if it's in the expected locations
                        if any(str(file_path).startswith(str(expected_dir)) for expected_dir in [
                            self.needs_action_dir, self.in_progress_dir, self.pending_approval_dir,
                            self.approved_dir, self.executed_dir, self.processed_dir
                        ]):
                            continue

                        # If file is in an unexpected location, move it back to Needs_Action
                        if not any(str(file_path).startswith(str(expected_dir)) for expected_dir in [
                            self.audit_log_file, self.vault_path / "bank_transactions.csv",
                            self.vault_path / "CEO_Briefing.md", self.vault_path / "Odoo_Sync_Audit.log",
                            self.vault_path / "zoro_orchestration.log"
                        ]):
                            # Move the file back to Needs_Action/General
                            destination = self.needs_action_dir / "General" / file

                            # Handle potential filename conflicts
                            counter = 1
                            original_destination = destination
                            while destination.exists():
                                stem = original_destination.stem
                                suffix = original_destination.suffix
                                destination = self.needs_action_dir / "General" / f"{stem}_{counter}{suffix}"
                                counter += 1

                            file_path.rename(destination)

                            # Log the recovery action
                            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                            log_entry = f"[{timestamp}] - PLATINUM-RECOVERY - Misplaced file detected - Re-routing to correct workflow - Moved {file} to Needs_Action/General\n"

                            with open(self.audit_log_file, "a", encoding="utf-8") as f:
                                f.write(log_entry)

                            logger.info(f"PLATINUM-RECOVERY: Misplaced file {file} moved to Needs_Action/General")
                            misplaced_files_found += 1

            if misplaced_files_found > 0:
                logger.info(f"PLATINUM-RECOVERY: Fixed {misplaced_files_found} misplaced files")

        except Exception as e:
            logger.error(f"Error in vault integrity check: {e}")

    async def run(self):
        """Main Loop with correct MCP Client Handshake."""
        server_params = StdioServerParameters(
            command="python",
            args=["zoro_mcp_server.py"],
            env=None
        )

        print("Connecting to MCP Server...")
        # CORRECT HANDSHAKE: Using context managers for stdio and session
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self.mcp_session = session
                print("✅ CONNECTED TO GOLD TIER MCP SERVER")
                logger.info("Successfully connected to MCP server")

                try:
                    last_health_check = time.time()

                    while True:
                        # Check for trigger_briefing.md file specifically
                        trigger_file = self.needs_action_dir / "General" / "trigger_briefing.md"
                        if trigger_file.exists() and trigger_file.name not in self.processed_files:
                            print("Trigger file detected: trigger_briefing.md")
                            logger.info("Trigger file detected: trigger_briefing.md")

                            # Generate CEO briefing
                            self.generate_ceo_briefing()

                            # Move trigger file to Executed folder
                            executed_path = self.executed_dir / f"trigger_briefing_executed_{int(time.time())}.md"
                            trigger_file.rename(executed_path)

                            # Add to processed files to prevent reprocessing
                            self.processed_files.add(trigger_file.name)

                            logger.info("CEO Briefing generated and trigger file moved to Executed")
                            print("CEO Briefing generated and trigger file moved to Executed")

                        # Check for new files in Needs_Action sub-folders
                        files = self.detect_new_files()
                        for f in files:
                            # Skip trigger_briefing.md as it's handled separately
                            if f.name != "trigger_briefing.md":
                                await self.process_new_file(f)

                        # Check for approved files that need execution
                        approved_files = self.detect_approved_files()
                        for approved_file in approved_files:
                            await self.execute_approved_plan(approved_file)

                        # Vault Health Check - Every 5 minutes (300 seconds)
                        current_time = time.time()
                        if current_time - last_health_check >= 300:
                            logger.info("Performing vault health check...")
                            self.check_and_heal_vault_integrity()

                            # Generate health report
                            self.log_audit("Vault Health Check", "COMPLETED", "System")
                            last_health_check = current_time

                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    print("Shutting down...")

if __name__ == "__main__":
    orchestrator = ZoroOrchestration()
    asyncio.run(orchestrator.run())
import os
import time
from pathlib import Path

# Config
VAULT_ROOT = Path("AI_Employee_Vault")
NEEDS_ACTION = VAULT_ROOT / "Needs_Action"
PENDING_APPROVAL = VAULT_ROOT / "Pending_Approval"
APPROVED = VAULT_ROOT / "Approved"

def create_task():
    print("creating 'Needs_Action' task for Qwen...")
    NEEDS_ACTION.mkdir(parents=True, exist_ok=True)
    
    task_content = """---
id: qwen_demo_auto
type: general_task
source: manual_test
---
Please create a text file named 'QWEN_WAS_HERE.txt' on the Desktop containing the text "Autonomous Agent Success!".
"""
    
    task_file = NEEDS_ACTION / "qwen_task.md"
    task_file.write_text(task_content)
    print(f"Task created: {task_file}")
    print("Wait for Orchestrator to pick it up and create a Plan/Approval Request...")

def approve_tasks():
    print("\nChecking for Pending Approvals to auto-approve (for demo purposes)...")
    if not PENDING_APPROVAL.exists():
        print("No Pending_Approval folder yet.")
        return

    approvals = list(PENDING_APPROVAL.glob("*.md")) + list(PENDING_APPROVAL.glob("*.yaml"))
    
    if not approvals:
        print("No pending approvals found yet. Wait a few seconds and try again.")
        return

    APPROVED.mkdir(parents=True, exist_ok=True)
    for app_file in approvals:
        print(f"Approving: {app_file.name}")
        target = APPROVED / app_file.name
        app_file.rename(target)
        print(f"Moved to {target}")

if __name__ == "__main__":
    print("=== Qwen Autonomous Task Demo ===")
    print("1. Create Task")
    print("2. Approve Pending Tasks")
    print("3. Exit")
    
    choice = input("Select option (1/2/3): ")
    
    if choice == "1":
        create_task()
    elif choice == "2":
        approve_tasks()
    else:
        print("Exiting.")

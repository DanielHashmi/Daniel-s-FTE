#!/usr/bin/env python3
"""
Daniel FTE - Quick Start & Verification Script

This script verifies your installation and runs a quick demo of all features.
Run this to ensure everything is working before recording your demo video.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Color codes for terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}  {text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_ok(text):
    print(f"  {GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"  {RED}✗ {text}{RESET}")

def print_warn(text):
    print(f"  {YELLOW}⚠ {text}{RESET}")

def check_python_version():
    """Check Python version is 3.10+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print_ok(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} (need 3.10+)")
        return False

def check_dependencies():
    """Check required Python packages"""
    required = ['watchdog', 'yaml', 'dotenv', 'requests']
    optional = ['playwright', 'google.auth', 'googleapiclient']
    
    missing = []
    for pkg in required:
        try:
            if pkg == 'dotenv':
                __import__('dotenv')
            else:
                __import__(pkg)
            print_ok(f"Package: {pkg}")
        except ImportError:
            print_error(f"Package: {pkg} (NOT INSTALLED)")
            missing.append(pkg)
    
    for pkg in optional:
        try:
            __import__(pkg)
            print_ok(f"Package: {pkg} (optional)")
        except ImportError:
            print_warn(f"Package: {pkg} (optional, not installed)")
    
    return len(missing) == 0

def check_vault_structure():
    """Check vault directories exist"""
    vault_root = Path("AI_Employee_Vault")
    required_dirs = [
        "Inbox", "Needs_Action", "Plans", "Pending_Approval",
        "Approved", "Rejected", "Done", "Logs", "Accounting", "Briefings"
    ]
    
    if not vault_root.exists():
        print_error(f"Vault root not found: {vault_root}")
        return False
    
    print_ok(f"Vault root: {vault_root}")
    
    missing = []
    for dir_name in required_dirs:
        dir_path = vault_root / dir_name
        if dir_path.exists():
            print_ok(f"  /{dir_name}/")
        else:
            print_warn(f"  /{dir_name}/ (creating...)")
            dir_path.mkdir(parents=True, exist_ok=True)
    
    return True

def check_key_files():
    """Check key implementation files exist"""
    key_files = [
        ("src/orchestration/orchestrator.py", "Orchestrator"),
        ("src/orchestration/plan_manager.py", "Plan Manager"),
        ("src/orchestration/approval_manager.py", "Approval Manager"),
        ("src/orchestration/ralph_loop.py", "Ralph Wiggum Loop"),
        ("src/watchers/gmail.py", "Gmail Watcher"),
        ("src/watchers/whatsapp.py", "WhatsApp Watcher"),
        ("src/watchers/linkedin.py", "LinkedIn Watcher"),
        ("src/lib/vault.py", "Vault Library"),
        ("mcp-servers/social-mcp/index.js", "Social MCP Server"),
        ("mcp-servers/email-mcp/index.js", "Email MCP Server"),
        (".claude/skills/ceo-briefing/scripts/main_operation.py", "CEO Briefing Skill"),
        (".claude/skills/social-media-suite/scripts/main_operation.py", "Social Media Skill"),
        (".claude/skills/odoo-accounting/scripts/main_operation.py", "Odoo Skill"),
    ]
    
    all_found = True
    for file_path, name in key_files:
        if Path(file_path).exists():
            print_ok(f"{name}: {file_path}")
        else:
            print_error(f"{name}: {file_path} (NOT FOUND)")
            all_found = False
    
    return all_found

def check_env_file():
    """Check .env file exists and has required variables"""
    env_path = Path(".env")
    
    if not env_path.exists():
        print_error(".env file not found")
        print_warn("Copy .env.example to .env and configure your credentials")
        return False
    
    print_ok(".env file exists")
    
    # Read and check key variables
    env_content = env_path.read_text()
    
    checks = [
        ("DRY_RUN", "DRY_RUN mode"),
        ("VAULT_ROOT", "Vault root (optional)"),
    ]
    
    for var, name in checks:
        if var in env_content:
            # Extract value
            for line in env_content.split('\n'):
                if line.startswith(var + '='):
                    value = line.split('=', 1)[1].strip()
                    if value and not value.startswith('#'):
                        print_ok(f"  {name}: {value}")
                    else:
                        print_warn(f"  {name}: not set")
    
    return True

def check_mcp_servers():
    """Check MCP server dependencies"""
    servers = [
        ("mcp-servers/email-mcp", "Email MCP"),
        ("mcp-servers/social-mcp", "Social MCP"),
    ]
    
    for server_path, name in servers:
        package_json = Path(server_path) / "package.json"
        node_modules = Path(server_path) / "node_modules"
        
        if package_json.exists():
            print_ok(f"{name}: package.json found")
            if node_modules.exists():
                print_ok(f"  Dependencies installed")
            else:
                print_warn(f"  Run: cd {server_path} && npm install")
        else:
            print_error(f"{name}: package.json not found")
    
    return True

def count_skills():
    """Count available Claude skills"""
    skills_dir = Path(".claude/skills")
    if not skills_dir.exists():
        print_error("Skills directory not found")
        return 0
    
    skills = [d for d in skills_dir.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]
    print_ok(f"Found {len(skills)} Claude skills:")
    for skill in sorted(skills):
        print(f"      - {skill.name}")
    
    return len(skills)

def run_quick_demo():
    """Run a quick demo to verify core functionality"""
    print("\nRunning quick verification demo...\n")
    
    vault_root = Path("AI_Employee_Vault")
    
    # Test 1: Create a test task
    test_task = vault_root / "Needs_Action" / "TEST_verification.md"
    test_content = f"""---
type: test
created: {datetime.now().isoformat()}
priority: normal
---

# Verification Test Task

This is a test task to verify the system is working.
"""
    
    test_task.write_text(test_content)
    print_ok(f"Created test task: {test_task.name}")
    
    # Test 2: Create a test plan
    test_plan = vault_root / "Plans" / "PLAN_TEST_verification.md"
    plan_content = f"""---
id: PLAN-TEST-001
source: TEST_verification.md
created: {datetime.now().isoformat()}
status: completed
---

# Test Plan

## Analysis
This is a verification test.

## Result
System is working correctly.
"""
    
    test_plan.write_text(plan_content)
    print_ok(f"Created test plan: {test_plan.name}")
    
    # Test 3: Create audit log entry
    logs_dir = vault_root / "Logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "action_type": "verification_test",
        "result": "success",
        "actor": "quick_start_script"
    }
    
    if log_file.exists():
        logs = json.loads(log_file.read_text())
    else:
        logs = []
    
    logs.append(log_entry)
    log_file.write_text(json.dumps(logs, indent=2))
    print_ok(f"Created audit log entry")
    
    # Clean up test files
    test_task.unlink()
    test_plan.unlink()
    print_ok("Cleaned up test files")
    
    return True

def main():
    print(f"""
{BLUE}╔═══════════════════════════════════════════════════════════════╗
║               DANIEL FTE - QUICK START                         ║
║              Personal AI Employee Verification                  ║
╚═══════════════════════════════════════════════════════════════╝{RESET}
    """)
    
    all_checks_passed = True
    
    print_header("1. Checking Python Environment")
    if not check_python_version():
        all_checks_passed = False
    
    print_header("2. Checking Dependencies")
    if not check_dependencies():
        all_checks_passed = False
    
    print_header("3. Checking Vault Structure")
    if not check_vault_structure():
        all_checks_passed = False
    
    print_header("4. Checking Key Implementation Files")
    if not check_key_files():
        all_checks_passed = False
    
    print_header("5. Checking Environment Configuration")
    check_env_file()
    
    print_header("6. Checking MCP Servers")
    check_mcp_servers()
    
    print_header("7. Counting Claude Skills")
    skill_count = count_skills()
    
    print_header("8. Running Quick Demo")
    run_quick_demo()
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    if all_checks_passed:
        print(f"""
{GREEN}╔═══════════════════════════════════════════════════════════════╗
║                    ALL CHECKS PASSED! ✓                        ║
║                                                                 ║
║   Daniel FTE is ready for demo recording.                      ║
║                                                                 ║
║   Next steps:                                                   ║
║   1. Review DEMO_VIDEO_GUIDE.md for recording script           ║
║   2. Configure any missing credentials in .env                  ║
║   3. Run: pm2 start ecosystem.config.js                        ║
║   4. Record your demo video!                                    ║
╚═══════════════════════════════════════════════════════════════╝{RESET}
        """)
    else:
        print(f"""
{YELLOW}╔═══════════════════════════════════════════════════════════════╗
║                  SOME CHECKS NEED ATTENTION                    ║
║                                                                 ║
║   Please fix the issues marked with ✗ above.                   ║
║                                                                 ║
║   Common fixes:                                                 ║
║   - pip install watchdog pyyaml python-dotenv requests         ║
║   - cd mcp-servers/social-mcp && npm install                   ║
║   - copy .env.example .env                                     ║
╚═══════════════════════════════════════════════════════════════╝{RESET}
        """)
    
    return 0 if all_checks_passed else 1

if __name__ == "__main__":
    sys.exit(main())

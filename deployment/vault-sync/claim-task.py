#!/usr/bin/env python3
"""
claim-task.py - Claim tasks by moving files with validation
"""

import os
import sys
import shutil
import yaml
from pathlib import Path
from datetime import datetime

class ClaimValidator:
    def __init__(self, vault_path, agent_id):
        self.vault_path = Path(vault_path)
        self.agent_id = agent_id
        self.claimed_path = self.vault_path / "In_Progress" / agent_id
        self.needs_action = self.vault_path / "Needs_Action"
        self.pending_approval = self.vault_path / "Pending_Approval"
        self.claimed_path.mkdir(parents=True, exist_ok=True)

    def validate_action_file(self, action_file):
        """Validate action file structure and permission"""
        if not action_file.exists():
            return False, "File does not exist"

        # Check YAML frontmatter
        try:
            with open(action_file, 'r') as f:
                content = f.read()

            if not content.startswith('---'):
                return False, "Missing YAML frontmatter"

            # Extract YAML
            parts = content.split('---', 2)
            if len(parts) < 3:
                return False, "Invalid frontmatter format"

            yaml_data = yaml.safe_load(parts[1])
            if not yaml_data or 'action_id' not in yaml_data:
                return False, "Missing required fields in frontmatter"

            action_id = yaml_data.get('action_id')
            if not action_id:
                return False, "Empty action_id"

        except Exception as e:
            return False, f"Invalid YAML: {str(e)}"

        return True, "Valid"

    def is_action_claimed_by_other(self, action_file):
        """Check if action is already claimed by another agent"""
        action_id = self._extract_action_id(action_file)
        if not action_id:
            return False

        # Check all In_Progress folders across agents
        in_progress_base = self.vault_path / "In_Progress"
        if in_progress_base.exists():
            for agent_folder in in_progress_base.iterdir():
                if agent_folder.is_dir() and agent_folder.name != self.agent_id:
                    # Look for a file starting with action_id
                    for f in agent_folder.iterdir():
                        if f.stem.startswith(action_id):
                            return True

        return False

    def _extract_action_id(self, action_file):
        """Extract action_id from YAML frontmatter"""
        try:
            with open(action_file, 'r') as f:
                content = f.read()
            parts = content.split('---', 2)
            if len(parts) >= 2:
                yaml_data = yaml.safe_load(parts[1])
                return yaml_data.get('action_id')
        except:
            pass
        return None

    def claim(self, action_file_path):
        """Claim an action by moving it to In_Progress/agent-id/"""
        action_file = Path(action_file_path)

        # Validate action file
        valid, message = self.validate_action_file(action_file)
        if not valid:
            return False, f"Validation failed: {message}"

        # Check if already claimed
        if self.is_action_claimed_by_other(action_file):
            return False, "Action already claimed by another agent"

        # Extract action_id
        action_id = self._extract_action_id(action_file)
        if not action_id:
            return False, "Could not extract action_id"

        # Create destination path with action_id prefix
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        dest_name = f"{action_id}_{timestamp}_{action_file.name}"
        dest_path = self.claimed_path / dest_name

        try:
            # Move the file (atomic on same filesystem)
            shutil.move(str(action_file), str(dest_path))

            # Create claim record
            claim_record = {
                'timestamp': datetime.utcnow().isoformat(),
                'action_id': action_id,
                'source_file': str(action_file),
                'agent_id': self.agent_id,
                'claimed_file': str(dest_path)
            }

            # Save claim record
            record_file = self.claimed_path / f"{action_id}_{timestamp}_claim.json"
            with open(record_file, 'w') as f:
                f.write(str(claim_record))  # Simple string representation

            return True, f"Claimed action {action_id} to {dest_path}"

        except Exception as e:
            return False, f"Failed to claim: {str(e)}"

def main():
    if len(sys.argv) < 3:
        print("Usage: python claim-task.py <vault_path> <agent_id> [action_file.yaml]")
        print("  If action_file not specified, lists available actions")
        sys.exit(1)

    vault_path = sys.argv[1]
    agent_id = sys.argv[2]
    validator = ClaimValidator(vault_path, agent_id)

    # If no specific file provided, list available actions
    if len(sys.argv) == 3:
        print(f"Available actions in {vault_path}/Needs_Action:")
        if validator.needs_action.exists():
            for f in validator.needs_action.glob("*.yaml"):
                valid, msg = validator.validate_action_file(f)
                claimed = validator.is_action_claimed_by_other(f)
                status = "✓" if valid else "✗"
                claimed_status = " [CLAIMED]" if claimed else ""
                print(f"{status} {f.name}{claimed_status}")
        sys.exit(0)

    action_file = sys.argv[3]
    success, message = validator.claim(action_file)
    print(message)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

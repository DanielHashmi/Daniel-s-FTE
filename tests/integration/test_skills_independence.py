"""Test to verify all Agent Skills are independently testable."""

import pytest
import subprocess
import sys
from pathlib import Path


# List of all Agent Skills with their script paths
SKILLS = [
    {
        "name": "setup-vault",
        "script": ".claude/skills/setup-vault/scripts/main_operation.py",
    },
    {
        "name": "watcher-manager",
        "script": ".claude/skills/watcher-manager/scripts/main_operation.py",
    },
    {
        "name": "process-inbox",
        "script": ".claude/skills/process-inbox/scripts/main_operation.py",
    },
    {
        "name": "view-dashboard",
        "script": ".claude/skills/view-dashboard/scripts/main_operation.py",
    },
]


@pytest.mark.parametrize("skill", SKILLS, ids=[s["name"] for s in SKILLS])
def test_skill_has_help_flag(skill):
    """Test that each skill supports --help flag."""
    result = subprocess.run(
        [sys.executable, skill["script"], "--help"],
        capture_output=True,
        text=True,
    )
    # --help should exit with 0 and print usage information
    assert result.returncode == 0, f"{skill['name']} --help failed"
    assert "usage" in result.stdout.lower() or "help" in result.stdout.lower(), \
        f"{skill['name']} --help doesn't show usage information"


@pytest.mark.parametrize("skill", SKILLS, ids=[s["name"] for s in SKILLS])
def test_skill_script_exists(skill):
    """Test that each skill script file exists."""
    script_path = Path(skill["script"])
    assert script_path.exists(), f"{skill['name']} script not found at {skill['script']}"
    assert script_path.is_file(), f"{skill['script']} is not a file"


@pytest.mark.parametrize("skill", SKILLS, ids=[s["name"] for s in SKILLS])
def test_skill_is_executable(skill):
    """Test that each skill script is executable (has shebang)."""
    script_path = Path(skill["script"])
    with open(script_path, "r") as f:
        first_line = f.readline()
    assert first_line.startswith("#!"), \
        f"{skill['name']} script doesn't have shebang line"


def test_all_skills_have_readme():
    """Test that each skill has a README.md file."""
    for skill in SKILLS:
        skill_dir = Path(skill["script"]).parent.parent
        readme = skill_dir / "README.md"
        assert readme.exists(), f"{skill['name']} missing README.md"


def test_all_skills_have_skill_json():
    """Test that each skill has a skill.json metadata file."""
    for skill in SKILLS:
        skill_dir = Path(skill["script"]).parent.parent
        skill_json = skill_dir / "skill.json"
        assert skill_json.exists(), f"{skill['name']} missing skill.json"


def test_skill_independence():
    """Test that skills can be invoked independently without dependencies."""
    # Each skill should be able to run --help without requiring other skills
    for skill in SKILLS:
        result = subprocess.run(
            [sys.executable, skill["script"], "--help"],
            capture_output=True,
            text=True,
            timeout=5,  # Should complete quickly
        )
        assert result.returncode == 0, \
            f"{skill['name']} cannot run independently (--help failed)"

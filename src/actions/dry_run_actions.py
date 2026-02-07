"""
Dry Run Actions - Simulate social media posts without actually posting.
Logs all simulated actions to the vault for demo purposes.
"""
import os
import time
from pathlib import Path
from datetime import datetime

VAULT_PATH = Path("AI_Employee_Vault")
LOG_FILE = VAULT_PATH / "Logs" / "simulated_actions.md"


def ensure_log_file():
    """Ensure the log directory and file exist."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        LOG_FILE.write_text("# Simulated Actions Log\n\n*These actions would have been performed in production.*\n\n---\n\n", encoding='utf-8')


def log_simulated_action(platform: str, action_type: str, content: str, metadata: dict = None):
    """Log a simulated action to the vault."""
    ensure_log_file()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    entry = f"""## [{platform}] {action_type}
**Time:** {timestamp}
**Status:** 🔶 SIMULATED (Dry Run)

**Would have posted:**
> {content[:280]}{'...' if len(content) > 280 else ''}

"""
    if metadata:
        entry += f"**Metadata:** {metadata}\n"
    entry += "\n---\n\n"
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(entry)
    
    return {
        "success": True,
        "simulated": True,
        "platform": platform,
        "message": f"[DRY RUN] Would post to {platform}: {content[:50]}..."
    }


def simulate_twitter_post(content: str, hashtags: list = None):
    """Simulate posting to Twitter/X."""
    full_content = content
    if hashtags:
        full_content += " " + " ".join([f"#{h}" for h in hashtags])
    
    return log_simulated_action(
        platform="Twitter/X",
        action_type="Tweet",
        content=full_content,
        metadata={"hashtags": hashtags}
    )


def simulate_linkedin_post(content: str, is_article: bool = False):
    """Simulate posting to LinkedIn."""
    return log_simulated_action(
        platform="LinkedIn",
        action_type="Article" if is_article else "Post",
        content=content,
        metadata={"is_article": is_article}
    )


def simulate_facebook_post(content: str, page_id: str = None):
    """Simulate posting to Facebook."""
    return log_simulated_action(
        platform="Facebook",
        action_type="Page Post" if page_id else "Personal Post",
        content=content,
        metadata={"page_id": page_id}
    )


def simulate_whatsapp_message(recipient: str, message: str):
    """Simulate sending a WhatsApp message."""
    return log_simulated_action(
        platform="WhatsApp",
        action_type="Message",
        content=f"To {recipient}: {message}",
        metadata={"recipient": recipient}
    )


# Convenience exports
post_tweet = simulate_twitter_post
post_linkedin = simulate_linkedin_post
post_facebook = simulate_facebook_post
send_whatsapp = simulate_whatsapp_message


if __name__ == "__main__":
    # Test dry run
    print("Testing dry run actions...")
    
    result = simulate_twitter_post("Hello from AI Employee! This is a test tweet.", ["AI", "Hackathon"])
    print(result)
    
    result = simulate_linkedin_post("Excited to share our new AI Employee system!")
    print(result)
    
    print(f"\nCheck {LOG_FILE} for simulated actions.")

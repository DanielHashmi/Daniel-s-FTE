"""
Email Classification and Tagging Service.

Uses Qwen (cloud-based, free & fast) to intelligently analyze emails and add metadata tags.
Qwen provides smart classification without the cost of Claude API.
"""

import subprocess
import json
import shutil
from typing import Dict, List, Optional

class EmailClassifier:
    """Classifies emails and generates intelligent tags using Qwen."""

    def __init__(self):
        self.qwen_path = shutil.which("qwen.cmd") or shutil.which("qwen")
        self.available = self.qwen_path is not None

    def classify_email(self, sender: str, subject: str, snippet: str) -> Dict[str, any]:
        """
        Analyze email and return classification metadata.

        Returns:
            {
                "priority": "high" | "normal" | "low",
                "tags": ["newsletter", "security-alert", "work", etc.],
                "category": "notification" | "personal" | "work" | "promotional",
                "requires_action": bool,
                "suggested_action": "reply" | "archive" | "flag" | "ignore"
            }
        """
        if not self.available:
            return self._fallback_classification(sender, subject, snippet)

        try:
            # Construct prompt for Qwen
            prompt = f"""Analyze this email and return ONLY a JSON object with classification metadata.

Email:
From: {sender}
Subject: {subject}
Preview: {snippet[:200]}

Return ONLY this JSON structure (no other text):
{{
    "priority": "high|normal|low",
    "tags": ["tag1", "tag2"],
    "category": "notification|personal|work|promotional|security|transactional",
    "requires_action": true|false,
    "suggested_action": "reply|archive|flag|ignore",
    "reasoning": "brief explanation"
}}

Rules:
- priority "high" ONLY for: job offers, client requests, urgent deadlines, security alerts
- priority "low" for: newsletters, automated notifications, promotional emails
- tags should be relevant keywords (max 3 tags)
- category should accurately reflect email type
- requires_action true if user needs to do something
- suggested_action based on email type

OUTPUT JSON ONLY:"""

            # Run Qwen
            result = subprocess.run(
                [self.qwen_path, '-y', '--input-format', 'text'],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='replace'
            )

            if result.returncode == 0:
                output = result.stdout.strip()

                # Try to extract JSON from output
                try:
                    # Look for JSON object
                    start_idx = output.find('{')
                    end_idx = output.rfind('}')

                    if start_idx != -1 and end_idx != -1:
                        json_str = output[start_idx:end_idx+1]
                        classification = json.loads(json_str)

                        # Validate and return
                        return {
                            "priority": classification.get("priority", "normal"),
                            "tags": classification.get("tags", [])[:3],  # Max 3 tags
                            "category": classification.get("category", "notification"),
                            "requires_action": classification.get("requires_action", False),
                            "suggested_action": classification.get("suggested_action", "archive"),
                            "reasoning": classification.get("reasoning", "")
                        }
                except json.JSONDecodeError:
                    pass

        except Exception as e:
            print(f"Qwen classification error: {e}")

        # Fallback if Qwen fails
        return self._fallback_classification(sender, subject, snippet)

    def _fallback_classification(self, sender: str, subject: str, snippet: str) -> Dict[str, any]:
        """Rule-based fallback classification."""

        sender_lower = sender.lower()
        subject_lower = subject.lower()
        snippet_lower = snippet.lower()

        tags = []
        category = "notification"
        priority = "normal"
        requires_action = False
        suggested_action = "archive"

        # Detect category
        if any(word in sender_lower for word in ["no-reply", "noreply", "do-not-reply"]):
            category = "notification"
            priority = "low"
            suggested_action = "archive"

        if any(word in subject_lower for word in ["security", "alert", "warning", "suspicious", "verify", "confirm"]):
            category = "security"
            tags.append("security-alert")
            priority = "high"
            requires_action = True
            suggested_action = "flag"

        if any(word in subject_lower for word in ["invoice", "payment", "receipt", "bill"]):
            category = "transactional"
            tags.append("finance")
            priority = "normal"
            suggested_action = "archive"

        if any(word in sender_lower for word in ["linkedin", "github", "indeed", "glassdoor"]):
            category = "work"
            tags.append("career")
            priority = "normal"

        if any(word in subject_lower for word in ["application", "job", "interview", "offer"]):
            category = "work"
            tags.append("job-opportunity")
            priority = "high"
            requires_action = True
            suggested_action = "reply"

        if any(word in subject_lower for word in ["newsletter", "digest", "weekly", "update"]):
            category = "promotional"
            tags.append("newsletter")
            priority = "low"
            suggested_action = "archive"

        if any(word in sender_lower for word in ["docker", "npm", "github", "gitlab"]):
            tags.append("dev-tools")

        # Ensure we have at least one tag
        if not tags:
            tags.append(category)

        return {
            "priority": priority,
            "tags": tags[:3],
            "category": category,
            "requires_action": requires_action,
            "suggested_action": suggested_action,
            "reasoning": f"Categorized as {category} based on sender and subject"
        }

# Singleton
_classifier_instance: Optional[EmailClassifier] = None

def get_classifier() -> EmailClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = EmailClassifier()
    return _classifier_instance

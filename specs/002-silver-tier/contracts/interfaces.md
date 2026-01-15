# System Interfaces

## Watcher Interface

All watchers must inherit from `BaseWatcher` and implement these methods:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseWatcher(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.processed_ids = set()

    @abstractmethod
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Poll source for new items.
        Returns list of event dictionaries.
        """
        pass

    @abstractmethod
    def create_action_file(self, event: Dict[str, Any]) -> str:
        """
        Convert event to structured action file.
        Returns file path of created action.
        """
        pass

    def run(self):
        """Main loop with error handling and backoff"""
        pass
```

## MCP Capabilities

### Email Server (`email-ops`)

**Tool**: `send_email`
```json
{
  "name": "send_email",
  "description": "Send an email via Gmail API",
  "inputSchema": {
    "type": "object",
    "properties": {
      "to": { "type": "string", "format": "email" },
      "subject": { "type": "string" },
      "body": { "type": "string" },
      "attachments": { "type": "array", "items": { "type": "string" } }
    },
    "required": ["to", "subject", "body"]
  }
}
```

### Social Server (`social-ops`)

**Tool**: `post_update`
```json
{
  "name": "post_update",
  "description": "Post content to LinkedIn feed",
  "inputSchema": {
    "type": "object",
    "properties": {
      "content": { "type": "string" },
      "visibility": { "type": "string", "enum": ["PUBLIC", "CONNECTIONS"] }
    },
    "required": ["content"]
  }
}
```

#!/usr/bin/env python
"""Update main.py to support Responses API"""
import re

# Read main.py
with open('main.py', 'r') as f:
    content = f.read()

# Update ChatMessage model
old_chatmessage = """class ChatMessage(BaseModel):
    \"\"\"Chat message model\"\"\"
    message: str
    context: Optional[str] = None
    reasoning_effort: Optional[str] = \"high\"
    user_id: Optional[str] = None
    session_id: Optional[str] = None"""

new_chatmessage = """class ChatMessage(BaseModel):
    \"\"\"Chat message model\"\"\"
    message: str
    context: Optional[str] = None
    reasoning_effort: Optional[str] = \"high\"
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    previous_response_id: Optional[str] = None
    use_encrypted_content: bool = False"""

if old_chatmessage in content:
    content = content.replace(old_chatmessage, new_chatmessage)
    print('✓ Updated ChatMessage model')
else:
    print('✗ ChatMessage pattern not found')

# Write back
with open('main.py', 'w') as f:
    f.write(content)

print('Done updating main.py')

#!/usr/bin/env python3
"""Fix grok_llm.py to make SDK imports optional"""

file_path = r'backend/grok_llm.py'

# Read the file
with open(file_path, 'r') as f:
    content = f.read()

# Replace the direct import with a try-except block
old_import = """import logging

from roboto_sai_sdk import get_xai_grok

logger = logging.getLogger(__name__)"""

new_import = """import logging

logger = logging.getLogger(__name__)

# Import Roboto SAI SDK (optional)
try:
    from roboto_sai_sdk import get_xai_grok
    HAS_SDK = True
except ImportError:
    logger.warning("roboto_sai_sdk not available in grok_llm")
    HAS_SDK = False
    get_xai_grok = None"""

content = content.replace(old_import, new_import)

# Write the file back
with open(file_path, 'w') as f:
    f.write(content)

print("✅ Fixed grok_llm.py - SDK import is now optional")

#!/usr/bin/env python3
"""Fix GrokLLM to handle missing SDK"""

file_path = r'backend/grok_llm.py'

# Read the file
with open(file_path, 'r') as f:
    content = f.read()

# Replace the __init__ method to handle None get_xai_grok
old_init = """    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        object.__setattr__(self, 'client', get_xai_grok())"""

new_init = """    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Only initialize client if SDK is available
        if HAS_SDK and get_xai_grok is not None:
            try:
                object.__setattr__(self, 'client', get_xai_grok())
            except Exception as e:
                logger.warning(f"Failed to initialize Grok client: {e}")
                object.__setattr__(self, 'client', None)
        else:
            object.__setattr__(self, 'client', None)"""

content = content.replace(old_init, new_init)

# Write the file back
with open(file_path, 'w') as f:
    f.write(content)

print("✅ Fixed GrokLLM.__init__ to handle missing SDK")

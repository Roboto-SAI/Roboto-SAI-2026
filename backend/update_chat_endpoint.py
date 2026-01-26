#!/usr/bin/env python
"""Update chat endpoint for Responses API"""

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the old _acall with acall_with_response_id
old_call = '''        # Call GrokLLM with full conversation history
        response_text = await grok_llm._acall(all_messages)'''

new_call = '''        # Call GrokLLM with Responses API for conversation chaining
        grok_result = await grok_llm.acall_with_response_id(
            all_messages,
            emotion=user_emotion.get('emotion_text', '') if user_emotion else '',
            user_name=user.get('user_metadata', {}).get('name', 'user'),
            previous_response_id=request.previous_response_id
        )
        response_text = grok_result.get('response', '')
        response_id = grok_result.get('response_id')
        encrypted_thinking = grok_result.get('encrypted_thinking')'''

if old_call in content:
    content = content.replace(old_call, new_call)
    print('✓ Updated acall_with_response_id call')
else:
    print('✗ Old _acall pattern not found')

# Also update the return to include actual response_id
old_return = '''            "response_id": f"lc-{session_id}",'''
new_return = '''            "response_id": response_id or f"lc-{session_id}",
            "encrypted_thinking": encrypted_thinking,
            "xai_stored": grok_result.get('stored', False),'''

if old_return in content:
    content = content.replace(old_return, new_return)
    print('✓ Updated response return fields')
else:
    print('✗ Old response_id pattern not found')

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done updating chat endpoint')

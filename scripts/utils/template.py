import re

def render_template(text, char_name, user_name):
    if not text:
        return ""
    text = text.replace('{{char}}', char_name).replace('{{Char}}', char_name)
    text = text.replace('{{user}}', user_name).replace('{{User}}', user_name)
    return text

def parse_mes_example(mes_example, char_name, user_name):
    # Splits the example messages by <START> into distinct interactions
    exchanges = []
    if not mes_example:
        return exchanges

    blocks = re.split(r'<START>', mes_example)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        # very rudimentary parsing assuming {{user}}: and {{char}}: patterns
        # In a real environment, it would handle complex prompt shapes
        exchanges.append(render_template(block, char_name, user_name))

    return exchanges

assistant_template = '''
<div class="chat-message bot">
    <div class="avatar">
        <img src={avatar_icon}>
    </div>
    <div class="message">{message}</div>
</div>
'''

user_template = '''
<div class="chat-message user">
    <div class="avatar">
        <img src="{avatar_icon}">
    </div>
    <div class="message">{message}</div>
</div>
'''

if __name__ == "__main__":
    # Example usage
    avatar_icon = "https://example.com/avatar.png"
    message = "Hello, this is a test message."

    # Render the templates with example data
    rendered_assistant = assistant_template.format(avatar_icon=avatar_icon, message=message)
    rendered_user = user_template.format(avatar_icon=avatar_icon, message=message)

    print(rendered_assistant)
    print(rendered_user)
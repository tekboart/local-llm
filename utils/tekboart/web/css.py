def load_css(file_name, add_tag:bool = False):
    """
    Load CSS from a file and return it as a string.

    Args:
        file_name (str): The name of the CSS file to load.
        add_tag (bool): Whether to add <style> tags around the CSS content.
    """
    with open(file_name, "r", encoding="utf-8") as f:
        css_file = f.read()
    if add_tag:
        css_file = f"<style>{css_file}</style>"
    return css_file
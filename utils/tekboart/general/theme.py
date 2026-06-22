import platform
import subprocess
import os


def get_system_theme():
    """
    Detects the system's theme (dark or light) based on the operating system.

    Returns:
        str: "dark" if the system is in dark mode, "light" if in light mode,
             or "unknown" if it cannot be determined.

    Methods:
        - Windows: Queries the registry for 'AppsUseLightTheme'.
        - macOS: Uses 'defaults' command to check 'AppleInterfaceStyle'.
        - Linux (GNOME-based): Uses 'gsettings' to check 'color-scheme' and WM theme.
        # TODO: Add support for other Linux desktop environments (e.g., KDE, XFCE).
    """
    system = platform.system()

    if system == "Windows":
        try:
            result = subprocess.run(
                ['reg', 'query', 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize', '/v', 'AppsUseLightTheme'],
                capture_output=True, text=True
            )
            return "dark" if '0x0' in result.stdout else "light"
        except Exception as e:
            print(f"Error in Windows theme detection: {e}")
            return "unknown"

    elif system == "Darwin":  # macOS
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True
            )
            return "dark" if "Dark" in result.stdout else "light"
        except Exception:
            print("Error in macOS theme detection")
            return "light"  # If AppleInterfaceStyle is not found, assume light mode

    elif system == "Linux":
        try:
            # Check the color-scheme setting
            color_scheme = os.popen("gsettings get org.gnome.desktop.interface color-scheme").read().strip()
            print(f"gsettings color-scheme result: {color_scheme}")  # Debug output to check what is returned

            if "dark" in color_scheme:
                return "dark"
            elif color_scheme == "'default'":
                # Check the current window manager theme
                wm_theme = os.popen("gsettings get org.gnome.desktop.wm.preferences theme").read().strip()
                print(f"Window Manager Theme: {wm_theme}")  # Debug output to check the WM theme

                if "dark" in wm_theme.lower():
                    return "dark"
                else:
                    return "light"
            else:
                return "unknown"
        except Exception as e:
            print(f"Error in Linux theme detection: {e}")
            return "unknown"

    return "unknown_os"


if __name__ == "__main__":
    print("System Theme:", get_system_theme())

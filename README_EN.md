# Pardus System Cleaner 🧹

Developed by the **İnoTürk** team for the 2026 Teknofest Pardus Bug Catching and Suggestion Competition (Development Category).

## About
Pardus System Cleaner is a modern, secure, and user-friendly Linux system cleaning tool. Unlike traditional cleaners, it uses a **rule-based, smart, and transparent** cleaning engine rather than blindly deleting system files. It securely removes unnecessary leftovers without touching any files that could disrupt the system's operation.

[Türkçe Dokümantasyon (README.md)](README.md)

## Key Features

*   🛡️ **Zero-Risk Rule Engine**: Operates with explicitly defined rules (RuleEngine) dictating exactly what to delete.
*   🔒 **Smart Administrator (Root) Privileges**: Only asks for the root password when system-level operations (like `apt-get clean` or `journalctl`) are required. It NEVER asks for root privileges when cleaning user-level data (Cache, Trash). If the password prompt is cancelled, it gracefully continues cleaning safe user files.
*   👯 **Advanced Duplicate File Finder**: Strictly adheres to XDG standards (Desktop, Documents, Downloads, etc.) to scan only personal user folders. It intentionally ignores developer SDKs (Android, node_modules) and hidden `.cache` folders to prevent system corruption. It compares files using MD5 hashes of their **contents**, not their names.
*   🎨 **Modern GTK4 & Libadwaita UI**: Provides a fluid user experience featuring dark mode compatibility, animations, and options for both card and list views.
*   🌍 **Dual Language Support**: Automatically switches between Turkish and English based on your system locale.

## Installation & Execution

### .deb Package Installation (Recommended)
To fully integrate the application into your system (app menu, icons, etc.), download the latest `.deb` package from the GitHub Releases section and install it via terminal:
```bash
sudo dpkg -i pardus-temizleyici_1.0.0_all.deb
sudo apt install -f  # (To automatically install any missing dependencies)
```
After installation, you can launch the application by clicking its icon in the Pardus Applications menu or by typing `pardus-temizleyici` in the terminal.

### Running from Source Code (For Developers)
If you want to test the application directly from the source code, ensure the following system packages are installed:
- Python 3.x, `python3-gi`, `gir1.2-gtk-4.0`, `gir1.2-adw-1`, `pkexec`

Then navigate to the project directory in your terminal and execute:
```bash
python3 main.py
```

## Security Infrastructure
Pardus System Cleaner is highly secure against command injection. Personal user files are safely deleted using Python's native `os` and `shutil` libraries. System tasks (apt-get, journalctl) are isolated and managed securely in the background.

## License
This project is open-source and protected under the GPL-3.0 license. You are free to use, modify, and distribute it.

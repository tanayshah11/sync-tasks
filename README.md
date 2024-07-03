# Sync-Tasks

Sync-Tasks is a Python application designed to synchronize Google Tasks from multiple email accounts with Apple Reminders. It ensures that tasks completed on one platform are reflected as completed on the other, providing seamless integration between your Google and Apple task management systems.

## Features

- Sync Google Tasks to Apple Reminders
- Sync completed Apple Reminders to Google Tasks and mark them as completed
- Delete completed Apple Reminders after synchronization
- Automated synchronization using `launchd` on macOS

## Installation

### Prerequisites

- Python 3.7 or higher
- `pip` for installing Python packages
- `osascript` for AppleScript integration (pre-installed on macOS)

### Setup

1. Clone the repository:
    ```bash
    git clone https://github.com/tanayshah11/sync-tasks.git
    cd sync-tasks
    ```

2. Create a virtual environment and activate it:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4. Configure your environment variables in a `.env` file:
    ```plaintext
    TASK_SYNC_BASE_DIR=</path/to/your/sync-tasks/directory>
    ```

5. Set up your Google API credentials:
    - Follow the instructions to create OAuth 2.0 credentials: [Google Cloud Console](https://console.developers.google.com/)
    - Download the `credentials.json` file and place it in the directory specified in the `TASK_SYNC_BASE_DIR` environment variable.

## Usage

### Initial Run

1. Run the script manually to authenticate your Google accounts:
    ```bash
    python sync-tasks.py
    ```
2. This will generate token_<email_id> files for your emails acting as Authentication Caches.

### Automate with `launchd` - An Automation tool to run this script at regular intervals.

To automate the synchronization process using `launchd` on macOS, follow these steps:

1. Create a `com.<your-mac-username>.sync-tasks.plist` file in `~/Library/LaunchAgents/` with the following content:
    ```xml
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.<your-mac-username>.sync-tasks</string>
        <key>ProgramArguments</key>
        <array>
            <string>/path/to/your/venv/bin/python</string>
            <string>/path/to/your/sync-tasks/sync-tasks.py</string>
        </array>
        <key>StartInterval</key>
        <integer>300</integer> <!-- Runs every 5 minutes. You can change it according to your needs -->
        <key>StandardOutPath</key>
        <string>/path/to/your/sync-tasks/sync-tasks.log</string>
        <key>StandardErrorPath</key>
        <string>/path/to/your/sync-tasks/sync-tasks.err</string>
    </dict>
    </plist>
    ```

2. Load the new `launchd` configuration:
    ```bash
    launchctl load ~/Library/LaunchAgents/com.<your-mac-username>.sync-tasks.plist
    ```

### Checking Logs

To view the logs, you can check the `sync-tasks.log` and `sync-tasks.err` files in your project directory.

## Thank You

Thank you for using Sync-Tasks! We hope this tool helps streamline your task management across Google and Apple platforms. If you have any questions, issues, or feedback, please feel free to open an issue on our [GitHub repository](https://github.com/yourusername/sync-tasks/issues).

Happy task syncing!

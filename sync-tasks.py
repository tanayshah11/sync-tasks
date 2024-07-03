import os
import json
import subprocess
import time
import requests
import logging
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Scopes for Google Tasks API
SCOPES = ["https://www.googleapis.com/auth/tasks"]

# Number of retries and delay between retries
RETRY_COUNT = 5
RETRY_DELAY = 60  # in seconds

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Suppress the informational messages from googleapiclient
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)

# Define base directory using environment variable
BASE_DIR = os.getenv("TASK_SYNC_BASE_DIR")


def is_connected():
    try:
        # Try to connect to a reliable site
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False


def authenticate_google_account(credentials_path, token_path):
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    return creds


def get_google_tasks(creds):
    try:
        service = build("tasks", "v1", credentials=creds)
        tasklists = service.tasklists().list().execute().get("items", [])
        tasks = []
        for tasklist in tasklists:
            tasklist_id = tasklist["id"]
            tasklist_tasks = (
                service.tasks().list(tasklist=tasklist_id).execute().get("items", [])
            )
            for task in tasklist_tasks:
                tasks.append(task)
        return tasks
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return []


def create_reminder(title, notes, list_name="Reminders"):
    script = f"""
    tell application "Reminders"
        set reminderList to list "{list_name}"
        set newReminder to make new reminder in reminderList with properties {{name:"{title}", body:"{notes}"}}
    end tell
    """
    subprocess.run(["osascript", "-e", script])


def reminder_exists(title, list_name="Reminders"):
    script = f"""
    tell application "Reminders"
        set reminderList to list "{list_name}"
        try
            set existingReminder to (first reminder in reminderList whose name is "{title}")
            return "true"
        on error
            return "false"
        end try
    end tell
    """
    result = (
        subprocess.check_output(["osascript", "-e", script]).decode("utf-8").strip()
    )
    return result == "true"


def sync_google_tasks_to_apple_reminders(email_to_list):
    credentials_path = os.path.join(BASE_DIR, "credentials.json")
    for email, reminder_list in email_to_list.items():
        token_path = os.path.join(BASE_DIR, f"token_{email}.json")
        creds = authenticate_google_account(credentials_path, token_path)
        tasks = get_google_tasks(creds)

        for task in tasks:
            if task.get("status") != "completed":
                title = task.get("title", "No Title")
                notes = task.get("notes", "No Notes")
                if not reminder_exists(title, reminder_list):
                    create_reminder(title, notes, reminder_list)


def get_completed_apple_reminders(list_name="Reminders"):
    script = f"""
    tell application "Reminders"
        set reminderList to list "{list_name}"
        set completedTasks to (every reminder in reminderList whose completed is true)
        set taskDetails to ""
        repeat with aTask in completedTasks
            set taskDetails to taskDetails & name of aTask & "|||" & body of aTask & "\n"
        end repeat
        return taskDetails
    end tell
    """
    completed_tasks = subprocess.check_output(["osascript", "-e", script])
    task_lines = completed_tasks.decode("utf-8").strip().split("\n")
    tasks = [line.split("|||") for line in task_lines if "|||" in line]
    return tasks


def delete_completed_apple_reminders(list_name="Reminders"):
    script = f"""
    tell application "Reminders"
        set reminderList to list "{list_name}"
        delete (every reminder in reminderList whose completed is true)
    end tell
    """
    subprocess.run(["osascript", "-e", script])


def mark_google_task_completed(creds, task_title, task_notes):
    try:
        service = build("tasks", "v1", credentials=creds)
        tasklists = service.tasklists().list().execute().get("items", [])

        for tasklist in tasklists:
            tasklist_id = tasklist["id"]
            tasklist_tasks = (
                service.tasks().list(tasklist=tasklist_id).execute().get("items", [])
            )

            for task in tasklist_tasks:
                if task["title"] == task_title and "completed" not in task:
                    task["status"] = "completed"
                    service.tasks().update(
                        tasklist=tasklist_id, task=task["id"], body=task
                    ).execute()
                    logger.info(f"Marked Google Task '{task_title}' as completed.")
                    return True

            logger.warning(f"Task '{task_title}' not found in Google Tasks.")
            return False
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False


def sync_completed_reminders_to_google_tasks(email_to_list):
    credentials_path = os.path.join(BASE_DIR, "credentials.json")

    for email, reminder_list in email_to_list.items():
        token_path = os.path.join(BASE_DIR, f"token_{email}.json")
        creds = authenticate_google_account(credentials_path, token_path)
        completed_reminders = get_completed_apple_reminders(reminder_list)

        for reminder in completed_reminders:
            task_title = reminder[0]
            task_notes = reminder[1] if len(reminder) > 1 else ""
            if not task_title:
                logger.info("Skipping reminder with empty title.")
                continue
            mark_google_task_completed(creds, task_title, task_notes)

        # After processing completed reminders, delete them
        delete_completed_apple_reminders(reminder_list)


def main():
    # Retry logic
    for attempt in range(RETRY_COUNT):
        if is_connected():
            # email to list mapping
            email_to_list = {
                "<EMAIL_1>": "<Apple Reminders List Name for the email you want it associated to>",
                "<EMAIL_2>": "<Apple Reminders List Name for the email you want it associated to>",
                "<EMAIL_3>": "<Apple Reminders List Name for the email you want it associated to>",
                "<EMAIL_4>": "<Apple Reminders List Name for the email you want it associated to>",
            }

            # First, sync completed Apple Reminders to Google Tasks
            sync_completed_reminders_to_google_tasks(email_to_list)

            # Then, sync Google Tasks to Apple Reminders
            sync_google_tasks_to_apple_reminders(email_to_list)
            break
        else:
            logger.warning(
                f"No internet connection. Retrying in {RETRY_DELAY} seconds..."
            )
            time.sleep(RETRY_DELAY)
    else:
        logger.error("Failed to connect to the internet after multiple attempts.")


if __name__ == "__main__":
    main()

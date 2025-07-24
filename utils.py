#!/usr/bin/env python3

import os
import sys
import getpass
import json
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# Load .env for credentials and URLs
load_dotenv()

# Try to import GUI components (optional)
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog
    HAS_GUI = True
except ImportError:
    HAS_GUI = False

# Config file for storing credentials
CONFIG_PATH = os.path.expanduser("~/.uc_anki_config.json")

# Parse environment variables
RAW_BASE_URL = os.getenv("UC_BASE_URL", "").strip()
ENV_BAG_ID = os.getenv("UC_BAG_ID", "").strip()  # optional

# Parse whatever the user put in UC_BASE_URL
if RAW_BASE_URL:
    parsed = urlparse(RAW_BASE_URL)
    BASE = f"{parsed.scheme}://{parsed.netloc}"
    # if they embedded a bag_id in the query, pull it out
    qs = parse_qs(parsed.query)
    parsed_bag = qs.get("bag_id", [None])[0]
    # if path is a full details URL, keep it
    default_details_url = RAW_BASE_URL if "/details/" in parsed.path else None
else:
    BASE = "https://cards.ucalgary.ca"
    parsed_bag = None
    default_details_url = None

# Priority for bag_id:
# 1. explicit UC_BAG_ID
# 2. parsed from UC_BASE_URL
# 3. fall back to deck_id at runtime
BAG_ID_DEFAULT = ENV_BAG_ID or parsed_bag

# Anki constants
DECK_ID_BASE = 1607392319000
MODEL_ID = 1607392319001

# Try to import tkinter for file dialogs (fallback to command line if not available)
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
    HAS_GUI = True
except ImportError:
    HAS_GUI = False


def get_chrome_options():
    """Get standardized Chrome options for Selenium"""
    from selenium import webdriver
    
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--kiosk-printing")
    # Suppress Chrome error messages and warnings
    opts.add_argument("--disable-logging")
    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-web-security")
    opts.add_argument("--disable-features=VizDisplayCompositor")
    opts.add_argument("--log-level=3")  # Only show fatal errors
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_experimental_option(
        "prefs",
        {
            "printing.print_preview_sticky_settings.appState": '{"recentDestinations":[],"selectedDestinationId":"Save as PDF","version":2}'
        },
    )
    return opts


def setup_driver_print_override(driver):
    """Setup driver to prevent print dialogs"""
    # Prevent the print dialog by overriding window.print before any page loads
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument", {"source": "window.print = () => {};"}
    )
    return driver


def save_credentials(email, password, base_host):
    """Save credentials to config file"""
    config = {"email": email, "password": password, "base_host": base_host}
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f)
        print(f"✅ Credentials saved to {CONFIG_PATH}")
    except Exception as e:
        print(f"⚠️ Could not save credentials: {e}")


def load_credentials():
    """Load credentials from config file"""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load saved credentials: {e}")
    return {}


def prompt_credentials(base_host):
    """Prompt user for credentials with GUI or CLI fallback, includes login validation"""
    # Import here to avoid circular imports
    from selenium import webdriver
    from auth import selenium_login
    
    for attempt in range(3):
        if HAS_GUI:
            try:
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                
                email = tk.simpledialog.askstring(
                    "Login", 
                    f"Enter your email for {base_host}:",
                    parent=root
                )
                if not email:
                    root.destroy()
                    sys.exit("Login cancelled by user.")
                    
                password = tk.simpledialog.askstring(
                    "Login", 
                    f"Enter your password for {base_host}:",
                    parent=root,
                    show="*"
                )
                if not password:
                    root.destroy()
                    sys.exit("Login cancelled by user.")
                    
                root.destroy()
                
            except Exception as e:
                print(f"⚠️ GUI prompt failed: {e}")
                # Fall through to CLI prompt
                email = input("Enter your UCalgary email: ").strip()
                password = getpass.getpass("Enter your UCalgary password: ")
        else:
            # CLI fallback
            print(f"\n🔐 Please enter your credentials for {base_host}")
            email = input("Email: ").strip()
            if not email:
                sys.exit("No email provided.")
                
            password = getpass.getpass("Password: ").strip()
            if not password:
                sys.exit("No password provided.")
        
        # Test login with Chrome
        opts = get_chrome_options()
        driver = webdriver.Chrome(options=opts)
        setup_driver_print_override(driver)
        
        try:
            selenium_login(driver, email, password, base_host)
            print("✅ Login successful")
            driver.quit()
            
            # Ask if user wants to save credentials (only after successful login)
            if HAS_GUI:
                try:
                    root = tk.Tk()
                    root.withdraw()
                    save_creds = messagebox.askyesno(
                        "Save Credentials", 
                        "Would you like to save these credentials for future use?\n\n"
                        "They will be stored locally in your home directory."
                    )
                    root.destroy()
                    if save_creds:
                        save_credentials(email, password, base_host)
                except:
                    pass
            else:
                save_choice = input("\nSave credentials for future use? (y/n): ").strip().lower()
                if save_choice in ['y', 'yes']:
                    save_credentials(email, password, base_host)
            
            return email, password
            
        except Exception as e:
            print(f"❌ Login failed: {e}")
            driver.quit()
            if attempt < 2:
                print(f"Please try again ({attempt + 1}/3 attempts)")
    
    sys.exit("❌ Failed to login after 3 attempts")


def prompt_save_location(default_filename):
    """Prompt user for save location with GUI or CLI fallback"""
    if HAS_GUI:
        try:
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            file_path = filedialog.asksaveasfilename(
                title="Save Anki deck as...",
                defaultextension=".apkg",
                filetypes=[("Anki deck files", "*.apkg"), ("All files", "*.*")],
                initialvalue=default_filename
            )
            
            root.destroy()
            return file_path if file_path else None
            
        except Exception as e:
            print(f"⚠️ GUI file dialog failed: {e}")
            # Fall through to CLI prompt
    
    # CLI fallback
    save_path = input(f"💾 Enter save path (default: {default_filename}): ").strip()
    return save_path if save_path else default_filename


def prompt_save_location(default_filename):
    """
    Prompt user for save location using GUI file dialog if available,
    otherwise fall back to command line input.
    """
    if HAS_GUI:
        try:
            # Create a root window but hide it
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            root.lift()  # Bring to front
            root.attributes("-topmost", True)  # Keep on top

            # Configure file dialog
            file_types = [("Anki Deck Files", "*.apkg"), ("All Files", "*.*")]

            # Show save dialog
            file_path = filedialog.asksaveasfilename(
                title="Save Anki Deck As...",
                defaultextension=".apkg",
                filetypes=file_types,
                initialfile=default_filename,
            )

            # Clean up
            root.destroy()

            if file_path:  # User selected a file
                return file_path
            else:  # User cancelled
                print("Save cancelled by user.")
                sys.exit(0)

        except Exception as e:
            print(f"GUI dialog failed ({e}), falling back to command line input...")
            # Fall through to command line prompt

    # Command line fallback
    print(f"\n📁 Save Location")
    print(f"Default: {default_filename}")
    user_input = input(
        f"Enter path to save Anki deck (or press Enter for default): "
    ).strip()
    return user_input if user_input else default_filename


def show_completion_message(output_path, card_count):
    """
    Show completion message with GUI if available, otherwise console only.
    """
    message = f"✅ Success! Created Anki deck with {card_count} cards.\n\nSaved to: {output_path}\n\nImport this file into Anki:\nFile → Import → Select your .apkg file"

    if HAS_GUI:
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("Anki Deck Created Successfully!", message)
            root.destroy()
        except Exception:
            # Fall back to console if GUI fails
            pass

    print(f"\n🎉 {message}")

#!/usr/bin/env python3

import os
import sys
import getpass
import json
import contextlib
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# Load .env for credentials and URLs
load_dotenv()

# Try to import GUI components (optional)
try:
    import tkinter as tk
    import tkinter.simpledialog
    import tkinter.filedialog
    import tkinter.messagebox

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


def get_chrome_options():
    """Get standardized Chrome options for Selenium"""
    from selenium import webdriver
    import os

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
    opts.add_argument("--silent")
    opts.add_argument("--disable-background-timer-throttling")
    opts.add_argument("--disable-backgrounding-occluded-windows")
    opts.add_argument("--disable-renderer-backgrounding")
    opts.add_argument("--disable-dev-tools")
    opts.add_argument("--disable-infobars")
    opts.add_argument("--disable-notifications")
    # Set remote debugging port to 0 to disable it
    opts.add_argument("--remote-debugging-port=0")
    opts.add_argument("--no-first-run")
    opts.add_argument("--no-default-browser-check")
    opts.add_experimental_option(
        "excludeSwitches",
        ["enable-logging", "enable-automation", "enable-development-tools"],
    )
    opts.add_experimental_option("useAutomationExtension", False)

    # Redirect Chrome logs to null to suppress DevTools messages
    if os.name == "nt":  # Windows
        opts.add_argument("--log-file=NUL")
    else:  # Unix-like
        opts.add_argument("--log-file=/dev/null")

    opts.add_experimental_option(
        "prefs",
        {
            "printing.print_preview_sticky_settings.appState": '{"recentDestinations":[],"selectedDestinationId":"Save as PDF","version":2}'
        },
    )
    return opts


def setup_driver_with_output_suppression():
    """Setup Chrome driver with output suppression for DevTools messages"""
    import sys
    import os
    import contextlib
    from selenium import webdriver

    # Context manager to suppress stdout/stderr temporarily during driver creation
    @contextlib.contextmanager
    def suppress_chrome_output():
        if os.name == "nt":  # Windows
            import msvcrt
            import ctypes
            from ctypes import wintypes

            # Temporarily redirect stdout/stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            try:
                with open(os.devnull, "w") as devnull:
                    sys.stdout = devnull
                    sys.stderr = devnull
                    yield
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
        else:
            # Unix-like systems
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            try:
                with open(os.devnull, "w") as devnull:
                    sys.stdout = devnull
                    sys.stderr = devnull
                    yield
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

    # Create driver with suppressed output
    opts = get_chrome_options()
    with suppress_chrome_output():
        driver = webdriver.Chrome(options=opts)

    return driver


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


def validate_saved_credentials_for_host(base_host):
    """Check if saved credentials are valid for the given host"""
    saved_creds = load_credentials()
    if not (saved_creds.get("email") and saved_creds.get("password")):
        return None

    # Check if the saved base_host matches the current one
    saved_host = saved_creds.get("base_host", "")
    if saved_host and base_host:
        from urllib.parse import urlparse

        saved_parsed = urlparse(saved_host)
        current_parsed = urlparse(base_host)

        # Compare just the netloc (domain) parts
        if saved_parsed.netloc.lower() == current_parsed.netloc.lower():
            return saved_creds

    # If no base_host info or they match, return credentials
    if not saved_host or not base_host:
        return saved_creds

    return None


def create_unified_login_dialog(base_host=None, url_required=False):
    """Create a unified dialog with URL (optional), username, password, and save option"""
    root = tk.Tk()
    root.title("UCalgary Anki Converter")

    # Adjust window size based on whether URL input is needed
    window_height = 320 if url_required else 250
    root.geometry(f"450x{window_height}")
    root.resizable(False, False)

    # Center the window
    root.eval("tk::PlaceWindow . center")

    # Make sure the window is on top and focused
    root.lift()
    root.focus_force()
    root.attributes("-topmost", True)
    root.after(100, lambda: root.attributes("-topmost", False))

    # Variables to store the results
    url_var = tk.StringVar(value=base_host or "")
    email_var = tk.StringVar()
    password_var = tk.StringVar()
    save_var = tk.BooleanVar(value=True)  # Default to saving credentials
    result = {
        "url": None,
        "email": None,
        "password": None,
        "save": False,
        "cancelled": True,
    }

    # Flag to track when dialog is complete
    dialog_complete = [False]

    # Create the form
    title_text = "UCalgary Anki Converter"
    tk.Label(root, text=title_text, font=("Arial", 14, "bold")).pack(pady=10)

    # URL field (only if required)
    if url_required:
        tk.Label(root, text="UCalgary Deck/Collection URL:", font=("Arial", 10)).pack(
            anchor="w", padx=20
        )
        url_entry = tk.Entry(root, textvariable=url_var, width=50, font=("Arial", 10))
        url_entry.pack(pady=(0, 10), padx=20)

    # Email field
    tk.Label(root, text="Email:", font=("Arial", 10)).pack(anchor="w", padx=20)
    email_entry = tk.Entry(root, textvariable=email_var, width=50, font=("Arial", 10))
    email_entry.pack(pady=(0, 10), padx=20)

    # Password field
    tk.Label(root, text="Password:", font=("Arial", 10)).pack(anchor="w", padx=20)
    password_entry = tk.Entry(
        root, textvariable=password_var, show="*", width=50, font=("Arial", 10)
    )
    password_entry.pack(pady=(0, 10), padx=20)

    # Save credentials checkbox
    save_checkbox = tk.Checkbutton(
        root,
        text="Save credentials for future use",
        variable=save_var,
        font=("Arial", 9),
    )
    save_checkbox.pack(pady=(5, 15))

    # Button frame
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    def validate_and_submit():
        url = url_var.get().strip() if url_required else base_host
        email = email_var.get().strip()
        password = password_var.get().strip()

        if url_required and not url:
            tk.messagebox.showerror("Error", "Please enter the UCalgary URL")
            if url_required:
                url_entry.focus()
            return

        if not email:
            tk.messagebox.showerror("Error", "Please enter your email")
            email_entry.focus()
            return

        if not password:
            tk.messagebox.showerror("Error", "Please enter your password")
            password_entry.focus()
            return

        result["url"] = url
        result["email"] = email
        result["password"] = password
        result["save"] = save_var.get()
        result["cancelled"] = False

        dialog_complete[0] = True
        root.quit()

    def cancel_dialog():
        result["cancelled"] = True
        dialog_complete[0] = True
        root.quit()

    # Buttons
    ok_button = tk.Button(
        button_frame,
        text="Login",
        command=validate_and_submit,
        width=12,
        font=("Arial", 10),
    )
    ok_button.pack(side="left", padx=(0, 10))

    cancel_button = tk.Button(
        button_frame, text="Cancel", command=cancel_dialog, width=12, font=("Arial", 10)
    )
    cancel_button.pack(side="left")

    # Set focus and bind keys
    if url_required:
        url_entry.focus()
    else:
        email_entry.focus()

    root.bind("<Return>", lambda event: validate_and_submit())
    root.bind("<Escape>", lambda event: cancel_dialog())

    # Handle window close button
    root.protocol("WM_DELETE_WINDOW", cancel_dialog)

    # Start the dialog and wait for it to complete
    while not dialog_complete[0]:
        try:
            root.update()
        except tk.TclError:
            # Window was destroyed
            break

    # Clean up
    try:
        root.destroy()
    except:
        pass

    return result


def prompt_url_only():
    """Prompt user for URL only when credentials are already saved"""
    if HAS_GUI:
        try:
            root = tk.Tk()
            root.title("UCalgary Anki Converter")
            root.geometry("450x180")
            root.resizable(False, False)

            # Center the window
            root.eval("tk::PlaceWindow . center")

            # Make sure the window is on top and focused
            root.lift()
            root.focus_force()
            root.attributes("-topmost", True)
            root.after(100, lambda: root.attributes("-topmost", False))

            # Variables to store the results
            url_var = tk.StringVar(value="")
            result = {"url": None, "cancelled": True}

            # Flag to track when dialog is complete
            dialog_complete = [False]

            # Create the form
            tk.Label(
                root, text="UCalgary Anki Converter", font=("Arial", 14, "bold")
            ).pack(pady=10)

            # URL field
            tk.Label(
                root, text="Enter UCalgary deck or collection URL:", font=("Arial", 10)
            ).pack(anchor="w", padx=20)
            tk.Label(
                root,
                text="(e.g., https://cards.ucalgary.ca/details/123 or /collection/456)",
                font=("Arial", 8),
                fg="gray",
            ).pack(anchor="w", padx=20)
            url_entry = tk.Entry(
                root, textvariable=url_var, width=50, font=("Arial", 10)
            )
            url_entry.pack(pady=(5, 15), padx=20)

            # Button frame
            button_frame = tk.Frame(root)
            button_frame.pack(pady=10)

            def validate_and_submit():
                url = url_var.get().strip()

                if not url:
                    tk.messagebox.showerror("Error", "Please enter the UCalgary URL")
                    url_entry.focus()
                    return

                result["url"] = url
                result["cancelled"] = False

                dialog_complete[0] = True
                root.quit()

            def cancel_dialog():
                result["cancelled"] = True
                dialog_complete[0] = True
                root.quit()

            # Buttons
            ok_button = tk.Button(
                button_frame,
                text="Continue",
                command=validate_and_submit,
                width=12,
                font=("Arial", 10),
            )
            ok_button.pack(side="left", padx=(0, 10))

            cancel_button = tk.Button(
                button_frame,
                text="Cancel",
                command=cancel_dialog,
                width=12,
                font=("Arial", 10),
            )
            cancel_button.pack(side="left")

            # Set focus and bind keys
            url_entry.focus()
            root.bind("<Return>", lambda event: validate_and_submit())
            root.bind("<Escape>", lambda event: cancel_dialog())

            # Handle window close button
            root.protocol("WM_DELETE_WINDOW", cancel_dialog)

            # Start the dialog and wait for it to complete
            while not dialog_complete[0]:
                try:
                    root.update()
                except tk.TclError:
                    # Window was destroyed
                    break

            # Clean up
            try:
                root.destroy()
            except:
                pass

            if result["cancelled"]:
                sys.exit("URL input cancelled by user.")

            return result["url"]

        except Exception as e:
            print(f"⚠️ GUI prompt failed: {e}")
            # Fall through to CLI prompt

    # CLI fallback
    url = input("Enter UCalgary collection or deck URL: ").strip()
    if not url:
        sys.exit("No URL provided.")
    return url


def prompt_url_with_validation(saved_email, saved_password):
    """Prompt user for URL with validation retry logic using saved credentials"""
    # Import here to avoid circular imports
    from selenium import webdriver
    from auth import selenium_login

    for attempt in range(3):
        print(f"Using saved credentials for {saved_email}. Please enter URL...")

        if HAS_GUI:
            try:
                full_url = prompt_url_only()
                parsed = urlparse(full_url)
                base_host = f"{parsed.scheme}://{parsed.netloc}"
            except Exception as e:
                print(f"⚠️ GUI prompt failed: {e}")
                full_url = input("Enter UCalgary URL: ").strip()
                if not full_url:
                    sys.exit("No URL provided.")
                parsed = urlparse(full_url)
                base_host = f"{parsed.scheme}://{parsed.netloc}"
        else:
            # CLI fallback
            full_url = input("Enter UCalgary collection or deck URL: ").strip()
            if not full_url:
                sys.exit("No URL provided.")
            parsed = urlparse(full_url)
            base_host = f"{parsed.scheme}://{parsed.netloc}"

        # Test the URL with saved credentials
        opts = get_chrome_options()
        driver = webdriver.Chrome(options=opts)
        setup_driver_print_override(driver)

        try:
            # Validate both login and target URL
            selenium_login(driver, saved_email, saved_password, base_host, full_url)
            print("✅ URL validation successful")
            driver.quit()
            return full_url

        except Exception as e:
            error_message = str(e)
            driver.quit()

            # Check if this is a URL/network issue vs credentials issue
            if "URL/Network error" in error_message:
                print(f"❌ {error_message}")
                if attempt < 2:
                    print(f"Please try a different URL ({attempt + 1}/3 attempts)")
            else:
                print(f"❌ {error_message}")
                print("⚠️ Your saved credentials may be invalid. Please re-enter them.")
                # Clear saved credentials and prompt for new ones
                try:
                    os.remove(CONFIG_PATH)
                    print("🗑️ Cleared saved credentials")
                except:
                    pass
                # Redirect to full login process
                return prompt_url_and_credentials_with_url()[2]  # Return just the URL

    # If we reach here, all URL attempts failed but credentials are valid
    print("❌ Failed to find a valid URL after 3 attempts.")
    print("💾 Your credentials are still saved for future use.")
    print("🔄 Please run the script again and try different URLs.")
    sys.exit("URL validation failed - credentials preserved")


def show_script_running_dialog():
    """Show a non-blocking dialog to inform user that script is running"""
    if HAS_GUI:
        try:
            root = tk.Tk()
            root.title("UCalgary Anki Converter - Processing")
            root.geometry(
                "600x300"
            )  # Increased width and height for better text visibility
            root.resizable(False, False)

            # Center the window
            root.eval("tk::PlaceWindow . center")

            # Make sure the window is on top and focused
            root.lift()
            root.focus_force()
            root.attributes("-topmost", True)

            # Create the content with better spacing
            tk.Label(root, text="🔄 Processing Cards", font=("Arial", 18, "bold")).pack(
                pady=(25, 15)  # More top padding, more bottom padding
            )

            message = (
                "The script is now running and processing your UCalgary cards.\n\n"
                "This may take a few minutes depending on the number of cards.\n\n"
                "Please wait... A file save dialog will appear when complete."
            )

            tk.Label(
                root,
                text=message,
                font=("Arial", 12),
                justify="center",
                wraplength=550,  # Increased wrap length to match wider dialog
            ).pack(pady=(15, 25))

            # Add a progress indicator (just visual, not functional)
            progress_frame = tk.Frame(root)
            progress_frame.pack(pady=(10, 25))

            tk.Label(
                progress_frame,
                text="⏳ Extracting and processing cards...",
                font=("Arial", 11),
            ).pack()

            # Update the window to show it
            root.update()

            return root

        except Exception as e:
            print(f"⚠️ Could not show progress dialog: {e}")
            return None
    return None


def close_script_running_dialog(dialog_root):
    """Close the script running dialog"""
    if dialog_root:
        try:
            dialog_root.destroy()
        except:
            pass


def create_login_dialog(base_host):
    """Create a custom login dialog with username, password, and save option"""
    return create_unified_login_dialog(base_host, url_required=False)


def prompt_url_and_credentials_with_url():
    """Prompt user for full URL and credentials in a unified dialog"""
    # Import here to avoid circular imports
    from selenium import webdriver
    from auth import selenium_login

    saved_credentials = None  # Track if we have valid credentials

    for attempt in range(3):
        # If we have saved credentials from a previous attempt, only prompt for URL
        if saved_credentials:
            print(
                "Using previously validated credentials. Please enter a different URL..."
            )
            if HAS_GUI:
                try:
                    full_url = prompt_url_only()
                    parsed = urlparse(full_url)
                    base_host = f"{parsed.scheme}://{parsed.netloc}"
                    email, password, should_save = saved_credentials
                except Exception as e:
                    print(f"⚠️ GUI prompt failed: {e}")
                    full_url = input("Enter UCalgary URL: ").strip()
                    if not full_url:
                        sys.exit("No URL provided.")
                    parsed = urlparse(full_url)
                    base_host = f"{parsed.scheme}://{parsed.netloc}"
                    email, password, should_save = saved_credentials
            else:
                # CLI fallback
                full_url = input("Enter UCalgary URL: ").strip()
                if not full_url:
                    sys.exit("No URL provided.")
                parsed = urlparse(full_url)
                base_host = f"{parsed.scheme}://{parsed.netloc}"
                email, password, should_save = saved_credentials
        else:
            # First attempt or no saved credentials - prompt for everything
            if HAS_GUI:
                try:
                    # Use unified login dialog with URL input required
                    login_result = create_unified_login_dialog(None, url_required=True)

                    if login_result["cancelled"]:
                        sys.exit("Login cancelled by user.")

                    # Extract full URL and parse host
                    full_url = login_result["url"]
                    parsed = urlparse(full_url)
                    base_host = f"{parsed.scheme}://{parsed.netloc}"

                    email = login_result["email"]
                    password = login_result["password"]
                    should_save = login_result["save"]

                except Exception as e:
                    print(f"⚠️ GUI prompt failed: {e}")
                    # Fall through to CLI prompt
                    full_url = input("Enter UCalgary URL: ").strip()
                    if not full_url:
                        sys.exit("No URL provided.")
                    parsed = urlparse(full_url)
                    base_host = f"{parsed.scheme}://{parsed.netloc}"

                    email = input("Enter your UCalgary email: ").strip()
                    password = getpass.getpass("Enter your UCalgary password: ")
                    should_save = input(
                        "Save credentials for future use? (y/n): "
                    ).strip().lower() in ["y", "yes"]
            else:
                # CLI fallback
                full_url = input("Enter UCalgary URL: ").strip()
                if not full_url:
                    sys.exit("No URL provided.")
                parsed = urlparse(full_url)
                base_host = f"{parsed.scheme}://{parsed.netloc}"

                print(f"\n🔐 Please enter your credentials for {base_host}")
                email = input("Email: ").strip()
                if not email:
                    sys.exit("No email provided.")

                password = getpass.getpass("Password: ").strip()
                if not password:
                    sys.exit("No password provided.")

                should_save = input(
                    "Save credentials for future use? (y/n): "
                ).strip().lower() in ["y", "yes"]

        # Test login with Chrome
        opts = get_chrome_options()
        driver = webdriver.Chrome(options=opts)
        setup_driver_print_override(driver)

        try:
            # Validate both login and target URL
            selenium_login(driver, email, password, base_host, full_url)
            print("✅ Login successful")
            driver.quit()

            # Save credentials only if user chose to
            if should_save:
                try:
                    save_credentials(email, password, base_host)
                    print("💾 Credentials saved")
                except Exception as e:
                    print(f"⚠️ Could not save credentials: {e}")
            else:
                print("📝 Credentials not saved (user choice)")

            return email, password, full_url

        except Exception as e:
            error_message = str(e)
            driver.quit()

            # Check if this is a URL/network issue vs credentials issue
            if "URL/Network error" in error_message:
                print(f"❌ {error_message}")
                if not saved_credentials:
                    # First failure due to URL issue - keep credentials for next attempt but don't save yet
                    saved_credentials = (email, password, should_save)
                    print(
                        "💾 Credentials will be validated with working URL before saving"
                    )
                if attempt < 2:
                    print(f"Please try a different URL ({attempt + 1}/3 attempts)")
            else:
                print(f"❌ {error_message}")
                if attempt < 2:
                    print(
                        f"Please check your credentials and try again ({attempt + 1}/3 attempts)"
                    )
                # Don't save credentials if login failed due to auth issues
                saved_credentials = None

    if saved_credentials:
        sys.exit("❌ Failed to find a valid URL after 3 attempts")
    else:
        sys.exit("❌ Failed to login after 3 attempts")


def prompt_url_and_credentials(base_host=None):
    """Prompt user for URL and credentials in a unified dialog"""
    # Import here to avoid circular imports
    from selenium import webdriver
    from auth import selenium_login

    for attempt in range(3):
        if HAS_GUI:
            try:
                # Use unified login dialog with URL input if base_host is not provided
                login_result = create_unified_login_dialog(
                    base_host, url_required=(base_host is None)
                )

                if login_result["cancelled"]:
                    sys.exit("Login cancelled by user.")

                # Extract URL if it was part of the dialog
                if base_host is None:
                    url = login_result["url"]
                    parsed = urlparse(url)
                    base_host = f"{parsed.scheme}://{parsed.netloc}"

                email = login_result["email"]
                password = login_result["password"]
                should_save = login_result["save"]

            except Exception as e:
                print(f"⚠️ GUI prompt failed: {e}")
                # Fall through to CLI prompt
                if base_host is None:
                    url = input("Enter UCalgary URL: ").strip()
                    if not url:
                        sys.exit("No URL provided.")
                    parsed = urlparse(url)
                    base_host = f"{parsed.scheme}://{parsed.netloc}"

                email = input("Enter your UCalgary email: ").strip()
                password = getpass.getpass("Enter your UCalgary password: ")
                should_save = input(
                    "Save credentials for future use? (y/n): "
                ).strip().lower() in ["y", "yes"]
        else:
            # CLI fallback
            if base_host is None:
                url = input("Enter UCalgary URL: ").strip()
                if not url:
                    sys.exit("No URL provided.")
                parsed = urlparse(url)
                base_host = f"{parsed.scheme}://{parsed.netloc}"

            print(f"\n🔐 Please enter your credentials for {base_host}")
            email = input("Email: ").strip()
            if not email:
                sys.exit("No email provided.")

            password = getpass.getpass("Password: ").strip()
            if not password:
                sys.exit("No password provided.")

            should_save = input(
                "Save credentials for future use? (y/n): "
            ).strip().lower() in ["y", "yes"]

        # Test login with Chrome
        opts = get_chrome_options()
        driver = webdriver.Chrome(options=opts)
        setup_driver_print_override(driver)

        try:
            # If we have a full URL (when base_host was None), validate it too
            if "url" in locals():
                selenium_login(driver, email, password, base_host, url)
            else:
                selenium_login(driver, email, password, base_host)
            print("✅ Login successful")
            driver.quit()

            # Save credentials only if user chose to
            if should_save:
                try:
                    save_credentials(email, password, base_host)
                    print("💾 Credentials saved")
                except Exception as e:
                    print(f"⚠️ Could not save credentials: {e}")
            else:
                print("📝 Credentials not saved (user choice)")

            return email, password, base_host

        except Exception as e:
            print(f"❌ Login failed: {e}")
            driver.quit()
            if attempt < 2:
                print(f"Please try again ({attempt + 1}/3 attempts)")

    sys.exit("❌ Failed to login after 3 attempts")


def prompt_credentials(base_host):
    """Prompt user for credentials with GUI or CLI fallback, includes login validation"""
    email, password, _ = prompt_url_and_credentials(base_host)
    return email, password


def prompt_save_location(default_filename):
    """
    Prompt user for save location using GUI file dialog if available,
    otherwise fall back to command line input.
    """
    if HAS_GUI:
        try:
            # Create a simple root window
            root = tk.Tk()
            root.withdraw()  # Hide the main window

            # Simple file dialog without complex configurations
            file_types = [("Anki Deck Files", "*.apkg"), ("All Files", "*.*")]

            # Show save dialog
            file_path = tk.filedialog.asksaveasfilename(
                title="Save Anki Deck As...",
                defaultextension=".apkg",
                filetypes=file_types,
                initialfile=default_filename,
            )

            # Clean up immediately
            root.quit()
            root.destroy()

            if file_path:  # User selected a file
                return file_path
            else:  # User cancelled
                print("Save cancelled by user.")
                sys.exit(0)

        except Exception as e:
            print(f"⚠️ GUI dialog failed ({e}), using command line...")
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
            tk.messagebox.showinfo("Anki Deck Created Successfully!", message)
            root.destroy()
        except Exception:
            # Fall back to console if GUI fails
            pass

    print(f"\n🎉 {message}")

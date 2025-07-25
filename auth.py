#!/usr/bin/env python3

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def selenium_login(driver, email, password, base_host, target_url=None):
    """
    Log into the UCalgary cards system using Selenium and optionally validate target URL
    """
    try:
        # Basic URL validation first
        if not base_host or not base_host.startswith(("http://", "https://")):
            raise RuntimeError(f"Invalid URL format: {base_host}")

        # Check if this is a UCalgary cards URL
        if "cards.ucalgary.ca" not in base_host.lower():
            raise RuntimeError(
                f"Invalid URL: Must be a UCalgary cards URL, got {base_host}"
            )

        login_url = f"{base_host}/login"
        driver.get(login_url)
        time.sleep(2)

        # Check if we can reach the login page and it has the expected elements
        page_source = driver.page_source.lower()
        if "login" not in page_source or "username" not in page_source:
            # Check if we got redirected or hit an error page
            current_url = driver.current_url.lower()
            if (
                "error" in current_url
                or "404" in current_url
                or "not found" in page_source
            ):
                raise RuntimeError(
                    f"Invalid URL: Page not found or error at {base_host}"
                )
            else:
                raise RuntimeError(
                    f"Invalid URL: Cannot reach proper login page at {base_host}"
                )

        # Find and fill login form
        username_field = driver.find_element(By.NAME, "username")
        password_field = driver.find_element(By.NAME, "password")

        username_field.send_keys(email)
        password_field.send_keys(password)
        password_field.send_keys(Keys.RETURN)
        time.sleep(3)

        # Check if login was successful
        if "Logout" not in driver.page_source:
            raise RuntimeError("Login failed – check credentials")

        # If target_url is provided, validate it after successful login
        if target_url:
            print(f"🔍 Validating target URL: {target_url}")
            driver.get(target_url)
            time.sleep(2)

            # Check if the target URL is valid
            current_url = driver.current_url.lower()
            page_source = driver.page_source.lower()

            # Check for error indicators
            if any(
                indicator in current_url
                for indicator in ["error", "404", "forbidden", "unauthorized"]
            ):
                raise RuntimeError(
                    f"Invalid URL: Target URL leads to error page - {target_url}"
                )

            if any(
                indicator in page_source
                for indicator in [
                    "not found",
                    "page not found",
                    "404 not found",
                    "404 error",
                    "access denied",
                    "forbidden",
                    "unauthorized",
                ]
            ):
                raise RuntimeError(
                    f"Invalid URL: Target URL not accessible - {target_url}"
                )

            # Check if we're still on UCalgary cards domain
            if "cards.ucalgary.ca" not in current_url:
                raise RuntimeError(
                    f"Invalid URL: Redirected away from UCalgary cards - {target_url}"
                )

            # Specific validation for UCalgary cards pages
            if "/details/" in target_url:
                # For details pages, just check we're not on an obvious error page
                if any(
                    indicator in page_source
                    for indicator in [
                        "404 not found",
                        "page not found",
                        "access denied",
                    ]
                ):
                    raise RuntimeError(
                        f"Invalid URL: Details page not found or inaccessible - {target_url}"
                    )
                # Details pages are valid if they don't show obvious errors
                print(f"✅ Valid details page: {target_url}")
            elif "/collection/" in target_url:
                # For collection pages, just check we're not on an obvious error page
                if any(
                    indicator in page_source
                    for indicator in [
                        "404 not found",
                        "page not found",
                        "access denied",
                    ]
                ):
                    raise RuntimeError(
                        f"Invalid URL: Collection page not found or inaccessible - {target_url}"
                    )
                # Collection pages are valid if they don't show obvious errors
                print(f"✅ Valid collection page: {target_url}")
            else:
                # For other pages (like just /), check if it's a valid landing page
                target_clean = target_url.rstrip("/")
                base_clean = base_host.rstrip("/")

                if (
                    target_clean == base_clean
                    or target_url.endswith(base_host + "/")
                    or target_url == base_host
                ):
                    # This is just the base URL - not a valid deck/collection URL
                    raise RuntimeError(
                        f"Invalid URL: Base URL is not a valid deck or collection page - {target_url}"
                    )

                # For any other path that's not /details/ or /collection/, validate it's not just a general page
                if not any(
                    path in target_url for path in ["/details/", "/collection/"]
                ):
                    raise RuntimeError(
                        f"Invalid URL: URL must be a valid deck (/details/) or collection (/collection/) page - {target_url}"
                    )

    except Exception as e:
        # Check if it's a URL/network issue vs credentials issue
        error_str = str(e).lower()
        if any(
            keyword in error_str
            for keyword in [
                "invalid url",
                "network",
                "timeout",
                "unreachable",
                "dns",
                "connection",
                "resolve",
                "err_name_not_resolved",
                "page not found",
                "error at",
                "not accessible",
                "appears empty",
                "not a valid deck",
                "leads to error",
            ]
        ):
            raise RuntimeError(f"URL/Network error: {e}")
        else:
            raise RuntimeError("Login failed – check credentials")

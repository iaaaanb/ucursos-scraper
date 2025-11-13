"""
Authentication module for U-Cursos portal.
Handles login and session management using Selenium WebDriver.
"""

import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options


def get_driver(headless=False, download_dir=None):
    """
    Initialize and return a Chromium WebDriver instance.

    Args:
        headless (bool): Run browser in headless mode
        download_dir (str, optional): Directory for file downloads

    Returns:
        WebDriver: Configured Chromium WebDriver instance
    """
    service = Service('/usr/bin/chromedriver')
    options = Options()
    options.binary_location = '/usr/bin/chromium-browser'
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')

    if headless:
        options.add_argument('--headless')

    # Configure download directory and behavior
    if download_dir:
        prefs = {
            'download.default_directory': download_dir,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True
        }
        options.add_experimental_option('prefs', prefs)

    driver = webdriver.Chrome(service=service, options=options)

    # Enable downloads in headless mode
    if headless and download_dir:
        driver.command_executor._commands["send_command"] = (
            "POST",
            '/session/$sessionId/chromium/send_command'
        )
        params = {
            'cmd': 'Page.setDownloadBehavior',
            'params': {'behavior': 'allow', 'downloadPath': download_dir}
        }
        driver.execute("send_command", params)

    return driver


def authenticate(headless=True):
    """
    Authenticate to U-Cursos portal using credentials from environment variables.

    Args:
        headless (bool): Run browser in headless mode

    Returns:
        WebDriver: Authenticated WebDriver instance

    Raises:
        ValueError: If credentials are not set in environment
        TimeoutException: If login fails or times out
    """
    # Get credentials from environment
    username = os.getenv('UCURSOS_USERNAME')
    password = os.getenv('UCURSOS_PASSWORD')
    url = os.getenv('UCURSOS_URL', 'https://www.u-cursos.cl')

    if not username or not password:
        raise ValueError(
            'Credentials not found. Please set UCURSOS_USERNAME and '
            'UCURSOS_PASSWORD in your .env file'
        )

    # Initialize driver
    driver = get_driver(headless=headless)

    try:
        # Navigate to U-Cursos login page
        driver.get(url)

        # Wait for login form to load
        wait = WebDriverWait(driver, 10)

        # 1. Find username field by name attribute
        username_field = wait.until(
            EC.presence_of_element_located((By.NAME, 'username'))
        )
        username_field.clear()
        username_field.send_keys(username)

        # 2. Find password field by name attribute
        password_field = driver.find_element(By.NAME, 'password')
        password_field.clear()
        password_field.send_keys(password)

        # 3. Click login button (submit button with class "boton")
        login_button = driver.find_element(By.CSS_SELECTOR, 'button[type="submit"].boton')
        login_button.click()

        # 4. Wait for successful login - check for course list
        # After login, we should see course elements with id like "curso.XXXXXX"
        try:
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li[id^="curso."]'))
            )
            print(f'✅ Successfully authenticated as: {username}')
        except TimeoutException:
            # If we don't see courses, check if we're still on login page (login failed)
            if 'login' in driver.current_url.lower() or driver.find_elements(By.NAME, 'username'):
                raise ValueError('Login failed - check your credentials')
            # Otherwise assume login was successful but no courses visible
            print(f'✅ Authenticated as: {username} (no courses found)')

        return driver

    except TimeoutException:
        driver.quit()
        raise TimeoutException('Login timeout - check credentials or network connection')

    except Exception as e:
        driver.quit()
        raise Exception(f'Authentication failed: {str(e)}')


def is_authenticated(driver):
    """
    Check if the current session is authenticated.

    Args:
        driver (WebDriver): WebDriver instance to check

    Returns:
        bool: True if authenticated, False otherwise
    """
    try:
        # Check if we can find course elements (only visible when logged in)
        courses = driver.find_elements(By.CSS_SELECTOR, 'li[id^="curso."]')
        # Also check we're not on the login page
        login_form = driver.find_elements(By.NAME, 'username')
        return len(courses) > 0 or len(login_form) == 0
    except NoSuchElementException:
        return False


def logout(driver):
    """
    Log out from U-Cursos portal.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
    """
    # TODO: Implement logout logic
    try:
        # Example: Find and click logout button
        # logout_button = driver.find_element(By.ID, 'logout')
        # logout_button.click()
        pass
    except Exception as e:
        print(f'Logout failed: {str(e)}')
    finally:
        driver.quit()

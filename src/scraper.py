"""
Scraper module for downloading files from U-Cursos.
Organizes downloads by Course/Category/files.pdf structure.
"""

import os
import time
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def sanitize_filename(filename):
    """
    Sanitize filename to remove invalid characters.

    Args:
        filename (str): Original filename

    Returns:
        str: Sanitized filename safe for filesystem
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()


def get_courses(driver):
    """
    Get list of enrolled courses from U-Cursos.

    Args:
        driver (WebDriver): Authenticated WebDriver instance

    Returns:
        list: List of course dictionaries with 'name', 'url', 'code'
    """
    courses = []

    try:
        # Find all course elements (li with id starting with "curso.")
        course_elements = driver.find_elements(By.CSS_SELECTOR, 'li[id^="curso."]')

        for course_elem in course_elements:
            try:
                # Get the main course link (first <a> inside the li)
                course_link = course_elem.find_element(By.CSS_SELECTOR, 'a[href*="/ingenieria/"]')
                course_url = course_link.get_attribute('href')

                # Get course name from the <span> inside <h1>
                course_name_elem = course_elem.find_element(By.CSS_SELECTOR, 'h1 span')
                course_name = course_name_elem.text.strip()

                # Get course code from <h2>
                course_code_elem = course_elem.find_element(By.CSS_SELECTOR, 'h2')
                course_code = course_code_elem.text.strip()

                # Get course ID from the li element's id attribute
                course_id = course_elem.get_attribute('id')

                courses.append({
                    'name': course_name,
                    'code': course_code,
                    'url': course_url,
                    'id': course_id
                })

            except NoSuchElementException as e:
                # Skip courses that don't have the expected structure
                print(f'   ⚠️  Skipping malformed course element: {e}')
                continue

        print(f'✅ Found {len(courses)} course(s)')
        return courses

    except Exception as e:
        print(f'❌ Error getting courses: {str(e)}')
        return []


def get_section_urls(course, sections=None):
    """
    Get URLs for specific sections of a course.

    Args:
        course (dict): Course dictionary with 'url' key
        sections (list, optional): List of section names to scrape.
                                   Defaults to ['calendario', 'material_docente', 'novedades', 'tareas']

    Returns:
        dict: Dictionary mapping section name to URL
    """
    if sections is None:
        sections = ['calendario', 'material_docente', 'novedades', 'tareas']

    base_url = course['url'].rstrip('/')
    section_urls = {}

    for section in sections:
        section_urls[section] = f"{base_url}/{section}/"

    return section_urls


def scrape_calendario(driver, course):
    """
    Scrape calendar events from Calendario section.
    Used for ICS export - extracts Control events (exams/tests) only.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        course (dict): Course dictionary

    Returns:
        list: List of control event dictionaries
    """
    print(f'   📅 Scraping Calendario for {course["code"]}...')

    # Import here to avoid circular imports
    from calendar_export import get_control_events

    # Navigate to calendario section
    calendario_url = course['url'].rstrip('/') + '/calendario/'
    driver.get(calendario_url)
    time.sleep(1)  # Wait for page to load

    # Extract control events
    events = get_control_events(driver, course)

    return events


def scrape_material_docente(driver, course):
    """
    Scrape teaching materials from Material Docente section.
    Extracts all files (PDFs, slides, documents, etc.) posted by instructors.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        course (dict): Course dictionary

    Returns:
        list: List of file dictionaries with 'name', 'url', 'category'
    """
    print(f'   📚 Scraping Material Docente for {course["code"]}...')

    # TODO: Implement material_docente scraping
    # Extract all teaching materials: PDFs, slides, documents, code files, etc.

    return []


def scrape_novedades(driver, course):
    """
    Scrape PDF attachments from Novedades (announcements) section.
    Only extracts PDF files, ignores announcement text.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        course (dict): Course dictionary

    Returns:
        list: List of PDF file dictionaries with 'name', 'url', 'category'
    """
    print(f'   📰 Scraping Novedades (PDFs only) for {course["code"]}...')

    # TODO: Implement novedades PDF scraping
    # Extract only PDF attachments from announcements, ignore text content

    return []


def scrape_tareas(driver, course):
    """
    Scrape attached files from Tareas (assignments) section.
    Only extracts attached files (PDFs, ZIPs, etc.), ignores deadlines.
    Note: Assignment deadlines are scraped from Calendario instead.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        course (dict): Course dictionary

    Returns:
        list: List of file dictionaries with 'name', 'url', 'category'
    """
    print(f'   📝 Scraping Tareas (files only) for {course["code"]}...')

    # TODO: Implement tareas file scraping
    # Extract only attached files (PDFs, ZIPs, etc.)
    # Ignore assignment deadlines (handled by Calendario)

    return []


def scrape_course_sections(driver, course, sections=None):
    """
    Scrape multiple sections for a course.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        course (dict): Course dictionary with course information
        sections (list, optional): List of sections to scrape

    Returns:
        dict: Dictionary with scraped data from each section
    """
    if sections is None:
        sections = ['calendario', 'material_docente', 'novedades', 'tareas']

    results = {
        'calendario': [],
        'material_docente': [],
        'novedades': [],
        'tareas': []
    }

    # Get section URLs
    section_urls = get_section_urls(course, sections)

    # Scrape each section
    for section_name, section_url in section_urls.items():
        try:
            # Navigate to the section
            driver.get(section_url)
            time.sleep(1)  # Wait for page to load

            # Call appropriate scraper function
            if section_name == 'calendario':
                results['calendario'] = scrape_calendario(driver, course)
            elif section_name == 'material_docente':
                results['material_docente'] = scrape_material_docente(driver, course)
            elif section_name == 'novedades':
                results['novedades'] = scrape_novedades(driver, course)
            elif section_name == 'tareas':
                results['tareas'] = scrape_tareas(driver, course)

        except Exception as e:
            print(f'   ⚠️  Error scraping {section_name}: {str(e)}')
            continue

    return results


def get_course_files(driver, course):
    """
    Get list of files for a specific course by scraping multiple sections.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        course (dict): Course dictionary with course information

    Returns:
        list: List of file dictionaries with 'name', 'url', 'category'
    """
    print(f'🔍 Scraping sections for {course["name"]} ({course["code"]})')

    # Scrape all relevant sections
    section_data = scrape_course_sections(driver, course)

    # Combine files from all sections
    all_files = []

    # Add files from Material Docente (teaching materials)
    if section_data['material_docente']:
        all_files.extend(section_data['material_docente'])

    # Add PDFs from Novedades (announcement attachments)
    if section_data['novedades']:
        all_files.extend(section_data['novedades'])

    # Add files from Tareas (assignment attachments)
    if section_data['tareas']:
        all_files.extend(section_data['tareas'])

    print(f'   ✅ Found {len(all_files)} file(s) across all sections')

    return all_files


def download_file(driver, file_info, output_path):
    """
    Download a single file from U-Cursos.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        file_info (dict): File information dictionary
        output_path (Path): Path where file should be saved

    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        # TODO: Implement file download
        # Navigate to file URL and trigger download

        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f'   📄 Downloading: {file_info["name"]} -> {output_path}')

        # Placeholder: simulate download
        # driver.get(file_info['url'])
        # Wait for download to complete
        # time.sleep(2)

        return True

    except Exception as e:
        print(f'   ❌ Failed to download {file_info["name"]}: {str(e)}')
        return False


def download_files(driver, output_dir, course_filter=None):
    """
    Download all files from U-Cursos, organized by Course/Category/files.pdf.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        output_dir (str): Base directory for downloads
        course_filter (str, optional): Only download files from this course

    Returns:
        dict: Statistics about downloaded files
    """
    output_path = Path(output_dir)
    stats = {
        'total_files': 0,
        'downloaded': 0,
        'skipped': 0,
        'failed': 0
    }

    try:
        # Get list of courses
        courses = get_courses(driver)

        # Filter courses if specified
        if course_filter:
            courses = [c for c in courses if course_filter.lower() in c['name'].lower()]

        if not courses:
            print(f'⚠️  No courses found matching filter: {course_filter}')
            return stats

        print(f'\n📚 Found {len(courses)} course(s) to process\n')

        # Process each course
        for course in courses:
            print(f'📖 Processing course: {course["name"]} ({course["code"]})')

            # Get files for this course
            files = get_course_files(driver, course)
            stats['total_files'] += len(files)

            if not files:
                print('   ℹ️  No files found for this course\n')
                continue

            # Download each file
            for file_info in files:
                # Organize: output_dir/Course/Category/file.pdf
                course_name = sanitize_filename(course['name'])
                category = sanitize_filename(file_info.get('category', 'Other'))
                filename = sanitize_filename(file_info['name'])

                file_path = output_path / course_name / category / filename

                # Skip if file already exists
                if file_path.exists():
                    print(f'   ⏭️  Skipping (already exists): {filename}')
                    stats['skipped'] += 1
                    continue

                # Download the file
                success = download_file(driver, file_info, file_path)

                if success:
                    stats['downloaded'] += 1
                else:
                    stats['failed'] += 1

            print()  # Empty line between courses

        # Print summary
        print('─' * 50)
        print(f'📊 Download Summary:')
        print(f'   Total files: {stats["total_files"]}')
        print(f'   Downloaded: {stats["downloaded"]}')
        print(f'   Skipped: {stats["skipped"]}')
        print(f'   Failed: {stats["failed"]}')
        print('─' * 50)

        return stats

    except Exception as e:
        print(f'❌ Error during file download: {str(e)}')
        raise

"""
Scraper module for downloading files from U-Cursos.
Organizes downloads by Course/Category/files.pdf structure.
"""

import os
import sys
import time
import shutil
import glob
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DOWNLOAD_DIR, COURSE_ABBREVIATIONS


def sanitize_filename(filename):
    """
    Sanitize filename to remove invalid characters and replace spaces with dashes.

    Args:
        filename (str): Original filename

    Returns:
        str: Sanitized filename safe for filesystem
    """
    # Replace invalid characters with underscore
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    # Replace spaces with dashes
    filename = filename.replace(' ', '-')

    return filename.strip()


def get_course_folder_name(course, output_dir):
    """
    Get smart folder name for course with priority order:
    1. Use existing abbreviated folder if exists
    2. Use existing full name folder if exists
    3. Create new abbreviated folder (if mapping exists)
    4. Create new full name folder (fallback)

    Args:
        course (dict): Course dictionary with 'name' key
        output_dir (str or Path): Base output directory

    Returns:
        str: Folder name to use (not full path)
    """
    # Defensive coding: validate course is a dictionary
    if not isinstance(course, dict):
        raise TypeError(f"Expected course to be dict, got {type(course).__name__}: {course}")

    if 'name' not in course:
        raise KeyError(f"Course dictionary missing 'name' key. Keys: {list(course.keys())}")

    output_path = Path(output_dir)
    course_name = course['name']

    # Check if course has abbreviation mapping
    abbreviated_name = COURSE_ABBREVIATIONS.get(course_name)

    # Priority 1: Check if abbreviated folder exists
    if abbreviated_name:
        abbrev_folder = output_path / sanitize_filename(abbreviated_name)
        if abbrev_folder.exists():
            print(f'   📁 Found existing course folder: {abbreviated_name}')
            return sanitize_filename(abbreviated_name)

    # Priority 2: Check if full name folder exists
    full_folder = output_path / sanitize_filename(course_name)
    if full_folder.exists():
        print(f'   📁 Found existing course folder: {course_name}')
        return sanitize_filename(course_name)

    # Priority 3: Use abbreviation for new folder (if mapping exists)
    if abbreviated_name:
        print(f'   📁 Creating course folder: {abbreviated_name}')
        return sanitize_filename(abbreviated_name)

    # Priority 4: Use full name for new folder (fallback)
    print(f'   📁 Creating course folder: {course_name}')
    return sanitize_filename(course_name)


def ensure_folders_exist(course, sections, output_dir):
    """
    Create course and section folders if they don't exist.
    Does NOT delete any existing content.

    Args:
        course (dict): Course dictionary with 'name' key
        sections (list): List of section names to create folders for
        output_dir (str or Path): Base output directory

    Returns:
        dict: {'course_folder': Path, 'created': int, 'existing': int}
    """
    # Defensive coding: validate inputs
    if not isinstance(course, dict):
        raise TypeError(f"ensure_folders_exist: Expected course to be dict, got {type(course).__name__}: {course}")

    if not isinstance(sections, list):
        raise TypeError(f"ensure_folders_exist: Expected sections to be list, got {type(sections).__name__}: {sections}")

    output_path = Path(output_dir)

    # Get smart course folder name
    course_folder_name = get_course_folder_name(course, output_dir)
    course_folder = output_path / course_folder_name

    # Create course folder if needed
    if not course_folder.exists():
        course_folder.mkdir(parents=True, exist_ok=True)

    # Track statistics
    created_count = 0
    existing_count = 0

    # Create section subfolders
    for section in sections:
        section_folder = course_folder / sanitize_filename(section)
        if section_folder.exists():
            print(f'      📂 Found existing section: {section}')
            existing_count += 1
        else:
            section_folder.mkdir(parents=True, exist_ok=True)
            print(f'      ✅ Created section: {section}')
            created_count += 1

    return {
        'course_folder': course_folder,
        'created': created_count,
        'existing': existing_count
    }


def get_courses(driver):
    """
    Get list of enrolled courses from U-Cursos.
    Only scrapes courses from the "Primavera 2025" section (div#cursos).
    Ignores "Comunidades" and "Instituciones" sections.

    Args:
        driver (WebDriver): Authenticated WebDriver instance

    Returns:
        list: List of course dictionaries with 'name', 'url', 'code'
    """
    courses = []

    try:
        # Find the "Primavera 2025" section (div#cursos)
        try:
            cursos_section = driver.find_element(By.CSS_SELECTOR, 'div#cursos')
            print(f'✅ Found "Primavera 2025" section (div#cursos)')
        except NoSuchElementException:
            print(f'❌ Could not find div#cursos section')
            return []

        # Find all course elements ONLY within the cursos section
        course_elements = cursos_section.find_elements(By.CSS_SELECTOR, 'li[id^="curso."]')
        print(f'🔍 Found {len(course_elements)} course element(s) in "Primavera 2025" section')

        for idx, course_elem in enumerate(course_elements):
            try:
                # Get the main course link (first <a> tag with title attribute)
                course_link = course_elem.find_element(By.CSS_SELECTOR, 'a[title]')
                course_url = course_link.get_attribute('href')

                # Get course name from the <span> inside <h1>
                course_name_elem = course_elem.find_element(By.CSS_SELECTOR, 'h1 span')
                course_name = course_name_elem.text.strip()

                # Get course code from <h2>
                course_code_elem = course_elem.find_element(By.CSS_SELECTOR, 'h2')
                course_code = course_code_elem.text.strip()

                # Get course ID from the li element's id attribute
                course_id = course_elem.get_attribute('id')

                course_dict = {
                    'name': course_name,
                    'code': course_code,
                    'url': course_url,
                    'id': course_id
                }

                courses.append(course_dict)
                print(f'   ✅ {course_name} ({course_code})')

            except NoSuchElementException as e:
                # Skip courses that don't have the expected structure
                print(f'   ⚠️  Skipping malformed course element {idx + 1}: {e}')
                print(f'      Element HTML: {course_elem.get_attribute("outerHTML")[:300]}')
                continue
            except Exception as e:
                print(f'   ❌ Unexpected error processing course element {idx + 1}: {e}')
                import traceback
                traceback.print_exc()
                continue

        print(f'✅ Successfully parsed {len(courses)} course(s)')
        return courses

    except Exception as e:
        print(f'❌ Error getting courses: {str(e)}')
        import traceback
        traceback.print_exc()
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


def scrape_material_docente(driver, course, output_dir=None):
    """
    Scrape teaching materials from Material Docente section.
    Extracts files organized by separator bar categories.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        course (dict): Course dictionary
        output_dir (str, optional): Output directory for folder creation

    Returns:
        list: List of file dictionaries with 'name', 'url', 'category', 'size'
    """
    # Defensive coding: validate course is a dictionary
    if not isinstance(course, dict):
        raise TypeError(f"scrape_material_docente: Expected course to be dict, got {type(course).__name__}: {course}")

    print(f'   📚 Scraping Material Docente for {course["code"]}...')

    all_files = []
    sections = []

    try:
        # Find the materials table
        table = driver.find_element(By.CSS_SELECTOR, 'table#materiales')

        # Find all tbody elements
        tbody_elements = table.find_elements(By.TAG_NAME, 'tbody')

        current_category = None

        for tbody in tbody_elements:
            # Check if this tbody contains a separator row
            separator_rows = tbody.find_elements(By.CSS_SELECTOR, 'tr.separador[data-categoria]')

            if separator_rows:
                # This is a separator - update current category
                separator = separator_rows[0]
                category_name = separator.get_attribute('data-categoria')

                # If empty or None, use "Otros" as default
                if not category_name or category_name.strip() == "":
                    category_name = "Otros"

                current_category = category_name

                # Add to sections list if not already present
                if category_name not in sections:
                    sections.append(category_name)

                continue

            # This tbody contains files - extract them
            file_rows = tbody.find_elements(By.CSS_SELECTOR, 'tr[data-id]')

            for row in file_rows:
                try:
                    # Extract file ID
                    file_id = row.get_attribute('data-id')

                    # Extract filename from h1 > a
                    filename_elem = row.find_element(By.CSS_SELECTOR, 'td.string h1 a')
                    filename = filename_elem.text.strip()

                    # Extract download URL (bajar link)
                    download_link = row.find_element(By.CSS_SELECTOR, f'a[href*="bajar?id={file_id}"]')
                    download_url = download_link.get_attribute('href')

                    # Extract file size
                    size_elem = row.find_element(By.CSS_SELECTOR, 'td.string h2')
                    file_size = size_elem.text.strip()

                    # Use current category or "Otros" if no category set yet
                    category = current_category if current_category else "Otros"

                    all_files.append({
                        'name': filename,
                        'url': download_url,
                        'category': category,
                        'size': file_size,
                        'id': file_id
                    })

                except NoSuchElementException as e:
                    print(f'      ⚠️  Error parsing file row: {e}')
                    continue

        # Create folders if output_dir provided
        if output_dir and sections:
            stats = ensure_folders_exist(course, sections, output_dir)

            # Print summary
            if stats['created'] > 0 and stats['existing'] > 0:
                print(f'   📁 Created {stats["created"]} new section folder(s), found {stats["existing"]} existing')
            elif stats['created'] > 0:
                print(f'   📁 Created {stats["created"]} new section folder(s)')
            elif stats['existing'] > 0:
                print(f'   📁 Found {stats["existing"]} existing section folder(s)')

        print(f'   ✅ Found {len(all_files)} file(s) in Material Docente')
        return all_files

    except NoSuchElementException:
        print(f'   ⚠️  No materials table found in Material Docente')
        return []
    except Exception as e:
        print(f'   ❌ Error scraping Material Docente: {str(e)}')
        import traceback
        traceback.print_exc()
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


def scrape_course_sections(driver, course, sections=None, output_dir=None):
    """
    Scrape multiple sections for a course.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        course (dict): Course dictionary with course information
        sections (list, optional): List of sections to scrape
        output_dir (str, optional): Output directory for folder creation

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
                results['material_docente'] = scrape_material_docente(driver, course, output_dir)
            elif section_name == 'novedades':
                results['novedades'] = scrape_novedades(driver, course)
            elif section_name == 'tareas':
                results['tareas'] = scrape_tareas(driver, course)

        except Exception as e:
            print(f'   ⚠️  Error scraping {section_name}: {str(e)}')
            continue

    return results


def get_course_files(driver, course, output_dir=None):
    """
    Get list of files for a specific course by scraping multiple sections.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        course (dict): Course dictionary with course information
        output_dir (str, optional): Output directory for folder creation

    Returns:
        list: List of file dictionaries with 'name', 'url', 'category'
    """
    print(f'🔍 Scraping sections for {course["name"]} ({course["code"]})')

    # Scrape all relevant sections
    section_data = scrape_course_sections(driver, course, output_dir=output_dir)

    # Combine files from all sections
    all_files = []

    # Add files from Material Docente (teaching materials)
    # NOTE: material_docente currently only creates folder structure, returns empty list
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


def wait_for_download(download_dir, timeout=30):
    """
    Wait for a file to finish downloading in the specified directory.

    Args:
        download_dir (str or Path): Directory to monitor for downloads
        timeout (int): Maximum time to wait in seconds

    Returns:
        Path: Path to the downloaded file, or None if timeout
    """
    download_path = Path(download_dir)
    seconds = 0

    while seconds < timeout:
        # Look for files that are not partial downloads (.crdownload, .tmp)
        files = list(download_path.glob('*'))
        complete_files = [
            f for f in files
            if f.is_file() and not f.name.endswith(('.crdownload', '.tmp', '.part'))
        ]

        if complete_files:
            # Return the most recently modified file
            latest_file = max(complete_files, key=lambda f: f.stat().st_mtime)
            return latest_file

        time.sleep(0.5)
        seconds += 0.5

    return None


def download_file(driver, file_info, output_path, download_dir):
    """
    Download a single file from U-Cursos.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        file_info (dict): File information dictionary with 'name', 'url', 'size'
        output_path (Path): Path where file should be saved
        download_dir (str or Path): Temporary download directory

    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Get file size for display
        file_size = file_info.get('size', 'unknown size')
        print(f'   ⬇️  Downloading: {file_info["name"]} ({file_size})')

        # Clear download directory before download
        download_path = Path(download_dir)
        for file in download_path.glob('*'):
            try:
                file.unlink()
            except:
                pass

        # Navigate to download URL to trigger download
        driver.get(file_info['url'])

        # Wait for file to appear in download directory
        downloaded_file = wait_for_download(download_dir, timeout=30)

        if not downloaded_file:
            print(f'      ⚠️  Download timeout for {file_info["name"]}')
            return False

        # Move file to final location
        shutil.move(str(downloaded_file), str(output_path))
        print(f'      ✅ Saved to: {output_path.relative_to(output_path.parents[2])}')

        return True

    except Exception as e:
        print(f'   ❌ Failed to download {file_info["name"]}: {str(e)}')
        import traceback
        traceback.print_exc()
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

    # Create temporary download directory
    temp_download_dir = output_path / '.temp_downloads'
    temp_download_dir.mkdir(parents=True, exist_ok=True)

    # Configure Chrome to download to temp directory
    try:
        driver.command_executor._commands["send_command"] = (
            "POST",
            '/session/$sessionId/chromium/send_command'
        )
        params = {
            'cmd': 'Page.setDownloadBehavior',
            'params': {'behavior': 'allow', 'downloadPath': str(temp_download_dir.absolute())}
        }
        driver.execute("send_command", params)
    except Exception as e:
        print(f'⚠️  Could not configure download directory: {e}')
        print(f'   Downloads may go to default browser location')

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

            # Get files for this course (will create folders)
            files = get_course_files(driver, course, output_dir=output_dir)
            stats['total_files'] += len(files)

            if not files:
                print('   ℹ️  No files found for this course\n')
                continue

            # Download each file
            for idx, file_info in enumerate(files):
                try:
                    # Validate file_info is a dictionary
                    if not isinstance(file_info, dict):
                        print(f'   ❌ ERROR: Expected dict but got {type(file_info).__name__}: {file_info}')
                        stats['failed'] += 1
                        continue

                    # Get smart course folder name
                    course_folder_name = get_course_folder_name(course, output_dir)

                    # Organize: output_dir/Course/Category/file.pdf
                    category = sanitize_filename(file_info.get('category', 'Otros'))
                    filename = sanitize_filename(file_info['name'])

                    file_path = output_path / course_folder_name / category / filename

                    # Check if file already exists
                    if file_path.exists():
                        print(f'   ⏭️  Skipped (exists): {filename}')
                        stats['skipped'] += 1
                        continue  # No wait time for skipped files

                    # Download the file
                    success = download_file(driver, file_info, file_path, temp_download_dir)

                    if success:
                        stats['downloaded'] += 1
                        # Wait after successful download to avoid rate limiting
                        time.sleep(2)
                    else:
                        stats['failed'] += 1

                except Exception as e:
                    print(f'   ❌ Error processing file {idx + 1}: {str(e)}')
                    import traceback
                    traceback.print_exc()
                    stats['failed'] += 1
                    continue

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

    finally:
        # Cleanup temporary download directory
        try:
            if temp_download_dir.exists():
                shutil.rmtree(temp_download_dir)
        except Exception as e:
            print(f'⚠️  Could not remove temporary download directory: {e}')

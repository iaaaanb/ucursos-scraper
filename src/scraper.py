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
from datetime import datetime
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


def scrape_novedades_page(driver, post_offset=0):
    """
    Scrape PDF and ZIP attachments from a single page of Novedades posts.
    Helper function for scrape_novedades() that handles one page at a time.

    PDFs are downloaded to folders named after the PDF filename.
    If a ZIP file immediately follows a PDF, it goes in the same folder.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        post_offset (int): Offset for post numbering (for sequential numbering across pages)

    Returns:
        tuple: (files_list, posts_processed_count)
    """
    page_files = []

    try:
        # Find all post elements on current page
        posts = driver.find_elements(By.CSS_SELECTOR, 'div.post.objeto')

        for idx, post in enumerate(posts):
            try:
                # Find all download links (PDFs and ZIPs) in order
                download_links = post.find_elements(By.CSS_SELECTOR, 'a[href]')

                # Filter to only file download links (have data-name or file extension in href)
                file_links = []
                for link in download_links:
                    href = link.get_attribute('href')
                    data_name = link.get_attribute('data-name')
                    class_attr = link.get_attribute('class') or ''

                    if not href:
                        continue

                    # Skip external links (different servers/domains)
                    # Only process internal U-Cursos files (relative URLs or same domain)
                    if href.startswith('http://') or href.startswith('https://'):
                        # External URL - skip it
                        continue

                    # Check if it's a file download link
                    is_pdf = '.pdf' in href.lower() or (data_name and data_name.lower().endswith('.pdf'))
                    is_zip = '.zip' in href.lower() or (data_name and data_name.lower().endswith('.zip'))

                    # Check if PDF uses lightbox (which needs special handling)
                    is_lightbox = 'lightbox' in class_attr

                    if is_pdf or is_zip:
                        file_links.append({
                            'element': link,
                            'href': href,
                            'data_name': data_name,
                            'is_pdf': is_pdf,
                            'is_zip': is_zip,
                            'is_lightbox': is_lightbox
                        })

                # Process file links sequentially
                i = 0
                while i < len(file_links):
                    link_info = file_links[i]

                    if link_info['is_pdf']:
                        # Extract PDF filename from data-name or href
                        pdf_filename = link_info['data_name']
                        if not pdf_filename:
                            # Fallback: extract from href
                            pdf_filename = link_info['href'].split('/')[-1].split('?')[0]

                        # Clean filename: replace spaces with dashes
                        pdf_filename = pdf_filename.replace(' ', '-')

                        # Create folder name from PDF filename (without .pdf extension)
                        folder_name = pdf_filename
                        if folder_name.lower().endswith('.pdf'):
                            folder_name = folder_name[:-4]  # Remove .pdf extension

                        # Sanitize folder name
                        folder_name = sanitize_filename(folder_name)

                        # Add PDF to download list
                        page_files.append({
                            'name': pdf_filename,
                            'url': link_info['href'],
                            'category': 'Cátedras',
                            'subfolder': folder_name,
                            'size': 'unknown',
                            'is_lightbox': link_info.get('is_lightbox', False)
                        })
                        print(f'      📄 Found PDF: {pdf_filename} -> {folder_name}/')

                        # Check if next link is a ZIP (companion file)
                        if i + 1 < len(file_links) and file_links[i + 1]['is_zip']:
                            zip_link = file_links[i + 1]

                            # Extract ZIP filename
                            zip_filename = zip_link['data_name']
                            if not zip_filename:
                                # Fallback: extract from href
                                zip_filename = zip_link['href'].split('/')[-1].split('?')[0]

                            # Clean filename
                            zip_filename = zip_filename.replace(' ', '-')

                            # Add ZIP to same folder as PDF
                            page_files.append({
                                'name': zip_filename,
                                'url': zip_link['href'],
                                'category': 'Cátedras',
                                'subfolder': folder_name,
                                'size': 'unknown'
                            })
                            print(f'      📦 Found ZIP: {zip_filename} -> {folder_name}/')

                            # Skip the ZIP link since we processed it
                            i += 2
                        else:
                            # No ZIP after this PDF, move to next
                            i += 1
                    else:
                        # Standalone ZIP (no PDF before it) - skip or handle differently
                        # For now, skip standalone ZIPs
                        i += 1

            except Exception as e:
                print(f'      ⚠️  Error processing post {post_offset + idx + 1}: {e}')
                import traceback
                traceback.print_exc()
                continue

        return page_files, len(posts)

    except Exception as e:
        print(f'      ⚠️  Error scraping page: {e}')
        import traceback
        traceback.print_exc()
        return page_files, 0


def scrape_novedades(driver, course, output_dir=None):
    """
    Scrape PDF and ZIP attachments from Novedades (announcements) section.
    Creates folder structure: Course/Cátedras/<post_name>/[files]
    Both PDF and ZIP files from the same post go in the same folder.
    Supports pagination - scrapes all pages automatically.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        course (dict): Course dictionary
        output_dir (str, optional): Output directory for folder creation

    Returns:
        list: List of file dictionaries with 'name', 'url', 'category', 'subfolder'
    """
    print(f'   📰 Scraping Novedades (PDFs and ZIPs) for {course["code"]}...')

    all_files = []
    sections = []
    post_offset = 0

    try:
        # Get base URL for novedades section
        base_url = driver.current_url.split('?')[0]  # Remove any existing query params

        # Detect pagination by looking for ul.paginas
        try:
            pagination = driver.find_elements(By.CSS_SELECTOR, 'ul.paginas li a[href*="?p="]')
            page_numbers = []

            for page_link in pagination:
                href = page_link.get_attribute('href')
                if '?p=' in href:
                    # Extract page number from URL
                    try:
                        page_num = int(href.split('?p=')[-1].split('&')[0])
                        if page_num not in page_numbers:
                            page_numbers.append(page_num)
                    except (ValueError, IndexError):
                        continue

            # Add page 0 if not in list (we're already on it)
            if page_numbers and 0 not in page_numbers:
                page_numbers.insert(0, 0)

            # Sort page numbers
            page_numbers.sort()

            if page_numbers:
                print(f'   📄 Found {len(page_numbers)} page(s) of novedades')
            else:
                # No pagination found, just one page
                page_numbers = [0]

        except Exception as e:
            # No pagination or error detecting it - assume single page
            print(f'   📄 Single page of novedades (no pagination detected)')
            page_numbers = [0]

        # Scrape each page
        for page_idx, page_num in enumerate(page_numbers):
            try:
                # Navigate to the page (unless it's page 0 and we're on first iteration)
                if page_idx > 0 or page_num > 0:
                    page_url = f"{base_url}?p={page_num}"
                    print(f'   📖 Scraping page {page_num + 1}/{len(page_numbers)}...')
                    driver.get(page_url)
                    time.sleep(1)  # Wait for page to load
                else:
                    print(f'   📖 Scraping page 1/{len(page_numbers)}...')

                # Scrape posts from current page
                page_files, posts_count = scrape_novedades_page(driver, post_offset)
                all_files.extend(page_files)
                post_offset += posts_count

                if posts_count > 0:
                    print(f'      ✅ Found {len(page_files)} file(s) from {posts_count} post(s) on page {page_num + 1}')
                else:
                    print(f'      ℹ️  No posts found on page {page_num + 1}')

            except Exception as e:
                print(f'      ⚠️  Error scraping page {page_num + 1}: {e}')
                continue

        # Ensure folders are created if output_dir provided
        if output_dir and all_files:
            # Create the main "Cátedras" folder
            if "Cátedras" not in sections:
                sections.append("Cátedras")
                stats = ensure_folders_exist(course, sections, output_dir)

        print(f'   ✅ Found {len(all_files)} file(s) total in Novedades across all pages')
        return all_files

    except NoSuchElementException:
        print(f'   ℹ️  No posts found in Novedades section')
        return []
    except Exception as e:
        print(f'   ❌ Error scraping Novedades: {str(e)}')
        import traceback
        traceback.print_exc()
        return []


def scrape_tareas(driver, course):
    """
    Scrape assignment deadlines from Tareas (assignments) section.
    Extracts deadline information for calendar event creation.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        course (dict): Course dictionary

    Returns:
        list: List of event dictionaries with deadline information
    """
    print(f'   📝 Scraping Tareas deadlines for {course["code"]}...')

    events = []

    try:
        # Find the tareas table
        table = driver.find_element(By.CSS_SELECTOR, 'table')

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

                if not category_name or category_name.strip() == "":
                    category_name = "Tareas"

                current_category = category_name
                continue

            # This tbody contains tarea rows - extract deadline info
            tarea_rows = tbody.find_elements(By.CSS_SELECTOR, 'tr')

            for row in tarea_rows:
                try:
                    # Extract title from h1 > a
                    title_elem = row.find_element(By.CSS_SELECTOR, 'td.string h1 a')
                    title = title_elem.text.strip()
                    url = title_elem.get_attribute('href')

                    # Extract deadline timestamps from h2
                    h2_elem = row.find_element(By.CSS_SELECTOR, 'td.string h2')

                    # Find all timestamp elements
                    time_spans = h2_elem.find_elements(By.CSS_SELECTOR, 'span.tiempo_rel[data-time]')

                    if len(time_spans) < 2:
                        # Need at least start and end timestamps
                        continue

                    # First timestamp is start time, second is main deadline
                    start_timestamp = int(time_spans[0].get_attribute('data-time'))
                    deadline_timestamp = int(time_spans[1].get_attribute('data-time'))

                    # Check for optional late deadline
                    late_deadline_timestamp = None
                    if len(time_spans) >= 3:
                        late_deadline_timestamp = int(time_spans[2].get_attribute('data-time'))

                    # Convert to datetime objects
                    start_time = datetime.fromtimestamp(start_timestamp)
                    deadline_time = datetime.fromtimestamp(deadline_timestamp)

                    # Extract state (Finalizada/En Plazo)
                    try:
                        state_elem = row.find_element(By.CSS_SELECTOR, 'td.string h1')
                        state_text = state_elem.text.strip()
                        is_finished = 'Finalizada' in state_text
                    except:
                        is_finished = False

                    # Extract submission state from pill
                    submission_state = "Pendiente"
                    try:
                        pill = row.find_element(By.CSS_SELECTOR, 'div.pill')
                        pill_text = pill.text.strip()
                        if 'Entregada' in pill_text or '✓' in pill_text:
                            submission_state = "Entregada"
                        elif 'Sin Entrega' in pill_text or '✗' in pill_text:
                            submission_state = "Sin Entrega"
                    except:
                        pass

                    # Create event dictionary for main deadline
                    event = {
                        'title': title,
                        'course': course['code'],
                        'course_name': course['name'],
                        'category': current_category if current_category else "Tareas",
                        'start_time': start_time,
                        'deadline': deadline_time,
                        'late_deadline': datetime.fromtimestamp(late_deadline_timestamp) if late_deadline_timestamp else None,
                        'state': 'Finalizada' if is_finished else 'En Plazo',
                        'submission_state': submission_state,
                        'url': url
                    }

                    events.append(event)
                    print(f'      📅 Found tarea: {title} -> Deadline: {deadline_time.strftime("%Y-%m-%d %H:%M")}')

                except NoSuchElementException:
                    # Skip rows that don't have the expected structure
                    continue
                except Exception as e:
                    print(f'      ⚠️  Error parsing tarea row: {e}')
                    continue

        print(f'   ✅ Found {len(events)} tarea deadline(s)')
        return events

    except NoSuchElementException:
        print(f'   ⚠️  No tareas table found')
        return []
    except Exception as e:
        print(f'   ❌ Error scraping Tareas: {str(e)}')
        import traceback
        traceback.print_exc()
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
                results['novedades'] = scrape_novedades(driver, course, output_dir)
            elif section_name == 'tareas':
                results['tareas'] = scrape_tareas(driver, course)

        except Exception as e:
            print(f'   ⚠️  Error scraping {section_name}: {str(e)}')
            continue

    return results


def get_course_files(driver, course, sections=None, output_dir=None):
    """
    Get list of files for a specific course by scraping multiple sections.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        course (dict): Course dictionary with course information
        sections (list, optional): List of sections to scrape. Defaults to all file sections.
        output_dir (str, optional): Output directory for folder creation

    Returns:
        list: List of file dictionaries with 'name', 'url', 'category'
    """
    # Default to all file sections (exclude calendario as it doesn't have files)
    if sections is None:
        sections = ['material_docente', 'novedades', 'tareas']

    print(f'🔍 Scraping sections for {course["name"]} ({course["code"]})')

    # Scrape specified sections
    section_data = scrape_course_sections(driver, course, sections=sections, output_dir=output_dir)

    # Combine files from all sections
    all_files = []

    # Add files from Material Docente (teaching materials)
    if 'material_docente' in section_data and section_data['material_docente']:
        all_files.extend(section_data['material_docente'])

    # Add PDFs from Novedades (announcement attachments)
    if 'novedades' in section_data and section_data['novedades']:
        all_files.extend(section_data['novedades'])

    # Add files from Tareas (assignment attachments)
    if 'tareas' in section_data and section_data['tareas']:
        all_files.extend(section_data['tareas'])

    print(f'   ✅ Found {len(all_files)} file(s) across selected sections')

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
    Handles lightbox PDFs and external links by using direct HTTP download.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        file_info (dict): File information dictionary with 'name', 'url', 'size', 'is_lightbox'
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

        # Check if this is a lightbox PDF (needs special handling)
        is_lightbox = file_info.get('is_lightbox', False)

        # Check if this is an external URL (different domain)
        file_url = file_info['url']
        is_external = file_url.startswith('http://') or file_url.startswith('https://')

        # For external URLs or lightbox PDFs, use requests library
        if is_lightbox or is_external:
            import requests

            # Get the absolute URL
            if not file_url.startswith('http'):
                # Relative URL - make it absolute
                current_url = driver.current_url
                from urllib.parse import urljoin
                file_url = urljoin(current_url, file_url)

            # For lightbox PDFs (internal U-Cursos), use session cookies
            if is_lightbox and not is_external:
                # Get cookies from Selenium driver
                cookies = driver.get_cookies()
                session = requests.Session()
                for cookie in cookies:
                    session.cookies.set(cookie['name'], cookie['value'])

                # Download the file using requests with authentication
                response = session.get(file_url, stream=True)
            else:
                # For external URLs, no authentication needed
                response = requests.get(file_url, stream=True, timeout=30)

            response.raise_for_status()

            # Write directly to output file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            print(f'      ✅ Saved to: {output_path.relative_to(output_path.parents[2])}')
            return True

        else:
            # For internal non-lightbox files, use regular Selenium download
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


def download_files(driver, output_dir, sections=None, course_filter=None):
    """
    Download files from U-Cursos, organized by Course/Category/files.pdf.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        output_dir (str): Base directory for downloads
        sections (list, optional): List of sections to scrape. Defaults to all file sections.
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
            files = get_course_files(driver, course, sections=sections, output_dir=output_dir)
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

                    # Organize files by category and optional subfolder
                    category = sanitize_filename(file_info.get('category', 'Otros'))
                    filename = sanitize_filename(file_info['name'])

                    # Check if file has a subfolder (for nested organization like Novedades)
                    if 'subfolder' in file_info and file_info['subfolder']:
                        # Structure: output_dir/Course/Category/Subfolder/file.pdf
                        subfolder = sanitize_filename(file_info['subfolder'])
                        file_path = output_path / course_folder_name / category / subfolder / filename
                    else:
                        # Structure: output_dir/Course/Category/file.pdf
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

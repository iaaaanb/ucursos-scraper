"""
Calendar export module for U-Cursos.
Exports Control events (exams/tests) to ICS calendar format.
"""

import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from icalendar import Calendar, Event, Alarm
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import COURSE_ABBREVIATIONS


def get_course_abbreviation(course_name):
    """
    Get abbreviated name for a course, or return full name if not in mapping.

    Args:
        course_name (str): Full course name

    Returns:
        str: Abbreviated course name or full name if not mapped
    """
    return COURSE_ABBREVIATIONS.get(course_name, course_name)


def parse_time_range(time_str):
    """
    Parse time range string like "(13:00 - 16:00)" into start/end times.

    Args:
        time_str (str): Time range string

    Returns:
        tuple: (start_hour, start_minute, end_hour, end_minute) or None if parsing fails
    """
    # Match pattern like "(13:00 - 16:00)"
    match = re.search(r'\((\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\)', time_str)
    if match:
        return (int(match.group(1)), int(match.group(2)),
                int(match.group(3)), int(match.group(4)))
    return None


def get_control_events(driver, course):
    """
    Extract Control events (exams/tests) from a course's Calendario page.
    Only scrapes events under "Control" separator bars, skips "Tareas" completely.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        course (dict): Course dictionary with 'code', 'name', 'url'

    Returns:
        list: List of control event dictionaries
    """
    events = []
    seen_events = set()  # Track (title, timestamp, time_range) to skip duplicates

    try:
        # Find the calendar table
        table = driver.find_element(By.CSS_SELECTOR, 'table.sortable')

        # Find all tbody elements
        tbody_elements = table.find_elements(By.TAG_NAME, 'tbody')

        current_section = None
        for tbody in tbody_elements:
            # Check if this tbody contains a separator row
            separator_rows = tbody.find_elements(By.CSS_SELECTOR, 'tr.separador')
            if separator_rows:
                # Get the section name from the separator
                separator_text = separator_rows[0].find_element(By.TAG_NAME, 'td').text.strip()
                current_section = separator_text
                continue

            # Only process events if we're in the "Control" section
            if current_section != 'Control':
                continue

            # Process event rows in this tbody
            event_rows = tbody.find_elements(By.CSS_SELECTOR, 'tr')
            for row in event_rows:
                try:
                    # Get the event cell
                    event_cell = row.find_element(By.CSS_SELECTOR, 'td.string')

                    # Extract timestamp from rel attribute
                    timestamp_str = event_cell.get_attribute('rel')
                    if not timestamp_str:
                        continue

                    timestamp = int(timestamp_str)
                    event_date = datetime.fromtimestamp(timestamp)

                    # Extract title and URL
                    title_link = event_cell.find_element(By.CSS_SELECTOR, 'h1 a')
                    title = title_link.text.strip()
                    url = title_link.get_attribute('href')

                    # Extract time range from h2
                    h2_elem = event_cell.find_element(By.TAG_NAME, 'h2')
                    h2_text = h2_elem.text

                    # Parse time range
                    time_range = parse_time_range(h2_text)

                    if time_range:
                        start_hour, start_min, end_hour, end_min = time_range

                        # Create start and end datetime objects
                        start_time = event_date.replace(hour=start_hour, minute=start_min, second=0, microsecond=0)
                        end_time = event_date.replace(hour=end_hour, minute=end_min, second=0, microsecond=0)

                        # Calculate duration in minutes
                        duration = int((end_time - start_time).total_seconds() / 60)

                        # Create duplicate detection key
                        dup_key = (title, timestamp, f"{start_hour}:{start_min}-{end_hour}:{end_min}")

                        # Skip if duplicate
                        if dup_key in seen_events:
                            continue

                        seen_events.add(dup_key)

                        # Create event dictionary
                        events.append({
                            'title': title,
                            'course': course['code'],
                            'course_name': course['name'],
                            'start_time': start_time,
                            'end_time': end_time,
                            'duration': duration,
                            'description': f"Duration: {duration} minutes",
                            'url': url
                        })

                except Exception as e:
                    print(f'      ⚠️  Error parsing event row: {str(e)}')
                    continue

        return events

    except Exception as e:
        print(f'   ❌ Error extracting control events: {str(e)}')
        return []


def create_control_event(event_data):
    """
    Create an iCalendar Event for a Control (exam/test).

    Args:
        event_data (dict): Event information with 'title', 'course', 'course_name',
                          'start_time', 'end_time', 'description', 'url'

    Returns:
        Event: iCalendar Event object
    """
    event = Event()

    # Set title with abbreviated course name prefix
    # Use custom abbreviation for readability, falls back to full name if not mapped
    course_abbrev = get_course_abbreviation(event_data['course_name'])
    title = f"[{course_abbrev}] {event_data['title']}"
    event.add('summary', title)

    # Set description
    description = event_data.get('description', '')
    if event_data.get('url'):
        description += f"\n\nURL: {event_data['url']}"
    event.add('description', description)

    # Set start and end times
    event.add('dtstart', event_data['start_time'])
    event.add('dtend', event_data['end_time'])

    # Set categories (using full course name, not abbreviation)
    event.add('categories', ['Controles', event_data['course_name']])

    # Add alarms: 1 day before and 1 hour before
    # Alarm 1 day before
    alarm_1day = Alarm()
    alarm_1day.add('action', 'DISPLAY')
    alarm_1day.add('trigger', timedelta(days=-1))
    alarm_1day.add('description', f'Control tomorrow: {title}')
    event.add_component(alarm_1day)

    # Alarm 1 hour before
    alarm_1hour = Alarm()
    alarm_1hour.add('action', 'DISPLAY')
    alarm_1hour.add('trigger', timedelta(hours=-1))
    alarm_1hour.add('description', f'Control in 1 hour: {title}')
    event.add_component(alarm_1hour)

    # Set UID for the event
    event.add('uid', f"control-{event_data['course']}-{hash(str(event_data))}@ucursos")

    # Add timestamp
    event.add('dtstamp', datetime.now())

    return event


def create_tarea_event(event_data):
    """
    Create an iCalendar Event for a Tarea (assignment) deadline.

    Args:
        event_data (dict): Event information with 'title', 'course', 'course_name',
                          'deadline', 'submission_state', 'url'

    Returns:
        Event: iCalendar Event object
    """
    event = Event()

    # Set title with abbreviated course name prefix and submission state
    course_abbrev = get_course_abbreviation(event_data['course_name'])
    submission_state = event_data.get('submission_state', 'Pendiente')
    title = f"[{course_abbrev}] {event_data['title']}"

    # Add submission status indicator
    if submission_state == 'Entregada':
        title += " ✓"
    elif submission_state == 'Sin Entrega':
        title += " ✗"

    event.add('summary', title)

    # Set description
    description = f"Estado: {event_data.get('state', 'Desconocido')}\n"
    description += f"Entrega: {submission_state}\n"

    if event_data.get('late_deadline'):
        late_deadline_str = event_data['late_deadline'].strftime('%Y-%m-%d %H:%M')
        description += f"Acepta atrasos hasta: {late_deadline_str}\n"

    if event_data.get('url'):
        description += f"\nURL: {event_data['url']}"

    event.add('description', description)

    # Use deadline as both start and end (all-day event)
    deadline = event_data['deadline']
    event.add('dtstart', deadline)
    event.add('dtend', deadline)

    # Set categories
    event.add('categories', ['Tareas', event_data['course_name']])

    # Add alarm: 1 day before deadline
    alarm = Alarm()
    alarm.add('action', 'DISPLAY')
    alarm.add('trigger', timedelta(days=-1))
    alarm.add('description', f'Tarea mañana: {title}')
    event.add_component(alarm)

    # Set UID for the event
    event.add('uid', f"tarea-{event_data['course']}-{hash(str(event_data))}@ucursos")

    # Add timestamp
    event.add('dtstamp', datetime.now())

    return event


def create_tarea_late_event(event_data):
    """
    Create an iCalendar Event for a Tarea's late submission deadline (Atrasos).

    Args:
        event_data (dict): Event information with 'title', 'course', 'course_name',
                          'late_deadline', 'submission_state', 'url'

    Returns:
        Event: iCalendar Event object for late deadline
    """
    event = Event()

    # Set title with abbreviated course name prefix, submission state, and " - Atraso" suffix
    course_abbrev = get_course_abbreviation(event_data['course_name'])
    submission_state = event_data.get('submission_state', 'Pendiente')
    title = f"[{course_abbrev}] {event_data['title']}"

    # Add submission status indicator
    if submission_state == 'Entregada':
        title += " ✓"
    elif submission_state == 'Sin Entrega':
        title += " ✗"

    # Add " - Atraso" suffix
    title += " - Atraso"

    event.add('summary', title)

    # Set description
    description = f"Estado: {event_data.get('state', 'Desconocido')}\n"
    description += f"Entrega: {submission_state}\n"
    description += "Plazo de atrasos\n"

    if event_data.get('url'):
        description += f"\nURL: {event_data['url']}"

    event.add('description', description)

    # Use late_deadline as both start and end
    late_deadline = event_data['late_deadline']
    event.add('dtstart', late_deadline)
    event.add('dtend', late_deadline)

    # Set categories
    event.add('categories', ['Tareas', 'Atrasos', event_data['course_name']])

    # Add alarm: 1 day before late deadline
    alarm = Alarm()
    alarm.add('action', 'DISPLAY')
    alarm.add('trigger', timedelta(days=-1))
    alarm.add('description', f'Plazo de atrasos mañana: {title}')
    event.add_component(alarm)

    # Set UID for the event - different from main event to allow independent updates
    event.add('uid', f"tarea-late-{event_data['course']}-{hash(str(event_data))}@ucursos")

    # Add timestamp
    event.add('dtstamp', datetime.now())

    return event


def export_calendar(driver, courses, output_path):
    """
    Export Control events and Tarea deadlines to ICS file.
    Scrapes calendario and tareas sections for each course.

    Args:
        driver (WebDriver): Authenticated WebDriver instance
        courses (list): List of course dictionaries with 'code', 'name', 'url'
        output_path (str): Path to output ICS file

    Returns:
        dict: Statistics about exported events
    """
    stats = {
        'controles': 0,
        'tareas': 0,
        'total': 0
    }

    # Create calendar
    cal = Calendar()
    cal.add('prodid', '-//U-Cursos Scraper//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('x-wr-calname', 'U-Cursos')
    cal.add('x-wr-timezone', 'America/Santiago')
    cal.add('x-wr-caldesc', 'Control events and Tarea deadlines from U-Cursos')

    try:
        print('📅 Extracting events from all courses...\n')

        all_control_events = []
        all_tarea_events = []

        # Scrape each course
        for course in courses:
            print(f'   📖 Scraping {course["code"]} - {course["name"]}')

            # Extract control events from calendario
            calendario_url = course['url'].rstrip('/') + '/calendario/'
            driver.get(calendario_url)

            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'table.sortable'))
                )
                control_events = get_control_events(driver, course)
                all_control_events.extend(control_events)
                print(f'      ✅ Found {len(control_events)} Control event(s)')
            except:
                print(f'      ⚠️  No calendario table found')

            # Extract tarea deadlines from tareas section
            from scraper import get_tarea_events
            tareas_url = course['url'].rstrip('/') + '/tareas/'
            driver.get(tareas_url)

            import time
            time.sleep(1)  # Wait for page to load

            tarea_events = get_tarea_events(driver, course)
            all_tarea_events.extend(tarea_events)
            print(f'      ✅ Found {len(tarea_events)} Tarea deadline(s)')

        # Add all control events to calendar
        for event_data in all_control_events:
            event = create_control_event(event_data)
            cal.add_component(event)
            stats['controles'] += 1

        # Add all tarea events to calendar
        for event_data in all_tarea_events:
            # Add main deadline event
            event = create_tarea_event(event_data)
            cal.add_component(event)
            stats['tareas'] += 1

            # If late deadline exists, create second event for "Atrasos"
            if event_data.get('late_deadline'):
                late_event = create_tarea_late_event(event_data)
                cal.add_component(late_event)
                stats['tareas'] += 1

        stats['total'] = stats['controles'] + stats['tareas']

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'wb') as f:
            f.write(cal.to_ical())

        print(f'\n✅ Calendar exported successfully!')
        print(f'   Control events: {stats["controles"]}')
        print(f'   Tarea deadlines: {stats["tareas"]}')
        print(f'   Total events: {stats["total"]}')
        print(f'   File: {output_file.absolute()}')

        return stats

    except Exception as e:
        print(f'❌ Error during calendar export: {str(e)}')
        raise

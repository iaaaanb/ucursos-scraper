#!/usr/bin/env python3
"""
U-Cursos Scraper CLI
A command-line tool to scrape and organize content from the U-Cursos university portal.
"""

import os
import sys
from pathlib import Path
import click
from dotenv import load_dotenv

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DOWNLOAD_DIR

# Load environment variables
load_dotenv()


@click.command()
@click.version_option(version='0.1.0')
@click.option('--headless/--no-headless', default=True, help='Run browser in headless mode')
@click.option('--output', '-o', default=f'./{DOWNLOAD_DIR}', help='Output directory path')
@click.option('--course', help='Scrape only this specific course')
@click.option('-c', '--calendario', 'sections', flag_value='calendario', multiple=True, help='Scrape calendario section only')
@click.option('-m', '--material', 'sections', flag_value='material_docente', multiple=True, help='Scrape material docente section only')
@click.option('-n', '--novedades', 'sections', flag_value='novedades', multiple=True, help='Scrape novedades section only')
@click.option('-t', '--tareas', 'sections', flag_value='tareas', multiple=True, help='Scrape tareas section only')
@click.option('--serve-calendar', is_flag=True, help='Start HTTP server to serve calendar file for subscription')
@click.option('--port', default=8000, type=int, help='Port for calendar server (default: 8000)')
@click.option('--host', default='localhost', help='Host for calendar server (default: localhost)')
def cli(headless, output, course, sections, serve_calendar, port, host):
    """
    U-Cursos Scraper - Download files and export calendar events from U-Cursos.

    By default (no flags), scrapes all sections: calendario, material docente, novedades, and tareas.

    Use section flags to scrape specific sections only:
    - -c, --calendario: Scrape calendario and export ICS file
    - -m, --material: Scrape material docente files
    - -n, --novedades: Scrape novedades (announcements) files
    - -t, --tareas: Scrape tareas (assignments) files

    Flags can be combined (e.g., -mt scrapes material docente and tareas only).

    Before running, create a .env file with your credentials:
    - UCURSOS_USERNAME
    - UCURSOS_PASSWORD

    Examples:
        python main.py              # Scrape all sections
        python main.py -m           # Only material docente
        python main.py -mt          # Material docente + tareas
        python main.py -c --course "Programación"  # Only calendario for one course
        python main.py --serve-calendar  # Serve calendar via HTTP for subscription
    """
    # Handle calendar server mode
    if serve_calendar:
        from calendar_server import serve_calendar as start_server
        calendar_path = Path(output) / 'calendar.ics'
        start_server(calendar_path, port=port, host=host)
        return  # Server runs until interrupted

    # Validate environment variables
    if not os.getenv('UCURSOS_USERNAME') or not os.getenv('UCURSOS_PASSWORD'):
        click.echo(click.style(
            '⚠️  Warning: UCURSOS_USERNAME and UCURSOS_PASSWORD not set in .env file',
            fg='yellow'
        ))
        sys.exit(1)

    # Determine which sections to scrape
    sections_list = list(sections) if sections else ['calendario', 'material_docente', 'novedades', 'tareas']

    # Display what we're scraping
    if sections:
        section_names = {
            'calendario': '📅 Calendario',
            'material_docente': '📚 Material Docente',
            'novedades': '📰 Novedades',
            'tareas': '📝 Tareas'
        }
        enabled = [section_names.get(s, s) for s in sections_list]
        click.echo(click.style(f'🔄 Scraping sections: {", ".join(enabled)}', fg='cyan', bold=True))
    else:
        click.echo(click.style('🔄 Scraping all sections (full sync)...', fg='cyan', bold=True))

    if course:
        click.echo(click.style(f'📖 Course filter: {course}', fg='cyan'))

    # Create output directory
    Path(output).mkdir(parents=True, exist_ok=True)

    # Import here to avoid circular imports
    from auth import authenticate
    from scraper import download_files, get_courses
    from calendar_export import export_calendar

    try:
        # Authenticate
        click.echo('📝 Authenticating to U-Cursos...')
        driver = authenticate(headless=headless)

        # Get courses
        click.echo('📚 Fetching courses...')
        courses = get_courses(driver)

        if not courses:
            click.echo(click.style('⚠️  No courses found', fg='yellow'))
            return

        # Filter courses if specified
        if course:
            courses = [c for c in courses if course.lower() in c['name'].lower()]
            if not courses:
                click.echo(click.style(f'⚠️  No courses found matching: {course}', fg='yellow'))
                return

        # Download files from selected sections
        file_sections = [s for s in sections_list if s != 'calendario']
        if file_sections:
            click.echo('📥 Downloading files...')
            download_files(driver, output, sections=file_sections, course_filter=course)

        # Export calendar if calendario section is selected
        if 'calendario' in sections_list:
            click.echo('📅 Exporting calendar...')
            calendar_path = Path(output) / 'calendar.ics'
            export_calendar(driver, courses, str(calendar_path))

        click.echo(click.style('✅ Scraping completed successfully!', fg='green', bold=True))

    except Exception as e:
        click.echo(click.style(f'❌ Error: {str(e)}', fg='red'))
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if 'driver' in locals():
            driver.quit()


if __name__ == '__main__':
    cli()

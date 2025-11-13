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


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """
    U-Cursos Scraper - Download files and export calendar events from U-Cursos.

    Before running, create a .env file with your credentials:
    - UCURSOS_USERNAME
    - UCURSOS_PASSWORD
    """
    # Validate environment variables
    if not os.getenv('UCURSOS_USERNAME') or not os.getenv('UCURSOS_PASSWORD'):
        click.echo(click.style(
            '⚠️  Warning: UCURSOS_USERNAME and UCURSOS_PASSWORD not set in .env file',
            fg='yellow'
        ))


@cli.command()
@click.option('--headless/--no-headless', default=True, help='Run browser in headless mode')
@click.option('--output', '-o', default=f'./{DOWNLOAD_DIR}', help='Download directory path')
def sync(headless, output):
    """
    Sync all content: download files and export calendar.

    This command performs both download and calendar export operations.
    """
    click.echo(click.style('🔄 Starting full sync...', fg='cyan', bold=True))

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

        # Download files
        click.echo('📥 Downloading files...')
        download_files(driver, output)

        # Export calendar
        if courses:
            click.echo('📅 Exporting calendar...')
            calendar_path = Path(output) / 'calendar.ics'
            export_calendar(driver, courses, str(calendar_path))

        click.echo(click.style('✅ Sync completed successfully!', fg='green', bold=True))

    except Exception as e:
        click.echo(click.style(f'❌ Error: {str(e)}', fg='red'))
        sys.exit(1)
    finally:
        if 'driver' in locals():
            driver.quit()


@cli.command()
@click.option('--headless/--no-headless', default=True, help='Run browser in headless mode')
@click.option('--output', '-o', default=f'./{DOWNLOAD_DIR}', help='Download directory path')
@click.option('--course', '-c', help='Download files for specific course only')
def download(headless, output, course):
    """
    Download PDF files organized by Course/Category/files.pdf.

    Files are automatically organized into a clean directory structure.
    """
    click.echo(click.style('📥 Starting file download...', fg='cyan', bold=True))

    # Create output directory
    Path(output).mkdir(parents=True, exist_ok=True)

    # Import here to avoid circular imports
    from auth import authenticate
    from scraper import download_files

    try:
        # Authenticate
        click.echo('📝 Authenticating to U-Cursos...')
        driver = authenticate(headless=headless)

        # Download files
        if course:
            click.echo(f'📥 Downloading files for course: {course}...')
        else:
            click.echo('📥 Downloading all files...')

        download_files(driver, output, course_filter=course)

        click.echo(click.style('✅ Download completed successfully!', fg='green', bold=True))

    except Exception as e:
        click.echo(click.style(f'❌ Error: {str(e)}', fg='red'))
        sys.exit(1)
    finally:
        if 'driver' in locals():
            driver.quit()


@cli.command()
@click.option('--headless/--no-headless', default=True, help='Run browser in headless mode')
@click.option('--output', '-o', default='./calendar.ics', help='Output ICS file path')
def calendar(headless, output):
    """
    Export Control events (exams/tests) to ICS calendar file.

    The generated file can be imported into Google Calendar, Outlook, etc.
    """
    click.echo(click.style('📅 Starting calendar export...', fg='cyan', bold=True))

    # Import here to avoid circular imports
    from auth import authenticate
    from scraper import get_courses
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

        # Export calendar
        click.echo('📅 Exporting Control events...')
        export_calendar(driver, courses, output)

        click.echo(click.style(f'✅ Calendar exported to: {output}', fg='green', bold=True))

    except Exception as e:
        click.echo(click.style(f'❌ Error: {str(e)}', fg='red'))
        sys.exit(1)
    finally:
        if 'driver' in locals():
            driver.quit()


if __name__ == '__main__':
    cli()

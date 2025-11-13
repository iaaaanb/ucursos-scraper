# U-Cursos Scraper

A Python CLI tool to scrape and organize content from the U-Cursos university portal.

## Features

- **Authenticate** to U-Cursos with username/password using Selenium
- **Download PDF files** organized as `Course/Category/files.pdf`
- **Export calendar** with assignments, exams, and lectures to ICS format
- **CLI interface** with multiple commands for different operations
- **Environment-based configuration** for secure credential management

## Project Structure

```
ucursos-scraper/
├── src/
│   ├── main.py              # CLI entry point
│   ├── auth.py              # Authentication logic
│   ├── scraper.py           # File download functionality
│   └── calendar_export.py   # Calendar export to ICS
├── config/                  # Configuration files (optional)
├── downloads/               # Downloaded files (auto-created)
├── .env                     # Your credentials (DO NOT COMMIT)
├── .env.example             # Credentials template
├── .gitignore               # Git ignore rules
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Prerequisites

- Python 3.8 or higher
- Firefox browser installed (default) or Chrome
- U-Cursos account credentials

## Installation

1. **Clone the repository**

```bash
cd ucursos-scraper
```

2. **Create and activate a virtual environment** (recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
UCURSOS_USERNAME=your_username
UCURSOS_PASSWORD=your_password
UCURSOS_URL=https://www.u-cursos.cl
DOWNLOAD_PATH=./downloads
BROWSER=firefox
HEADLESS=true
```

**IMPORTANT:** Never commit your `.env` file to version control!

## Usage

### Run the CLI

All commands are run from the `src/` directory:

```bash
cd src
python main.py [COMMAND] [OPTIONS]
```

Or make it executable:

```bash
chmod +x src/main.py
./src/main.py [COMMAND] [OPTIONS]
```

### Available Commands

#### 1. Full Sync (Download + Calendar)

Performs both file download and calendar export:

```bash
python main.py sync
```

Options:
- `--headless/--no-headless`: Run browser in headless mode (default: headless)
- `--output`, `-o`: Download directory path (default: `./downloads`)

Example:
```bash
python main.py sync --no-headless --output ./my-files
```

#### 2. Download Files Only

Download PDF files organized by course and category:

```bash
python main.py download
```

Options:
- `--headless/--no-headless`: Run browser in headless mode
- `--output`, `-o`: Download directory path
- `--course`, `-c`: Download files for specific course only

Examples:
```bash
# Download all files
python main.py download

# Download files for a specific course
python main.py download --course "Programación"

# Download with custom output directory
python main.py download --output ~/Documents/UCursos
```

#### 3. Export Calendar Only

Export assignments, exams, and lectures to ICS format:

```bash
python main.py calendar
```

Options:
- `--headless/--no-headless`: Run browser in headless mode
- `--output`, `-o`: Output ICS file path (default: `./calendar.ics`)
- `--types`, `-t`: Event types to export (can specify multiple)

Examples:
```bash
# Export all event types
python main.py calendar

# Export only assignments and exams
python main.py calendar --types assignments --types exams

# Custom output file
python main.py calendar --output ~/Documents/ucursos-calendar.ics
```

### Help

Get help for any command:

```bash
python main.py --help
python main.py download --help
python main.py calendar --help
```

## File Organization

Downloaded files are automatically organized in the following structure:

```
downloads/
├── Course Name 1/
│   ├── Lectures/
│   │   ├── Lecture_01.pdf
│   │   └── Lecture_02.pdf
│   ├── Assignments/
│   │   └── Assignment_01.pdf
│   └── Exams/
│       └── Midterm_Study_Guide.pdf
└── Course Name 2/
    └── ...
```

## Calendar Import

The generated `.ics` file can be imported into:

- **Google Calendar**: Settings → Import & Export → Import
- **Apple Calendar**: File → Import
- **Outlook**: File → Open & Export → Import/Export
- **Thunderbird**: Events → Import

## Development

### TODO: Implementation Steps

The following functions need to be implemented with actual U-Cursos selectors:

1. **Authentication** (`src/auth.py`):
   - Inspect U-Cursos login page
   - Implement username/password field selectors
   - Add login button click logic
   - Verify successful authentication

2. **Course Discovery** (`src/scraper.py`):
   - Implement `get_courses()` to scrape enrolled courses
   - Implement `get_course_files()` to find downloadable files
   - Implement `download_file()` to download files

3. **Calendar Scraping** (`src/calendar_export.py`):
   - Implement `get_assignments()` to scrape assignment deadlines
   - Implement `get_exams()` to scrape exam schedules
   - Implement `get_lectures()` to scrape lecture times

### Running in Development Mode

To see browser actions (non-headless):

```bash
python main.py download --no-headless
```

### Testing

Before running on real data:

1. Test authentication with correct credentials
2. Verify file download paths are correct
3. Check calendar export format
4. Ensure environment variables are properly loaded

## Security

- **Never commit credentials** to version control
- `.env` file is in `.gitignore` by default
- Use strong, unique passwords
- Consider using application-specific passwords if available

## Troubleshooting

### Browser driver issues

If you get WebDriver errors:

```bash
pip install --upgrade selenium webdriver-manager
```

### Permission errors

Ensure the download directory is writable:

```bash
chmod 755 downloads/
```

### Authentication failures

1. Verify credentials in `.env` file
2. Check if U-Cursos URL is correct
3. Run with `--no-headless` to see browser actions
4. Check if login page structure has changed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational purposes. Respect U-Cursos terms of service and use responsibly.

## Disclaimer

This tool is not officially affiliated with U-Cursos or Universidad de Chile. Use at your own risk and responsibility.

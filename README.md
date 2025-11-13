# U-Cursos Scraper

A Python CLI tool to scrape and organize content from the U-Cursos university portal.

## Features

- **Authenticate** to U-Cursos with username/password using Selenium
- **Download files** organized by course and category:
  - Material Docente (teaching materials)
  - Novedades (announcements with pagination support)
  - Tareas (assignments - coming soon)
- **Export calendar** with Control events to ICS format
- **Selective scraping** with section-specific flags (-c, -m, -n, -t)
- **Smart folder naming** with course abbreviations
- **Nested folder structure** for announcements (PDF/ZIP files)
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
python main.py [OPTIONS]
```

Or make it executable:

```bash
chmod +x src/main.py
./src/main.py [OPTIONS]
```

### Section Flags

By default, the scraper downloads all sections. Use flags to selectively scrape specific sections:

- `-c, --calendario`: Scrape calendario section and export ICS file
- `-m, --material`: Scrape material docente files
- `-n, --novedades`: Scrape novedades (announcements) files
- `-t, --tareas`: Scrape tareas (assignments) files

**Flags can be combined!** For example, `-mt` scrapes both material docente and tareas.

### Common Options

- `--headless/--no-headless`: Run browser in headless mode (default: headless)
- `--output`, `-o`: Output directory path (default: `./downloads`)
- `--course`: Scrape only a specific course (filters by course name)

### Examples

#### Full Sync (All Sections)
Download all files and export calendar:
```bash
python main.py
```

#### Selective Section Scraping
```bash
# Only material docente
python main.py -m

# Material docente + tareas
python main.py -mt

# Novedades only
python main.py -n

# Calendar only
python main.py -c
```

#### With Course Filter
```bash
# All sections for a specific course
python main.py --course "Programación"

# Only calendar for a specific course
python main.py -c --course "Programación"

# Material docente + novedades for specific course
python main.py -mn --course "Cálculo"
```

#### Custom Output Directory
```bash
# All sections to custom directory
python main.py --output ~/Documents/UCursos

# Only novedades to custom directory
python main.py -n --output ./my-files
```

#### Visible Browser (Non-Headless)
```bash
# Run with visible browser
python main.py --no-headless

# Debug specific section
python main.py -n --no-headless
```

### Help

Get detailed help:

```bash
python main.py --help
```

## File Organization

Downloaded files are automatically organized in the following structure:

```
downloads/
├── Course Name 1/
│   ├── Material Docente/
│   │   ├── Category 1/
│   │   │   ├── Lecture_01.pdf
│   │   │   └── Lecture_02.pdf
│   │   └── Category 2/
│   │       └── Assignment_01.pdf
│   ├── Cátedras/
│   │   ├── unix-exec/
│   │   │   ├── unix-exec.pdf
│   │   │   └── exec.zip
│   │   └── unix-varenv/
│   │       ├── unix-varenv.pdf
│   │       └── setjmp.zip
│   └── Tareas/
│       └── (coming soon)
└── Course Name 2/
    └── ...
```

**Note:** The scraper uses smart folder naming with course abbreviations when available (configured in `config.py`).

## ✅ Implemented Features

### Novedades Section - PDF/ZIP Downloads (Completed)

The Novedades (announcements) section scraper is fully implemented with:

- ✅ Automatic pagination support - scrapes all pages
- ✅ PDF and ZIP file detection from `data-name` attributes
- ✅ Nested folder structure: `downloads/<course>/Cátedras/<pdf_filename>/[files]`
- ✅ Sequential link processing - if ZIP follows PDF, both go in same folder
- ✅ Folders named after PDF filenames (without extension)
- ✅ Proper filename extraction with space-to-dash conversion
- ✅ Robust error handling for malformed posts

**Implementation**: `src/scraper.py:scrape_novedades()` and `scrape_novedades_page()`

## 🚧 Pending Implementation

The following features are planned but not yet implemented:

### Tareas Section - Enhanced Scraping

Currently only basic scraping is implemented. The following enhancements are needed:

- **Category grouping**: Apply same separator bar logic as Material Docente section
- **Deadline tracking**:
  - Extract primary deadline
  - Extract optional "Aceptando atrasos hasta:" (accepting late submissions) deadline
- **State tracking**:
  - Assignment state: `Finalizada` / `En Plazo`
  - Submission state: `entregada` / `sin entrega` / `pendiente`
- **File downloads**: Download attached files from the "descripción" (description) section
- **Desired structure**: `downloads/<course>/<tarea_name>/` for each assignment's files

**Implementation location**: `src/scraper.py:scrape_tareas()`

## Calendar Import

The generated `.ics` file can be imported into:

- **Google Calendar**: Settings → Import & Export → Import
- **Apple Calendar**: File → Import
- **Outlook**: File → Open & Export → Import/Export
- **Thunderbird**: Events → Import

## Development

### Current Implementation Status

✅ **Completed:**
- Authentication system with U-Cursos login
- Course discovery and listing (Primavera 2025 section)
- Material Docente scraping with category support
- Novedades scraping with pagination and nested folders
- Calendar export (Control events to ICS format)
- File download system with smart folder naming
- Selective section scraping with CLI flags

🚧 **In Progress:**
- Tareas (assignments) enhanced scraping

### Running in Development Mode

To see browser actions (non-headless):

```bash
python main.py --no-headless
```

To debug a specific section:

```bash
python main.py -n --no-headless  # Debug novedades only
python main.py -m --no-headless  # Debug material docente only
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

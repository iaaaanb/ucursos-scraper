# U-Cursos Scraper

A Python CLI tool to scrape and organize content from the U-Cursos university portal.

## Features

- **Authenticate** to U-Cursos with username/password using Selenium
- **Download files** organized by course and category:
  - Material Docente (teaching materials)
  - Novedades (announcements with pagination support)
- **Export calendar** with Control events and Tarea deadlines to ICS format
  - Includes main deadlines and late submission deadlines ("Atrasos")
  - Shows submission status (✓ entregada, ✗ sin entrega, pending)
- **Selective scraping** with section-specific flags (-c, -m, -n, -t)
- **Smart folder naming** with course abbreviations
- **Nested folder structure** for announcements (PDF/ZIP files)
- **External link filtering** - automatically skips external PDFs/files
- **Lightbox download handling** - bypasses JavaScript viewers for direct downloads
- **Environment-based configuration** for secure credential management

## Project Structure

```
ucursos-scraper/
├── src/
│   ├── main.py              # CLI entry point
│   ├── auth.py              # Authentication logic
│   ├── scraper.py           # File download functionality
│   └── calendar_export.py   # Calendar export to ICS
├── config.py                # Configuration and course abbreviations
├── downloads/               # Downloaded files (auto-created)
├── .env                     # Your credentials (DO NOT COMMIT)
├── .env.example             # Credentials template
├── .gitignore               # Git ignore rules
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Installation

### Option 1: Install from .deb Package (Recommended)

**For Debian/Ubuntu users**, the easiest way to install ucursito is using the `.deb` package.

#### Prerequisites
- Debian/Ubuntu-based Linux distribution
- Python 3.8 or higher
- Chrome/Chromium browser
- U-Cursos account credentials

#### Install Steps

1. **Download the package**
   ```bash
   # Download from releases or build locally (see "Building from Source" below)
   wget https://github.com/iaaaanb/ucursos-scraper/releases/download/v0.2.0/ucursito_0.2.0_all.deb
   ```

2. **Install the package** (apt handles dependencies automatically)
   ```bash
   sudo apt install ./ucursito_0.2.0_all.deb
   ```

3. **Install browser dependencies** (if not already installed)
   ```bash
   sudo apt install chromium-browser chromium-chromedriver
   # OR for Google Chrome:
   # sudo apt install google-chrome-stable
   ```

4. **Run ucursito**
   ```bash
   ucursito
   ```

   On first run, you'll be prompted to enter your U-Cursos credentials:
   ```
   U-Cursos Username: your_username
   U-Cursos Password: ********
   ```

   Credentials are securely stored in `~/.config/ucursito/credentials` with 600 permissions.

#### What Gets Installed

- **Installation location**: `/opt/ucursito/`
- **Command**: `ucursito` (available system-wide from `/usr/local/bin/`)
- **Credentials**: Stored in `~/.config/ucursito/credentials`
- **Downloads**: Default to `./downloads/` in your current directory

#### Uninstall

```bash
# Remove package
sudo apt remove ucursito

# Remove package + configuration files
sudo apt purge ucursito

# Note: User credentials in ~/.config/ucursito/ are preserved
# To remove them manually:
rm -rf ~/.config/ucursito/
```

### Option 2: Install from Source (Development)

**For developers** or users who want to run from source without installing system-wide.

#### Prerequisites
- Python 3.8 or higher
- Chrome/Chromium browser installed
- ChromeDriver (automatically managed by Selenium)
- U-Cursos account credentials

#### Install Steps

1. **Clone the repository**

```bash
git clone https://github.com/iaaaanb/ucursos-scraper.git
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
BROWSER=chromium
HEADLESS=true
```

**IMPORTANT:** Never commit your `.env` file to version control!

## Usage

### Run the CLI

All commands are run from the project root directory:

```bash
python src/main.py [OPTIONS]
```

Or make it executable:

```bash
chmod +x src/main.py
./src/main.py [OPTIONS]
```

### Section Flags

By default, the scraper syncs all sections. Use flags to selectively scrape specific sections:

- `-c, --calendario`: Export calendario section to ICS file (Control events and Tarea deadlines)
- `-m, --material`: Scrape material docente files
- `-n, --novedades`: Scrape novedades (announcements) files
- `-t, --tareas`: Scrape tareas section (currently exports deadlines to calendar)

**Flags can be combined!** For example:
- `-mt` scrapes both material docente and tareas
- `-mn` scrapes material docente and novedades
- `-ct` exports calendar with both controls and tarea deadlines

### Common Options

- `--headless/--no-headless`: Run browser in headless mode (default: headless)
- `--output`, `-o`: Output directory path (default: `./downloads`)
- `--course`: Scrape only a specific course (filters by course name)
- `--help`: Show help message and available options
- `--version`: Show version information

### Examples

#### Full Sync (All Sections)
Download all files and export calendar:
```bash
python src/main.py
```

#### Selective Section Scraping
```bash
# Only material docente
python src/main.py -m

# Material docente + tareas
python src/main.py -mt

# Novedades only
python src/main.py -n

# Calendar only (exports both Control events and Tarea deadlines)
python src/main.py -c
```

#### With Course Filter
```bash
# All sections for a specific course
python src/main.py --course "Programación"

# Only calendar for a specific course
python src/main.py -c --course "Programación"

# Material docente + novedades for specific course
python src/main.py -mn --course "Cálculo"
```

#### Custom Output Directory
```bash
# All sections to custom directory
python src/main.py --output ~/Documents/UCursos

# Only novedades to custom directory
python src/main.py -n --output ./my-files
```

#### Visible Browser (Non-Headless)
Useful for debugging or seeing what the scraper is doing:
```bash
# Run with visible browser
python src/main.py --no-headless

# Debug specific section
python src/main.py -n --no-headless
```

#### Calendar Server
Serve the calendar via HTTP for live subscription in calendar apps:
```bash
# Start calendar server (default: localhost:8000)
python src/main.py --serve-calendar

# Custom port
python src/main.py --serve-calendar --port 9000

# Allow remote access (⚠️ security warning)
python src/main.py --serve-calendar --host 0.0.0.0
```

Then subscribe in your calendar app using: `http://localhost:8000/calendar.ics`

### Help

Get detailed help:

```bash
python src/main.py --help
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
│   └── Cátedras/              # Novedades files
│       ├── unix-exec/
│       │   ├── unix-exec.pdf
│       │   └── exec.zip
│       └── unix-varenv/
│           ├── unix-varenv.pdf
│           └── setjmp.zip
└── Course Name 2/
    └── ...
```

**Notes:**
- The scraper uses smart folder naming with course abbreviations when available (configured in `config.py`)
- Novedades files are organized in nested folders under `Cátedras/`
- Each announcement's PDF and ZIP files are grouped in a folder named after the PDF filename
- Spaces in filenames are automatically converted to dashes

## Calendar Features

### Calendar Export

The scraper exports calendar events to ICS format including:

**Control Events:**
- Event title: `[Course Abbrev] Control Name`
- Includes date, time, and location
- 1-day-before reminder alarm

**Tarea Deadlines:**
- Event title: `[Course Abbrev] Tarea Name [✓/✗]`
  - ✓ = Entregada (submitted)
  - ✗ = Sin Entrega (not submitted)
  - No symbol = Pendiente (pending)
- Main deadline event
- **Separate "Atraso" event** if late submissions are accepted
  - Title format: `[Course Abbrev] Tarea Name [✓/✗] - Atraso`
  - Uses the late submission deadline timestamp
- Includes state (Finalizada/En Plazo) in description
- 1-day-before reminder alarm

### Calendar Import

The generated `ucursos_calendar.ics` file can be imported into:

- **Google Calendar**: Settings → Import & Export → Import
- **Apple Calendar**: File → Import
- **Outlook**: File → Open & Export → Import/Export
- **Thunderbird**: Events → Import

**Updating Events:** When you re-sync, the calendar file will update existing events (same UIDs), so you can simply re-import to update deadlines, submission status, or newly added late deadlines.

### Calendar Server (Live Subscription)

Instead of manually importing the calendar file, you can subscribe to it via HTTP. The calendar will automatically refresh when you re-run the scraper.

#### Start the Calendar Server

```bash
python src/main.py --serve-calendar
```

This starts an HTTP server at `http://localhost:8000/calendar.ics`

**Custom Port/Host:**
```bash
python src/main.py --serve-calendar --port 9000 --host 0.0.0.0
```

#### Subscribe in Calendar Apps

**Thunderbird:**
1. Right-click on calendar list → New Calendar
2. Choose "On the Network"
3. Enter URL: `http://localhost:8000/calendar.ics`
4. Set a name: "U-Cursos"

**Google Calendar:**
1. Settings → Add calendar → From URL
2. Enter: `http://localhost:8000/calendar.ics`
3. Click "Add calendar"

**Apple Calendar:**
1. File → New Calendar Subscription
2. Enter: `http://localhost:8000/calendar.ics`
3. Set refresh interval (e.g., every hour)

**Benefits:**
- ✅ Automatic refresh - calendar updates when you re-run the scraper
- ✅ No manual re-importing needed
- ✅ Works across all calendar apps
- ✅ Can subscribe from multiple devices

**Notes:**
- Keep the server running in a terminal window
- Run `python src/main.py` to re-sync, calendar apps will auto-refresh
- Use `Ctrl+C` to stop the server
- For remote access, use `--host 0.0.0.0` (⚠️ be aware of security implications)

## Implemented Features

### Material Docente Section ✅
- File downloads with category organization
- Separator bar detection for categories
- Smart filename handling

### Novedades Section ✅
- Automatic pagination support - scrapes all pages
- PDF and ZIP file detection from `data-name` attributes
- Nested folder structure: `downloads/<course>/Cátedras/<pdf_filename>/[files]`
- Sequential link processing - if ZIP follows PDF, both go in same folder
- Folders named after PDF filenames (without extension)
- Proper filename extraction with space-to-dash conversion
- External link filtering (skips http:// and https:// links)
- Lightbox PDF handling (bypasses JavaScript viewers)

### Tareas Section ✅
- Calendar deadline export for main deadlines
- Late submission deadline tracking ("Aceptando atrasos hasta:")
- Separate calendar events for late deadlines (with " - Atraso" suffix)
- Submission state tracking (Entregada ✓ / Sin Entrega ✗ / Pendiente)
- Assignment state tracking (Finalizada / En Plazo)
- Category grouping support

### Calendar Export ✅
- Control events from calendario section
- Tarea deadline events (main + late deadlines)
- ICS format compatible with all major calendar applications
- Unique UIDs for independent event updates
- Submission status indicators in event titles
- Pre-deadline reminder alarms

## Pending Features

The following features are planned but not yet implemented:

### Tareas - File Downloads 🚧
- Download attached files from the "descripción" (description) section of each tarea
- Organize tarea files in `downloads/<course>/Tareas/<tarea_name>/` folders
- Handle multiple file attachments per tarea

## Development

### Running in Development Mode

To see browser actions (non-headless):

```bash
python src/main.py --no-headless
```

To debug a specific section:

```bash
python src/main.py -n --no-headless  # Debug novedades only
python src/main.py -m --no-headless  # Debug material docente only
python src/main.py -t --no-headless  # Debug tareas only
```

### Testing

Before running on real data:

1. Test authentication with correct credentials
2. Verify file download paths are correct
3. Check calendar export format
4. Ensure environment variables are properly loaded
5. Test with `--no-headless` to visually verify scraping behavior

### Building the .deb Package

**For developers** who want to build the Debian package from source.

#### Prerequisites for Building

- Debian/Ubuntu-based Linux distribution
- `dpkg-deb` installed (usually pre-installed)
- All project dependencies installed

#### Build Steps

1. **Clone the repository** (if not already done)
   ```bash
   git clone https://github.com/iaaaanb/ucursos-scraper.git
   cd ucursos-scraper
   ```

2. **Run the build script**
   ```bash
   ./build-deb.sh
   ```

   This script will:
   - Create the `debian/` directory structure
   - Copy all application files to `/opt/ucursito/`
   - Copy DEBIAN control files (control, postinst, prerm)
   - Clean up Python cache files
   - Build the package with `dpkg-deb`
   - Clean up build artifacts

3. **Verify the package**
   ```bash
   # The package is created: ucursito_0.2.0_all.deb
   ls -lh ucursito_0.2.0_all.deb

   # Inspect package contents
   dpkg -c ucursito_0.2.0_all.deb

   # Show package information
   dpkg -I ucursito_0.2.0_all.deb
   ```

4. **Test the package**
   ```bash
   # Install locally
   sudo apt install ./ucursito_0.2.0_all.deb

   # Test the command
   ucursito --help

   # Remove for cleanup
   sudo apt remove ucursito
   ```

#### Build Output

The build script creates:
- `ucursito_0.2.0_all.deb` - The installable Debian package (~26KB)

#### Package Structure

The `.deb` package contains:

```
/opt/ucursito/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── auth.py
│   ├── scraper.py
│   ├── calendar_export.py
│   └── calendar_server.py
├── config.py
├── requirements.txt
├── .env.example
├── README.md
└── ucursito (wrapper script)

/usr/local/bin/ucursito → /opt/ucursito/ucursito (symlink)
```

#### Customizing the Build

To modify the package:

1. **Edit package metadata**: `debian-template/DEBIAN/control`
   - Change version, dependencies, description, etc.

2. **Edit post-installation script**: `debian-template/DEBIAN/postinst`
   - Modify what happens after installation

3. **Edit pre-removal script**: `debian-template/DEBIAN/prerm`
   - Modify cleanup behavior before removal

4. **Edit build script**: `build-deb.sh`
   - Change build process, file locations, etc.

After modifications, run `./build-deb.sh` to rebuild the package.

#### Distribution

Once built, you can distribute the `.deb` file:

```bash
# Upload to GitHub releases
gh release create v0.2.0 ucursito_0.2.0_all.deb

# Or share directly
scp ucursito_0.2.0_all.deb user@server:/path/
```

Users can then install with:
```bash
sudo apt install ./ucursito_0.2.0_all.deb
```

## Security

- **Never commit credentials** to version control
- `.env` file is in `.gitignore` by default
- Use strong, unique passwords
- Consider using application-specific passwords if available
- The scraper only downloads files from authenticated sessions

## Troubleshooting

### Browser driver issues

If you get WebDriver errors:

```bash
pip install --upgrade selenium
```

Make sure Chrome or Chromium is installed:
```bash
# Ubuntu/Debian
sudo apt-get install chromium-browser chromium-chromedriver

# Arch Linux
sudo pacman -S chromium

# macOS
brew install --cask google-chrome
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
5. Ensure you're using your U-Cursos username (not email)

### File download timeouts

If files are timing out:
- External links (starting with `http://` or `https://`) are automatically skipped
- Lightbox PDFs are handled with direct HTTP downloads
- Check your internet connection
- Try running with `--no-headless` to see what's happening

### Calendar not importing

If the ICS file won't import:
1. Check the file was created: `ls downloads/ucursos_calendar.ics`
2. Verify the file isn't empty: `cat downloads/ucursos_calendar.ics`
3. Try opening with a text editor to check for errors
4. Some calendar apps require specific file paths - try moving the file to your desktop

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Implement your changes with clear commit messages
4. Test thoroughly with `--no-headless` mode
5. Update documentation if needed
6. Submit a pull request

## Technical Details

**Web Scraping:**
- Uses Selenium WebDriver for browser automation
- Chrome/Chromium browser with automatic driver management
- Handles both static and dynamic content
- Bypasses JavaScript lightbox viewers for direct downloads

**File Handling:**
- Uses `requests` library for authenticated HTTP downloads
- Selenium session cookies for authenticated file access
- Automatic folder creation and organization
- Filename sanitization (spaces to dashes)

**Calendar Generation:**
- Uses `icalendar` library for ICS format
- Unique UIDs based on course + event hash
- Timezone-aware datetime handling
- Standard alarm components for reminders

## License

This project is for educational purposes. Respect U-Cursos terms of service and use responsibly.

## Disclaimer

This tool is not officially affiliated with U-Cursos or Universidad de Chile. Use at your own risk and responsibility. Always respect the university's terms of service and download policies.

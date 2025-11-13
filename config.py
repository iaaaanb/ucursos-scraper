"""
Global configuration for U-Cursos Scraper.
Centralized location for all configuration settings.
"""

# Course name abbreviations for calendar event titles
# Used to make event titles more readable with personalized short names
# These abbreviations are ONLY used in calendar event titles, not in:
# - File download folder names (keep full course names)
# - Category tags (use full course name)
# - Any other output
# TODO: When Tareas scraping is implemented, use this same mapping for event titles
COURSE_ABBREVIATIONS = {
    "Análisis Avanzado de Algoritmos": "Análisis",
    "Bases de Datos": "Batos",
    "Matemáticas Discretas para la Computación": "Discretas",
    "Metodologías de Diseño y Programación": "Memes",
    "Programación de Software de Sistemas": "PSS",
}


# Default download directory
DOWNLOAD_DIR = "downloads"


# Add other global configuration here in the future
# Examples:
# - Browser settings
# - Timeout values
# - File organization preferences
# - Logging configuration

"""
All initializations and settings. You do not need to change any of these values, unless you are making some changes to the . These are just presets and will be
changed while running the code.
"""
from . import custom_formatter as cf
from pathlib import Path

import logging


# paths
code_dir = Path(__file__).resolve().parent
build_dir = Path(Path.cwd() / "_build")

not_in_slides = ":not_in_slides"
poi = 'point-of-interest::'
note = ".. note::"

# language settings
default_language = "fi"
# for the variable name
language = "language"

# verbose, set true with verbose command line parameter.
verbose = False

# like global variables. Flags for columns and background images.
bg_img = False

# has column width ratios for each slide that has columns and is included in slides. ["5 1 2", "3 1", ...]
column_ratios = []
col_step = 0

# headers and footer visibility
header_visible = True
footer_visible = True

# logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(cf.CustomFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# create console handler with a higher log level
handler.setLevel(logging.DEBUG)

# Configuration file name
config_name = "presentation_config.yaml"
default_css = "presentation.css"

# default values
default_filename = "_build/presentation.rst"
# CSS file was defined in parse_config_file
# default_css is defined in presentation_maker
default_make_pdf = False
default_hovercraft_target_dir = "presentation"
default_overwrite_earlier_versions = True
default_course_rounds = "all"
default_rst2pdf = True
# default_course_path is defined in presentation_maker set_defaults function

# if deck2pdf directory name changes. Change it here too.
deck2pdf_dir_name = "deck2pdf-0.3.0"

pdf_folder = "pdf"

converted_rst_filename = "converted_rst.rst"

# config variable names - these are used in multiple places. If you change some of the variable values here. You must
# also change the corresponding value in the presentation_config.yaml.
presentation_start = "presentation_start"
title = "title"
subtitle = "subtitle"
author = "author"
name = "name"
last = "last"
name = "name"
description = "description"

slide_options = "slide_options"
data_transition_duration = "data-transition-duration"
skip_help = "skip-help"

files = "files"
filename = "filename"
css = "css"
course_path = "course_path"
make_pdf = "make_pdf"
hovercraft_target_dir = "hovercraft_target_dir"
overwrite_earlier_versions = "overwrite_earlier_versions"
course_rounds = "course_rounds"
rst2pdf = "rst2pdf"

header_footer = "header_footer"
header = "header"
header_visible = "header_visible"
footer = "footer"
footer_visible = "footer_visible"

first_slide = "first_slide"
other_slides = "other_slides"
slide_class = "class"

last_slide = "last_slide"
content = "content"



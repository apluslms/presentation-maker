"""
Creates pdf from html slides.
Intended to run in this order:
1. create_with_deck2pdf
2. convert_png_to_pdf

This file and deck2pdf folder needs to be in presentation_maker folder.

"""

import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path

import yaml

from . import presentation_maker as pm
from . import settings


def create_with_deck2pdf(deck2pdf_folder, pres_folder, filename, build_path):
    """
    Creates pdf from index.html (presentation) file.
    """
    current_path = Path.cwd()
    run_deck2pdf = "./deck2pdf"
    path_to_html = str(current_path / pres_folder / 'index.html')

    # output = filename
    output = Path(build_path) / settings.pdf_folder / filename

    if not output.parent.is_dir():
        # if pdf folder does not exist it will be created
        pm.create_dir(output.parent)

    os.chdir("{}/bin".format(deck2pdf_folder))

    style_profile = "--profile=impressjs"
    try:
        command = [run_deck2pdf, style_profile, path_to_html, str(output)]
        subprocess.call(command)
    except Exception as e:
        settings.logger.critical("Error occurred while trying to run deck2pdf. Error message: {}".format(e))


def create_with_rst2pdf(rst2pdf_rst, output_pdf, code_dir):
    # run rst2pdf with parameters
    # rst2pdf -s light.style -b1 converted_rst.rst -o presentation.pdf
    """
    Creates pdf from rst2pdf compatible rst file.
    """

    run_rst2pdf = "rst2pdf"
    font = "freetype-serif"
    # possible fonts
    # serif, freetype-sans, freetype-serif, twelvepoint, tenpoint, eightpoint, kerning

    style_profile = font + "," + str(Path(code_dir) / "light.style")
    # if page breaking fails try using -b1 or -b3 in a command below instead of -b2
    try:
        command = [run_rst2pdf, "-s", style_profile, "-b2", rst2pdf_rst, "-o", output_pdf]
        subprocess.call(command)
    except Exception as e:
        settings.logger.critical("Error occurred while trying to run rst2pdf. Error message: {}".format(e))


def convert_rst_to_rst2pdf_compatible(build_path, rst_file):
    """
    Convert "hovercraft RST" to "rst2pdf RST"

    skip all the rows that follow these guidelines and append all other lines to list.
        0) remove all lines that are before first transition line (----), before first title
        1) remove all lines that start with colon (:)
        2) remove all transition lines (----)

    replace all characters with these patterns:
        3) replace title under lines from (-) to (=)
        4) replace (=) with (#) under the main title

        optional: delete notes from rst, otherwise those notes will be showed in pdf
    """
    filename = settings.converted_rst_filename
    file_to_write = Path(build_path) / filename
    temporary_lines = []    # lines which will be added to file
    first_title_reached = False
    done = False
    note = False
    open(file_to_write, 'w').close()
    with open(rst_file, 'r') as reader, open(file_to_write, 'a') as writer:

        for line in reader.readlines():
            if re.search("^[\s]?[:][a-zA-Z0-9]+.+$", line):
                # searches lines that has (0 or more space and) colon at start, some text after
                # :options: skipped
                pass
            elif re.search("^[-]{4}$", line):
                # searches lines that has exactly four dashes in a line. (transitions) and skip them.
                first_title_reached = True
            elif re.search(settings.note, line):
                # if this is found then skip lines as long as there is something in the beginning of a line
                if note:
                    pass
                else:
                    note = True
                # remove notes from pdf. Could also be saved to another file if wanted.
            elif re.search(settings.newcol, line):
                pass
            else:
                # store this line since it's ok
                if note:
                    if re.search("^([a-zA-Z0-9\S]+)", line):
                        # checks if note has ended. if there is any character in the beginning of the line
                        note = False
                        temporary_lines.append(line)
                    else:
                        # if note has not ended then continue skipping
                        pass
                elif first_title_reached:
                    temporary_lines.append(line)

        # still steps 3 and 4 need to be implemented to temporary lines
        for line in temporary_lines:
            if re.search("^[=]{2,}$", line):
                # this is only needed for the main title. After first round done flag is set to True
                if not done:
                    line = line.replace("=", "#")
                    writer.write(line)
                    done = True
                else:
                    pass
            elif re.search("^[-]{2,}$", line):
                # find lines with two or more dashes and nothing else
                # replacing "-" with "="
                line = line.replace("-", "=")
                writer.write(line)
            else:
                writer.write(line)
    settings.logger.info("RST conversion completed.")
    return file_to_write


def clean_filename(filename):
    """
    Changes file suffix from .rst to .pdf

    :return: new filename for pdf-file.
    """
    filename = filename.replace(".rst", ".pdf")
    filename = Path(filename).name
    return filename


def move_pdf(filename, build_path):
    """
    Moves pdf file to destination location.
    """
    # cwd: something/presentation-maker/presentation_maker/deck2pdf-0.3.0/bin
    cwd = Path.cwd()
    # build_path: something/else/test_course/course-templates/_build
    source = cwd / filename
    pdf_folder = settings.pdf_folder

    destination = build_path / pdf_folder / filename
    if not destination.parent.is_dir():
        settings.logger.info("Creating directory for pdf")
        pm.create_dir(destination.parent)
    if not destination.exists():
        shutil.move(str(source), str(destination))
    else:
        # shutil.copy will overwrite if file exists and if it doesn't it will be moved
        shutil.copy(str(source), str(destination))


def handle_existing_pdf(filename, source, destination):
    """ If pdf file exists then unique name will be created. Only if overwrite is set to false."""
    old = filename
    filename = create_unique_filename(filename, destination)

    settings.logger.info("{} already exists. Creating {}".format(old, filename))
    destination = destination.parent / filename
    shutil.copy(str(source), str(destination))


def create_unique_filename(filename, destination):
    """
    Creates unique filename for pdf to prevent overwrite.
    Names pdf files with suffix _1, _2, ... , _n.

    :return: unique file name.
    """
    try:
        # checks if there are other versions of pdf
        # if there is presentation.pdf it raises ValueError
        # and creates presentation_2.pdf
        num = int(filename[-1])
    except ValueError:
        num = 2
        filename = filename[:-4].split(".pdf")[0] + '_' + str(num) + ".pdf"
    while (destination.parent / filename).exists():
        # if new file exist try again until it does not
        filename = filename[:-5].split(".pdf")[0] + str(num) + ".pdf"
        num += 1
    return filename


def deck2pdf_method(pres_folder, filename, code_dir, build_path):
    # if deck2pdf directory name changes. Change it here too.
    deck2pdf_dir_name = settings.deck2pdf_dir_name
    deck2pdf_path = str(code_dir / deck2pdf_dir_name)
    try:
        settings.logger.info("deck2pdf method selected")
        settings.logger.info("Creating pdf slides...")
        create_with_deck2pdf(deck2pdf_path, pres_folder, filename, build_path)
    except KeyError:
        settings.logger.critical("deck2pdf_dir not set in presentation_config.yaml")
        pm.exiting()


def rst2pdf_method(pdf, rst, code_dir, build_path):
    settings.logger.info("rst2pdf method selected")
    converted_rst = convert_rst_to_rst2pdf_compatible(build_path, rst)
    settings.logger.info("Creating pdf slides...")
    create_with_rst2pdf(converted_rst, pdf, code_dir)


def create(dictionary, rst_file, pres_folder, build_path, code_dir):
    """
    This function is being run as a module from presentation_maker.py.
    Function starts other functions in order to create pdf.
    """
    # changes .rst suffix to .pdf
    pdf_file = clean_filename(rst_file)

    if dictionary.get(settings.files)[settings.make_pdf]:
        # pdf creation set to true
        if dictionary.get(settings.files)[settings.rst2pdf]:
            # rst2pdf selected
            rst2pdf_method(pdf_file, rst_file, code_dir, build_path)
            move_pdf(pdf_file, build_path)
        else:
            # deck2pdf selected
            deck2pdf_method(pres_folder, pdf_file, code_dir, build_path)

            pdf_file = Path(build_path) / settings.pdf_folder / pdf_file

            path = Path.cwd() / pdf_file

            if Path(pdf_file).exists():
                settings.logger.info("{} created".format(pdf_file))
            else:
                settings.logger.warning("PDF file creation failed. Pdf file was not found "
                                        "in the location:\n {}".format(path))
    else:
        settings.logger.info("Skipping pdf creation...\nNote: edit presentation_config.yaml to enable pdf creation")
    pm.print_spacer()


# if this file is being run directly by it's own from terminal. Then do stuff below.

def independent_title():
    pm.print_spacer()
    settings.logger.info("***                Independent PDF creation.                    ***")
    pm.print_spacer()
    settings.logger.info("Creates pdf from HTML presentation file to current working directory.")


def parse_command():
    """
    Argument parsing when create_pdf.py is being run directly from command line.
    For example: python3 create_pdf.py -i <dir for index.html presentation> -o <output pdf file>

    Function gets names of presentation folder and pdf file. Then returns those as tuple.

    :return: (input file, output file)
    """
    parser = argparse.ArgumentParser(description="Creating pdf file from HTML.")
    parser.add_argument("-i", "--input", required=True, help="input as HTML folder which contains index.html")
    parser.add_argument("-o", "--output", required=True, help="name of pdf-file which will be created")
    parser.add_argument("-v", "--verbose", action="store_true")

    arguments = parser.parse_args()

    if arguments.verbose:
        settings.logger.info("Using create_pdf script to create PDF file from HTML file.")
        if arguments.input:
            settings.logger.info("input folder: {}".format(arguments.input))
        if arguments.output:
            settings.logger.info("output file: {}".format(arguments.output))
    else:
        settings.logger.info("Creating presentation with parameters given.")

    files = (arguments.input, arguments.output)
    return files


def independent_create_pdf(arguments):
    """
    This is similar to create function, but this is called when create_pdf.py
    is being run directly from command line with options and arguments.

    This will not be used for the most of the time.
    """
    files = arguments
    presentation_folder = files[0]
    deck2pdf_folder = independent_get_config()
    settings.logger.info("Creating pdf slides...")
    create_with_deck2pdf(deck2pdf_folder, presentation_folder, files[1])
    settings.logger.info("{} created.".format(files[1]))
    move_pdf(files[1], True, True)


def independent_get_config():
    """
    Only used when create_pdf.py is being run directly from cmd-line. Get's deck2pdf folder
    name and returns it.
    """

    config_file = settings.config_name

    with open(config_file) as file:
        docs = yaml.load_all(file, Loader=yaml.FullLoader)
        for d in docs:
            if settings.files in d:
                deck2pdf_folder = d.get(settings.files)['deck2pdf_dir']
    return deck2pdf_folder


if __name__ == "__main__":
    """
    If create_pdf.py is being run directly with arguments then this is true.
    Pdf will be created from presentation HTML file.
    """
    independent_title()
    args = parse_command()
    independent_create_pdf(args)

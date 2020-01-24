"""
Runs Hovercraft and creates html-presentation from hovercraft compatible
RST file. Presentation (index.html) will be in the folder called presentation.

"""

import subprocess
from pathlib import Path

from bs4 import BeautifulSoup as bs

from . import presentation_maker as pm
from . import create_columns as column
from . import settings


def create_unique_folder(current_path):
    """
    Creates unique folder for presentation to prevent overwrite.
    Names presentations with suffix _1, _2, ... , _n.

    :return: unique folder name for presentation.
    """
    name_pattern = 'presentation_{:02d}'
    counter = 0
    while True:
        counter += 1
        presentation_folder = name_pattern.format(counter)
        if not (current_path / presentation_folder).is_dir():
            settings.logger.info("Created folder {} for presentation.".format(presentation_folder))
            return presentation_folder


def get_folder_name(dictionary):
    """
    Gets folder name for presentation. Primarily tries to get name from
    presentation_config.yaml. If there isn't one then create folder
    'presentation', if it already exist then create unique folder.

    :return: folder name for presentation
    """

    try:
        presentation_folder = dictionary.get(settings.files)[settings.hovercraft_target_dir]
        p = Path.cwd()
        if not presentation_folder:
            raise TypeError
        return presentation_folder
    except (TypeError, KeyError):
        # presentation_config.yaml does not have files in it.
        settings.logger.warning(
            "'hovercraft_destination_folder' not set in presentation_config.yaml\nSelecting destination "
            "folder...")
        p = Path.cwd()
        # trying to use name as a default name
        presentation_folder = settings.default_hovercraft_target_dir
        if (p / presentation_folder).is_dir():
            # presentation folder already exists. Select new name to prevent overwrite
            presentation_folder = create_unique_folder(p)
        else:
            # presentation_folder 'presentation' does not exist so use it
            pass

        settings.logger.info("Creating presentation in folder: {}".format(presentation_folder))
        return presentation_folder


def handle_images(pres_dir_path, rst_file):
    """
    Handles all the functions which are needed to copy images (used in presentation) to images directory.
    And also changes image paths in presentation.rst to match new paths.

    :param pres_dir_path:
    :param rst_file:
    :return:
    """
    pres_dir_path = Path(pres_dir_path)
    images_dir_path = pres_dir_path.parent / "images"
    if not images_dir_path.exists():
        settings.logger.info("Images folder does not exist. Creating {}".format(images_dir_path))
        images_dir_path.mkdir(exist_ok=False)
    image_list = find_images(rst_file)
    copy(image_list, images_dir_path)
    change_paths(rst_file)


def copy(image_list, images_dir_path):
    """
    Copies images (which are used in presentation) into images directory.

    :param image_list:
    :param images_dir_path:
    :return:
    """
    settings.logger.info("Starting to copy images...")
    new_paths = []
    for image in image_list:
        image = Path(image).resolve()
        source = image
        destination = images_dir_path / image.name
        new_paths.append(destination)
        pm.copy_file(source, destination)
    settings.logger.info("Images copied to {}".format(images_dir_path))
    return new_paths


def find_images(rst_file):
    """
    Finds images from hovercraft compatible RST file and creates image path list and returns it.

    :param rst_file:
    :return:
    """
    img_list = []
    with open(rst_file, 'r') as reader:
        for line in reader.readlines():
            if ".. image::" in line:
                path = line.split(".. image::")[1].strip()
                img_list.append(path)
            elif ".. figure::" in line:
                path = line.split(".. figure::")[1].strip()
                img_list.append(path)
            elif ":bgimg:" in line:
                path = line.split(":bgimg:")[1].strip()
                img_list.append(path)
    return img_list


def change_paths(rst_file):
    """
    Changes all image paths in RST file to point in the images directory. All images are in images directory. Paths
    will be edited to match following pattern: "../images/image.jpg". All changes will be written to rst file.

    These new paths needs to be in relation to the index.html. So "../images/image.png" is correct way to do this.
    :param rst_file:
    """
    with open(rst_file, 'r') as file:
        # read a list of lines into data
        file = file.readlines()
    index = 0
    for line in file:
        if ".. image::" in line:
            parts = line.split(".. image::")
            old_path = Path(line.split(".. image::")[1].strip())
            relative = str(Path('..') / old_path.parent.name / old_path.name)
            # write ".. image::" back
            # parts[0] for indentation
            new = "{}{}{}\n".format(parts[0], ".. image:: ", relative)
            file[index] = str(new)
        elif ".. figure::" in line:
            parts = line.split(".. figure::")
            old_path = Path(line.split(".. figure::")[1].strip())
            relative = str(Path('..') / old_path.parent.name / old_path.name)
            # write ".. figure::" back
            # parts[0] for indentation
            new = "{}{}{}\n".format(parts[0], ".. figure:: ", relative)
            file[index] = str(new)
        elif ":bgimg:" in line:
            parts = line.split(":bgimg:")
            old_path = Path(line.split(":bgimg:")[1].strip())
            relative = str(Path('..') / old_path.parent.name / old_path.name)
            # no need to write it back ".. figure::" back
            # parts[0] for indentation
            new = "{}{}{}\n".format(parts[0], ":bgimg: ", relative)
            file[index] = str(new)
        index += 1

    # write changed paths to presentation.rst file.
    with open(rst_file, 'w') as writer:
        writer.writelines(file)


def make_columns(filename):
    """
    Creates columns if ::newcol option is used inside of point-of-interest in RST material.
    :param filename:
    :return:
    """
    column.create(filename)


def add_bgimg_to_steps(soup):
    steps = soup.find_all(attrs={'class': 'step', 'bgimg': True})

    for step in steps:
        img = soup.find(attrs={'class': 'step', 'bgimg': True})['bgimg']
        # if you don't want background to repeat add this below: background-repeat: no-repeat;
        style = "background-image: url(" + img + ");"
        # deleting bgimg attribute from step div: bgimg="images/image.jpg"
        # hovercraft creates these tags from options in rst. e.g. :bgimg: images/image.jpg
        del soup.find(attrs={'class': 'step', 'bgimg': True})['bgimg']
        # appending styles to older styles if there are any
        if not step.style:
            step['style'] = style
        else:
            old_style = step.style
            step['style'] = old_style + style


def make_soup(filename):
    with open(str(filename)) as file:
        html = file.read()
        soup = bs(html, 'html.parser')
    return soup


def write_to_file(soup, file):
    with open(str(file), "w") as out_file:
        out_file.write(str(soup.prettify()))


def add_background_images(soup, html_file):
    add_bgimg_to_steps(soup)
    write_to_file(soup, html_file)


def hide_header(soup, html_file):
    """
    Adds style tag to header to make it hidden.
    :param soup:
    :param html_file:
    :return:
    """
    header = soup.find(attrs={'class': 'header'})
    style = "visibility: hidden;"
    if not header.style:
        header['style'] = style

    write_to_file(soup, html_file)


def hide_footer(soup, html_file):
    """
    Adds style tag to header to make it hidden.
    :param soup:
    :param html_file:
    :return:
    """
    footer = soup.find(attrs={'class': 'footer'})
    style = "visibility: hidden;"
    if not footer.style:
        footer['style'] = style
    write_to_file(soup, html_file)


def links_to_new_tabs(soup, html_file):
    """
    RST links open in the same tab. So all the links need to be changed to open in a new tab.
    To make it happen we need to add a target="_blank" attribute to the links (anchor tags).
    :param soup:
    :param html_file:
    :return:
    """
    links = soup.find_all('a')
    if links:
        for l in links:
            if not l.target:
                l['target'] = "_blank"
        write_to_file(soup, html_file)


def run(filename, dictionary, build_dir):
    """
    Runs hovercraft command. Creates presentation in presentation folder.
    """

    try:
        pm.print_spacer()
        settings.logger.info("Running hovercraft to create presentation...\n")
        # with os.system command it is hard to catch errors
        hovercraft_target_dir = get_folder_name(dictionary)
        hovercraft_target_dir = str(Path(build_dir) / hovercraft_target_dir)

        command = ["hovercraft", filename, hovercraft_target_dir]

        # if Path(filename).exists():
        handle_images(hovercraft_target_dir, filename)
        subprocess.run(command, check=True)
        html_file = Path(hovercraft_target_dir) / "index.html"
        if settings.columns:
            make_columns(str(html_file))
        if settings.bg_img:
            soup = make_soup(html_file)
            add_background_images(soup, html_file)
        if not settings.header_visible:
            soup = make_soup(html_file)
            hide_header(soup, html_file)
        if not settings.footer_visible:
            soup = make_soup(html_file)
            hide_footer(soup, html_file)
        links_to_new_tabs(soup, html_file)
        settings.logger.info("Hovercraft presentation created.")
        return hovercraft_target_dir
        # else:
        #     raise FileNotFoundError("{} does not exist.".format(filename))
    except FileNotFoundError as fnf_error:
        settings.logger.critical("\nCritical error occurred while running hovercraft."
                                 "\nFile not found.\nError message: {}".format(fnf_error))
        pm.exiting()

    except OSError as error:
        settings.logger.critical("\nError occurred while running hovercraft.\nError message: {}".format(error))
        pm.exiting()
    except subprocess.CalledProcessError as e:
        settings.logger.critical("\nError occurred while running hovercraft.\nError: {}, \noutput: {} "
                                 "\nPossible cause: Header and/or footer images do not exist or image paths are not "
                                 "correct in presentation_config.yaml".format(e, e.output))
        pm.exiting()
    finally:
        pm.print_spacer()
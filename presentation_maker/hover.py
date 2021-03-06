"""
Runs Hovercraft and creates html-presentation from hovercraft compatible
RST file. Presentation (index.html) will be in the folder called presentation.

"""

import subprocess
import traceback
from pathlib import Path

from bs4 import BeautifulSoup as bs

from . import presentation_maker as pm
from . import create_columns as column
from . import settings

from docutils import nodes
from docutils.parsers.rst import Directive, directives

import hovercraft


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


def handle_images(pres_dir_path, rst_file, image_paths):
    """
    Handles all the functions which are needed to copy images (used in presentation) to images directory.
    And also changes image paths in presentation.rst to match new paths.

    :param image_paths:
    :param pres_dir_path:
    :param rst_file:
    :return:
    """

    pres_dir_path = Path(pres_dir_path)
    images_dir_path = pres_dir_path.parent / "images"
    if not images_dir_path.exists():
        settings.logger.info("Images folder does not exist. Creating {}".format(images_dir_path))
        images_dir_path.mkdir(exist_ok=False)
    # image_list = find_images(rst_file)
    image_list = image_paths
    copy(image_list, images_dir_path)
    # change_paths(rst_file)


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
        if image:
            image = Path(image).resolve()
            source = image
            destination = images_dir_path / image.name
            new_paths.append(destination)
            pm.copy_file(source, destination)
    settings.logger.info("Images copied to {}".format(images_dir_path))
    return new_paths


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


def make_columns(filename):
    """
    Creates columns if ::newcol option is used inside of point-of-interest in RST material.
    :param filename:
    :return:
    """
    column.create(filename)


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


# hovercraft directives. Same directives as in a-plus-rst-tools but done with docutils. In order to make column and
# row directives to work in hovercraft

class Column(Directive):
    option_spec = {settings.column_width: directives.unchanged,
                   settings.column_class: directives.unchanged,
                   }

    final_argument_whitespace = True
    has_content = True

    def run(self):
        if settings.column_width in self.options:
            col_width = str(self.options[settings.column_width])
        else:
            col_width = str(12)
        if settings.column_class in self.options:
            classes = str(self.options[settings.column_class])
        else:
            classes = ""
        column_content = '\n'.join(self.content)
        node = nodes.container(column_content)
        node['classes'] = 'col-sm-' + col_width + ' ' + classes

        self.state.nested_parse(self.content, self.content_offset, node)
        return [node]


class Row(Directive):
    required_arguments = 0

    has_content = True

    def run(self):
        self.assert_has_content()

        row_container = nodes.container()
        row_container['classes'].append('row')

        self.state.nested_parse(self.content, self.content_offset, row_container)

        return [row_container]


def add_bootstrap(soup, filename):
    """
    Adds bootstrap to the hovercraft.
    :param filename:
    :param soup:
    :return:
    """

    settings.logger.info("Adding bootstrap styles to hovercraft.")
    try:
        new_link = soup.new_tag("link")
        new_link.attrs["crossorigin"] = "anonymous"
        new_link.attrs["integrity"] = "sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh"
        new_link.attrs["href"] = "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"
        new_link.attrs["rel"] = "stylesheet"
        soup.head.link.insert_after(new_link)
    except AttributeError as no_head:
        settings.logger.error("Error - Bootstrap link creation failed. Could not find head tag in {}".format(filename))

    write_to_file(soup, filename)


def run(filename, dictionary, build_dir, image_paths):
    settings.logger.info("Bootstrap added successfully.")

    """
    Runs hovercraft command. Creates presentation in presentation folder.
    """

    try:
        settings.logger.info("registering directives...")
        directives.register_directive('row', Row)
        directives.register_directive('column', Column)
        settings.logger.info("Done")

        pm.print_spacer()
        settings.logger.info("Running hovercraft to create presentation...\n")
        hovercraft_target_dir = get_folder_name(dictionary)
        hovercraft_target_dir = str(Path(build_dir) / hovercraft_target_dir)

        command = ["--skip-help", filename, hovercraft_target_dir]

        handle_images(hovercraft_target_dir, filename, image_paths)
        hovercraft.main(command)
        html_file = Path(hovercraft_target_dir) / "index.html"
        if settings.columns:
            make_columns(str(html_file))
        soup = make_soup(html_file)
        add_bootstrap(soup, html_file)
        if settings.bg_img:
            add_background_images(soup, html_file)
        if not settings.header_visible:
            hide_header(soup, html_file)
        if not settings.footer_visible:
            hide_footer(soup, html_file)
        links_to_new_tabs(soup, html_file)
        settings.logger.info("Hovercraft presentation created.")
        return hovercraft_target_dir
    except FileNotFoundError as fnf_error:
        settings.logger.critical("\nCritical error occurred while running hovercraft."
                                 "\nFile not found.\nError message: {}".format(fnf_error))
        tb = traceback.format_exc()
        settings.logger.warning(tb)
        pm.exiting()

    except OSError as error:
        settings.logger.critical("\nError occurred while running hovercraft.\nError message: {}".format(error))
        tb = traceback.format_exc()
        settings.logger.warning(tb)
        pm.exiting()
    except subprocess.CalledProcessError as e:
        settings.logger.critical("\nError occurred while running hovercraft.\nError: {}, \noutput: {} "
                                 "\nPossible cause: Header and/or footer images do not exist or image paths are not "
                                 "correct in presentation_config.yaml".format(e, e.output))
        tb = traceback.format_exc()
        settings.logger.warning(tb)
        pm.exiting()
    finally:
        pm.print_spacer()

#!/usr/bin/python3

"""
    This is script makes hovercraft compatible RST-file from RST-file
    using configuration file (presentation.config.yaml). Hovercraft
    can use this created RST-file to create presentation.
"""

import argparse
import pathlib
import re
import sys
from shutil import copyfile
from pathlib import Path

import yaml

from . import pathfinder
from . import create_pdf
from . import hover
from . import settings


def write_ending(file_to_write, ending, last_slide_content):
    # make these settings from config
    """
    Writes ending to a rst-file.
    Ending contains last slide and transitions to it.
    Basically anything that is in last_slide in presentation_config.yaml.
    """
    with open(file_to_write, 'a') as writer:
        writer.writelines(ending)
        writer.writelines(last_slide_content)


def exiting():
    settings.logger.info("Fix errors and try again. Exiting...")
    sys.exit(2)


def get_title_from_options(line):
    """
    Gets title from poi if someone uses old way of defining poi.
    (This is old way)
    Get header from POI :title: option. There is another function
    (get_title_without_options) when title option is not available.

    .. point-of-interest:: 0
        :title: Example Title
        :next: 1

    :return: Array of heading text and header underline.
    """
    # Assumes that the line parameter is in this form "title: Test title"
    title = line.split(":")[2].lstrip()
    title_underline = "-" * len(title) + "\n\n"

    return [title, title_underline]


def get_title_without_options(line):
    """
    Gets headers from POI. This function is used when there are no :title:
    option available. (This is new)

    This is the POI format in this case.

    .. point-of-interest:: Example Title
        :id: 0
        :next: 1
        :class: borderless

    :return: Array of heading text and header underline.
    """
    try:
        title = "\n" + line.split(settings.poi)[1].lstrip()
        title_underline = "-" * len(title) + "\n\n"

        return [title, title_underline]
    except IndexError:
        # IndexError occurs so
        # it has :title: option in POI. Title has been set the old way
        # ignoring and returning empty list.
        # returned array will be overwritten later by get_title_from_options
        return [""]


def create_first_slide(dictionary):
    """
    Get title, subtitle and append to list for later use.

    :return: List of title and subtitle
    """
    # initializing list with zeroes
    # [title, underline, subtitle]
    first_slide = [0, 0, 0]
    try:
        title = dictionary.get(settings.presentation_start)[settings.title]
        first_slide[0] = title + "\n"
        first_slide[1] = "=" * len(title) + "\n\n"
        subtitle = dictionary.get(settings.presentation_start)[settings.subtitle]
        first_slide[2] = subtitle + "\n"
    except KeyError as e:
        settings.logger.critical("Title and/or subtitle missing from presentation_config.yaml. Message: {}".format(e))
        exiting()
    return first_slide


def depth_of_indentation(line, spaces):
    """
    Calculates how many spaces is in the indentation.
    :param line:
    :param spaces:
    :return:
    """
    if spaces == 0:
        for char in line:
            if char.isspace():
                spaces += 1
            else:
                return spaces
    else:
        return spaces


def write_poi(file_to_read, file_to_write, transition, first_slide, image_paths, other_transitions,
              raw_dict, step_num):
    """
    This is just for extracting point-of-interest from rst-files.
    It will get images too if there are any inside the POI.

    Needs some cleaning and more functions since now it is kind of a mess.
    """
    extract = settings.poi
    # flag when POI starts
    start = False
    # for counting spaces in indentation
    spaces = 0
    # title_option flag separates new version of POI from old one.
    # Since old version uses title_option and new POI does not.
    title_option = False
    # see if title is already written to rst, so it does not write it multiple times
    title_written = False
    # flag to see if current POI is wanted in slides
    in_slides = True
    # not_in_slides is defined in point_of_interest.py directive in a-plus-rst-tools
    # if 'not_in_slides' flag is changed in that file, it should be changed here as well.
    not_in_slides = settings.not_in_slides
    # directives which are handled differently while writing
    directive = ['.. image::', '.. figure::', '.. youtube::', '.. local-video::']

    # columns in slides.
    newcol = settings.newcol

    # exceptions handled for these files in write_rst function

    with open(file_to_read, 'r') as reader, open(file_to_write, 'a') as writer:

        def write_transition(file_writer, transitions):
            for k, v in transitions.items():
                file_writer.write("\n:{}: {}".format(k, v))
            file_writer.write("\n\n")

        def transition_line(file_writer):
            file_writer.write("\n----\n\n")

        for line in reader.readlines():
            if start:
                if first_slide:
                    # if it is first slide then write transition line and transitions
                    # and cover slide which contains title and subtitle
                    transition_line(writer)
                    # write transitions
                    write_transition(writer, transition)
                    first_slide = False
                    writer.write("\n")
                    writer.writelines(create_first_slide(raw_dict))
                    transition_line(writer)
                # regex below searches lines that starts with a (1 or more) whitespaces and
                # after that ":"
                if re.search("^(\s+:)", line):
                    # inside poi, in options
                    # from here count how many spaces are in the indentation
                    # later that amount is used to remove extra whitespaces
                    # to indent correctly in presentation.rst
                    spaces = depth_of_indentation(line, spaces)
                    if not_in_slides in line:
                        # If poi has this option, then exclude from presentation
                        in_slides = False
                    else:
                        if ":title:" in line:
                            # if there are title option then it will be used
                            # to provide header to the slide
                            title_option = True
                            title = get_title_from_options(line)
                        if ":columns:" in line:
                            settings.column_ratios.append(line.split(":columns:")[1].lstrip().rstrip())
                        if newcol in line:
                            settings.columns = True
                            # keep ::newcol in rst. Later it is easier to know how columns are set
                            writer.write("\n::newcol\n")
                        if ":bgimg:" in line:
                            # if poi has background image in it. We need to keep it in rst. It will be used later.
                            image = line.split(":bgimg:")[1].lstrip().rstrip()
                            writer.write("\n:bgimg: {}".format(image))
                            settings.bg_img = True

                elif re.search("^([a-zA-Z0-9\S]+)", line):
                    # if the line starts with numbers or characters
                    # means poi has ended
                    # regex searches for lines that start normally without indentation
                    # means: poi has ended
                    start = False
                    title_written = False
                    # ends slide
                    # if option :not_in_slides: is activated then do not write
                    # transition. Otherwise it will print double transition and
                    # blank slide will appear
                    if in_slides:
                        transition_line(writer)
                    else:
                        pass
                elif in_slides:
                    spaces = depth_of_indentation(line, spaces)
                    if not title_written:
                        write_transition(writer, other_transitions)
                        writer.writelines(title)
                        title_written = True
                        writer.write(line[spaces:])
                        # if directives specified in the directive list are in line
                        # those will be written to the file
                        # gets the spaces in case if user has not set any options in poi
                    if directive[0] in line:
                        newline = find_image_path(image_paths, line.split(directive[0])[1])
                        writer.write(directive[0] + " " + str(newline) + "\n")
                    elif directive[1] in line:
                        # strips .. figure from the line so path remains
                        newline = find_image_path(image_paths, line.split(directive[1])[1])
                        writer.write(directive[1] + " " + str(newline) + "\n")
                    elif directive[2] in line:
                        # Handling youtube video
                        # line looks like this: .. youtube:: Yw6u6YkTgQ4
                        video_id = line.split(directive[2])[1].rstrip().lstrip()
                        writer.write(".. raw:: html\n\n")
                        writer.write('  <iframe width="800" height="600" src="https://www.youtube.com/embed/' + video_id + '" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>\n')
                    elif directive[3] in line:
                        # Handling local-video directive
                        video_name = line.split(directive[3])[1].rstrip().lstrip()
                        writer.write(".. raw:: html\n\n")
                        writer.write('  <video width="65%" controls><source src="../../_static/videot/' + video_name + '.mp4" type="video/mp4">Your browser does not support the video element.</video>')
                    else:
                        # empty lines need to be written
                        # otherwise some important empty lines will be deleted
                        if re.search("^\s*$", line):
                            writer.write(line)
                        else:
                            writer.write(line[spaces:])
            if extract in line:
                # if POI then start extract
                # keeping count of the slides (steps)
                step_num += 1
                start = True
                in_slides = True

                if not title_option:
                    # if there is title option this variable will be overwritten by that option value
                    title = get_title_without_options(line)
                else:
                    settings.logger.warning("POI titled: {} has two titles. Please remove other one."
                                            .format(title[0].rstrip()))

                settings.logger.info("\nextracting '{}' from {}".format(title[0].rstrip().lstrip(), file_to_read))

        if start:
            # if file has ended unexpectedly, write transition
            transition_line(writer)
    return first_slide


def find_image_path(image_paths, line):
    """
    Find working image path to a given image from image_paths list.
    Works if you have correct image name in the path and image exists.
    image_paths has paths which are gathered from file system.

    :return: path to the image if it is found.
    """
    # very simple url validation
    url = ("http://", "https://")
    is_url = False

    for u in url:
        if u in line:
            is_url = True

    if is_url:
        # If image path is URL return as it is. Since it will work.
        settings.logger.info("Image URL {} found.".format(line.rstrip()))
        return line
    else:
        # image_path is from rst file, which user has typed. May have errors.
        image_path = pathlib.Path(line)
        # image_name is from rst file, which user has typed. May have errors.
        image_name = pathlib.Path(line).name

        for p in image_paths:
            suffix = pathlib.Path(p).suffix
            if p.name == image_name:
                new_path = p
                settings.logger.info("Image {} found.".format(new_path))
                return new_path
            elif p.name == str(image_path.with_suffix(suffix.upper()).name):
                new_path = p
                settings.logger.info("Image {} found.".format(new_path))
                return new_path
            elif p.name == str(image_path.with_suffix(suffix.lower()).name):
                new_path = p
                settings.logger.info("Image {} found.".format(new_path))
                return new_path
            else:
                pass

        print_spacer()
        settings.logger.error("Image {} was not found. \nMake sure it exist and it is named the same way as the "
                              "rst-file.".format(str(image_path).rstrip()))
        print_spacer()
        exiting()


def create_img_path_list(course_path):
    """
    Creates image list (.png) from all the images in folders from ../ to sub directories
    recursively. If you need to go deeper change cwd_parent to Path.cwd().parent.parent
    keep in mind that if you go too deep, presentation creation time will increase.

    :return: Image list which contains all the images which have defined image format.
    """
    # finding all images with suffixes in img_format list. Creating list from output.
    # If you need support for another types of image files. Insert suffix in the list.

    img_formats = [".png", ".jpg", ".jpeg", ".gif", ".PNG", ".JPG", ".JPEG", ".GIF"]
    # creating image list
    image_paths = []
    for f in img_formats:
        for filepath in Path(course_path).glob('**/*' + f):
            if "build" in str(filepath):
                pass
            else:
                image_paths.append(filepath)
    return image_paths


def handle_css(build_path, code_dir, user_given_css):
    """
    Copies presentation.css file to presentation directory and creates new path to it.
    If someone copies presentation to external location such as USB stick it should work there also.

    Hovercraft copies all external files into the presentation folder that uses relative paths. CSS will be copied to
    _build/css new_css_path will be set to 'css/presentation.css' which will be used in (hovercraft) RST file. (
    relative path so hovercraft will copy this file to presentation folder and keeps relative path.) if absolute path
    is used hovercraft will not copy external files.

    :param user_given_css: path or None
    :param build_path:
    :param code_dir:
    :return: relative_css_path
    """
    css = Path("css")
    if user_given_css:
        css_file = Path(user_given_css).name
        settings.logger.info("User given {} found.".format(css_file))
        old_css_path = user_given_css
    else:
        # css_file default value is 'presentation.css'
        css_file = Path(settings.default_css)
        old_css_path = code_dir / css_file

    new_css_path = build_path / css / css_file

    # moving css file to course/_build directory
    if old_css_path == new_css_path:
        pass
    else:
        try:
            copy_file(old_css_path, new_css_path)
        except Exception as e:
            settings.logger.error("Error occurred during copying CSS file.\nError: {}".format(e))
    # since css was copied to css folder we can create relative path to it. Which will be used in html presentation

    relative_css_path = css / css_file

    return relative_css_path


def copy_file(source, target):
    """
    Copy file function.
    :param source:
    :param target:
    :return:
    """

    if target.exists() and source.lstat().st_mtime <= target.lstat().st_mtime:
        # if file has not changed then skip.
        pass
    else:
        if not source == target:
            settings.logger.info("Copying {} to {}".format(source, target))
            if not target.parent.is_dir():
                target.parent.mkdir(parents=True)
                copyfile(str(source), str(target))
            else:
                copyfile(str(source), str(target))


def parse_config_file(code_dir, config_name, build_dir, config_path_as_param):
    """
    Parse config file and return list of parameters.

    :returns: a list of parameters from presentation_config.yaml formatted as rst. :name: param
    """

    try:
        if config_path_as_param:
            if Path(config_path_as_param).parent == Path('.'):
                # config_path_as_param is just a file and probably needs to find it from code_dir
                config_file = (code_dir / config_path_as_param).resolve()
            else:
                # user given path to config
                config_file = Path(config_path_as_param).resolve()
        else:
            # if no config given by parameters then use default configuration file
            config_file = (code_dir / config_name).resolve()
        if not config_file.exists():
            raise FileNotFoundError
    except FileNotFoundError as fnf:
        settings.logger.error("trying to open config from: {}".format(str(config_file)))
        settings.logger.error("Configuration file was not found. Make sure that path to the configuration file is "
                              "correct.")
        settings.logger.error("error message: {}".format(fnf))
        exiting()

    with open(str(config_file)) as file:
        doc = yaml.load(file, Loader=yaml.Loader)
        params_dict = []
        params = []
        ending = []
        last_slide_content = []
        config = doc

        for k, v in doc.items():
            if k == settings.presentation_start:
                try:
                    for keys, values in v.items():
                        params.append(":{}: {}\n".format(keys, values))
                except KeyError as e:
                    settings.logger.error("Missing keys in presentation_start. Error message: {}".format(e))
                    exiting()
            if k == settings.files:
                if config.get(settings.files) and config[settings.files].get(settings.css):
                    css_path = Path(config[settings.files].get(settings.css))
                    css_path = str(handle_css(build_dir, code_dir, css_path))
                    params.append(":{}: {}\n".format("css", css_path))
                else:
                    # if css is not set. It will be set up in set_defaults function
                    css_path = str(handle_css(build_dir, code_dir, None))
                    params.append(":{}: {}\n".format("css", css_path))

            if k == 'slide_options':
                try:
                    for keys, values in v.items():
                        params.append(":{}: {}\n".format(keys, values))
                except KeyError:
                    settings.logger.error("{} missing from slide_options in {}.".format(keys, Path(config_file).name))
                    exiting()

                params_dict.append(v)

            if k == settings.header_footer:
                if not doc[settings.header_footer].get(settings.header):
                    config[settings.header_footer][settings.header] = " "
                if not doc[settings.header_footer].get(settings.footer):
                    config[settings.header_footer][settings.footer] = " "
                params.append("\n{}\n\n".format(".. header::"))
                params.append("\n{}\n\n".format("      " + doc.get(settings.header_footer).get(settings.header)))
                params.append("\n{}\n\n".format(".. footer::"))
                params.append("\n{}\n\n".format("      " + doc.get(settings.header_footer).get(settings.footer)))

                if not doc[settings.header_footer].get(settings.header_visible):
                    # make header disappear
                    settings.header_visible = False
                if not doc[settings.header_footer].get(settings.footer_visible):
                    # make footer disappear
                    settings.footer_visible = False
            elif k == settings.first_slide:
                # getting transitions for easier access
                transition = v
            elif k == settings.other_slides:
                other_transitions = v
            else:
                if k == settings.last_slide:
                    # does not append ending to the params, makes it
                    # easier to get later when writing ending
                    if settings.content in v:
                        last_slide_content = doc.get(settings.last_slide)[settings.content]
                    if settings.slide_class in v:
                        ending.append(":{}: {}\n".format("class", doc.get(settings.last_slide)[settings.slide_class]))
        config = set_defaults(config, config_file, css_path)
        file_to_write = config[settings.files][settings.filename]

    return params, config, params_dict, file_to_write, ending, last_slide_content, transition, other_transitions


def set_defaults(config, config_path, css_path):
    """
    Set default values if other values are not used.
    :param css_path:
    :param config_path:
    :param config:
    :return:
    """
    master_key = settings.files
    # default values
    default_filename = settings.default_filename
    # CSS file was defined in parse_config_file
    default_css = css_path
    default_make_pdf = settings.default_make_pdf
    default_hovercraft_target_dir = settings.default_hovercraft_target_dir
    default_course_rounds = settings.default_course_rounds
    default_rst2pdf = settings.default_rst2pdf
    default_course_path = str(Path.cwd())
    defaults = {settings.filename: default_filename, settings.css: default_css,
                settings.course_path: default_course_path, settings.make_pdf: default_make_pdf,
                settings.hovercraft_target_dir: default_hovercraft_target_dir,
                settings.course_rounds: default_course_rounds, settings.rst2pdf: default_rst2pdf}

    if not config[master_key]:
        # if no settings were defined in presentation_config.yaml then use only defaults in files
        settings.logger.info("Using default settings for the files and paths.")
        config.update({master_key: {settings.filename: default_filename,
                                    settings.css: css_path,
                                    settings.make_pdf: default_make_pdf,
                                    settings.course_rounds: default_course_rounds,
                                    settings.rst2pdf: default_rst2pdf,
                                    settings.course_path: default_course_path,
                                    settings.config_name: config_path,
                                    settings.hovercraft_target_dir: default_hovercraft_target_dir
                                    }})

    else:
        print_dashes()
        settings.logger.info("These settings are set via configuration file.")

        for key, default_value in defaults.items():
            if not config[master_key].get(key):
                # add default default_value, since it is not in config
                config[master_key][key] = default_value
            else:
                # these are from configuration file
                # keep older default_value, it has higher priority than default value
                settings.logger.info("{}: {}".format(key, config[master_key][key]))
                if key == settings.make_pdf:
                    if config[master_key].get(settings.make_pdf):
                        # rst2pdf method does not do anything if make_pdf is false
                        if config[master_key].get(settings.rst2pdf):
                            settings.logger.info("pdf creation method: rst2pdf")
                        else:
                            settings.logger.info("pdf creation method: deck2pdf")

        print_dashes()

    return config


def write_rst(raw_dict, param, file_to_write, paths, ending, last_slide_content, transition, other_transitions,
              course_path, step_num):
    """ Writes rst-file."""
    settings.logger.info("Creating {}".format(file_to_write))
    # find paths for images
    img_paths = create_img_path_list(course_path)
    presentation_dir = Path(file_to_write).parent

    if not presentation_dir.exists():
        # usually this path refers to _build path. If it does not exist yet, it will be created.
        settings.logger.info("Creating directory {}".format(presentation_dir))
        create_dir(Path(file_to_write).parent)

    with open(file_to_write, 'w') as writer:
        writer.writelines(param)

    # for loop goes thought the list of rst files in the project and extract POIs
    # first_slide keeps track if it is on the first slide or not
    first_slide = True

    for file in paths:
        try:
            first_slide = write_poi(file, file_to_write, transition, first_slide, img_paths, other_transitions,
                                    raw_dict, step_num)
        except PermissionError as pe:
            settings.logger.error("Permission error while handling {}\nError: {}".format(file, pe))
            exiting()
        except FileNotFoundError as fnf:
            settings.logger.error("{} was not found.\nError: {}".format(file, fnf))
            exiting()
        except Exception as err:
            settings.logger.error("Error occurred during write_poi function.\nError: {}".format(err))
            exiting()
    write_ending(file_to_write, ending, last_slide_content)
    settings.logger.info("\n{} is created.".format(file_to_write))

    return step_num


def selected_rounds(dictionary):
    """
    Select which rounds will be included in presentation.
    Gets rounds from dictionary and creates a list of numbers from that data.

    :return: selected rounds in list. e.g. [1,3,5,6]
    """
    try:
        rounds = dictionary.get(settings.files)[settings.course_rounds]
    except (TypeError, KeyError):
        settings.logger.warning("Course rounds not set in presentation_config.yaml. Selecting all course rounds for "
                                "presentation.")
        return settings.default_course_rounds
    parsed_rounds = []

    if isinstance(rounds, int):
        # if course_round is a single int in presentation_config.yaml
        parsed_rounds.append(rounds)
        return parsed_rounds
    else:
        # removing all whitespaces.
        rounds = rounds.replace(" ", "")
        rounds = rounds.split(",")
        for r in rounds:
            if "-" in r:
                # changing format from "1-4" to [1,2,3,4]
                course_range = range(int(r[0]), int(r[2]) + 1)
                parsed_rounds = [num for num in course_range]
            else:
                if isinstance(r, str):
                    # when in config course_rounds is set to 'all'
                    parsed_rounds = [-1]
                else:
                    parsed_rounds.append(int(r))
        # filtering same numbers. Changing variable to set and back to list.
        parsed_rounds = set(parsed_rounds)
        parsed_rounds = list(parsed_rounds)
        return parsed_rounds


def header():
    print_spacer()
    settings.logger.info("*                     Presentation Maker 0.0.1                    *")
    print_spacer()


def print_spacer():
    settings.logger.info("\n*******************************************************************\n")


def print_dashes():
    settings.logger.info("-----------------------------------------------------------------")


def cmd_line_parsing():
    """
    Parses command-line arguments with argparse.

    :return: list of boolean flags and argument list.
    """
    parser = argparse.ArgumentParser(description="Edit presentation_config.yaml settings in command-line.")
    file_group = parser.add_argument_group('presentation creation')
    creator = parser.add_argument_group('authors and titles')
    parser.add_argument("-v", "--verbose", action="store_true")
    creator.add_argument("-t", "--title", help="title of the presentation. Will be shown at the first slide")
    creator.add_argument("-s", "--subtitle",
                         help="subtitle of the presentation. Will be shown at the first slide, below title")
    creator.add_argument("-a", "--author", help="author of the presentation.")
    file_group.add_argument("-f", "--filename", help="filename of the presentation you want to create. Suffix needs "
                                                     "to be .rst")
    file_group.add_argument("-c", "--course_path", help="path to the root of course directory which has index.rst")
    file_group.add_argument("-y", "--config_path", help="path to the configuration file (presentation_config.yaml)")
    file_group.add_argument("-p", "--pdf", action="store_true", help="enable pdf creation")
    file_group.add_argument("-m", "--html2pdf", action="store_true", help="enables deck2pdf (html to pdf) as a pdf "
                                                                          "creation method")
    file_group.add_argument("-r", "--rounds", help="select which course rounds will be included to presentation. e.g. "
                                                   "1-3, 5")
    parser.add_argument("-d", "-direct", metavar="<name of presentation.rst>", help="creates presentation directly "
                                                                                    "from available (hovercraft "
                                                                                    "compatible) RST-file.")
    args = parser.parse_args()

    if args.verbose:
        settings.logger.info("Following parameters were used:")
        for arg in vars(args):
            if getattr(args, arg):
                settings.logger.info("{}: {}".format(arg, getattr(args, arg)))
        settings.logger.info("\nRest of the parameters are from configuration file or are using default values.")
        print_spacer()
    else:
        pass

    if args:
        # explanation for boolean values
        # [parameters used, direct parameter used, arguments]
        if args.d:
            # parameters used and direct was used
            return [True, True, args]
        else:
            # parameters used, not direct parameter
            return [True, False, args]
    else:
        # no parameters were used
        return [False, False, args]


def set_parameters(dictionary, args, params):
    """
    Sets parameters (which were given through command-line) to dictionary and list.

    Command line parameters have highest priority. Parameters > config > defaults

    :return: dictionary and list.
    """

    try:
        if args.filename:
            dictionary[settings.files][settings.filename] = args.filename
        if args.pdf:
            dictionary[settings.files][settings.make_pdf] = args.pdf
        if args.rounds:
            dictionary[settings.files][settings.course_rounds] = args.rounds
        if args.html2pdf:
            dictionary[settings.files][settings.rst2pdf] = False
        if args.course_path:
            dictionary[settings.files][settings.course_path] = args.course_path
        if args.config_path:
            dictionary[settings.files][settings.config_name] = args.config_path

        if settings.presentation_start in dictionary:
            if args.title:
                dictionary[settings.presentation_start][settings.title] = args.title
                index = [i for i, s in enumerate(params) if ':title:' in s]
                params[index[0]] = ":title: {}\n".format(args.title)
            if args.subtitle:
                dictionary[settings.presentation_start][settings.subtitle] = args.subtitle
                index = [i for i, s in enumerate(params) if ':subtitle:' in s]
                params[index[0]] = ":subtitle: {}\n".format(args.subtitle)
            if args.author:
                dictionary[settings.presentation_start][settings.author] = args.author
                index = [i for i, s in enumerate(params) if ':author:' in s]
                params[index[0]] = ":author: {}\n".format(args.author)
    except (TypeError, KeyError) as e:
        settings.logger.error("Errors occurred during setting parameters in set_parameters function. Error: {}"
                              .format(e))

    return dictionary, params


def create_dir(directory):
    """
    Creates directory given as a parameter.
    :return:
    """
    if not Path(directory).exists():
        settings.logger.info("Creating directory {}".format(str(directory)))
        Path(directory).mkdir(parents=True, exist_ok=True)


def create_presentation(args):
    """
    Creates presentation (HTML, PDF) from POIs which are gathered from other RST files.
    Pdf will be created if you enable it from presentation_config.yaml.

    presentation_config.yaml will be copied to _build directory where user can change settings.

    """
    code_dir = settings.code_dir
    build_dir = settings.build_dir

    # background image related variables
    step_num = 0

    if args[2].config_path:
        settings.logger.info("Using presentation configure file at {}".format(args[2].config_path))
        config_path = args[2].config_path
    else:
        # default name for configuration file
        config_path = build_dir / settings.config_name
        settings.logger.info("Using default configuration file: {}".format(config_path))
    params, raw_dict, dictionary, rst_file, ending, last_slide_content, transition, other_transitions = \
        parse_config_file(code_dir, config_path, build_dir, args[2].config_path)
    raw_dict, params = set_parameters(raw_dict, args[2], params)

    if args[1]:
        # if direct create was used (--direct, d). Does not write_rst, uses available rst file to create presentation.
        # other parameters do not affect the output, since given rst file will be used
        custom_rst_file = args[2].d
        presentation_folder = hover.run(custom_rst_file, raw_dict)
        create_pdf.create(raw_dict, custom_rst_file, presentation_folder, build_dir, code_dir)
    else:
        if args[0]:
            # if parameters were used
            rst_file = raw_dict[settings.files][settings.filename]  # needs to be reassigned if it was changed via cmd
            # arguments
            course_path = raw_dict[settings.files][settings.course_path]

        write_rst(raw_dict, params, rst_file, pathfinder.create_paths(selected_rounds(raw_dict), course_path), ending,
                  last_slide_content, transition, other_transitions, course_path, step_num)
        presentation_folder = hover.run(rst_file, raw_dict, build_dir)
        create_pdf.create(raw_dict, rst_file, presentation_folder, build_dir, code_dir)
    settings.logger.info("If no errors occurred, presentation should be ready.")
    settings.logger.info("Exiting...\n")


def initialization():
    """
    Makes all sorts of initializations in order to make everything work as easily as possible.

    :return:
    """
    settings.logger.info("Making initializations")
    # creating _build if it is not created yet
    create_dir(settings.build_dir)
    # config file will be copied to _build directory for easier access. Especially when using with roman.
    copy_file(settings.code_dir / settings.config_name, settings.build_dir / settings.config_name)


def main():
    initialization()
    header()
    cmd_args = cmd_line_parsing()
    create_presentation(cmd_args)


if __name__ == "__main__":
    main()

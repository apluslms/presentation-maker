"""
This script creates list of paths to all course materials (RST) in correct order.
"""

import re

from pathlib import Path

from . import presentation_maker as pm
from . import settings


def filter_rounds(rounds, indexes):
    """
    Filters rounds from indexes.
    If round is not in rounds it will be filtered from indexes.

    :return: new filtered index in array.
    """
    if rounds[0] == -1:
        # this is used when all rounds are selected
        # see selected_rounds function in presentation_maker.py
        return indexes
    else:
        rnd = 1
        filtered_index = []
        for index in indexes:
            if rnd in rounds:
                filtered_index.append(index)
            rnd += 1
        return filtered_index


def read_index_rst(path_to_index):
    """
    This function reads index.rst files and scrapes file structure.

    :return: list of files from index.rst
    """

    indexes = []
    path = path_to_index
    try:
        with open(str(path), 'r') as reader:
            start = False
            aplusmeta = False
            for line in reader.readlines():
                if ".. aplusmeta::" in line:
                    aplusmeta = True
                if ":caption:" in line:
                    # ignore
                    pass
                if "toctree::" in line:
                    start = True
                    aplusmeta = False
                else:
                    if start and not aplusmeta:
                        line = line.rstrip().lstrip()
                        if re.search('^\..$', line):
                            # if line has only ..
                            # toctree no longer continues
                            break
                        elif not re.search('[a-zA-Z]', line):
                            pass
                        elif ("maxdepth" in line) or ("|" in line):
                            pass
                        elif not line:
                            # empty line
                            pass
                        else:
                            # WARNING! if maxdepth > 2 you might have some problems with this solution
                            # lines in this format: m01_introduction/index
                            indexes.append(line)
                    else:
                        # important stuff hasn't started so ignore
                        pass
        if not start:
            # This is probably wrong kind of file, if not yet started at this point
            raise Exception("Error - index.rst is not not valid. '.. toctree:: missing'")

    except FileNotFoundError:
        settings.logger.info("Error - No such file: {} \n".format(str(path)))
        settings.logger.info("Make sure you are running this from A+ course directory where index.rst is located.")
        pm.exiting()
    except PermissionError as pe:
        settings.logger.error("Permission error while handling {}\n"
                              "Error: {}".format(path, pe))
        pm.exiting()
    return indexes


def build_paths(index_path, paths, file):
    """
    Builds course list from index.rst.

    :return: list of tuples which contains folder and files in that specific folder.
    """
    # filestructure [(foldername, files in folder), ...]
    # e.g. [(m01_introduction, [01_installation, 0X_gallery...]), (m02_programming_exercises, [...])]
    # dictionary does not work since it doesn't keep the order

    filestructure = []
    for path in paths:
        # this assumes that each folder contains index.rst
        path = Path(path)
        if path.name == "index":
            path = path.with_suffix(".rst")
        if index_path.name == file:
            index_path = index_path.parent
        # with open(str(index_path / path), 'r') as reader:
        #     # opens index.rst in all the folders
        #     # split folder/index and get folder-part
        filestructure.append((path, read_index_rst(index_path / path)))
    return filestructure


def remake_paths(index_path, paths, language):
    """
    Creates paths for each .rst file.

    :return: list of paths to each .RST file.
    """
    index_path = index_path.parent
    path_list = []

    for folder, files in paths:
        folder = folder.parent
        for file in files:
            p = Path(index_path / folder / (file + ".rst"))
            # NOTE: This works when system uses 'language suffix' naming convention. e.g. example_file_en.rst
            # uncomment to use it, instead of this path dependent language selection.
            # if language == "fi":
            #     # Here assumes that files that are written in finnish do not have _fi ending. Currently it does not.
            #     p = Path(index_path / folder / (file + ".rst"))
            # else:
            #     # checking if the file already has a language suffix e.g. '_en' in the name of the file
            #     if ("_" + language) not in file:
            #         # file do not have language suffix and if it does it will not make another
            #         f = file + "_" + language + ".rst"
            #         p = Path(index_path / folder / f)
            if p.exists():
                # some files may not exist even if they are in the index
                # or files have naming discrepancy.
                path_list.append(str(p))
            else:
                if settings.verbose:
                    settings.logger.info("File {} not found, skipping...".format(f))
    return path_list


def create_paths(rounds, course_path, language):
    """
    Main function. Calls all the other functions in pathfinder.

    :return: list of paths to each .RST file.
    """
    # if language is set then index.rst file has different ending depending on the language e.g index_en.rst
    if not language:
        file = "index.rst"
    else:
        file = "index_" + language + ".rst"

    index_path = Path(course_path) / file

    paths = read_index_rst(index_path)
    paths = filter_rounds(rounds, paths)
    structure = build_paths(index_path, paths, file)
    path_list = remake_paths(index_path, structure, language)
    return path_list

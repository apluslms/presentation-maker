
"""
Creates columns to the slides after hovercraft has been run. Creates columns based on the number of ::newcol options.
Calculates how many columns will be created on the slide and creates row div which has all the columns inside.

This works only with impress.js presentations (hovercraft).
"""

from bs4 import BeautifulSoup as bs
from bs4.element import NavigableString

from . import settings


def find_all_steps(soup):
    steps = soup.find_all('div', attrs={'class': 'step'})
    cloned = bs(str(steps), 'html.parser')
    return cloned


def add_column_ratios(ratio, step):
    # ratio is string like this "5 1 1"
    # each value is width of column first is 5/7  and other are 1/7 from the full slide

    # style="flex-basis: 60%;"
    values = [int(x) for x in ratio.split(" ")]
    total = 0
    for w in values:
        total += w

    columns = step.find_all(attrs={'class': 'column'})

    for column, v in zip(columns, values):
        style = "flex-basis: " + str(round(v/total*100)) + "%;"

        # appending styles to older styles if there are any
        if not step.style:
            column['style'] = style
        else:
            old_style = column.style
            column['style'] = old_style + style


def make_columns(soup, steps):
    """
    Creates dictionary for column data. Appends steps to soup that do not have any columns.
    :param soup:
    :param steps:
    :return:
    """
    temp_rows = []
    columns = {}
    col_ratios = settings.column_ratios
    # how many columns is in current step
    col = 1
    # col_step keeps count which step has columns, we need it for col_ratios
    is_columns = False
    index = 0
    for step in list(steps):
        if not isinstance(step, NavigableString):
            for row in step:
                if "::newcol" in row:
                    # add temp_rows to columns directory
                    # empty temp_rows for next column contents
                    columns[col] = temp_rows
                    temp_rows = []
                    col += 1
                    is_columns = True
                else:
                    if str(step.h1) in str(row):
                        # skips main titles but other titles are appended. If user wants to use multiple h1 elements
                        # in one slide
                        pass
                    else:
                        temp_rows.append(row)

            if col == 1:
                # only one column in this step. Can be appended to soup
                soup.find('div', attrs={'id': 'impress'}).append(step)
            else:
                # add rows to next column. Last is not added since it is <p>::newcol</p>
                columns[col] = temp_rows
                edit_step(step, columns, soup)

            temp_rows = []
            # restart indexing at new step
            col = 1
            # empty columns for the next step
            columns = {}
        if is_columns and (index < len(col_ratios)):
            # if condition: if it has columns and it is a new step then add column ratios
            is_columns = False
            add_column_ratios(col_ratios[index], step)
            index += 1

    return columns


def edit_step(step, columns, soup):
    """
    Creates row and column divs inside the step using column data created in make_columns.

    :param step:
    :param columns:
    :param soup:
    :return:
    """
    row_tag = soup.new_tag('div', **{"class": "row"})
    title = step.h1
    # clearing step contents, appending title and row div
    step.clear()
    step.append(title)
    step.append(row_tag)
    r = step.find('div', attrs={'class': 'row'})

    # appending new columns to row
    for num in columns:
        if columns[num]:
            r.append(soup.new_tag('div', **{"class": "column"}))
            # co = r.find('div', attrs={'class': 'column'})

    # writing column dictionary contents to empty columns
    i = 1
    for sibling in step.find_all('div', attrs={'column'}):
        if not columns[i] == []:
            for content in columns[i]:
                sibling.append(content)
        i += 1
    # appending modified step to impress div which has all the steps
    soup.find('div', attrs={'id': 'impress'}).append(step)


def delete_old_steps(step_container):
    for elm in step_container.find_all():
        elm.decompose()
    return step_container


def write_to_file(soup, filename):
    with open(filename, "w") as out_file:
        out_file.write(str(soup.prettify()))


def open_file(filename):
    with open(filename) as file:
        html = file.read()
        soup = bs(html, 'html.parser')
    return soup


def create(filename):
    """
    Creates rows and columns in html after the hovercraft.
    :param filename:
    :return:
    """

    soup = open_file(filename)
    settings.logger.info("Creating columns.")
    steps = find_all_steps(soup)
    step_container = soup.find(id="impress").extract()
    # after header class insert steps back, after they have been modified
    step_container = delete_old_steps(step_container)
    try:
        soup.find('div', attrs={'class': 'header'}).insert_after(step_container)
    except AttributeError as no_header:
        # if headers are not used
        try:
            # try to insert before footer
            soup.find('div', attrs={'class': 'footer'}).insert_before(step_container)
        except AttributeError as no_footer:
            # and if no footer then insert it before hovercraft-help div
            soup.find('div', attrs={'class': 'hovercraft-help'}).insert_before(step_container)
    make_columns(soup, steps)
    write_to_file(soup, filename)
    settings.logger.info("Columns created successfully.")


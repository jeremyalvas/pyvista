"""This is a helper module to generate tables that can be included in the documentation."""

# ruff: noqa: PTH102,PTH103,PTH107,PTH112,PTH113,PTH117,PTH118,PTH119,PTH122,PTH123,PTH202
from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from enum import StrEnum, auto
import inspect
import io
import os
from pathlib import Path
import re
import textwrap
from types import FunctionType
from typing import Any, Callable, Dict, Iterable, List, Literal, Optional, Tuple, Type, Union, final

import numpy as np

import pyvista
import pyvista as pv
from pyvista.core.errors import VTKVersionError
from pyvista.examples import _dataset_loader, downloads
from pyvista.examples._dataset_loader import (
    _MultiFileDownloadableLoadable,
    _SingleFileDownloadableLoadable,
)

DatasetLoaderObj = Union[_MultiFileDownloadableLoadable, _SingleFileDownloadableLoadable]

# Paths to directories in which resulting rst files and images are stored.
CHARTS_TABLE_DIR = "api/plotting/charts"
CHARTS_IMAGE_DIR = "images/charts"
COLORS_TABLE_DIR = "api/utilities"
DATASET_GALLERY_DIR = "api/examples/dataset-gallery"
DATASET_GALLERY_IMAGE_DIR = "images/dataset-gallery"


def _aligned_dedent(txt):
    """Custom variant of `textwrap.dedent`.

    Helper method to dedent the provided text up to the special alignment character ``'|'``.
    """
    return textwrap.dedent(txt).replace('|', '')


class DocTable:
    """Helper class to create tables for the documentation.

    The ``generate`` method creates the table rst file (and possibly any other
    files, such as images, used by the table). This method internally calls
    the ``fetch_data``, ``get_header`` and ``get_row`` methods, which should be
    provided by any subclass.
    Each table is generated from a list of 'row_data' provided by the ``fetch_data``
    method. The ``get_header`` and ``get_row`` methods generate the required rst
    for the table's header and table's rows respectively.
    """

    path = None  # Path to the rst file to which the table will be written

    @classmethod
    def generate(cls):
        """Generate this table."""
        assert cls.path is not None, f"Subclass {cls} should specify a path."
        if isinstance(cls.path, property):
            cls.path = cls.path.fget(cls)

        data = cls.fetch_data()
        assert data is not None, f"No data was fetched by {cls}."

        with io.StringIO() as fnew:
            fnew.write(cls.get_header(data))
            for i, row_data in enumerate(data):
                row = cls.get_row(i, row_data)
                if row is not None:
                    fnew.write(row)

            # if file exists, verify that we have no new content
            fnew.seek(0)
            new_txt = fnew.read()

        # determine if existing file needs to be rewritten
        if Path(cls.path).exists():
            with Path(cls.path).open(encoding="utf-8") as fold:
                orig_txt = fold.read()
            if orig_txt == new_txt:
                new_txt = ''

        # write if there is any text to write. This avoids resetting the documentation cache
        if new_txt:
            with open(cls.path, 'w', encoding="utf-8") as fout:
                fout.write(new_txt)

        pv.close_all()

    @classmethod
    def fetch_data(cls):
        """Get a list of row_data used to generate the table."""
        raise NotImplementedError("Subclasses should specify a fetch_data method.")

    @classmethod
    def get_header(cls, data):
        """Get the table's header rst."""
        raise NotImplementedError("Subclasses should specify a table header.")

    @classmethod
    def get_row(cls, i, row_data):
        """Get the rst for the given row. Can return ``None`` if no row should
        be generated for the provided ``row_data``."""
        raise NotImplementedError("Subclasses should specify a get_row method.")


class LineStyleTable(DocTable):
    """Class to generate line style table."""

    path = f"{CHARTS_TABLE_DIR}/pen_line_styles.rst"
    header = _aligned_dedent(
        """
        |.. list-table:: Line styles
        |   :widths: 20 40 40
        |   :header-rows: 1
        |
        |   * - Style
        |     - Description
        |     - Example
        """
    )
    row_template = _aligned_dedent(
        """
        |   * - ``"{}"``
        |     - {}
        |     - .. image:: /{}
        """
    )

    @classmethod
    def fetch_data(cls):
        # Fetch table data from ``LINE_STYLES`` dictionary.
        return [{"style": ls, **data} for (ls, data) in pv.charts.Pen.LINE_STYLES.items()]

    @classmethod
    def get_header(cls, data):
        return cls.header

    @classmethod
    def get_row(cls, i, row_data):
        if row_data["descr"] is None:
            return None  # Skip line style if description is set to ``None``.
        else:
            # Create an image from the given line style and generate the row rst.
            img_path = f"{CHARTS_IMAGE_DIR}/ls_{i}.png"
            cls.generate_img(row_data["style"], img_path)
            return cls.row_template.format(row_data["style"], row_data["descr"], img_path)

    @staticmethod
    def generate_img(line_style, img_path):
        """Generate and save an image of the given line_style."""
        p = pv.Plotter(off_screen=True, window_size=[100, 50])
        p.background_color = 'w'
        chart = pv.Chart2D()
        chart.line([0, 1], [0, 0], color="b", width=3.0, style=line_style)
        chart.hide_axes()
        p.add_chart(chart)

        # Generate and crop the image
        _, img = p.show(screenshot=True, return_cpos=True)
        img = img[18:25, 22:85, :]

        # exit early if the image already exists and is the same
        if os.path.isfile(img_path) and pv.compare_images(img, img_path) < 1:
            return

        # save it
        p._save_image(img, img_path, False)


class MarkerStyleTable(DocTable):
    """Class to generate marker style table."""

    path = f"{CHARTS_TABLE_DIR}/scatter_marker_styles.rst"
    header = _aligned_dedent(
        """
        |.. list-table:: Marker styles
        |   :widths: 20 40 40
        |   :header-rows: 1
        |
        |   * - Style
        |     - Description
        |     - Example
        """
    )
    row_template = _aligned_dedent(
        """
        |   * - ``"{}"``
        |     - {}
        |     - .. image:: /{}
        """
    )

    @classmethod
    def fetch_data(cls):
        # Fetch table data from ``MARKER_STYLES`` dictionary.
        return [
            {"style": ms, **data} for (ms, data) in pv.charts.ScatterPlot2D.MARKER_STYLES.items()
        ]

    @classmethod
    def get_header(cls, data):
        return cls.header

    @classmethod
    def get_row(cls, i, row_data):
        if row_data["descr"] is None:
            return None  # Skip marker style if description is set to ``None``.
        else:
            # Create an image from the given marker style and generate the row rst.
            img_path = f"{CHARTS_IMAGE_DIR}/ms_{i}.png"
            cls.generate_img(row_data["style"], img_path)
            return cls.row_template.format(row_data["style"], row_data["descr"], img_path)

    @staticmethod
    def generate_img(marker_style, img_path):
        """Generate and save an image of the given marker_style."""
        p = pv.Plotter(off_screen=True, window_size=[100, 100])
        p.background_color = 'w'
        chart = pv.Chart2D()
        chart.scatter([0], [0], color="b", size=9, style=marker_style)
        chart.hide_axes()
        p.add_chart(chart)

        # generate and crop the image
        _, img = p.show(screenshot=True, return_cpos=True)
        img = img[40:53, 47:60, :]

        # exit early if the image already exists and is the same
        if os.path.isfile(img_path) and pv.compare_images(img, img_path) < 1:
            return

        # save it
        p._save_image(img, img_path, False)


class ColorSchemeTable(DocTable):
    """Class to generate color scheme table."""

    path = f"{CHARTS_TABLE_DIR}/plot_color_schemes.rst"
    header = _aligned_dedent(
        """
        |.. list-table:: Color schemes
        |   :widths: 15 50 5 30
        |   :header-rows: 1
        |
        |   * - Color scheme
        |     - Description
        |     - # colors
        |     - Example
        """
    )
    row_template = _aligned_dedent(
        """
        |   * - ``"{}"``
        |     - {}
        |     - {}
        |     - .. image:: /{}
        """
    )

    @classmethod
    def fetch_data(cls):
        # Fetch table data from ``COLOR_SCHEMES`` dictionary.
        return [{"scheme": cs, **data} for (cs, data) in pv.colors.COLOR_SCHEMES.items()]

    @classmethod
    def get_header(cls, data):
        return cls.header

    @classmethod
    def get_row(cls, i, row_data):
        if row_data["descr"] is None:
            return None  # Skip color scheme if description is set to ``None``.
        else:
            # Create an image from the given color scheme and generate the row rst.
            img_path = f"{CHARTS_IMAGE_DIR}/cs_{i}.png"
            n_colors = cls.generate_img(row_data["scheme"], img_path)
            return cls.row_template.format(
                row_data["scheme"], row_data["descr"], n_colors, img_path
            )

    @staticmethod
    def generate_img(color_scheme, img_path):
        """Generate and save an image of the given color_scheme."""
        p = pv.Plotter(off_screen=True, window_size=[240, 120])
        p.background_color = 'w'
        chart = pv.Chart2D()
        # Use a temporary plot to determine the total number of colors in this scheme
        tmp_plot = chart.bar([0], [[1]] * 2, color=color_scheme, orientation="H")
        n_colors = len(tmp_plot.colors)
        plot = chart.bar([0], [[1]] * n_colors, color=color_scheme, orientation="H")
        chart.remove_plot(tmp_plot)
        plot.pen.color = 'w'
        chart.x_range = [0, n_colors]
        chart.hide_axes()
        p.add_chart(chart)

        # Generate and crop the image
        _, img = p.show(screenshot=True, return_cpos=True)
        img = img[34:78, 22:225, :]

        # exit early if the image already exists and is the same
        if os.path.isfile(img_path) and pv.compare_images(img, img_path) < 1:
            return n_colors

        # save it
        p._save_image(img, img_path, False)

        return n_colors


class ColorTable(DocTable):
    """Class to generate colors table."""

    path = f"{COLORS_TABLE_DIR}/colors.rst"
    header = _aligned_dedent(
        """
        |.. list-table::
        |   :widths: 50 20 30
        |   :header-rows: 1
        |
        |   * - Name
        |     - Hex value
        |     - Example
        """
    )
    row_template = _aligned_dedent(
        """
        |   * - {}
        |     - ``{}``
        |     - .. raw:: html
        |
        |          <span style='width:100%; height:100%; display:block; background-color: {};'>&nbsp;</span>
        """
    )

    @classmethod
    def fetch_data(cls):
        # Fetch table data from ``hexcolors`` dictionary.
        colors = {
            name: {"name": name, "hex": hex, "synonyms": []} for name, hex in pv.hexcolors.items()
        }
        # Add synonyms defined in ``color_synonyms`` dictionary.
        for s, name in pv.colors.color_synonyms.items():
            colors[name]["synonyms"].append(s)
        return colors.values()

    @classmethod
    def get_header(cls, data):
        return cls.header

    @classmethod
    def get_row(cls, i, row_data):
        name_template = '``"{}"``'
        names = [row_data["name"]] + row_data["synonyms"]
        name = " or ".join(name_template.format(n) for n in names)
        return cls.row_template.format(name, row_data["hex"], row_data["hex"])


def _get_doc(func: Callable[[], Any]) -> str:
    """Return the first line of the callable's docstring."""
    return func.__doc__.splitlines()[0]


def _get_fullname(typ: Type) -> str:
    """Return the fully qualified name of the given type object."""
    return f"{typ.__module__}.{typ.__qualname__}"


def _ljust_lines(lines: List[str], min_width=None) -> List[str]:
    """Left-justify a list of lines."""
    min_width = min_width if min_width else _max_width(lines)
    return [line.ljust(min_width) for line in lines]


def _max_width(lines: List[str]) -> int:
    """Compute the max line-width from a list of lines."""
    return max(map(len, lines))


def _repeat_string(string: str, num_repeat: int) -> str:
    """Repeat `string` `num_repeat` times."""
    return ''.join([string] * num_repeat)


def _pad_lines(
    lines: Union[str, List[str]],
    *,
    pad_left: str = '',
    pad_right: str = '',
    ljust=False,
    return_shape=False,
):
    """Add padding to the left or right of each line with a specified string.

    Optionally, padding may be applied to left-justify the text such that the lines
    all have the same width.

    Optionally, the lines may be padded using a specified string on the left or right.

    Parameters
    ----------
    lines : str | list[str]
        Lines to be padded. If a string, it is first split with splitlines.

    pad_left : str, default: ''
        String to pad the left of each line with.

    pad_right : str, default: ''
        String to pad the right of each line with.

    ljust : bool, default: False
        If ``True``, left-justify the lines such that they have equal width
        before applying any padding.

    return_shape : bool, default: False
        If ``True``, also return the width and height of the padded lines.

    """
    if is_str := isinstance(lines, str):
        lines = lines.splitlines()
    # Justify
    lines = _ljust_lines(lines) if ljust else lines
    # Pad
    lines = [pad_left + line + pad_right for line in lines]

    if return_shape:
        width, height = _max_width(lines), len(lines)
        lines = '\n'.join(lines) if is_str else lines
        return lines, width, height
    return '\n'.join(lines) if is_str else lines


def _indent_multi_line_string(
    string: str, indent_size=3, indent_level: int = 1, omit_first_line=True
) -> str:
    """Indent each line of a multi-line string by a specified indentation level.

    Optionally specify the indent size (e.g. 3 spaces for rst).
    Optionally omit indentation from the first line if it is already indented.

    This function is used to support de-denting formatted multi-line strings.
    E.g. for the following rst text with item {} indented by 3 levels:

        |      .. some_directive::
        |
        |         {}

    a multi-line string input such as 'line1\nline2\nline3' will be formatted as:

        |      .. some_directive::
        |
        |         line1\n         line2\n         line3
        |

    which will result in the correct indentation applied to all lines of the string.

    """
    lines = string.splitlines()
    indentation = _repeat_string(' ', num_repeat=indent_size * indent_level)
    first_line = lines.pop(0) if omit_first_line else None
    lines = _pad_lines(lines, pad_left=indentation) if len(lines) > 0 else lines
    lines.insert(0, first_line) if first_line else None
    return '\n'.join(lines)


def _as_iterable(item) -> Iterable[Any]:
    return [item] if not isinstance(item, (Iterable, str)) else item


class DatasetCard:
    """Class for creating a rst-formatted card for a dataset.

    Create a card with header, footer, and four grid items.
    The four grid items are displayed as:
        - 2x2 grid for large screens
        - 4x1 grid for small screens

    Each card has roughly following structure:

        +-Card----------------------+
        | Header: Dataset name      |
        |                           |
        | +-Grid------------------+ |
        | | Dataset doc           | |
        | +-----------------------+ |
        | | Image                 | |
        | +-----------------------+ |
        | | Dataset metadata      | |
        | +-----------------------+ |
        | | File metadata         | |
        | +-----------------------+ |
        |                           |
        | Footer: Data source links |
        +---------------------------+

    See https://sphinx-design.readthedocs.io/en/latest/index.html for
    details on the directives used and their formatting.
    """

    card_template = _aligned_dedent(
        """
        |.. card::
        |
        |   {}
        |
        |   ^^^
        |
        |   .. grid:: 1 2 2 2
        |      :margin: 1
        |
        |      .. grid-item::
        |         :columns: 12 8 8 8
        |
        |         {}
        |
        |      .. grid-item::
        |         :columns: 12 4 4 4
        |
        |         {}
        |
        |      .. grid-item::
        |
        |         .. card::
        |            :shadow: none
        |            :class-header: sd-text-center sd-font-weight-bold sd-px-0 sd-border-right-0 sd-border-left-0 sd-border-top-0
        |            :class-body: sd-border-0
        |
        |            :octicon:`info` Dataset Info
        |            ^^^
        |            {}
        |
        |      .. grid-item::
        |
        |         .. card::
        |            :shadow: none
        |            :class-header: sd-text-center sd-font-weight-bold sd-px-0 sd-border-right-0 sd-border-left-0 sd-border-top-0
        |            :class-body: sd-border-0
        |
        |            :octicon:`file` File Info
        |            ^^^
        |            {}
        |
        |   +++
        |   {}
        |
        |
        """
    )

    HEADER_FOOTER_INDENT_LEVEL = 1
    GRID_ITEM_INDENT_LEVEL = 3
    GRID_ITEM_FIELDS_INDENT_LEVEL = 4
    REF_ANCHOR_INDENT_LEVEL = 2

    # Template for dataset name and badges
    header_template = _aligned_dedent(
        """
        |.. grid:: 1
        |   :margin: 0
        |
        |   .. grid-item::
        |      :class: sd-text-center sd-font-weight-bold sd-fs-5
        |
        |      {}
        |
        |   .. grid-item::
        |      :class: sd-text-center
        |
        |      {}
        |
        """
    )[1:-1]

    # Template title with a reference anchor
    dataset_title_with_ref_template = _aligned_dedent(
        """
        |.. _{}:
        |
        |{}
        """
    )[1:-1]

    # Template for dataset func and doc
    dataset_info_template = _aligned_dedent(
        """
        |{}
        |
        |{}
        """
    )[1:-1]

    # Template for dataset image
    # The image is encapsulated in its own card
    image_template = _aligned_dedent(
        """
        |.. card::
        |   :class-body: sd-px-0 sd-py-0 sd-rounded-3
        |
        |   .. image:: /{}
        """
    )[1:-1]

    footer_template = _aligned_dedent(
        """
        |.. dropdown:: Data Source
        |   :icon: mark-github
        |
        |   {}
        """
    )[1:-1]

    # Format fields in a grid where the first item is a left-justified
    # name and the second is a right-justified value.
    # The grid boxes are justified to push them toward opposite sides.
    #
    #   Smaller entries should fit on one line:
    #       | Field      Value |
    #
    #   Longer entries should fit on two lines:
    #       | LongField        |
    #       |        LongValue |
    #
    #   Fields with many values should align to the right
    #   and can stack together on one line if they fit.
    #       | LongField        |
    #       |        LongValue |
    #       |   ExtraLongValue |
    #       |    Value3 Value4 |
    field_grid_template = _aligned_dedent(
        """
        |.. grid:: auto
        |   :class-container: sd-align-major-justify sd-px-0
        |   :class-row: sd-align-major-justify sd-px-0
        |   :margin: 1
        |   :padding: 0
        |   :gutter: 1
        |
        |   .. grid-item::
        |      :columns: auto
        |      :class: sd-text-nowrap
        |
        |      **{}**
        |
        |   .. grid-item::
        |      :columns: auto
        |      :class: sd-text-right sd-text-nowrap
        |      :child-align: justify
        |
        |      {}
        |
        """
    )[1:-1]

    # If the field has more than one value, all additional values are
    # placed in a second grid and aligned towards the 'right' side
    # of the grid.
    field_grid_extra_values_grid_template = _aligned_dedent(
        """
        |.. grid:: auto
        |   :class-container: sd-align-major-end sd-px-0
        |   :class-row: sd-align-major-end sd-px-0
        |   :margin: 1
        |   :padding: 0
        |   :gutter: 1
        |
        """
    )[1:-1]
    field_grid_extra_values_item_template = _aligned_dedent(
        """
        |   .. grid-item::
        |      :columns: auto
        |      :class: sd-text-right sd-text-nowrap
        |
        |      {}
        |
        """
    )[1:-1]

    _NOT_AVAILABLE_IMG_PATH = os.path.join(DATASET_GALLERY_IMAGE_DIR, 'not_available.png')

    def __init__(
        self,
        dataset_name: str,
        loader: DatasetLoaderObj,
    ):
        self.dataset_name = dataset_name
        self.loader = loader
        self._badges: List[Optional[_BaseDatasetBadge]] = []
        self.card = None
        self.ref = None

    def add_badge(self, badge: _BaseDatasetBadge):
        self._badges.append(badge)

    def generate(self):
        # Get rst dataset name-related info
        index_name, header_name, func_ref, func_doc, func_name = self._generate_dataset_name(
            self.dataset_name
        )
        # Process dataset image
        img_path = self._search_image_path(func_name)
        self._process_img(img_path)

        # Get rst file and instance metadata
        (
            file_size,
            num_files,
            file_ext,
            reader_type,
            dataset_type,
            datasource_links,
            n_cells,
            n_points,
            length,
            dimensions,
            spacing,
            n_arrays,
        ) = DatasetCard._generate_dataset_properties(self.loader)

        # Generate rst for badges
        carousel_badges = self._generate_carousel_badges(self._badges)
        celltype_badges = self._generate_celltype_badges(self._badges)

        # Assemble rst parts into main blocks used by the card
        header_block, header_ref_block = self._create_header_block(
            index_name, header_name, carousel_badges
        )
        info_block = self._create_info_block(func_ref, func_doc)
        img_block = self._create_image_block(img_path)
        dataset_props_block = self._create_dataset_props_block(
            dataset_type, celltype_badges, n_cells, n_points, length, dimensions, spacing, n_arrays
        )
        file_info_block = self._create_file_props_block(file_size, num_files, file_ext, reader_type)
        footer_block = self._create_footer_block(datasource_links)

        # Create two versions of the card
        # First version has no ref label
        card_no_ref = self.card_template.format(
            header_block,
            info_block,
            img_block,
            dataset_props_block,
            file_info_block,
            footer_block,
        )
        # Second version has a ref label in header
        card_with_ref = self.card_template.format(
            header_ref_block,
            info_block,
            img_block,
            dataset_props_block,
            file_info_block,
            footer_block,
        )

        return card_no_ref, card_with_ref

    @staticmethod
    def _generate_dataset_properties(loader):
        try:
            # Get data from loader
            loader.download()

            # properties collected by the loader
            file_size = DatasetPropsGenerator.generate_file_size(loader)
            num_files = DatasetPropsGenerator.generate_num_files(loader)
            file_ext = DatasetPropsGenerator.generate_file_ext(loader)
            reader_type = DatasetPropsGenerator.generate_reader_type(loader)
            dataset_type = DatasetPropsGenerator.generate_dataset_type(loader)
            datasource_links = DatasetPropsGenerator.generate_datasource_links(loader)

            # properties collected directly from the dataset
            n_cells = DatasetPropsGenerator.generate_n_cells(loader)
            n_points = DatasetPropsGenerator.generate_n_points(loader)
            length = DatasetPropsGenerator.generate_length(loader)
            dimensions = DatasetPropsGenerator.generate_dimensions(loader)
            spacing = DatasetPropsGenerator.generate_spacing(loader)
            n_arrays = DatasetPropsGenerator.generate_n_arrays(loader)

        except VTKVersionError:
            # Exception is caused by 'download_can'
            # Set default values
            NOT_AVAILABLE = '``Not available``'
            file_size = NOT_AVAILABLE
            num_files = NOT_AVAILABLE
            file_ext = NOT_AVAILABLE
            reader_type = NOT_AVAILABLE
            dataset_type = NOT_AVAILABLE
            datasource_links = NOT_AVAILABLE

            n_cells = None
            n_points = None
            length = None
            dimensions = None
            spacing = None
            n_arrays = None

        return (
            file_size,
            num_files,
            file_ext,
            reader_type,
            dataset_type,
            datasource_links,
            n_cells,
            n_points,
            length,
            dimensions,
            spacing,
            n_arrays,
        )

    @staticmethod
    def _generate_dataset_name(dataset_name: str):
        # Format dataset name for indexing and section heading
        index_name = dataset_name + '_dataset'
        header = ' '.join([word.capitalize() for word in index_name.split('_')])

        # Get the corresponding 'download' function of the loader
        func_name = 'download_' + dataset_name
        func = getattr(downloads, func_name)

        # Get the card's header info
        func_ref = f':func:`~{_get_fullname(func)}`'
        func_doc = _get_doc(func)
        return index_name, header, func_ref, func_doc, func_name

    @staticmethod
    def _generate_carousel_badges(badges: List[_BaseDatasetBadge]):
        """Sort badges by type and join all badge rst into a single string."""
        module_badges, datatype_badges, special_badges, category_badges = [], [], [], []
        for badge in badges:
            if isinstance(badge, ModuleBadge):
                module_badges.append(badge)
            elif isinstance(badge, DataTypeBadge):
                datatype_badges.append(badge)
            elif isinstance(badge, SpecialDataTypeBadge):
                special_badges.append(badge)
            elif isinstance(badge, CategoryBadge):
                category_badges.append(badge)
            elif isinstance(badge, CellTypeBadge):
                pass  # process these separately
            elif isinstance(badge, _BaseDatasetBadge):
                raise NotImplementedError(f'No implementation for badge type {type(badge)}.')
        all_badges = module_badges + datatype_badges + special_badges + category_badges
        rst = ' '.join([badge.generate() for badge in all_badges])
        return rst

    @staticmethod
    def _generate_celltype_badges(badges: List[_BaseDatasetBadge]):
        """Sort badges by type and join all badge rst into a single string."""
        celltype_badges = [badge for badge in badges if isinstance(badge, CellTypeBadge)]
        rst = '\n'.join([badge.generate() for badge in celltype_badges])
        if rst == '':
            rst = '``None``'
        return rst

    @staticmethod
    def _search_image_path(dataset_download_func_name: str):
        """Search the thumbnail directory and return its path.

        If no thumbnail is found, the path to a "not available" image is returned.
        """
        # Search directory and match:
        #     any word character(s), then function name, then any non-word character(s),
        #     then a 3character file extension, e.g.:
        #       'pyvista-examples...download_name...ext'
        #     or simply:
        #       'download_name.ext'
        all_filenames = '\n' + '\n'.join(os.listdir(DATASET_GALLERY_IMAGE_DIR)) + '\n'
        match = re.search(
            pattern=r'\n([\w|\-]*' + dataset_download_func_name + r'(\-\w*\.|\.)[a-z]{3})\n',
            string=all_filenames,
            flags=re.MULTILINE,
        )

        if match:
            groups = match.groups()
            assert (
                sum(dataset_download_func_name in grp for grp in groups) <= 1
            ), f"More than one thumbnail image was found for {dataset_download_func_name}, got:\n{groups}"
            img_fname = groups[0]
            img_path = os.path.join(DATASET_GALLERY_IMAGE_DIR, img_fname)
            assert os.path.isfile(img_path)
        else:
            print(f"WARNING: Missing thumbnail image file for \'{dataset_download_func_name}\'")
            img_path = os.path.join(DATASET_GALLERY_IMAGE_DIR, 'not_available.png')
        return img_path

    @staticmethod
    def _process_img(img_path):
        """Process the thumbnail image to ensure it's the right size."""
        from PIL import Image

        IMG_WIDTH, IMG_HEIGHT = 400, 300

        if os.path.basename(img_path) == 'not_available.png':
            not_available_mesh = pv.Text3D('Not Available')
            p = pv.Plotter(off_screen=True, window_size=(IMG_WIDTH, IMG_HEIGHT))
            p.background_color = 'white'
            p.add_mesh(not_available_mesh, color='black')
            p.view_xy()
            p.camera.up = (1, IMG_WIDTH / IMG_HEIGHT, 0)
            p.enable_parallel_projection()
            img_array = p.show(screenshot=True)

            # exit early if the image is the same
            if os.path.isfile(img_path) and pv.compare_images(img_path, img_path) < 1:
                return

            img = Image.fromarray(img_array)
            img.save(img_path)
        else:
            # Resize existing image if necessary
            img = Image.open(img_path)
            if img.width > IMG_WIDTH or img.height > IMG_HEIGHT:
                img.thumbnail(size=(IMG_WIDTH, IMG_HEIGHT))
                img.save(img_path)

    @staticmethod
    def _format_and_indent_from_template(*args, template=None, indent_level=None):
        """Format args using a template and indent all formatted lines by some amount."""
        assert template is not None
        assert indent_level is not None
        formatted = template.format(*args)
        indented = _indent_multi_line_string(formatted, indent_level=indent_level)
        return indented

    @classmethod
    def _generate_field_grid(cls, field_name, field_values):
        """Generate a rst grid with field data.

        The grid uses the class templates for the field name and field value(s).
        """
        if field_values in [None, '']:
            return None
        value_lines = str(field_values).splitlines()
        first_value = value_lines.pop(0)
        field = cls.field_grid_template.format(field_name, first_value)
        if len(value_lines) >= 1:
            # Add another grid for extra values
            extra_values_grid = cls.field_grid_extra_values_grid_template
            extra_values = [
                cls.field_grid_extra_values_item_template.format(val) for val in value_lines
            ]
            return '\n'.join([field, extra_values_grid, *extra_values])
        return field

    @staticmethod
    def _generate_field_block(fields: List[Tuple[str, Union[str, None]]], indent_level: int = 0):
        """Generate a grid for each field and combine the grids into an indented multi-line rst block.

        Any fields with a `None` value are completely excluded from the block.
        """
        field_grids = [DatasetCard._generate_field_grid(name, value) for name, value in fields]
        block = '\n'.join([grid for grid in field_grids if grid])
        return _indent_multi_line_string(block, indent_level=indent_level)

    @classmethod
    def _create_header_block(cls, index_name, header_name, carousel_badges):
        """Generate header rst block."""
        # Two headers are created: one with a reference target and one without
        header = cls._format_and_indent_from_template(
            header_name,
            carousel_badges,
            template=cls.header_template,
            indent_level=cls.HEADER_FOOTER_INDENT_LEVEL,
        )

        header_name_with_ref = DatasetCard._format_and_indent_from_template(
            index_name,
            header_name,
            template=cls.dataset_title_with_ref_template,
            indent_level=cls.REF_ANCHOR_INDENT_LEVEL,
        )
        header_ref = DatasetCard._format_and_indent_from_template(
            header_name_with_ref,
            carousel_badges,
            template=cls.header_template,
            indent_level=cls.HEADER_FOOTER_INDENT_LEVEL,
        )
        return header, header_ref

    @classmethod
    def _create_image_block(cls, img_path):
        """Generate rst block for the dataset image."""
        block = cls._format_and_indent_from_template(
            img_path,
            template=cls.image_template,
            indent_level=cls.GRID_ITEM_INDENT_LEVEL,
        )
        return block

    @classmethod
    def _create_info_block(cls, func_ref, func_doc):
        block = cls._format_and_indent_from_template(
            func_ref,
            func_doc,
            template=cls.dataset_info_template,
            indent_level=cls.GRID_ITEM_INDENT_LEVEL,
        )
        return block

    @classmethod
    def _create_dataset_props_block(
        cls, dataset_type, celltype_badges, n_cells, n_points, length, dimensions, spacing, n_arrays
    ):
        dataset_fields = [
            ('Data Type', dataset_type),
            ('Cell Type', celltype_badges),
            ('N Cells', n_cells),
            ('N Points', n_points),
            ('Length', length),
            ('Dimensions', dimensions),
            ('Spacing', spacing),
            ('N Arrays', n_arrays),
        ]
        dataset_fields_block = cls._generate_field_block(
            dataset_fields, indent_level=cls.GRID_ITEM_FIELDS_INDENT_LEVEL
        )
        return dataset_fields_block

    @classmethod
    def _create_file_props_block(cls, file_size, num_files, file_ext, reader_type):
        file_info_fields = [
            ('File Size', file_size),
            ('Num Files', num_files),
            ('File Ext', file_ext),
            ('Reader', reader_type),
        ]
        file_info_fields_block = DatasetCard._generate_field_block(
            file_info_fields, indent_level=cls.GRID_ITEM_FIELDS_INDENT_LEVEL
        )
        return file_info_fields_block

    @classmethod
    def _create_footer_block(cls, datasource_links):
        # indent links one level from the dropdown directive in template
        datasource_links = _indent_multi_line_string(datasource_links, indent_level=1)
        footer_block = cls._format_and_indent_from_template(
            datasource_links,
            template=cls.footer_template,
            indent_level=cls.HEADER_FOOTER_INDENT_LEVEL,
        )
        return footer_block


class DatasetPropsGenerator:
    """Static class to generate rst for dataset properties collected by a dataset loader.

    This class is purely static and is only useful to separate rst generation from the
    dataset loader from all other rst generation.
    """

    @staticmethod
    def generate_file_size(loader: _dataset_loader._FileProps):
        return '``' + loader.total_size + '``'

    @staticmethod
    def generate_num_files(loader: _dataset_loader._FileProps):
        return '``' + str(loader.num_files) + '``'

    @staticmethod
    def generate_file_ext(loader: _dataset_loader._FileProps):
        # Format extension as single str with rst backticks
        # Multiple extensions are comma-separated
        file_ext = loader.unique_extension
        file_ext = [file_ext] if isinstance(file_ext, str) else file_ext
        file_ext = '\n'.join(['``\'' + ext + '\'``' for ext in file_ext])
        return file_ext

    @staticmethod
    def generate_reader_type(loader: _dataset_loader._FileProps):
        """Format reader type(s) with doc references to reader class(es)."""
        reader_type = loader.unique_reader_type
        if reader_type is None:
            return "``None``"
        else:
            reader_type = (
                repr(loader.unique_reader_type)
                .replace('<class \'', ':class:`~')
                .replace('\'>', '`')
                .replace('(', '')
                .replace(')', '')
            ).replace(', ', '\n')
        return reader_type

    @staticmethod
    def generate_dataset_type(loader: _dataset_loader._FileProps):
        """Format dataset type(s) with doc references to dataset class(es)."""
        dataset_type = (
            repr(loader.unique_dataset_type)
            .replace('<class \'', ':class:`~')
            .replace('\'>', '`')
            .replace('(', '')
            .replace(')', '')
        ).replace(', ', '\n')
        return dataset_type

    @staticmethod
    def _generate_dataset_repr(loader: _dataset_loader._FileProps, indent_level: int) -> str:
        """Format the dataset's representation as a single multi-line string.

        The returned string is indented up to the specified indent level.
        """
        # Replace any hex code memory addresses with ellipses
        dataset_repr = repr(loader.dataset)
        dataset_repr = re.sub(
            pattern=r'0x[0-9a-f]*',
            repl='...',
            string=dataset_repr,
        )
        return _indent_multi_line_string(dataset_repr, indent_size=3, indent_level=indent_level)

    @staticmethod
    def generate_datasource_links(loader: _dataset_loader._Downloadable) -> str:
        def _rst_link(name, url):
            return f'`{name} <{url}>`_'

        # Collect url names and links as sequences
        names = [name] if isinstance(name := loader.source_name, str) else name
        urls = [url] if isinstance(url := loader.source_url_blob, str) else url

        # Use dict to create an ordered set to make sure links are unique
        url_dict = {}
        for name, url in zip(names, urls):
            url_dict[url] = name

        rst_links = [_rst_link(name, url) for url, name in url_dict.items()]
        rst_links = '\n'.join(rst_links)
        return rst_links

    @staticmethod
    def generate_n_cells(loader):
        return DatasetPropsGenerator._generate_num(
            DatasetPropsGenerator._try_getattr(loader.dataset, 'n_cells'), fmt='spaced'
        )

    @staticmethod
    def generate_n_points(loader):
        return DatasetPropsGenerator._generate_num(
            DatasetPropsGenerator._try_getattr(loader.dataset, 'n_points'), fmt='spaced'
        )

    @staticmethod
    def generate_length(loader):
        return DatasetPropsGenerator._generate_num(
            DatasetPropsGenerator._try_getattr(loader.dataset, 'length'), fmt='exp'
        )

    @staticmethod
    def generate_dimensions(loader):
        return DatasetPropsGenerator._generate_num(
            DatasetPropsGenerator._try_getattr(loader.dataset, 'dimensions')
        )

    @staticmethod
    def generate_spacing(loader):
        return DatasetPropsGenerator._generate_num(
            DatasetPropsGenerator._try_getattr(loader.dataset, 'spacing')
        )

    @staticmethod
    def generate_n_arrays(loader):
        return DatasetPropsGenerator._generate_num(
            DatasetPropsGenerator._try_getattr(loader.dataset, 'n_arrays')
        )

    @staticmethod
    def _try_getattr(dataset, attr: str):
        try:
            return getattr(dataset, attr)
        except AttributeError:
            return None

    @staticmethod
    def _generate_num(num: Optional[float], fmt: Literal['exp', 'spaced'] = None):
        if num is None:
            return None
        if fmt == 'exp':
            num_fmt = f"{num:.3e}"
        elif fmt == 'spaced':
            num_fmt = f"{num:,}".replace(',', ' ')
        else:
            num_fmt = str(num)
        return f"``{num_fmt}``"


class DatasetCardFetcher:
    # Dict of all card objects
    DATASET_CARDS_OBJ: Dict[str, DatasetCard] = {}

    # Dict of generated rst cards
    DATASET_CARDS_RST_REF: Dict[str, str] = {}
    DATASET_CARDS_RST: Dict[str, str] = {}

    @classmethod
    def init_cards(cls):
        """Download and load all datasets and initialize a card objects for each dataset."""
        # Collect all `_dataset_<name>` file loaders
        module_members: Dict[str, FunctionType] = dict(inspect.getmembers(pv.examples.downloads))

        for name, item in sorted(module_members.items()):
            # Extract data set name from loader name

            if name.startswith('_dataset_') and isinstance(
                item,
                (
                    _SingleFileDownloadableLoadable,
                    _MultiFileDownloadableLoadable,
                ),
            ):
                # Make card
                dataset_name = name.replace('_dataset_', '')
                dataset_loader = item
                cls.DATASET_CARDS_OBJ[dataset_name] = DatasetCard(dataset_name, dataset_loader)

                # Load data
                try:
                    dataset_loader.download()
                    dataset_loader.load()
                except pyvista.VTKVersionError:
                    # deal with this later
                    pass

    @classmethod
    def generate(cls):
        """Generate formatted rst output for all cards."""
        for name in cls.DATASET_CARDS_OBJ:
            card, card_with_ref = cls.DATASET_CARDS_OBJ[name].generate()
            # indent one level from the carousel header directive
            cls.DATASET_CARDS_RST_REF[name] = _pad_lines(card_with_ref, pad_left='   ')
            cls.DATASET_CARDS_RST[name] = _pad_lines(card, pad_left='   ')

    @classmethod
    def add_badge_to_cards(cls, dataset_names: List[str], badge: _BaseDatasetBadge):
        """Add a single badge to all specified datasets."""
        for dataset_name in dataset_names:
            cls.DATASET_CARDS_OBJ[dataset_name].add_badge(badge)

    @classmethod
    def add_cell_badges_to_all_cards(cls):
        """Add cell type badge(s) to every dataset."""
        for card in cls.DATASET_CARDS_OBJ.values():
            for cell_type in card.loader.unique_cell_types:
                card.add_badge(CellTypeBadge(cell_type.name))

    @classmethod
    def fetch_dataset_names_by_datatype(cls, datatype) -> List[str]:
        for name, dataset_iterable in cls.fetch_all_dataset_objects():
            if datatype in [type(data) for data in dataset_iterable]:
                yield name

    @classmethod
    def fetch_all_dataset_objects(cls) -> Dict[str, Iterable[Any]]:
        for name, card in DatasetCardFetcher.DATASET_CARDS_OBJ.items():
            yield name, card.loader.dataset_iterable

    @classmethod
    def fetch_and_filter(cls, filter_func: Callable[[], bool]) -> List[str]:
        """Return dataset names where any dataset object returns 'True' for a given function."""
        dataset_names_out = {}  # Use dict as an ordered set
        for name, dataset_iterable in cls.fetch_all_dataset_objects():
            for obj in dataset_iterable:
                try:
                    keep = filter_func(obj)
                except AttributeError:
                    keep = False
                if keep:
                    dataset_names_out[name] = None
        dataset_names_out = list(dataset_names_out.keys())
        assert len(dataset_names_out) > 0, f"No datasets were matched by the filter {filter_func}."
        return dataset_names_out

    @classmethod
    def fetch_multiblock(cls, kind: Literal['hetero', 'homo', 'single']):
        dataset_names = []
        for name, dataset_objects in cls.fetch_all_dataset_objects():
            types_list = [type(obj) for obj in dataset_objects]
            if pv.MultiBlock in types_list:
                types_list.remove(pv.MultiBlock)
                num_datasets = len(types_list)
                if (
                    num_datasets == 1
                    and kind == 'single'
                    or (
                        num_datasets >= 2
                        and len(set(types_list)) == 1
                        and kind == 'homo'
                        or len(set(types_list)) > 1
                        and kind == 'hetero'
                    )
                ):
                    dataset_names.append(name)
        return dataset_names


@dataclass
class _BaseDatasetBadge:
    class SemanticColorEnum(StrEnum):
        """Enum of badge colors.
        See: https://sphinx-design.readthedocs.io/en/latest/badges_buttons.html"""

        primary = auto()
        secondary = auto()
        success = auto()
        dark = auto()

    # Name of the badge
    name: str

    # Internal reference label for the badge to link to
    ref: str = None

    @classmethod
    def __post_init__(cls):
        """Use post-init to set private variables.

        Sub classes should configure these options as required.
        """
        # Configure whether the badge should appear filled or not.
        # If False, a badge outline is shown.
        cls.filled: bool = True

        # Set the badge's color
        cls.semantic_color: _BaseDatasetBadge.SemanticColorEnum = None

    def generate(self):
        # Generate rst
        color = self.semantic_color.name
        name = self.name
        line = '-line' if hasattr(self, 'filled') and not self.filled else ''
        if self.ref:
            # the badge's bdg-ref uses :any: under the hood to find references
            # so we use _gallery to point to the explicit reference instead
            # of the carousel's rst file
            ref_name = self.ref.replace('_carousel', '_gallery')
            ref_link_rst = f' <{ref_name}>'
            bdg_ref_rst = 'ref-'
        else:
            bdg_ref_rst = ''
            ref_link_rst = ''
        return f':bdg-{bdg_ref_rst}{color}{line}:`{name}{ref_link_rst}`'


@dataclass
class ModuleBadge(_BaseDatasetBadge):
    """Badge given to a dataset based on its source module,

    e.g. 'Downloads' for datasets from `pyvista.examples.downloads`.
    """

    name: str
    ref: str

    @classmethod
    def __post_init__(cls):
        cls.semantic_color = _BaseDatasetBadge.SemanticColorEnum.primary


@dataclass
class DataTypeBadge(_BaseDatasetBadge):
    """Badge given to a dataset based strictly on its type.

    The badge name should correspond to the type of the dataset.
    e.g. 'UnstructuredGrid'.
    """

    name: str
    ref: str

    @classmethod
    def __post_init__(cls):
        cls.semantic_color = _BaseDatasetBadge.SemanticColorEnum.secondary


@dataclass
class SpecialDataTypeBadge(_BaseDatasetBadge):
    """Badge given to a dataset with special properties.

    Use this badge for specializations of data types (e.g. 2D ImageData
    as a special kind of ImageData, or Cubemap as a special kind of Texture),
    or for special classifications of datasets (e.g. point clouds).
    """

    name: str
    ref: str

    @classmethod
    def __post_init__(cls):
        cls.filled = False
        cls.semantic_color = _BaseDatasetBadge.SemanticColorEnum.secondary


@dataclass
class CategoryBadge(_BaseDatasetBadge):
    """Badge given to a dataset based on its application or use.

    e.g. 'Medical' for medical datasets.
    """

    name: str
    ref: str

    @classmethod
    def __post_init__(cls):
        cls.semantic_color = _BaseDatasetBadge.SemanticColorEnum.success


@dataclass
class CellTypeBadge(_BaseDatasetBadge):
    """Badge given to a dataset based with a specific cell type.

    e.g. 'Medical' for medical datasets.
    """

    name: str
    ref: str

    @classmethod
    def __post_init__(cls):
        cls.filled = False
        cls.semantic_color = _BaseDatasetBadge.SemanticColorEnum.dark


class DatasetGalleryCarousel(DocTable):
    # Print the doc, badges, and dataset count
    # The header defines the start of the card carousel
    header_template = _aligned_dedent(
        """
        |{}
        |
        |{}
        |:Dataset Count: ``{}``
        |
        |.. card-carousel:: 1
        |
        """
    )[1:-1]

    # Subclasses should give the carousel a name
    # The name should end with '_carousel'
    name: str = None

    # Subclasses should give the carousel a short description
    # describing the carousel's contents
    doc: str = None

    # Subclasses may optionally define a badge for the carousel
    # All datasets in the carousel will be given this badge.
    badge: _BaseDatasetBadge = None

    dataset_names: Optional[List[str]] = None

    @property
    @final
    def path(cls):
        assert isinstance(cls.name, str), 'Table name must be defined.'
        assert cls.name.endswith('_carousel'), 'Table name must end with "_carousel".'
        return f"{DATASET_GALLERY_DIR}/{cls.name}.rst"

    @classmethod
    def fetch_data(cls):
        return list(cls.dataset_names)

    @classmethod
    @abstractmethod
    def fetch_dataset_names(cls) -> List[str]:
        """Return all dataset names to include in the gallery."""

    @classmethod
    @final
    def init_dataset_names(cls):
        names = list(cls.fetch_dataset_names())
        assert names is not None, (
            f'Dataset names cannot be None, {cls.fetch_dataset_names} must return '
            f'a string iterable.'
        )
        cls.dataset_names = names

    @classmethod
    @final
    def get_header(cls, data):
        """Generate the rst for the carousel's header."""
        assert cls.name is not None, f"Carousel {cls} must have a name."
        assert cls.doc is not None, f"Carousel {cls} must have a doc string."

        badge_info = f":Section Badge: {cls.badge.generate()}" if cls.badge else ''
        num_datasets = len(data)
        assert num_datasets > 0, f"No datasets were found for carousel {cls}."
        return cls.header_template.format(cls.doc, badge_info, num_datasets)

    @classmethod
    def get_row(cls, _, dataset_name: str):
        """Generate the rst card for a given dataset.

        A standard card is returned by default. Subclasses
        should override this method to customize the card.
        """
        assert isinstance(
            dataset_name, str
        ), f"Dataset name {dataset_name} for {cls} must be a string."
        return DatasetCardFetcher.DATASET_CARDS_RST[dataset_name]


class DownloadsCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel with cards from the downloads module."""

    name = 'downloads_carousel'
    doc = 'Datasets from the :mod:`downloads <pyvista.examples.downloads>` module.'
    badge = ModuleBadge('Downloads', ref='downloads_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        return DatasetCardFetcher.DATASET_CARDS_OBJ.keys()

    @classmethod
    def get_row(cls, _, dataset_name):
        # Override method since we want to include a reference label for each card
        return DatasetCardFetcher.DATASET_CARDS_RST_REF[dataset_name]


class BuiltinCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel with cards for built-in datasets."""

    # TODO: add builtin datasets
    name = 'builtin_carousel'
    doc = 'Built-in datasets that ship with pyvista. Available through :mod:`examples <pyvista.examples.examples>` module.'
    badge = ModuleBadge('Built-in', ref='builtins_gallery')


class PlanetsCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel with cards from the planets module."""

    # TODO: add planets datasets
    name = 'planets_carousel'
    doc = 'Datasets from the :mod:`planets <pyvista.examples.planets>` module.'
    badge = ModuleBadge('Planets', ref='planets_gallery')


class PointSetCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of PointSet cards."""

    name = 'pointset_carousel'
    doc = ':class:`~pyvista.PointSet` datasets.'
    badge = DataTypeBadge('PointSet', ref='pointset_datatype_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        return DatasetCardFetcher.fetch_dataset_names_by_datatype(pv.PointSet)


class PolyDataCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of PolyData cards."""

    name = 'polydata_carousel'
    doc = ':class:`~pyvista.PolyData` datasets.'
    badge = DataTypeBadge('PolyData', ref='pointset_datatype_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        return DatasetCardFetcher.fetch_dataset_names_by_datatype(pv.PolyData)


class UnstructuredGridCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of UnstructuredGrid cards."""

    name = 'unstructuredgrid_carousel'
    doc = ':class:`~pyvista.UnstructuredGrid` datasets.'
    badge = DataTypeBadge('UnstructuredGrid', ref='pointset_datatype_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        return DatasetCardFetcher.fetch_dataset_names_by_datatype(pv.UnstructuredGrid)


class StructuredGridCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of StructuredGrid cards."""

    name = 'structuredgrid_carousel'
    doc = ':class:`~pyvista.StructuredGrid` datasets.'
    badge = DataTypeBadge('StructuredGrid', ref='pointset_datatype_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        return DatasetCardFetcher.fetch_dataset_names_by_datatype(pv.StructuredGrid)


class ExplicitStructuredGridCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of ExplicitStructuredGrid cards."""

    name = 'explicitstructuredgrid_carousel'
    doc = ':class:`~pyvista.ExplicitStructuredGrid` datasets.'
    badge = DataTypeBadge('ExplicitStructuredGrid', ref='pointset_datatype_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        return DatasetCardFetcher.fetch_dataset_names_by_datatype(pv.ExplicitStructuredGrid)


class PointCloudCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of point cloud cards."""

    name = 'pointcloud_carousel'
    doc = 'Datasets represented as points in space. May be :class:`~pyvista.PointSet` or :class:`~pyvista.PolyData` with :any:`VERTEX<pyvista.CellType.VERTEX>` cells.'
    badge = SpecialDataTypeBadge('Point Cloud', ref='pointcloud_surfacemesh_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        pointset_names = DatasetCardFetcher.fetch_dataset_names_by_datatype(pv.PointSet)
        vertex_polydata_filter = (
            lambda poly: isinstance(poly, pv.PolyData) and poly.n_verts == poly.n_cells
        )
        vertex_polydata_names = DatasetCardFetcher.fetch_and_filter(vertex_polydata_filter)
        return sorted(list(pointset_names) + list(vertex_polydata_names))


class SurfaceMeshCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of surface mesh cards."""

    name = 'surfacemesh_carousel'
    doc = ':class:`~pyvista.PolyData` surface meshes.'
    badge = SpecialDataTypeBadge('Surface Mesh', ref='pointcloud_surfacemesh_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        surface_polydata_filter = (
            lambda poly: isinstance(poly, pv.PolyData)
            and (poly.n_cells - poly.n_verts - poly.n_lines) > 0
        )
        surface_polydata_names = DatasetCardFetcher.fetch_and_filter(surface_polydata_filter)
        return sorted(surface_polydata_names)


class RectilinearGridCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of RectilinearGrid cards."""

    name = 'rectilineargrid_carousel'
    doc = ':class:`~pyvista.RectilinearGrid` datasets.'
    badge = DataTypeBadge('RectilinearGrid', ref='grid_datatype_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        return DatasetCardFetcher.fetch_dataset_names_by_datatype(pv.RectilinearGrid)


class ImageDataCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of ImageData cards."""

    name = 'imagedata_carousel'
    doc = ':class:`~pyvista.ImageData` datasets.'
    badge = DataTypeBadge('ImageData', ref='grid_datatype_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        return DatasetCardFetcher.fetch_dataset_names_by_datatype(pv.ImageData)


class ImageData3DCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of 3D ImageData cards."""

    name = 'imagedata_3d_carousel'
    doc = 'Three-dimensional volumetric :class:`~pyvista.ImageData` datasets.'
    badge = SpecialDataTypeBadge('3D Volume', ref='imagedata_texture_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        image_3d_filter = lambda img: isinstance(img, pv.ImageData) and not np.any(
            np.array(img.dimensions) == 1
        )
        return DatasetCardFetcher.fetch_and_filter(image_3d_filter)


class ImageData2DCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of 2D ImageData cards."""

    name = 'imagedata_2d_carousel'
    doc = 'Two-dimensional :class:`~pyvista.ImageData` datasets.'
    badge = SpecialDataTypeBadge('2D Image', ref='imagedata_texture_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        image_2d_filter = lambda img: isinstance(img, pv.ImageData) and np.any(
            np.array(img.dimensions) == 1
        )
        return DatasetCardFetcher.fetch_and_filter(image_2d_filter)


class TextureCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of all Texture cards."""

    name = 'texture_carousel'
    doc = ':class:`~pyvista.Texture` datasets.'
    badge = DataTypeBadge('Texture', ref='imagedata_texture_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        return DatasetCardFetcher.fetch_dataset_names_by_datatype(pv.Texture)


class CubemapCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of cubemap cards."""

    name = 'cubemap_carousel'
    doc = ':class:`~pyvista.Texture` datasets with six images: one for each side of the cube.'
    badge = SpecialDataTypeBadge('Cubemap', ref='imagedata_texture_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        cube_map_filter = lambda cubemap: isinstance(cubemap, pv.Texture) and cubemap.cube_map
        return DatasetCardFetcher.fetch_and_filter(cube_map_filter)


class MultiBlockCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of MultiBlock dataset cards."""

    name = 'multiblock_carousel'
    doc = ':class:`~pyvista.MultiBlock` datasets.'
    badge = DataTypeBadge('MultiBlock', ref='composite_dataset_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        return DatasetCardFetcher.fetch_dataset_names_by_datatype(pv.MultiBlock)


class MultiBlockHeteroCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of heterogeneous MultiBlock dataset cards."""

    name = 'multiblock_hetero_carousel'
    doc = ':class:`~pyvista.MultiBlock` datasets with multiple blocks of different mesh types.'
    badge = SpecialDataTypeBadge('Heterogeneous', ref='composite_dataset_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        return DatasetCardFetcher.fetch_multiblock('hetero')


class MultiBlockHomoCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of homogeneous MultiBlock dataset cards."""

    name = 'multiblock_homo_carousel'
    doc = ':class:`~pyvista.MultiBlock` datasets with multiple blocks of the same mesh type.'
    badge = SpecialDataTypeBadge('Homogeneous', ref='composite_dataset_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        return DatasetCardFetcher.fetch_multiblock('homo')


class MultiBlockSingleCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of MultiBlock dataset cards which contain a single mesh."""

    name = 'multiblock_single_carousel'
    doc = ':class:`~pyvista.MultiBlock` datasets which contain a single mesh.'
    badge = SpecialDataTypeBadge('Single Block', ref='composite_dataset_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        return DatasetCardFetcher.fetch_multiblock('single')


class MiscCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of misc dataset cards."""

    name = 'misc_carousel'
    doc = 'Datasets which have a non-standard representation.'
    badge = DataTypeBadge('Misc', ref='misc_dataset_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        misc_dataset_filter = lambda obj: not isinstance(
            obj, (pv.MultiBlock, pv.Texture, pv.DataSet)
        )
        return DatasetCardFetcher.fetch_and_filter(misc_dataset_filter)


class MedicalCarousel(DatasetGalleryCarousel):
    """Class to generate a carousel of medical dataset cards."""

    name = 'medical_carousel'
    doc = 'Medical datasets.'
    badge = CategoryBadge('Medical', ref='medical_dataset_gallery')

    @classmethod
    def fetch_dataset_names(cls):
        return sorted(
            (
                'brain',
                'brain_atlas_with_sides',
                'chest',
                'carotid',
                'dicom_stack',
                'embryo',
                'foot_bones',
                'frog',
                'frog_tissue',
                'head',
                'head_2',
                'knee',
                'knee_full',
                'prostate',
            )
        )


def make_all_carousels(carousels: List[DatasetGalleryCarousel]):
    # Load datasets and create card objects
    DatasetCardFetcher.init_cards()

    # Create lists of dataset names for each carousel
    [carousel.init_dataset_names() for carousel in carousels]

    # Add carousel badges to cards
    [
        DatasetCardFetcher.add_badge_to_cards(carousel.dataset_names, carousel.badge)
        for carousel in carousels
    ]
    # Add celltype badges to cards
    DatasetCardFetcher.add_cell_badges_to_all_cards()

    # Generate rst for all card objects
    DatasetCardFetcher.generate()

    # Generate rst for all carousels
    [carousel.generate() for carousel in carousels]


CAROUSEL_LIST = [
    DownloadsCarousel,
    PointSetCarousel,
    PolyDataCarousel,
    UnstructuredGridCarousel,
    StructuredGridCarousel,
    # TODO: There is no dataset of this type yet.
    #  Add new dataset and uncomment this line
    # ExplicitStructuredGridCarousel,
    PointCloudCarousel,
    SurfaceMeshCarousel,
    RectilinearGridCarousel,
    ImageDataCarousel,
    ImageData3DCarousel,
    ImageData2DCarousel,
    TextureCarousel,
    CubemapCarousel,
    MultiBlockCarousel,
    MultiBlockHomoCarousel,
    MultiBlockHeteroCarousel,
    MultiBlockSingleCarousel,
    MiscCarousel,
    MedicalCarousel,
]


def make_all_tables():
    # Make color and chart tables
    os.makedirs(CHARTS_IMAGE_DIR, exist_ok=True)
    LineStyleTable.generate()
    MarkerStyleTable.generate()
    ColorSchemeTable.generate()
    ColorTable.generate()

    # Make dataset gallery carousels
    os.makedirs(DATASET_GALLERY_DIR, exist_ok=True)
    make_all_carousels(CAROUSEL_LIST)

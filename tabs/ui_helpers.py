from gui.widgets import PyLineEdit, PyPushButton, PyTableWidget
from gui.core.functions import Functions
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidgetItem


DARK_ONE = "#1b1e23"
DARK_TWO = "#252a33"
DARK_THREE = "#303744"
DARK_FOUR = "#3a4554"
TEXT = "#dce1ec"
MUTED = "#8a95aa"
CONTEXT = "#568af2"


def make_button(text, parent=None, danger=False):
    button = PyPushButton(
        text=text,
        radius=8,
        color="#ffffff" if danger else TEXT,
        bg_color="#7d2d35" if danger else DARK_TWO,
        bg_color_hover="#a43b46" if danger else DARK_THREE,
        bg_color_pressed="#c24b57" if danger else DARK_FOUR,
        parent=parent,
    )
    button.setIcon(QIcon(Functions.set_svg_icon("icon_send.svg")))
    return button


def make_line_edit(placeholder="", parent=None):
    line_edit = PyLineEdit(
        place_holder_text=placeholder,
        color=TEXT,
        selection_color="#ffffff",
        bg_color=DARK_ONE,
        bg_color_active=DARK_TWO,
        context_color=CONTEXT,
    )
    if parent is not None:
        line_edit.setParent(parent)
    return line_edit


def make_table(rows=0, columns=0, parent=None):
    table = PyTableWidget(
        radius=8,
        color=TEXT,
        selection_color=CONTEXT,
        bg_color=DARK_TWO,
        header_horizontal_color=DARK_ONE,
        header_vertical_color=DARK_THREE,
        bottom_line_color=DARK_THREE,
        grid_line_color=DARK_ONE,
        scroll_bar_bg_color=DARK_ONE,
        scroll_bar_btn_color=DARK_FOUR,
        context_color=CONTEXT,
    )
    if parent is not None:
        table.setParent(parent)
    table.setRowCount(rows)
    table.setColumnCount(columns)
    table.setSortingEnabled(False)
    table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
    table.setUpdatesEnabled(False)
    table.setUpdatesEnabled(True)
    return table


def update_table(table, rows, columns, values):
    table.setUpdatesEnabled(False)
    table.setSortingEnabled(False)
    table.setColumnCount(columns)
    table.setRowCount(rows)
    for row, row_values in enumerate(values):
        for column, value in enumerate(row_values):
            item = table.item(row, column)
            text = str(value)
            if item is None:
                table.setItem(row, column, QTableWidgetItem(text))
            elif item.text() != text:
                item.setText(text)
    table.setUpdatesEnabled(True)
    table.viewport().update()

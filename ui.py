import curses
import curses.textpad
import os


class Message:
    def __init__(self, time=None, name=None, text=None):
        self.time = time
        self.name = name
        self.text = text


class Layout:
    TITLE_ROWS = 1
    PROMPT_ROWS = 1

    def __init__(self):
        "Determine the terminal size, and size of each window"

        # Get terminal size
        self.rows, self.cols = Layout.terminal_size()

        # Calculate dimensions of each window
        self.title_rows = Layout.TITLE_ROWS
        self.title_cols = self.cols
        self.title_start_row = 0
        self.title_start_col = 0

        self.history_rows = self.rows - Layout.TITLE_ROWS - Layout.PROMPT_ROWS
        self.history_cols = self.cols
        self.history_start_row = 1
        self.history_start_col = 0

        self.prompt_rows = Layout.PROMPT_ROWS
        self.prompt_cols = self.cols
        self.prompt_start_row = self.rows - 1
        self.prompt_start_col = 0

    @staticmethod
    def terminal_size():
        "Return the current terminal size, as a tuple of (rows, cols)"
        rows, cols = os.popen('stty size', 'r').read().split()
        return (int(rows), int(cols))


# ==============================================================================
# This just displays the title
# ==============================================================================

class Title:
    def __init__(self, layout, screen):
        self.window = curses.newwin(layout.title_rows, layout.title_cols,
                                    layout.title_start_row, layout.title_start_col)
        start_col = (layout.title_cols - len("чят хуесосов")) // 2
        self.window.addstr(0, start_col, "чят хуесосов", curses.A_BOLD)

    def redraw(self):
        self.window.refresh()


# ==============================================================================
# The History class displays the chat history.
# ==============================================================================

class History:
    def __init__(self, layout, screen):
        self.messages = []
        self.layout = layout
        self.screen = screen
        self.window = curses.newwin(layout.history_rows, layout.history_cols,
                                    layout.history_start_row, layout.history_start_col)
        self.visible_rows = self.layout.history_rows - 2
        self.visible_cols = self.layout.history_cols - 2

    def append(self, msg):
        self.messages.append(msg)

    def redraw(self):
        self.window.clear()
        self.window.border(0)

        row = 1
        for msg in self.messages[-self.visible_rows:]:
            self.window.move(row, 1)
            time = "[%02d:%02d] " % (msg.time.hour, msg.time.minute)
            self.window.addstr(time, curses.A_BOLD)
            self.window.addstr(msg.name + ': ', curses.A_BOLD)
            self.window.addstr(msg.text)
            row += 1

        self.window.refresh()


class Prompt:
    def __init__(self, layout, screen):
        self.layout = layout
        self.screen = screen
        self.window = curses.newwin(layout.prompt_rows, layout.prompt_cols,
                                    layout.prompt_start_row, layout.prompt_start_col)
        self.window.keypad(1)
        self.window.addstr('> ')

    def getchar(self):
        return self.window.getch()

    def getstr(self):
        return self.window.getstr()

    def redraw(self):
        self.window.refresh()

    def reset(self):
        self.window.clear()
        self.window.addstr('> ')
        self.redraw()

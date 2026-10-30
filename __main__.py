from tkinter import Tk, messagebox

from utils.logging_setup import configure_logging
from MusicBox import MusicBox


logger = configure_logging()


def run():
    try:
        logger.info('Starting Music Box')
        root = Tk()
        MusicBox(root)
        root.mainloop()
    except Exception:
        logger.exception('Unhandled application error')
        try:
            root = Tk()
            root.withdraw()
            messagebox.showerror(
                'Error',
                'An unexpected error occurred. See logs/music_box.log for details.',
            )
            root.destroy()
        except Exception:
            logger.exception('Unable to display the application error dialog')


if __name__ == '__main__':
    run()

import traceback
from tkinter import Tk, messagebox

from main import MusicBox


def run():
    try:
        root = Tk()
        MusicBox(root)
        root.mainloop()
    except Exception:
        try:
            with open('error_log.txt', 'w', encoding='utf-8') as error_file:
                error_file.write(traceback.format_exc())
            root = Tk()
            root.withdraw()
            messagebox.showerror(
                'Error',
                'An unexpected error occurred. See error_log.txt for details.',
            )
            root.destroy()
        except Exception:
            pass


if __name__ == '__main__':
    run()

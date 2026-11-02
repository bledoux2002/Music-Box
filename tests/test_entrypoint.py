import importlib.util
from pathlib import Path
from unittest.mock import Mock

ENTRYPOINT_PATH = Path(__file__).parents[1] / '__main__.py'
SPEC = importlib.util.spec_from_file_location('music_box_entrypoint', ENTRYPOINT_PATH)
entrypoint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(entrypoint)


def test_run_starts_application(monkeypatch):
    root = Mock()
    app = Mock()
    monkeypatch.setattr(entrypoint, 'Tk', Mock(return_value=root))
    monkeypatch.setattr(entrypoint, 'MusicBox', Mock(return_value=app))

    entrypoint.run()

    entrypoint.MusicBox.assert_called_once_with(root)
    root.mainloop.assert_called_once_with()


def test_run_logs_and_displays_startup_errors(monkeypatch):
    root = Mock()
    failed_app = RuntimeError('startup failed')
    monkeypatch.setattr(entrypoint, 'Tk', Mock(side_effect=[root, root]))
    monkeypatch.setattr(entrypoint, 'MusicBox', Mock(side_effect=failed_app))
    monkeypatch.setattr(entrypoint.messagebox, 'showerror', Mock())

    entrypoint.run()

    entrypoint.messagebox.showerror.assert_called_once()
    root.withdraw.assert_called_once_with()
    root.destroy.assert_called_once_with()

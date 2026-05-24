"""主题偏好读写。"""

import json

from src.ui.theme import ThemeController, load_appearance, save_appearance


def test_appearance_roundtrip(tmp_path, monkeypatch) -> None:
    settings = tmp_path / "settings.json"
    monkeypatch.setattr("src.ui.theme.SETTINGS_PATH", settings)

    save_appearance("light")
    assert load_appearance() == "light"

    save_appearance("dark")
    assert load_appearance() == "dark"

    settings.write_text('{"appearance": "light"}', encoding="utf-8")
    assert load_appearance() == "light"


def test_theme_controller_toggle(monkeypatch) -> None:
    monkeypatch.setattr("src.ui.theme._controller", None)
    ctrl = ThemeController("dark")
    assert ctrl.is_dark()
    ctrl.toggle()
    assert not ctrl.is_dark()
    assert ctrl.colors()["bg_primary"] == "#FFFFFF"

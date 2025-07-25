import os
import json
import builtins
import getpass
import types
import pytest

import utils
import auth
import selenium.webdriver as webdriver

VALID_URL_DETAILS = "https://cards.ucalgary.ca/details/1261?bag_id=151"
VALID_URL_COLLECTION = "https://cards.ucalgary.ca/collection/150"
INVALID_URLS = [
    "https://cards.ucalgary.ca/",
    "asdasdsadsa",
    "https://cards.ucalgary.ccom",
    "https://cards.ucalgary.ca/details/",
    "https://cards.ucalgary.ca/details/test123?bag_id=test123",
    "https://cards.ucalgary.ca/collection/",
    "https://cards.ucalgary.ca/collection/test123",
]


class DummyChrome:
    def __init__(self, options=None):
        pass

    def quit(self):
        pass

    def execute_cdp_cmd(self, cmd, params=None):
        pass


def make_inputs(values):
    values_iter = iter(values)
    return lambda prompt="": next(values_iter)


def setup_common_patches(monkeypatch, tmp_path, inputs, fake_login_side_effects):
    config = tmp_path / "config.json"
    monkeypatch.setattr(utils, "CONFIG_PATH", str(config))
    monkeypatch.setattr(utils, "HAS_GUI", False)
    monkeypatch.setattr(utils, "get_chrome_options", lambda: None)
    monkeypatch.setattr(utils, "setup_driver_print_override", lambda d: d)
    monkeypatch.setattr(webdriver, "Chrome", DummyChrome)

    def fake_login(driver, email, password, base_host, target_url=None):
        effect = fake_login_side_effects.pop(0)
        if isinstance(effect, Exception):
            raise effect
        return effect

    monkeypatch.setattr(auth, "selenium_login", fake_login)
    monkeypatch.setattr(builtins, "input", make_inputs(inputs))
    monkeypatch.setattr(getpass, "getpass", lambda prompt="": "secretpw")
    return config


def load_config(path):
    with open(path) as f:
        return json.load(f)


def test_first_time_login_saves_credentials(monkeypatch, tmp_path):
    inputs = [VALID_URL_DETAILS, "user@example.com", "y"]
    effects = [None]
    config = setup_common_patches(monkeypatch, tmp_path, inputs, effects)

    email, password, url = utils.prompt_url_and_credentials_with_url()
    assert email == "user@example.com"
    assert password == "secretpw"
    assert url == VALID_URL_DETAILS
    assert os.path.exists(config)
    data = load_config(config)
    assert data["email"] == "user@example.com"
    assert data["password"] == "secretpw"


def test_invalid_url_and_credentials(monkeypatch, tmp_path):
    inputs = [
        INVALID_URLS[0],
        "user@example.com",
        "y",
        INVALID_URLS[1],
        "user@example.com",
        "y",
        INVALID_URLS[2],
        "user@example.com",
        "y",
    ]
    effects = [RuntimeError("Login failed – check credentials")] * 3
    config = setup_common_patches(monkeypatch, tmp_path, inputs, effects)

    with pytest.raises(SystemExit):
        utils.prompt_url_and_credentials_with_url()
    assert not os.path.exists(config)


def test_valid_url_invalid_credentials(monkeypatch, tmp_path):
    inputs = [
        VALID_URL_COLLECTION,
        "user@example.com",
        "y",
        VALID_URL_COLLECTION,
        "user@example.com",
        "y",
        VALID_URL_COLLECTION,
        "user@example.com",
        "y",
    ]
    effects = [RuntimeError("Login failed – check credentials")] * 3
    config = setup_common_patches(monkeypatch, tmp_path, inputs, effects)

    with pytest.raises(SystemExit):
        utils.prompt_url_and_credentials_with_url()
    assert not os.path.exists(config)


def test_invalid_url_then_valid(monkeypatch, tmp_path):
    inputs = [
        INVALID_URLS[4],
        "user@example.com",
        "y",
        VALID_URL_COLLECTION,
    ]
    effects = [RuntimeError("URL/Network error"), None]
    config = setup_common_patches(monkeypatch, tmp_path, inputs, effects)

    email, password, url = utils.prompt_url_and_credentials_with_url()
    assert url == VALID_URL_COLLECTION
    assert os.path.exists(config)
    data = load_config(config)
    assert data["email"] == "user@example.com"


def test_invalid_urls_preserve_credentials(monkeypatch, tmp_path):
    inputs = [
        INVALID_URLS[3],
        "user@example.com",
        "y",
        INVALID_URLS[5],
        INVALID_URLS[6],
    ]
    effects = [RuntimeError("URL/Network error")] * 3
    config = setup_common_patches(monkeypatch, tmp_path, inputs, effects)

    with pytest.raises(SystemExit):
        utils.prompt_url_and_credentials_with_url()
    assert os.path.exists(config)
    data = load_config(config)
    assert data["email"] == "user@example.com"


def test_second_run_uses_saved_credentials(monkeypatch, tmp_path):
    config = tmp_path / "config.json"
    with open(config, "w") as f:
        json.dump({"email": "user@example.com", "password": "secretpw"}, f)

    inputs = [INVALID_URLS[0], VALID_URL_DETAILS]
    effects = [RuntimeError("URL/Network error"), None]

    monkeypatch.setattr(utils, "CONFIG_PATH", str(config))
    monkeypatch.setattr(utils, "HAS_GUI", False)
    monkeypatch.setattr(utils, "get_chrome_options", lambda: None)
    monkeypatch.setattr(utils, "setup_driver_print_override", lambda d: d)
    monkeypatch.setattr(webdriver, "Chrome", DummyChrome)

    def fake_login(driver, email, password, base_host, target_url=None):
        effect = effects.pop(0)
        if isinstance(effect, Exception):
            raise effect
        return effect

    monkeypatch.setattr(auth, "selenium_login", fake_login)
    monkeypatch.setattr(builtins, "input", make_inputs(inputs))

    url = utils.prompt_url_with_validation("user@example.com", "secretpw")
    assert url == VALID_URL_DETAILS
    data = load_config(config)
    assert data["email"] == "user@example.com"

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def test_app_runs_against_bundled_sample_data_with_no_exception():
    at = AppTest.from_file(APP_PATH)
    at.run()

    assert not at.exception

    assert at.metric[0].value == "50"
    assert at.metric[1].value == "6"
    assert at.metric[2].value == "9"

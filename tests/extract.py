from dualsrt.extract import find_subtitles, extract_subtitle_tracks
from pathlib import Path


TEST_DATA = Path(__file__).parent.parent / "testdata"


def test_find_subtitles_f1():
    input_file = TEST_DATA / "f1.mkv"
    subs = find_subtitles(input_file, ("eng", "rus"))
    assert len(subs["eng"]) == 1
    assert subs["eng"][0]["index"] == 15
    assert len(subs["rus"]) == 1
    assert subs["rus"][0]["index"] == 13


def test_find_subtitles_f2():
    input_file = TEST_DATA / "f2.m4v"
    subs = find_subtitles(input_file, ("eng", "rus"))
    assert len(subs["eng"]) == 1
    assert subs["eng"][0]["index"] == 6
    assert len(subs["rus"]) == 1
    assert subs["rus"][0]["index"] == 5


def test_find_subtitles_f3():
    input_file = TEST_DATA / "f3.mkv"
    subs = find_subtitles(input_file, ("eng", "rus"))
    assert len(subs["eng"]) == 1
    assert subs["eng"][0]["index"] == 5
    assert len(subs["rus"]) == 1
    assert subs["rus"][0]["index"] == 4


def test_find_subtitles_f4():
    input_file = TEST_DATA / "f4.mkv"
    subs = find_subtitles(input_file, ("eng", "rus"))
    assert len(subs["eng"]) == 1
    assert subs["eng"][0]["index"] == 17
    assert len(subs["rus"]) == 5
    assert subs["rus"][0]["index"] == 10


def test_extract_english_track_f1():
    input_file = TEST_DATA / "f1.mkv"
    subs = extract_subtitle_tracks(input_file, 15, 13)

    assert subs

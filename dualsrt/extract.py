from tempfile import TemporaryDirectory

import ffmpeg
from pathlib import Path


def find_subtitles(
        file: Path,
        languages,
        skip_forced=True,
        skip_commentary=True,
        drop_redundant_sdh=True,
):
    subtitles = {language: [] for language in languages}
    probe = ffmpeg.probe(file, select_streams="s")
    for stream in probe["streams"]:
        stream_language = stream["tags"]["language"]
        if stream_language in subtitles:
            title = stream["tags"].get("title", "").lower()
            if skip_forced and "forc" in title:
                continue
            if skip_commentary and "comm" in title:
                continue
            subtitles[stream_language].append(stream)
    if drop_redundant_sdh:
        subtitles = {
            lang: [s for s in subs if "sdh" not in s["tags"].get("title", "").lower()]
            for lang, subs in subtitles.items()
        }

    return subtitles


def extract_subtitle_tracks(file: Path, *tracks: int) -> dict[int, str]:
    with TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        subs = [(track, tmp_dir / f"{track}.srt") for track in tracks]

        stream = ffmpeg.input(file)
        outputs = [stream.output(str(sub), map=f"0:{track}") for track, sub in subs]
        ffmpeg.merge_outputs(*outputs).run()

        return {track: sub.read_text() for track, sub in subs}


TEST_DATA = Path(__file__).parent.parent / "testdata"


def test_find_subtitles_f1():
    input_file = TEST_DATA / "f1.mkv"
    subs = find_subtitles(input_file, ('eng', 'rus'))
    assert len(subs['eng']) == 1
    assert subs['eng'][0]['index'] == 15
    assert len(subs['rus']) == 1
    assert subs['rus'][0]['index'] == 13


def test_find_subtitles_f2():
    input_file = TEST_DATA / "f2.m4v"
    subs = find_subtitles(input_file, ('eng', 'rus'))
    assert len(subs['eng']) == 1
    assert subs['eng'][0]['index'] == 6
    assert len(subs['rus']) == 1
    assert subs['rus'][0]['index'] == 5


def test_find_subtitles_f3():
    input_file = TEST_DATA / "f3.mkv"
    subs = find_subtitles(input_file, ('eng', 'rus'))
    assert len(subs['eng']) == 1
    assert subs['eng'][0]['index'] == 5
    assert len(subs['rus']) == 1
    assert subs['rus'][0]['index'] == 4


def test_find_subtitles_f4():
    input_file = TEST_DATA / "f4.mkv"
    subs = find_subtitles(input_file, ('eng', 'rus'))
    assert len(subs['eng']) == 1
    assert subs['eng'][0]['index'] == 17
    assert len(subs['rus']) == 5
    assert subs['rus'][0]['index'] == 10


def test_extract_english_track_f1():
    input_file = TEST_DATA / "f1.mkv"
    subs = extract_subtitle_tracks(input_file, 15, 13)

    assert subs

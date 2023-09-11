from pathlib import Path
import sys
import srt
from .mux import dual_subtitles
from .extract import find_subtitles, extract_subtitle_tracks
from itertools import product


def produce_dual_subtitles(video: Path, primary_lang: str, secondary_lang: str):
    subtitle_tracks = find_subtitles(video, (primary_lang, secondary_lang))
    all_tracks = [s['index'] for lang in subtitle_tracks.values() for s in lang]
    all_subs = extract_subtitle_tracks(video, *all_tracks)
    for idx, combination in enumerate(product(*subtitle_tracks.values())):
        tracks = {t['tags']["language"]: t['index'] for t in combination}
        subs = all_subs[tracks[primary_lang]], all_subs[tracks[secondary_lang]]
        subs = [srt.parse(sub) for sub in subs]
        dual = dual_subtitles(*subs)
        dual_file = video.parent / f"{video.stem}.{primary_lang}.{idx}.srt"
        dual_file.write_text(srt.compose(dual))
    return 1


def main():
    video = Path(sys.argv[1])
    produce_dual_subtitles(video, "eng", "rus")
    return 0


TEST_DATA = Path(__file__).parent.parent / "testdata"


def test_produce_dual_subtitles():
    produce_dual_subtitles(TEST_DATA / "f1.mkv", "eng", "rus")

from pathlib import Path
import sys
import srt
from .mux import dual_subtitles
from .extract import find_subtitles, extract_subtitle_tracks
from itertools import product
from re import sub


def produce_dual_subtitles(video: Path, primary_lang: str, secondary_lang: str):
    subtitle_tracks = find_subtitles(video, (primary_lang, secondary_lang))
    all_tracks = [s["index"] for lang in subtitle_tracks.values() for s in lang]
    all_subs = extract_subtitle_tracks(video, *all_tracks)
    combos = product(subtitle_tracks[primary_lang], subtitle_tracks[secondary_lang])
    for primary, secondary in combos:
        subs = all_subs[primary["index"]], all_subs[secondary["index"]]
        dual = dual_subtitles(*(srt.parse(s) for s in subs))
        t1 = primary["tags"].get("title") or primary["tags"]["language"]
        t2 = secondary["tags"].get("title") or secondary["tags"]["language"]
        sfx = "_".join(sub(r"[^0-9a-z]+", "_", t.lower()) for t in (t1, t2))
        dual_file = video.parent / f"{video.stem}.{primary_lang}.{sfx}.srt"
        dual_file.write_text(srt.compose(dual))
    return 1


def main():
    video = Path(sys.argv[1])
    produce_dual_subtitles(video, "eng", "rus")
    return 0


TEST_DATA = Path(__file__).parent.parent / "testdata"


def test_produce_dual_subtitles():
    produce_dual_subtitles(TEST_DATA / "f1.mkv", "eng", "rus")

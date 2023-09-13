from pathlib import Path
import srt
from .mux import dual_subtitles
from .extract import find_subtitles, extract_subtitle_tracks
from itertools import product
from re import sub
from argparse import ArgumentParser, ArgumentTypeError


def existing_file_path(path_str):
    path = Path(path_str)
    if not path.is_file():
        raise ArgumentTypeError(f"file {path_str} does not exist")
    else:
        return path


def font_attributes(text):
    pairs = [entry.split(":") for entry in text.split(",") if entry]
    attributes = {attr: value for attr, value in pairs}
    unknown_attributes = attributes.keys() - {"size", "color"}
    if unknown_attributes:
        raise ArgumentTypeError(f"unknown attribute(s) {unknown_attributes}")
    else:
        return attributes


def produce_dual_subtitles(
    video: Path,
    primary_lang: str,
    secondary_lang: str,
    output_language: str,
    primary_font: dict,
    secondary_font: dict,
):
    subtitle_tracks = find_subtitles(video, (primary_lang, secondary_lang))
    all_tracks = [s["index"] for lang in subtitle_tracks.values() for s in lang]
    all_subs = extract_subtitle_tracks(video, *all_tracks)
    combos = product(subtitle_tracks[primary_lang], subtitle_tracks[secondary_lang])
    for primary, secondary in combos:
        subs = all_subs[primary["index"]], all_subs[secondary["index"]]
        dual = dual_subtitles(
            *(srt.parse(s) for s in subs), primary_font, secondary_font
        )
        t1 = primary["tags"].get("title") or primary["tags"]["language"]
        t2 = secondary["tags"].get("title") or secondary["tags"]["language"]
        sfx = "_".join(sub(r"[^0-9a-z]+", "_", t.lower()) for t in (t1, t2))
        dual_file = (
            video.parent / f"{video.stem}.{output_language or primary_lang}.{sfx}.srt"
        )
        dual_file.write_text(srt.compose(dual))


def main():
    parser = ArgumentParser(description="Subtitle extraction and combining tool")
    parser.add_argument(
        "primary_language",
        help="primary subtitle stream language (the one you learn)",
    )
    parser.add_argument(
        "secondary_language",
        help="secondary subtitle stream language (the one you understand)",
    )
    parser.add_argument(
        "video_file",
        nargs="+",
        type=existing_file_path,
        help="video file with both subtitle streams",
    )
    parser.add_argument(
        "--primary-font",
        type=font_attributes,
        default="size:18",
        help='font attirubtes of primary titles (default: "size:18")',
    )
    parser.add_argument(
        "--secondary-font",
        type=font_attributes,
        default="size:15,color:gray",
        help='font attributes of secondary titles (default: "size:15,color:gray")',
    )
    parser.add_argument(
        "--output-language",
        help="combined subtitle language (default is same as primary)",
    )
    args = parser.parse_args()
    for video_file in args.video_file:
        produce_dual_subtitles(
            video_file,
            args.primary_language,
            args.secondary_language,
            args.output_language,
            args.primary_font,
            args.secondary_font,
        )
    return 0

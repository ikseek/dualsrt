from tempfile import TemporaryDirectory

import ffmpeg
from pathlib import Path


def find_subtitles(
    file: Path,
    languages,
    skip_commentary=True,
    drop_redundant_forced=True,
    drop_redundant_sdh=True,
):
    subtitles = {language: [] for language in languages}
    probe = ffmpeg.probe(file, select_streams="s")
    for stream in probe["streams"]:
        stream_language = stream["tags"]["language"]
        if stream_language in subtitles:
            title = stream["tags"].get("title", "").lower()
            if skip_commentary and "comm" in title:
                continue
            subtitles[stream_language].append(stream)
    for streams in subtitles.values():
        if drop_redundant_forced:
            cleaned = [
                s for s in streams if "forc" not in s["tags"].get("title", "").lower()
            ]
            if len(cleaned) > 0:
                streams[:] = cleaned
        if drop_redundant_sdh:
            cleaned = [
                s for s in streams if "sdh" not in s["tags"].get("title", "").lower()
            ]
            if len(cleaned) > 0:
                streams[:] = cleaned

    return subtitles


def extract_subtitle_tracks(file: Path, *tracks: int) -> dict[int, str]:
    with TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        subs = [(track, tmp_dir / f"{track}.srt") for track in tracks]

        stream = ffmpeg.input(file)
        outputs = [stream.output(str(sub), map=f"0:{track}") for track, sub in subs]
        ffmpeg.merge_outputs(*outputs).run()

        return {track: sub.read_text() for track, sub in subs}

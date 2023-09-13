import re
from datetime import timedelta
from heapq import merge
from itertools import chain
from typing import Iterable, Optional

from srt import Subtitle

FONT_TAG = re.compile(r"^<font\s+[^>]+>(.*)</font>$", re.DOTALL)


def pairwise(iter):
    cached = list(iter)
    return zip(cached, cached[1:])


def patched_eq(self, other):
    return isinstance(other, Subtitle) and vars(self) == vars(other)


Subtitle.__eq__ = patched_eq


def dual_subtitles(
    primary: Iterable[Subtitle], secondary: Iterable[Subtitle]
) -> Iterable[Subtitle]:
    combined = []
    aligned = align_subtitles(
        combine_subtitles(primary, secondary), timedelta(milliseconds=900)
    )
    for idx, (prim, sec) in enumerate(aligned):
        prim_content = ""
        sec_content = ".\n."
        if prim:
            prim_content = strip_font(prim.content.strip())
            prim_content = f'<font color="#ffffff" size="18">{prim_content}</font>'
        if sec:
            sec_content = strip_font(sec.content.strip())
            if "\n" not in sec_content and prim_content:
                sec_content += "\n."
        sec_content = f'<font color="#555555" size="10">{sec_content}</font>'
        start = (prim or sec).start
        end = (prim or sec).end
        combined.append(Subtitle(idx, start, end, f"{prim_content}\n{sec_content}"))
    return combined


def combine_subtitles(
    primary: Iterable[Subtitle], secondary: Iterable[Subtitle]
) -> Iterable[tuple[Subtitle, Subtitle]]:
    current = [None, None]
    combined = []
    for sub, position in merge(((p, 0) for p in primary), ((s, 1) for s in secondary)):
        if current[position]:
            combined.append(current)
            current = [None, None]
        current[position] = sub
        *overlapped, current = overlaps(*current)
        combined.extend(overlapped)
    if any(current):
        combined.append(current)
    return combined


def align_subtitles(
    subs: Iterable[list[Subtitle, Subtitle]], min_len
) -> Iterable[list[Subtitle, Subtitle]]:
    aligned = []
    subs = iter(subs)
    prev_prim = prev_sec = None
    cur_prim, cur_sec = next(subs)

    for next_prim, next_sec in chain(subs, [[None, None]]):
        length = (cur_prim or cur_sec).end - (cur_prim or cur_sec).start
        if length <= min_len:
            can_drop_prim = redundant(cur_prim, prev_prim, next_prim)
            can_drop_sec = redundant(cur_sec, prev_sec, next_sec)
            if can_drop_prim and can_drop_sec:
                adjust_prev = repeats(cur_prim, prev_prim) or repeats(cur_sec, prev_sec)
                adjust_next = repeats(cur_prim, next_prim) or repeats(cur_sec, next_sec)
                shift = length // 2 if adjust_prev and adjust_next else length
                if adjust_prev:
                    if prev_prim:
                        prev_prim.end += shift
                    if prev_sec:
                        prev_sec.end += shift
                if adjust_next:
                    if next_prim:
                        next_prim.start -= shift
                    if next_sec:
                        next_sec.start -= shift
                cur_prim, cur_sec = next_prim, next_sec
                continue
        if prev_prim or prev_sec:
            aligned.append([prev_prim, prev_sec])
        prev_prim, prev_sec, cur_prim, cur_sec = cur_prim, cur_sec, next_prim, next_sec

    if prev_prim or prev_sec:
        aligned.append([prev_prim, prev_sec])
    if cur_prim or cur_sec:
        aligned.append([prev_prim, prev_sec])
    return aligned


def strip_font(text: str) -> str:
    if match := FONT_TAG.match(text):
        return match.group(1)
    else:
        return text


def redundant(sub: Optional[Subtitle], *adjacent: Optional[Subtitle]) -> bool:
    return not sub or any(sub.content == o.content for o in adjacent if o)


def repeats(sub: Optional[Subtitle], other: Optional[Subtitle]) -> bool:
    return bool(sub and other and sub.content == other.content)


def overlaps(
    sub1: Subtitle, sub2: Subtitle
) -> list[list[Optional[Subtitle], Optional[Subtitle]]]:
    if not sub1 or not sub2:
        return [[sub1, sub2]]
    result = []
    change_points = sorted({sub1.start, sub1.end, sub2.start, sub2.end})
    for t1, t2 in pairwise(change_points):
        s1 = (
            Subtitle(sub1.index, t1, t2, sub1.content, sub1.proprietary)
            if is_visible(sub1, t1, t2)
            else None
        )
        s2 = (
            Subtitle(sub2.index, t1, t2, sub2.content, sub2.proprietary)
            if is_visible(sub2, t1, t2)
            else None
        )
        if s1 or s2:
            result.append([s1, s2])
    return result


def is_visible(sub: Subtitle, start, end):
    return sub.start <= start and end <= sub.end

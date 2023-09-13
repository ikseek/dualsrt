import re
from datetime import timedelta
from typing import Iterable, Optional

from srt import Subtitle
from heapq import merge
from itertools import chain


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


FONT_TAG = re.compile(r"^<font\s+[^>]+>(.*)</font>$", re.DOTALL)


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


def test_overlaps_one():
    result = overlaps(Subtitle(None, 1, 2, "a"), Subtitle(None, 1, 2, "b"))
    assert result == [[Subtitle(None, 1, 2, "a"), Subtitle(None, 1, 2, "b")]]


def test_overlaps_sub1_earlier():
    result = overlaps(Subtitle(None, 1, 3, "a"), Subtitle(None, 2, 3, "b"))
    assert result == [
        [Subtitle(None, 1, 2, "a", ""), None],
        [Subtitle(None, 2, 3, "a"), Subtitle(None, 2, 3, "b")],
    ]


def test_overlaps_sub2_earlier():
    result = overlaps(Subtitle(None, 2, 3, "a"), Subtitle(None, 1, 3, "b"))
    assert result == [
        [None, Subtitle(None, 1, 2, "b")],
        [Subtitle(None, 2, 3, "a"), Subtitle(None, 2, 3, "b")],
    ]


def test_overlaps_sub2_during_sub1():
    result = overlaps(Subtitle(None, 1, 4, "a"), Subtitle(None, 2, 3, "b"))
    assert result == [
        [Subtitle(None, 1, 2, "a"), None],
        [Subtitle(None, 2, 3, "a"), Subtitle(None, 2, 3, "b")],
        [Subtitle(None, 3, 4, "a"), None],
    ]


def test_combine_subtitles_only_primary():
    primary = [Subtitle(None, 1, 2, "a")]
    secondary = []

    assert combine_subtitles(primary, secondary) == [[Subtitle(None, 1, 2, "a"), None]]


def test_combine_subtitles_only_secondary():
    primary = []
    secondary = [Subtitle(None, 1, 2, "a")]

    assert combine_subtitles(primary, secondary) == [[None, Subtitle(None, 1, 2, "a")]]


def test_combine_subtitles_overlapping():
    primary = [Subtitle(None, 1, 3, "a")]
    secondary = [Subtitle(None, 2, 3, "b")]

    assert combine_subtitles(primary, secondary) == [
        [Subtitle(None, 1, 2, "a"), None],
        [Subtitle(None, 2, 3, "a"), Subtitle(None, 2, 3, "b")],
    ]


def test_combine_subtitles_included():
    primary = [Subtitle(None, 1, 4, "a")]
    secondary = [Subtitle(None, 2, 3, "b")]

    assert combine_subtitles(primary, secondary) == [
        [Subtitle(None, 1, 2, "a"), None],
        [Subtitle(None, 2, 3, "a"), Subtitle(None, 2, 3, "b")],
        [Subtitle(None, 3, 4, "a"), None],
    ]


def test_combine_subtitles_not_intersect():
    primary = [Subtitle(None, 1, 2, "a")]
    secondary = [Subtitle(None, 3, 4, "b")]

    assert combine_subtitles(primary, secondary) == [
        [Subtitle(None, 1, 2, "a"), None],
        [None, Subtitle(None, 3, 4, "b")],
    ]


def test_combine_subtitles_chain():
    primary = [Subtitle(None, 1, 3, "a1"), Subtitle(None, 4, 5, "a2")]
    secondary = [Subtitle(None, 2, 3, "b1")]

    assert combine_subtitles(primary, secondary) == [
        [Subtitle(None, 1, 2, "a1"), None],
        [Subtitle(None, 2, 3, "a1"), Subtitle(None, 2, 3, "b1")],
        [Subtitle(None, 4, 5, "a2"), None],
    ]


def test_combine_subtitles_chain2():
    primary = [Subtitle(None, 1, 3, "a1"), Subtitle(None, 4, 6, "a2")]
    secondary = [Subtitle(None, 2, 3, "b1"), Subtitle(None, 5, 6, "b2")]

    assert combine_subtitles(primary, secondary) == [
        [Subtitle(None, 1, 2, "a1"), None],
        [Subtitle(None, 2, 3, "a1"), Subtitle(None, 2, 3, "b1")],
        [Subtitle(None, 4, 5, "a2"), None],
        [Subtitle(None, 5, 6, "a2"), Subtitle(None, 5, 6, "b2")],
    ]


def test_combine_subtitles_chain3():
    primary = [
        Subtitle(None, 1, 2, "a1"),
        Subtitle(None, 2, 3, "a2"),
        Subtitle(None, 3, 4, "a3"),
    ]
    secondary = [Subtitle(None, 1, 4, "b1")]

    assert combine_subtitles(primary, secondary) == [
        [Subtitle(None, 1, 2, "a1"), Subtitle(None, 1, 2, "b1")],
        [Subtitle(None, 2, 3, "a2"), Subtitle(None, 2, 3, "b1")],
        [Subtitle(None, 3, 4, "a3"), Subtitle(None, 3, 4, "b1")],
    ]


def test_combine_subtitles_chain4():
    primary = [
        Subtitle(None, 1, 2, "a1"),
        Subtitle(None, 2, 3, "a2"),
        Subtitle(None, 3, 4, "a3"),
        Subtitle(None, 4, 5, "a4"),
        Subtitle(None, 5, 6, "a5"),
    ]
    secondary = [Subtitle(None, 3, 4, "b1")]

    assert combine_subtitles(primary, secondary) == [
        [Subtitle(None, 1, 2, "a1"), None],
        [Subtitle(None, 2, 3, "a2"), None],
        [Subtitle(None, 3, 4, "a3"), Subtitle(None, 3, 4, "b1")],
        [Subtitle(None, 4, 5, "a4"), None],
        [Subtitle(None, 5, 6, "a5"), None],
    ]


def test_combine_subtitles_chain5():
    primary = [
        Subtitle(None, 1, 2, "a1"),
        Subtitle(None, 2, 3, "a2"),
        Subtitle(None, 3, 4, "a3"),
        Subtitle(None, 4, 5, "a4"),
        Subtitle(None, 5, 6, "a5"),
    ]
    secondary = [Subtitle(None, 2, 5, "b1")]

    assert combine_subtitles(primary, secondary) == [
        [Subtitle(None, 1, 2, "a1"), None],
        [Subtitle(None, 2, 3, "a2"), Subtitle(None, 2, 3, "b1")],
        [Subtitle(None, 3, 4, "a3"), Subtitle(None, 3, 4, "b1")],
        [Subtitle(None, 4, 5, "a4"), Subtitle(None, 4, 5, "b1")],
        [Subtitle(None, 5, 6, "a5"), None],
    ]


def test_combine_subtitles_chain6():
    primary = [
        Subtitle(None, 1, 2, "a1"),
        Subtitle(None, 3, 4, "a3"),
        Subtitle(None, 5, 6, "a5"),
    ]
    secondary = [Subtitle(None, 1, 6, "b1")]

    assert combine_subtitles(primary, secondary) == [
        [Subtitle(None, 1, 2, "a1"), Subtitle(None, 1, 2, "b1")],
        [None, Subtitle(None, 2, 3, "b1")],
        [Subtitle(None, 3, 4, "a3"), Subtitle(None, 3, 4, "b1")],
        [None, Subtitle(None, 4, 5, "b1")],
        [Subtitle(None, 5, 6, "a5"), Subtitle(None, 5, 6, "b1")],
    ]


def test_align_subtitles_aligned():
    subs = [[Subtitle(1, 2, 4, "a1"), Subtitle(1, 2, 4, "b1")]]

    assert align_subtitles(subs, 1) == [
        [Subtitle(1, 2, 4, "a1"), Subtitle(1, 2, 4, "b1")]
    ]


def test_align_subtitles_first_early():
    subs = [
        [Subtitle(1, 1, 2, "a1"), None],
        [Subtitle(1, 2, 4, "a1"), Subtitle(1, 2, 4, "b1")],
    ]

    assert align_subtitles(subs, 1) == [
        [Subtitle(1, 1, 4, "a1"), Subtitle(1, 1, 4, "b1")]
    ]


def test_align_subtitles_first_late():
    subs = [
        [Subtitle(1, 1, 3, "a1"), Subtitle(1, 1, 3, "b1")],
        [Subtitle(1, 3, 4, "a1"), None],
    ]

    assert align_subtitles(subs, 1) == [
        [Subtitle(1, 1, 4, "a1"), Subtitle(1, 1, 4, "b1")]
    ]


def test_align_subtitles_fill_gap():
    subs = [
        [Subtitle(1, 1, 4, "a1"), Subtitle(1, 1, 4, "b1")],
        [Subtitle(1, 4, 6, "a1"), Subtitle(1, 4, 6, "b2")],
        [Subtitle(1, 6, 9, "a2"), Subtitle(1, 6, 9, "b2")],
    ]

    assert align_subtitles(subs, 2) == [
        [Subtitle(1, 1, 5, "a1"), Subtitle(1, 1, 5, "b1")],
        [Subtitle(1, 5, 9, "a2"), Subtitle(1, 5, 9, "b2")],
    ]


def test_align_subtitles_keeps_non_repeating_short_tilte():
    subs = [
        [None, Subtitle(1, 1, 4, "b1")],
        [Subtitle(2, 4, 5, "a1"), Subtitle(1, 4, 5, "b2")],
        [None, Subtitle(2, 6, 9, "b3")],
    ]

    assert align_subtitles(subs, 2) == [
        [None, Subtitle(1, 1, 4, "b1")],
        [Subtitle(2, 4, 5, "a1"), Subtitle(1, 4, 5, "b2")],
        [None, Subtitle(2, 6, 9, "b3")],
    ]


def test_align_subtitles_extends_unique_short_title():
    subs = [
        [Subtitle(1, 1, 4, "a1"), None],
        [Subtitle(1, 4, 5, "a1"), Subtitle(1, 4, 5, "b1")],
        [Subtitle(1, 5, 6, "a1"), None],
    ]

    assert align_subtitles(subs, 1) == [
        [Subtitle(1, 1, 4, "a1"), None],
        [Subtitle(1, 4, 6, "a1"), Subtitle(1, 4, 6, "b1")],
    ]


def test_align_subtitles_keeps_unique_short_title():
    subs = [
        [Subtitle(1, 1, 4, "a1"), None],
        [Subtitle(1, 4, 5, "a1"), Subtitle(1, 4, 5, "b1")],
        [Subtitle(1, 5, 6, "a2"), None],
    ]

    assert align_subtitles(subs, 1) == [
        [Subtitle(1, 1, 4, "a1"), None],
        [Subtitle(1, 4, 5, "a1"), Subtitle(1, 4, 5, "b1")],
        [Subtitle(1, 5, 6, "a2"), None],
    ]


def test_align_subtitles_removes_series_of_shorts():
    subs = [
        [Subtitle(1, 1, 5, "a1"), Subtitle(5, 1, 5, "b1")],
        [None, Subtitle(5, 5, 7, "b1")],
        [Subtitle(2, 7, 9, "a2"), Subtitle(5, 7, 9, "b1")],
        [Subtitle(2, 9, 11, "a2"), None],
    ]

    assert align_subtitles(subs, 3) == [
        [Subtitle(1, 1, 7, "a1"), Subtitle(5, 1, 7, "b1")],
        [Subtitle(2, 8, 11, "a2"), None],
    ]


def test_strip_font():
    assert strip_font('<font face="Serif" size="18">text</font>') == "text"
    assert strip_font('<font face="Serif" size="18">l1\nl2</font>') == "l1\nl2"
    assert strip_font('<font size="1"><b>bold</b></font>') == "<b>bold</b>"

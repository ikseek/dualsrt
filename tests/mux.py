from srt import Subtitle
from dualsrt.mux import (
    overlaps,
    combine_subtitles,
    align_subtitles,
    strip_font,
    extract_position,
)


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
    assert strip_font('a<font size="1">b</font>c') == "abc"


def test_extract_position():
    assert extract_position("no position") == ("no position", "")
    assert extract_position(r"{\an8}top") == ("top", r"{\an8}")
    assert extract_position(r"<font>{\an8}a</font>") == ("<font>a</font>", r"{\an8}")

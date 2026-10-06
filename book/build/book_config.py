"""Single source of book metadata for the KDP build.

Every page that prints the title, subtitle or author (title page, copyright
page, running heads, cover) reads it from here, so a change is made once.
"""

BOOK_TITLE = "The Lion's Problem"
BOOK_SUBTITLE = "From Refusal to Authorship"
AUTHOR_NAME = "Brian Danzyger"
EDITION_LABEL = "First edition"
VERSION_LABEL = "v1.0 revised draft"
PUBLICATION_YEAR = "2026"
ISBN_PAPERBACK = "xxx-xxx-xxxxx"   # placeholder; replace with the real ISBN-13 (or a free KDP ISBN) before upload

# KDP paperback geometry (checked against KDP rules 26 Sep 2026; re-check before upload).
TRIM_WIDTH_IN = 6.0
TRIM_HEIGHT_IN = 9.0
INNER_MARGIN_IN = 0.75   # clears KDP's minimum gutter at every page count up to 700
OUTER_MARGIN_IN = 0.6
TOP_MARGIN_IN = 0.75
BOTTOM_MARGIN_IN = 0.8

# Cover spine: pages x thickness per page (KDP, white paper / cream paper).
SPINE_PER_PAGE_WHITE_IN = 0.002252
SPINE_PER_PAGE_CREAM_IN = 0.0025
COVER_BLEED_IN = 0.125

# Master file naming follows [Volume]_[Edition]_[Version]_[Descriptor]_[YYYY-MM-DD].
MASTER_NAME = "LP_KDP-Trade_v1.0_Revised-Draft_2026-10-03"

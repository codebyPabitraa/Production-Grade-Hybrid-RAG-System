from rag_pipeline.chunking.strategies import split_markdown_sections, split_table_rows


def test_split_markdown_sections_groups_headings():
    text = "# Title\n\nIntro text\n\n## Details\n\nMore text"
    sections = split_markdown_sections(text)
    assert len(sections) == 2
    assert sections[0].startswith("# Title")
    assert sections[1].startswith("## Details")


def test_split_table_rows_keeps_rows():
    text = "a | b | c\n1 | 2 | 3"
    rows = split_table_rows(text)
    assert rows == ["a | b | c", "1 | 2 | 3"]


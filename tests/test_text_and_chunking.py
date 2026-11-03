from rag_template.documents import Chunker, Document, parse_heading
from rag_template.loaders import html_to_text, load_bytes, page_url
from rag_template.text import tokenize


def test_tokenize_stems_russian_and_english():
    assert tokenize("параметры")[0] == tokenize("параметр")[0]
    assert tokenize("Parameters")[0] == tokenize("parameter")[0]
    assert tokenize("Ёлка") == tokenize("елка")


def test_tokenize_drops_stopwords_and_splits_identifiers():
    tokens = tokenize("как и the response_model")
    assert "как" not in tokens and "the" not in tokens
    assert "response_model" in tokens and "respons" in tokens and "model" in tokens


def test_heading_anchor_is_parsed():
    assert parse_heading("## Значения по умолчанию { #defaults }") == (2, "Значения по умолчанию", "defaults")
    assert parse_heading("обычный текст") is None


def test_chunks_keep_section_path_and_anchor_url():
    text = "# Гайд { #guide }\n\nВступление.\n\n## Установка { #install }\n\n" + "Шаг. " * 60
    doc = Document("guide.md", text, url="https://site/guide/")
    chunks = Chunker(chunk_size=200, overlap=0, min_size=10).split(doc)
    assert chunks[0].title == "Гайд"
    install = [c for c in chunks if c.section == "Установка"]
    assert install and install[0].url == "https://site/guide/#install"
    assert all(len(c.text) <= 200 for c in chunks)
    assert install[0].indexed_text().startswith("Гайд — Установка")


def test_code_block_stays_whole_when_it_fits():
    code = "```python\n" + "\n".join(f"x{i} = {i}" for i in range(20)) + "\n```"
    doc = Document("c.md", "# T\n\nТекст до кода.\n\n" + code + "\n\nТекст после.")
    chunks = Chunker(chunk_size=400, overlap=0).split(doc)
    assert sum(c.text.count("```") for c in chunks) == 2
    assert any(code in c.text for c in chunks)


def test_long_code_block_is_split_by_lines():
    code = "```python\n" + "\n".join(f"value_{i} = {i}" for i in range(200)) + "\n```"
    chunks = Chunker(chunk_size=300, overlap=0).split(Document("c.md", code))
    assert len(chunks) > 5 and all(len(c.text) <= 300 for c in chunks)
    assert all(not line or line.startswith(("value_", "```")) for c in chunks for line in c.text.splitlines())


def test_short_paragraph_overlaps_into_next_chunk():
    paragraphs = [f"Абзац номер {i} " + "слово " * 25 for i in range(6)]
    chunks = Chunker(chunk_size=400, overlap=200).split(Document("p.md", "\n\n".join(paragraphs)))
    assert len(chunks) >= 2
    tail = chunks[0].text.split("\n\n")[-1]
    assert chunks[1].text.startswith(tail)


def test_chunk_ids_are_stable():
    doc = Document("a.md", "# A\n\n" + "текст " * 400)
    assert [c.id for c in Chunker().split(doc)] == [c.id for c in Chunker().split(doc)]


def test_html_loader_keeps_headings_and_drops_scripts():
    text, title = html_to_text("<html><title>Док</title><script>x=1</script><h2>Раздел</h2><p>Текст</p></html>")
    assert "## Раздел" in text and "Текст" in text and "x=1" not in text and title == "Док"


def test_page_url_mapping():
    assert page_url("https://s/ru/", "tutorial/query-params.md") == "https://s/ru/tutorial/query-params/"
    assert page_url("https://s/ru/", "index.md") == "https://s/ru/"
    assert page_url("https://s/ru", "learn/index.md") == "https://s/ru/learn/"
    assert page_url(None, "a.md") is None


def test_load_bytes_title_from_markdown():
    doc = load_bytes("x/file-name.md", "# Заголовок\n\nтекст".encode())
    assert doc.title == "Заголовок"
    assert load_bytes("x/file-name.txt", b"plain").title == "file name"

import re
import html
from typing import Optional


class DataCleaner:
    """
    Reusable text sanitization and entity cleaning processor.
    Never mutates original raw data in-place; provides purified string outputs.
    """

    # HTML tag stripper regex (matches valid opening/closing/self-closing HTML tags)
    HTML_TAG_PATTERN = re.compile(r'</?[a-zA-Z][^>]*>')
    # Whitespace normalization regex
    MULTI_WHITESPACE_PATTERN = re.compile(r'[\r\n\t]+|\s{2,}')
    # Zero-width / invisible unicode characters
    INVISIBLE_CHARS_PATTERN = re.compile(r'[\u200b\u200c\u200d\uFEFF]')

    @classmethod
    def clean_text(cls, text: Optional[str]) -> Optional[str]:
        """
        Sanitizes text strings by stripping HTML markup tags first, decoding entities,
        collapsing erratic linebreaks and whitespace, and eliminating non-printable chars.
        Returns None for empty or null inputs.
        """
        if text is None:
            return None

        if not isinstance(text, str):
            text = str(text)

        # 1. Strip true HTML tags first before unescaping entities
        no_html = cls.HTML_TAG_PATTERN.sub(' ', text)

        # 2. Decode HTML entities (e.g. &amp; -> &, &lt; -> <, &nbsp; -> ' ')
        decoded = html.unescape(no_html)

        # 3. Remove invisible zero-width unicode
        no_invisible = cls.INVISIBLE_CHARS_PATTERN.sub('', decoded)

        # 4. Replace non-breaking space with standard space
        standard_space = no_invisible.replace('\xa0', ' ')

        # 5. Collapse excessive spaces and linebreaks
        collapsed = cls.MULTI_WHITESPACE_PATTERN.sub(' ', standard_space).strip()

        return collapsed if collapsed else None

    @classmethod
    def clean_company_name(cls, name: Optional[str]) -> Optional[str]:
        """
        Normalizes company names by cleaning whitespace and capitalizing words,
        while preserving recognized uppercase technical acronyms.
        """
        cleaned = cls.clean_text(name)
        if not cleaned:
            return None

        # Known acronyms to preserve in all-caps
        ACRONYMS = {
            "IBM", "AWS", "TCS", "IDC", "HCL", "L&T", "DE", "GE",
            "HP", "SAP", "AMD", "ARM", "EY", "PWC", "KPMG", "SDE", "IT"
        }

        # Tokenize and format casing properly
        words = cleaned.split()
        formatted_words = []
        for word in words:
            upper_clean = word.upper().strip(".,()[]")
            if upper_clean in ACRONYMS:
                formatted_words.append(word.upper())
            elif word.isupper() and len(word) <= 4 and word.isalpha():
                formatted_words.append(word)
            else:
                formatted_words.append(word.capitalize())

        return " ".join(formatted_words)

    @classmethod
    def clean_url(cls, url: Optional[str]) -> Optional[str]:
        """
        Strips whitespace and verifies basic URL validity.
        """
        cleaned = cls.clean_text(url)
        if not cleaned:
            return None

        # Ensure minimal URL integrity
        if cleaned.startswith("http://") or cleaned.startswith("https://") or cleaned.startswith("/"):
            return cleaned.strip()

        return cleaned

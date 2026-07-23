from dataclasses import dataclass, field


@dataclass(frozen=True)
class WordNote:
    word: str
    explanation: str


@dataclass(frozen=True)
class TranslationResult:
    source_language: str
    target_language: str
    natural_translation: str
    literal_translation: str
    word_notes: list[WordNote] = field(default_factory=list)

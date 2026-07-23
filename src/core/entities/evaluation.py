from dataclasses import dataclass, field


@dataclass(frozen=True)
class MistakeItem:
    category: str  # grammar | vocabulary | fluency | naturalness
    original: str
    corrected: str
    explanation: str


@dataclass(frozen=True)
class VocabularyNote:
    word_or_phrase: str
    translation_ru: str
    example_sentence: str


@dataclass(frozen=True)
class TurnEvaluation:
    grammar_score: int
    vocabulary_score: int
    fluency_score: int
    naturalness_score: int
    corrected_sentence: str
    mistakes: list[MistakeItem] = field(default_factory=list)
    vocabulary_notes: list[VocabularyNote] = field(default_factory=list)

from dataclasses import dataclass


@dataclass(frozen=True)
class InterviewFeedback:
    passes: bool
    score: int
    spoken_response: str

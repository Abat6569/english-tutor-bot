import random
from dataclasses import dataclass

PERSONAS: list[tuple[str, str]] = [
    (
        "the EPC contractor's site engineer",
        "a site engineer from the EPC contractor who wants to close out inspection "
        "items quickly and sometimes pushes back on findings",
    ),
    (
        "a third-party inspector",
        "an independent third-party inspector who is strict about documentation and "
        "code compliance",
    ),
    (
        "the client's QA/QC representative",
        "the end client's QA/QC representative who cares about schedule impact and "
        "asks pointed follow-up questions",
    ),
]

TOPICS: list[str] = [
    "reviewing an RFI (Request for Inspection) before a cable pulling activity",
    "discussing an NCR (Non-Conformance Report) raised on torque values for busbar " "connections",
    "walking through an ITP (Inspection and Test Plan) for a BESS container " "installation",
    "a Material Inspection Report for incoming switchgear",
    "a punch list review before SAT (Site Acceptance Test)",
    "clarifying scope in a Method Statement for transformer commissioning",
    "an as-built documentation discrepancy on cable routing",
    "a fire fighting system inspection before energization",
    "a pre-commissioning check for a substation feeder bay",
    "a standards reference dispute (IEC vs IEEE) during equipment testing",
]


@dataclass(frozen=True)
class ProfessionalScenario:
    persona: str
    persona_description: str
    topic: str


def random_scenario() -> ProfessionalScenario:
    persona, persona_description = random.choice(PERSONAS)
    topic = random.choice(TOPICS)
    return ProfessionalScenario(
        persona=persona, persona_description=persona_description, topic=topic
    )

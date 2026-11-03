"""Testers' feedback, emailed to the team. Nothing is stored in the database.

Open to anyone (testers may not have an account). Kept from being abused by
the app header, a honeypot field, length caps and a per-visitor limit.
"""

import os
from functools import lru_cache
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from api.auth import require_app_header
from api.mailer import get_mailer, send_safely
from api.ratelimit import RateLimiter
from api.schemas import MessageOut

router = APIRouter(prefix="/public", tags=["public"], dependencies=[Depends(require_app_header)])

DEFAULT_TO = "quoteyard.alerts@gmail.com"
PER_HOUR = 5

# The highlight colours testers can pick from (frontend/src/pages/Feedback.jsx).
Colour = Literal["neon-green", "sunflower", "coral", "sky", "lavender", "ink", "other", ""]
Fatigue = Literal["not-at-all", "a-little", "quite", "very", ""]
Device = Literal["phone", "computer", "tablet", ""]

COLOUR_NAMES = {
    "neon-green": "Neon green #4DFF00 (current)", "sunflower": "Sunflower #FFD23F",
    "coral": "Coral #FF8A65", "sky": "Sky #6CC4FF", "lavender": "Lavender #B9A4FF",
    "ink": "Ink black #141414", "other": "Other (see note)", "": "(not answered)",
}
FATIGUE_NAMES = {
    "not-at-all": "Not at all", "a-little": "A little", "quite": "Quite tiring",
    "very": "Very tiring", "": "(not answered)",
}

Text = Field(default="", max_length=2000)


class FeedbackIn(BaseModel):
    colour: Colour = ""
    colour_note: str = Field(default="", max_length=300)
    fatigue: Fatigue = ""
    fatigue_note: str = Text
    problems: str = Text
    mistakes: str = Text
    questions: str = Text
    suggestions: str = Text
    device: Device = ""
    name: str = Field(default="", max_length=80)
    email: str = Field(default="", max_length=254)
    website: str = Field(default="", max_length=200)  # honeypot: people leave it empty


@lru_cache
def _limiter() -> RateLimiter | None:
    if os.environ.get("QUOTE_YARD_RATE_LIMIT") == "0":
        return None
    return RateLimiter(PER_HOUR, window=60 * 60)


def feedback_to() -> str:
    return os.environ.get("QUOTE_YARD_FEEDBACK_EMAIL", "").strip() or DEFAULT_TO


def _section(title: str, text: str) -> str:
    return f"{title}\n{text.strip() or '(nothing)'}\n"


def feedback_body(f: FeedbackIn) -> str:
    who = ", ".join(x for x in (f.name.strip(), f.email.strip()) if x) or "(anonymous)"
    return "\n".join([
        f"From: {who}",
        f"Device: {f.device or '(not answered)'}",
        "",
        _section("Highlight colour:", COLOUR_NAMES[f.colour] + (f" ({f.colour_note.strip()})" if f.colour_note.strip() else "")),
        _section("Does the site feel tiring?", FATIGUE_NAMES[f.fatigue] + (f" ({f.fatigue_note.strip()})" if f.fatigue_note.strip() else "")),
        _section("Problems:", f.problems),
        _section("Spelling mistakes or wrong details:", f.mistakes),
        _section("Questions:", f.questions),
        _section("Other suggestions:", f.suggestions),
    ])


@router.post("/feedback", response_model=MessageOut, status_code=202)
def send_feedback(body: FeedbackIn, request: Request, background: BackgroundTasks,
                  mailer=Depends(get_mailer)):
    texts = (body.colour, body.colour_note, body.fatigue, body.fatigue_note, body.problems,
             body.mistakes, body.questions, body.suggestions)
    if not any(t.strip() for t in texts):
        raise HTTPException(status_code=422, detail="Please answer at least one question.")
    limiter = _limiter()
    if limiter is not None:
        client = request.client.host if request.client else "unknown"
        wait = limiter.check(client)
        if wait is not None:
            raise HTTPException(status_code=429, detail="too many attempts, try again later",
                                headers={"Retry-After": str(int(wait) + 1)})
    if not body.website:  # a bot filled the hidden field: say thanks, send nothing
        subject = "Quote Yard feedback" + (f" from {body.name.strip()}" if body.name.strip() else "")
        background.add_task(send_safely, mailer, feedback_to(), subject, feedback_body(body))
    return MessageOut(message="Thank you! Your feedback was sent.")

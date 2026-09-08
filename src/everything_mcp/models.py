"""Validated search filters and public parameter types."""

import re
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Sort = Literal["name", "path", "size", "extension", "date-created", "date-modified"]
Kind = Literal["all", "file", "folder"]


class Filters(BaseModel):
    """Index metadata only. Dates include the whole calendar day; size is bytes."""

    model_config = ConfigDict(extra="forbid")
    extensions: list[str] = Field(default_factory=list, max_length=30)
    min_bytes: int | None = Field(default=None, ge=0)
    max_bytes: int | None = Field(default=None, ge=0)
    modified_from: date | None = None
    modified_to: date | None = None
    recent_days: int | None = Field(default=None, ge=1, le=36500)

    @model_validator(mode="after")
    def validate_ranges(self):
        if (
            self.min_bytes is not None
            and self.max_bytes is not None
            and self.min_bytes > self.max_bytes
        ):
            raise ValueError("min_bytes exceeds max_bytes")
        if self.modified_from and self.modified_to and self.modified_from > self.modified_to:
            raise ValueError("modified_from exceeds modified_to")
        if self.recent_days and (self.modified_from or self.modified_to):
            raise ValueError("use recent_days or a date range, not both")
        for ext in self.extensions:
            if not re.fullmatch(r"\.?[A-Za-z0-9]+", ext):
                raise ValueError("extensions must be plain extensions, e.g. pdf or .docx")
        return self

    def expression(self):
        terms = []
        if self.extensions:
            terms.append("ext:" + ";".join(e.lstrip(".") for e in self.extensions))
        if self.min_bytes is not None:
            terms.append(f"size:>={self.min_bytes}")
        if self.max_bytes is not None:
            terms.append(f"size:<={self.max_bytes}")
        start = (
            date.today() - timedelta(days=self.recent_days - 1)
            if self.recent_days
            else self.modified_from
        )
        end = date.today() if self.recent_days else self.modified_to
        if start:
            terms.append(f"dm:>={start.isoformat()}")
        if end:
            terms.append(f"dm:<{(end + timedelta(days=1)).isoformat()}")
        return " ".join(terms)

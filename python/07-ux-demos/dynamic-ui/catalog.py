"""The component catalog: every UI component the agent is allowed to render.

These models are the input schema of the `render_ui` tool, so the model sees
exactly these components and props, and Strands validates its output against
them before the tool runs. The browser has one renderer per `type`
(see web/app.js). To add a component, add a model here and a renderer there.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, Field


class Text(BaseModel):
    type: Literal["text"]
    content: str = Field(description="A short paragraph of plain text.")


class Stat(BaseModel):
    type: Literal["stat"]
    label: str
    value: str = Field(description="The headline number, formatted for display, e.g. '42 km'.")
    hint: str | None = Field(default=None, description="Optional small print, e.g. 'up 12% on last week'.")


class Table(BaseModel):
    type: Literal["table"]
    title: str | None = None
    columns: list[str]
    rows: list[list[str]] = Field(description="One list of cell values per row, in column order.")


class Bar(BaseModel):
    label: str
    value: float


class BarChart(BaseModel):
    type: Literal["bar_chart"]
    title: str | None = None
    unit: str | None = Field(default=None, description="Unit shown after each value, e.g. 'min'.")
    bars: list[Bar]


class FormField(BaseModel):
    name: str = Field(description="Key for this field in the submitted values.")
    label: str
    kind: Literal["text", "number", "date", "select"]
    options: list[str] | None = Field(default=None, description="Choices, required when kind is 'select'.")
    value: str | None = Field(default=None, description="Pre-filled value.")


class Form(BaseModel):
    type: Literal["form"]
    title: str | None = None
    action: str = Field(description="Name sent back to you with the values when the user submits.")
    submit: str | None = Field(default=None, description="Submit button label.")
    fields: list[FormField]


class Button(BaseModel):
    type: Literal["button"]
    label: str
    action: str = Field(description="Name sent back to you when the user clicks.")


Leaf = Annotated[Text | Stat | Table | BarChart | Form | Button, Field(discriminator="type")]


class Row(BaseModel):
    type: Literal["row"]
    items: list[Leaf] = Field(description="Components shown side by side, e.g. a few stats.")


Component = Annotated[Text | Stat | Table | BarChart | Form | Button | Row, Field(discriminator="type")]

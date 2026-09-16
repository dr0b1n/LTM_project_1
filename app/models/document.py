from pydantic import BaseModel, Field


class ExtractedPage(BaseModel):
    page_number: int = Field(ge=1)
    text: str


class ExtractedDocument(BaseModel):
    filename: str
    page_count: int = Field(ge=1)
    pages: list[ExtractedPage]

    @property
    def character_count(self) -> int:
        return sum(len(page.text) for page in self.pages)

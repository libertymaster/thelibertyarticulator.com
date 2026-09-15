from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock

class ReferenceBlock(blocks.StructBlock):
    source_key = blocks.CharBlock(help_text="Stable key from this article's Sources tab.", max_length=60)
    locator = blocks.CharBlock(required=False, max_length=160, help_text="Page, chapter, folio, or timestamp.")
    note = blocks.TextBlock(required=False, help_text="An editorial footnote, not an automatically generated claim.")

class ParagraphBlock(blocks.StructBlock):
    text = blocks.RichTextBlock(features=["bold", "italic", "ol", "ul", "link", "superscript", "subscript"])
    references = blocks.ListBlock(ReferenceBlock(), required=False)

class HeadingBlock(blocks.StructBlock):
    text = blocks.CharBlock(max_length=200)
    level = blocks.ChoiceBlock(choices=[("h2", "Section"), ("h3", "Subsection"), ("h4", "Sub-subsection")], default="h2")

class QuoteBlock(blocks.StructBlock):
    text = blocks.TextBlock()
    attribution = blocks.CharBlock(required=False, max_length=240)
    references = blocks.ListBlock(ReferenceBlock(), required=False)

class FigureBlock(blocks.StructBlock):
    image = ImageChooserBlock()
    alt_text = blocks.CharBlock(max_length=250, help_text="Describe the image's relevant content.")
    caption = blocks.CharBlock(required=False, max_length=500)
    credit = blocks.CharBlock(required=False, max_length=250)

class ArticleBodyBlock(blocks.StreamBlock):
    paragraph = ParagraphBlock()
    heading = HeadingBlock()
    quote = QuoteBlock()
    figure = FigureBlock()

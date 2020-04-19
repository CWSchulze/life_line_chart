# """
# markdown renderer to realize a configurable label

# Issue:
# - this will not enable conditional statements, but this is essential

# => other use case?
# """
# import mistune
# class HighlightRenderer(mistune.Renderer):
#     def placeholder(self):
#         return []
#     def block_code(self, code, language=None):
#         return [code]
#     def block_quote(self, text):
#         return [text]
#     def block_html(self, html):
#         return [html]
#     def header(self, text, level, raw=None):
#         return [text]
#     def hrule(self):
#         return ''
#     def list(self, body, ordered=True):
#         return [body]
#     def list_item(self, text):
#         return [text]
#     def paragraph(self, text):
#         return text
#     def table(self, header, body):
#         return [header + body]
#     def table_row(self, content):
#         return [content]
#     def table_cell(self, content, **flags):
#         return [content]

#     def autolink(self, link, is_email=False):
#         return link
#     def codespan(self, text):
#         return text
#     def double_emphasis(self, text):
#         return text
#     def emphasis(self, text):
#         for t in text:
#             t['style'] = 'font-weight: bold'
#         return text
#     def image(self, src, title, alt_text):
#         return title
#     def linebreak(self):
#         return '\n'
#     def newline(self):
#         return '\n'
#     def link(self, link, title, content):
#         return title
#     def strikethrough(self, text):
#         return text
#     def inline_html(self, text):
#         return text
#     def text(self, text):
#         return [{'value' : text}]


# renderer = HighlightRenderer()
# markdown_to_spans = mistune.Markdown(renderer=renderer)

# print(markdown_to_spans.parse('first name *last name* * date'))

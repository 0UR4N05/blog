from src.init import app
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
import pygments
from pygments import highlight
from pygments.lexers import guess_lexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
import markdown

def render_markdown(file):
    f = open(file, "r")
    content = f.read()
    f.close()
    md = markdown.Markdown(extensions=[
        'tables',
        CodeHiliteExtension(css_class='highlight'),
        FencedCodeExtension()
    ])
    mark = md.convert(content)
    return (mark)

def render_code(file):
    f = open(file, "r")
    content = f.read()
    f.close()
    lexer = guess_lexer(content)

    # Create HTML formatter
    formatter = HtmlFormatter(
        style='monokai',
        linenos=True,
        cssclass='highlight',
        wrapcode=True
    )
    code = highlight(content, lexer, formatter)
    return (code)

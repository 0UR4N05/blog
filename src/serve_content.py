from src.init import app
from flask import render_template, abort, request
from src.getfiles import return_files
import markdown
from os.path import exists
from pygments.lexers import guess_lexer
from pygments.formatters import HtmlFormatter
from pygments import highlight
from pygments.styles import get_style_by_name
import os


def render_code(code):
    lexer = guess_lexer(code)
    style = get_style_by_name('lightbulb')

    formatter = HtmlFormatter(linenos=True, style='lightbulb', cssclass='code', noclasses=True, style_kwargs={'font-size': '6px'})
    css = formatter.get_style_defs('.code-highlight')
    highlighted_code = highlight(code, lexer, formatter)

    return highlighted_code, style, lexer.name.lower()

@app.route("/<path:file>")
def serve_content(file):
    file = 'content/' + file
    if (exists(file) == False):
        return "file_not_found"
    files = return_files(file)
    if (os.path.isfile(file)):
        f = open("./" + file)
        if (".md" in file):
            content = markdown.markdown(f.read())
            return render_template("code.html", page_name=file, content=content, dirs=files)
        elif ("." in file):
            content, style, lang= render_code(f.read())
            return render_template("code.html", page_name=file, content=content, dirs=files, css=style, lang=lang)
        f.close()
    return render_template("empty.html", cdir=file, dirs=files)

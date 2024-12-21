from src.init import app
from flask import request, send_from_directory
from os import getcwd, path, listdir
from src.render import render_markdown, render_code
import json

def isbin(filename):
    f = open(filename, "rb")
    con = f.read(10)
    f.close()
    for i in con:
        if (i > 126):
            return (True)
    return (False)

def process_file(lfile):
    codes = ["lua", "py", "c", "cxx", "cpp", "rs", "js", "log", "sh", "s", "json", "yml", "h", "hpp",
             "hxx"]
    ext = lfile.split(".")[-1]
    content = None

    if (ext == "md"):
        content = render_markdown(lfile)
    elif (ext in codes):
        content = render_code(lfile)
    else:
        if (isbin(lfile) == False):
            with open(lfile, 'r') as file:
                data = file.read().replace("\n", "<br>")
                return (data)
        return ("Binary File")
    return (content)

def process_dir(ldir):
    files = []
    for file in listdir(ldir):
        if (file[0] == '.'):
            continue
        if (path.isdir(ldir + file)):
            files.append({
                "filename" : file + "/",
                "type" : "dir"
                })
        else :
            files.append({
                "filename" : file,
                "type" : "file"
                })
    return files

def process(upath):
    response = {
            "type" : None,
            "contents" : None
            }
    if (path.exists(upath) == False):
        return False
    if (path.isdir(upath)):
        response["contents"] = process_dir(upath)
        response["type"] = "directory"
    else :
        response["type"] = "file"
        response["contents"] = process_file(upath)

    return (response)

@app.route("/ls")
def ls():
    path = getcwd() + "/content" + request.args.get("path")
    return (json.dumps(process(path)))

@app.route('/content/<path:filename>')
def serve_file(filename):
    return send_from_directory('../content', filename)

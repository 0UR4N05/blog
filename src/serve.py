from src.init import app
from flask import request
from os import getcwd, path, listdir
from src.render import render_markdown, render_code
import json
import chardet

def process_file(lfile):
    codes = ["lua", "py", "c", "cxx", "cpp", "rs", "js", "log", "sh", "s", "json", "yml"]
    ext = lfile.split(".")[-1]
    content = None

    if (ext == "md"):
        content = render_markdown(lfile)
    elif (ext in codes):
        content = render_code(lfile)
    else:
        with open(lfile, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            if (result["encoding"] == "ascii"):
                return (raw_data)
            return (None)
    return (content)

def process_dir(ldir):
    files = []
    for file in listdir(ldir):
        if (path.isdir(ldir + file)):
            files.append(file + "/")
        else :
            files.append(file)
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
    response = process(path)
    if (response["contents"] == None):
        response["type"] = "link"
        response["contents"] = "/content" + request.args.get("path")
    return (json.dumps(response))

@app.route('/content/<path:filename>')
def serve_from_directory(filename):
    return send_from_directory('content', filename)

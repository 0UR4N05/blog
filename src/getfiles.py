from src.const import dirimg, fileimg, fdirimg
import time
import os

def return_files(cdir = "content/"):
    purelink = cdir
    purelink = purelink.replace("content/", "")
    base_files = []
    # include base dirs
    basedirs = [".", "../"]
    for i in range(2):
        file = {}
        file["link"] = basedirs[i]
        file["image"] = dirimg
        file["filename"] = basedirs[i]
        file["file_size"] = "0"
        file["date"] = "0"
        base_files.append(file)
    if (os.path.isfile(cdir)):
        return (base_files)
    for filex in os.scandir(cdir) :
        file = {}
        if (filex.name[0] == '.' or filex.name[0] == '_'):
            continue
        if (len(purelink) > 0 and purelink[0] != '/'):
            purelink = "/" + purelink
        file["link"] = purelink +"/"+ filex.name
        file["date"] = time.ctime(os.path.getctime(cdir + "/" + filex.name))
        if filex.is_file():
            file["file_size"] = filex.stat(follow_symlinks=False).st_size
            file["image"] = fileimg
        else :
            file["image"] = fdirimg
            if (len(os.listdir(cdir)) == 0):
                file["image"] = dirimg
            file["file_size"] = "0"

        file["filename"] = filex.name
        base_files.append(file)
    return(base_files)

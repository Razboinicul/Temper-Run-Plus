from pythonic_archive_kit import PAK, save_pak, load_pak
from tempfile import gettempdir
from platform import system
from os import chdir, makedirs, getcwd, path
if system() == "Windows":
    tmpdir = gettempdir()+"\\trtemp"
else:
    tmpdir = gettempdir()+"/trtemp"

def set_high_score(score: int = 0):
    pak = load_pak("data.pak")
    pak.high_score = score
    save_pak(pak, "data.pak")

def save():
    pak = PAK()
    pak.high_score = 0
    pak.files = {}
    pak.files['bg.png'] = open('bg.png', 'rb+').read()
    pak.files['character_run.png'] = open('character_run.png', 'rb+').read()
    pak.files['Space.png'] = open('Space.png', 'rb+').read()
    pak.files['spikes_1.png'] = open('spikes_1.png', 'rb+').read()
    pak.files['spikes_2.png'] = open('spikes_2.png', 'rb+').read()
    save_pak(pak, "data.pak")

def load():
    pak = load_pak("data.pak")
    if path.exists(tmpdir):
      chdir(tmpdir)
    else:
      makedirs(tmpdir)
      chdir(tmpdir)
    for i in pak.files.keys():
        f = open(i, "wb+")
        f.write(pak.files[i])
        f.close()
    return pak.high_score

if __name__ == "__main__":
    ...
    #save()
    #load()

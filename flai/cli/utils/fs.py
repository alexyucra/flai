def write_utf8(path, content):
    path.write_text(content, encoding="utf-8")

def read_utf8(path):
    return path.read_text(encoding="utf-8")

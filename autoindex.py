from argparse import ArgumentParser
from os import walk, chdir, getcwd
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime
from jinja2 import Environment, BaseLoader, select_autoescape

env = Environment(
    loader=BaseLoader,
    autoescape=select_autoescape(['html', 'xml'])
)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Index of "{{ root.name }}"</title>
    <style type="text/css">
        @media only screen and (min-width: 900px) {
            .autoindex { max-width: 900px; margin-left: auto; margin-right: auto; }
            .header { max-width: 900px; margin-left: auto; margin-right: auto; }
        }

        @media only screen and (max-width: 440px) {
            .autoindex .date { display: none; }
            .autoindex .breadscrumbs { display: none; }
            .autoindex .resource { max-width: 150px; text-overflow: ellipsis; overflow: hidden; }
        }

        body { padding: 10px; background-color: #212121; font-family: sans-serif; }
        .autoindex .breadscrumbs a:hover { color: #ffffff; }
        a, body { color: #dad379; }
        .autoindex table { text-overflow: ellipsis; overflow: hidden; white-space: nowrap; }
        .autoindex table, .autoindex td, .autoindex tr { border: 0; border-spacing: 0; }
        .autoindex { padding: 1% 3% 2% 3%; background-color: #3d3f41; border-radius: 10px; }
        .autoindex table td:children { display: block; }
        .autoindex table td * { display: block; }
        .even { background-color: #303030; }
        .autoindex a { text-decoration: none; }
        .autoindex .date { max-width: 150em; }
        .autoindex .size { text-align: right; }
        .autoindex .even:hover, .autoindex .odd:hover { background-color: #15283c; }
        .autoindex .even { background-color: #383a3c; }
        .autoindex .directory::before { content: "📁  "; }
        .autoindex .file::before { content: "📄 "; }
        .autoindex .file-sig::before { content: "🔏 "; }
        .autoindex .file-gz::before { content: "🗜 "; }
        .autoindex .file-ipk::before { content: "📦 "; }
        .autoindex .file-buildinfo::before { content: "🧾 "; }
        .autoindex .file-bin::before { content: "🗄 "; }
        .autoindex .file-manifest::before { content: "🗒 "; }
        .header {
            background: #313131;
            padding: 1% 3% 2% 3%;
            margin-bottom: 20px;
            border-radius: 10px;
            display: block;
            color: #f9f9f9;
            line-height: 1.4;
        }
        .header .note {
            padding: 2%;
            margin-bottom: 20px;
            border-radius: 10px;
            display: block;
            color: #ffffff;
        }
        .header .note { background: #414141; }
        .header .note { background: #414141; }
        .header .warn { background: #616131; }
        .header .error { background: #613131; }
        .header img {
            padding: 0;
            max-width: 100%;
            display: block;
            margin: 2%;
            border-radius: 10px;
        }
        .header pre {
            font-size: 120%;
            background: #111111; 
            padding: 10px; 
            border-radius: 5px;
            word-break: break-all;
            white-space: pre-line; 
        }
        .header pre.inline { display: inline; padding: 1px 5px 1px 5px; }
        .header table {
            margin: 10px;
            border: 1px solid;
            border-color: #f1f1f1;
            border-collapse: collapse;
            border-spacing: 0;
        }
        .header table th {text-align: center; background-color: #414141; }
        .header table th, .header table td {
            padding: 10px;
            border: 1px solid;
        }
        .header ul, .header ol {
            line-height: 1.5;
        }
        .header li {
            margin-top: 0.5em;
            margin-bottom: 0.5em;
        }
        .center {text-align: center;}
    </style>
</head>
<body>
{% if header %}<div class="header">{{ header | safe }}</div>{% endif %}
<div class="autoindex">
    <h1 class="breadscrumbs"><a href="{{ root_path }}">/</a>{% for part in root.relative_to(base).parts %}<a href="{{ "../" * loop.revindex0 }}">{{ part }}</a>/{% endfor %}</h1>
    <table width="100%">
    {% if root.parts %}
	<tr class="odd">
        <td><a class="item directory" href="..">..</a></td>
	    <td width="150em">–</td>
	    <td></td>

	</tr>
    {% endif %}
	{%- for directory in dirs %}
	{%- set elem_class = "even" if loop.index0 % 2 == 0 else "odd" %}
	<tr class="{{ elem_class }}">
	    <td class="resource"><a class="item directory" href="{{ directory }}">{{ directory }}</a></td>
	    <td class="date"><div>{{ directory.stat().st_ctime | timestamp_format }}</div></td>
	    <td class="size"><div>{{ directory | dir_size | humanize }}</div></td>
	</tr>
	{%- endfor %}
	{%- for file in files %}
	{%- set elem_class = "even" if loop.index0 % 2 == 0 else "odd" %}
	<tr class="{{ elem_class }}">
        {%- set kind = file.suffix.strip('.').lower() %}
	    <td class="resource"><a class="item file {% if kind %}file-{{ kind }}{% endif %}" href="{{ file }}">{{ file }}</a></td>
	    <td class="date"><div>{{ file.stat().st_ctime | timestamp_format }}<div></td>
	    <td class="size"><div>{{ file.stat().st_size | humanize }}</div></td>
	</tr>
	{%- endfor %}
    </table>
</div>
</body>
</html>
"""

def timestamp_format(ts):
    dt = datetime.utcfromtimestamp(ts)
    return dt.isoformat(" ", timespec="minutes")


def humanize(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def dir_size(path):
    path = Path(path)
    count = 0
    for child in path.glob("**/*"):
        if not child.is_file:
            continue
        count += child.stat().st_size
    return count


@contextmanager
def cd(path):
    cwd = getcwd()
    chdir(path)
    try:
        yield
    finally:
        chdir(cwd)


env.filters['timestamp_format'] = timestamp_format
env.filters['humanize'] = humanize
env.filters['dir_size'] = dir_size


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--index-name", default="index.html")
    parser.add_argument("--header-name", default="header.html")
    parser.add_argument("--root-path", default="/")

    arguments = parser.parse_args()

    template = env.from_string(TEMPLATE)

    def files_filter(fpath: Path) -> bool:
        if fpath.name == arguments.index_name:
            return False
        if fpath.name == arguments.header_name:
            return False
        if fpath.name.endswith(".py"):
            return False
        if fpath.name.startswith("."):
            return False
        return True

    def filter_dirs(path: Path) -> bool:
        for part in path.parts:
            if part.startswith("."):
                return False
        return True

    for root, dirs, files in walk(str(arguments.directory), topdown=False):
        root = Path(root)
        if not filter_dirs(root):
            continue

        fname = root / arguments.index_name

        print("Creating", fname)

        with open(fname, "w") as fp, cd(root):
            header_path = root / arguments.header_name
            header = None
            if header_path.exists():
                header = open(header_path).read()

            fp.write(
                template.render(
                    base=arguments.directory,
                    root=Path(root),
                    dirs=sorted(filter(filter_dirs, map(Path, dirs))),
                    files=sorted(filter(files_filter, map(Path, files))),
                    header=header,
                    root_path=arguments.root_path,
                )
            )


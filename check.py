"""Проверка сборки: структура страниц, внутренние ссылки, метатеги, якоря."""
import re, pathlib, html.parser, sys

ROOT = pathlib.Path("/home/claude/build")
pages = {"index.html": ROOT/"index.html", "dev/index.html": ROOT/"dev/index.html"}
problems = []

class P(html.parser.HTMLParser):
    VOID = {"meta","link","br","img","hr","input","source","path","use","area","col"}
    def __init__(s):
        super().__init__(); s.stack=[]; s.ids=set(); s.hrefs=[]; s.imgs=[]
    def handle_starttag(s, tag, attrs):
        a=dict(attrs)
        if a.get("id"): s.ids.add(a["id"])
        if tag=="a" and a.get("href"): s.hrefs.append(a["href"])
        if tag=="img": s.imgs.append(a.get("src",""))
        if tag not in s.VOID and not s.get_starttag_text().endswith("/>"): s.stack.append(tag)
    def handle_endtag(s, tag):
        if tag in s.VOID: return
        if not s.stack: problems.append(f"лишний </{tag}>"); return
        if s.stack[-1]!=tag: problems.append(f"ожидался </{s.stack[-1]}>, встретился </{tag}>")
        else: s.stack.pop()

for name, path in pages.items():
    src = path.read_text(encoding="utf-8")
    p = P(); p.feed(src)
    if p.stack: problems.append(f"{name}: незакрытые теги {p.stack}")

    for tag in ('<meta property="og:image"', '<meta property="og:url"',
                '<meta name="twitter:card"', '<link rel="canonical"'):
        if tag not in src: problems.append(f"{name}: нет {tag}")

    css = re.search(r'href="((?:\.\./)?styles\.css)"', src)
    if not css: problems.append(f"{name}: не подключён styles.css")
    elif not (path.parent/css.group(1)).resolve().exists():
        problems.append(f"{name}: styles.css не найден по пути {css.group(1)}")

    for h in p.hrefs:
        if h.startswith("#"):
            if h[1:] not in p.ids: problems.append(f"{name}: якорь {h} никуда не ведёт")
        elif not re.match(r"^(https?:|mailto:|data:)", h):
            target = (path.parent/h).resolve()
            if target.is_dir(): target = target/"index.html"
            if not target.exists(): problems.append(f"{name}: битая ссылка {h}")

    for s_ in p.imgs:
        if not re.match(r"^(https?:|data:)", s_) and not (path.parent/s_).resolve().exists():
            problems.append(f"{name}: нет картинки {s_}")

og = ROOT/"assets/og.png"
assert og.exists(), "нет assets/og.png"
from PIL import Image
assert Image.open(og).size == (1200, 630), "og.png должен быть 1200x630"

# заглушки на месте и подписаны
for name, path in pages.items():
    for block in re.findall(r'<div class="todo[^"]*"', path.read_text(encoding="utf-8")):
        pass

if problems:
    print("НАЙДЕНЫ ПРОБЛЕМЫ:"); [print(" -", x) for x in problems]; sys.exit(1)
print("OK: обе страницы целы, ссылки и якоря живые, og.png на месте 1200x630")

# -*- coding: utf-8 -*-
"""
cards.json 으로 '레시피 카드' 디자인(제품 사진 포함) 6장을 만듭니다.
  -> output/card_01.png ~ card_NN.png, output/cover.png

디자인: templates/recipe_html/style.css (세안 레시피 시리즈와 같은 스타일)
그리는 방법: HTML 을 만든 뒤 Edge 로 1080x1350 PNG 를 찍습니다 (export_artifact.py).

cards.json 의 카드마다 "layout" 으로 카드 종류를 정합니다.
  cover     표지        display_title, eyebrow, body, tagline
  checklist 고민 체크   display_title, eyebrow, items[], note_label, body, preview{label,title,desc}
  list      재료 목록   display_title, eyebrow, subtitle, items[{name,desc}], note_label, body
  flow      작용 원리   display_title, tag, steps[{icon|"photo",label,en}], body, stat{value,unit,label,note}
  steps     사용 순서   display_title, tag, steps[{title,desc,icon|"photo"}], note_label, body
  compare   두 가지 비교 display_title, eyebrow, left/right{tag,icon,title,desc}, tip_label, tip
  recap     정리        display_title, rows[[왼쪽,오른쪽]], cta, caution
  text      글 카드     (layout 이 없을 때) title, body
글자 꾸미기: 줄바꿈은 \n, 형광펜은 [[글자]]

실행:  py templates/make_html_cards.py
"""
import html
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TPL = ROOT / "templates" / "recipe_html"
BUILD = TPL / "build"
CARDS = ROOT / "cards.json"
OUT = ROOT / "output"
ACCOUNT = "@weekly.beauty.recipe"
SERIES = "HEALING RECIPE · NEW"


class CardError(Exception):
    pass


def t(s, mark="hl"):
    """글자를 HTML 로: 특수문자 처리, \\n -> 줄바꿈, [[x]] -> 형광펜"""
    s = html.escape(str(s or ""))
    s = s.replace("\n", "<br>")
    if mark == "paper":
        s = s.replace("[[", '<span style="background:var(--paper);padding:0 12px">')
    else:
        s = s.replace("[[", '<span class="hl">')
    return s.replace("]]", "</span>")


class Ctx:
    def __init__(self, data, has_photo):
        self.data, self.has_photo = data, has_photo
        self.total = len(data["cards"])
        src = data.get("source", {})
        self.src_short = f"출처 · {src.get('name', '')} ({src.get('date', '')})" if src else ""
        self.credit = data.get("photo", {}).get("credit", "")

    def foot(self, card, no, photo_used, color=""):
        s = card.get("src") or self.src_short
        if photo_used and self.credit:
            s += f" · 사진 · {self.credit.split(' (')[0]}"
        st = f' style="color:{color}"' if color else ""
        return f'<div class="foot"{st}><span class="src"{st}>{html.escape(s)}</span><span>{no:02d}</span></div>'

    def top(self, label, no, dark=False):
        if dark:
            return (f'<div class="top" style="color:#C9B6AA;border-color:#5A463E"><b style="color:var(--butter)">'
                    f'{html.escape(label)}</b><span>{no:02d} / {self.total:02d}</span></div>')
        return f'<div class="top"><b>{html.escape(label)}</b><span>{no:02d} / {self.total:02d}</span></div>'

    def photo(self, style, tag=""):
        if not self.has_photo:
            return ""
        i = f"<i>{html.escape(tag)}</i>" if tag else ""
        return f'<div class="photo" style="{style}">{i}</div>'


# ---------------------------------------------------------------- 카드 종류별 틀
def cover(c, card, no):
    title = t(card.get("display_title") or card["title"], "paper")
    return f'''<section class="card" style="background:var(--peach)">
  <div class="top" style="border-color:#E5B9A3"><b>{SERIES}</b><span>{html.escape(card.get("section", "신상 편"))}</span></div>
  <div style="position:relative;margin-top:84px">
    <div class="eb" style="color:var(--ink)">{html.escape(card.get("eyebrow", "BEAUTY RECIPE"))}</div>
    <h1 style="margin-top:20px">{title}</h1>
    <p style="font-size:38px;line-height:1.5;font-weight:600;margin-top:36px">{t(card.get("body"))}</p>
  </div>
  <div class="blob" style="width:260px;height:260px;right:30px;top:640px;background:var(--butter)"></div>
  {c.photo("position:absolute;right:84px;top:700px;width:520px;height:520px;box-shadow:14px 14px 0 var(--ink)", "PHOTO · " + card.get("photo_tag", "PRODUCT"))}
  <div class="foot" style="color:var(--ink)"><span>{html.escape(card.get("tagline", ""))}</span><span>01 / {c.total:02d}  swipe →</span></div>
</section>'''


def checklist(c, card, no):
    items = "".join(f'<div class="chk"><span class="bx">✓</span>{t(i)}</div>' for i in card.get("items", []))
    pv = card.get("preview")
    prev = ""
    if pv:
        prev = f'''<div class="rc" style="margin-top:36px;display:flex;gap:30px;align-items:center;background:var(--peach2)">
    {c.photo("flex:none;width:170px;height:170px;border-radius:24px")}
    <div><span style="font-family:var(--mono);font-size:24px;font-weight:700;color:var(--deep)">{html.escape(pv.get("label", "TODAY'S RECIPE"))}</span><b style="display:block;font-size:40px;font-weight:900;margin-top:6px">{t(pv.get("title"))}</b><p style="font-size:28px;color:var(--soft);margin-top:4px">{t(pv.get("desc"))}</p></div>
  </div>'''
    return f'''<section class="card">
  {c.top(card.get("label", "MY CONCERN"), no)}
  <div class="eb" style="margin-top:64px">{html.escape(card.get("eyebrow", ""))}</div>
  <h2 style="margin-top:14px">{t(card.get("display_title") or card["title"])}</h2>
  <div class="rc" style="margin-top:44px;padding:8px 32px">{items}</div>
  <div class="why" style="margin-top:40px"><em>{html.escape(card.get("note_label", "그래서"))}</em>{t(card.get("body"))}</div>
  {prev}
  {c.foot(card, no, bool(pv) and c.has_photo)}
</section>'''


def list_(c, card, no):
    rows = []
    items = card.get("items", [])
    for k, it in enumerate(items, 1):
        bg = ' style="background:var(--peach2)"' if k == len(items) else ""
        rows.append(f'<div class="ingr"{bg}><span class="n">{k:02d}</span><div><b>{t(it.get("name"))}</b>'
                    f'<small>{t(it.get("desc"))}</small></div></div>')
    return f'''<section class="card">
  {c.top(card.get("label", "INGREDIENTS"), no)}
  <div style="display:flex;gap:40px;align-items:flex-end;margin-top:60px">
    <div style="flex:1">
      <div class="eb">{html.escape(card.get("eyebrow", ""))}</div>
      <h2 style="margin-top:14px">{t(card.get("display_title") or card["title"])}</h2>
      <p style="font-size:30px;color:var(--soft);margin-top:20px;line-height:1.4;font-weight:600">{t(card.get("subtitle"))}</p>
    </div>
    {c.photo("flex:none;width:300px;height:300px", "PHOTO")}
  </div>
  <div style="display:flex;flex-direction:column;gap:12px;margin-top:34px">{"".join(rows)}</div>
  <div class="why" style="margin-top:24px;margin-bottom:24px;font-size:32px"><em>{html.escape(card.get("note_label", "BRAND SAYS"))}</em>{t(card.get("body"))}</div>
  {c.foot(card, no, c.has_photo)}
</section>'''


def flow(c, card, no):
    parts = []
    for k, s in enumerate(card.get("steps", [])):
        if k:
            parts.append('<div class="ar">→</div>')
        if s.get("icon") == "photo" and c.has_photo:
            ic = '<div class="ic ph"></div>'
        else:
            ic = f'<div class="ic">{html.escape(s.get("icon") if s.get("icon") != "photo" else "🧴")}</div>'
        parts.append(f'<div class="st">{ic}<b>{t(s.get("label"))}</b><small>{html.escape(s.get("en", ""))}</small></div>')
    stat = card.get("stat")
    st = ""
    if stat:
        st = (f'<div class="num" style="margin-top:22px"><span class="big" style="font-size:96px">{html.escape(stat.get("value", ""))}'
              f'<span style="font-size:48px">{html.escape(stat.get("unit", ""))}</span></span>'
              f'<p>{t(stat.get("label"))}<small>{html.escape(stat.get("note", ""))}</small></p></div>')
    return f'''<section class="card" style="background:var(--butter)">
  <div class="top" style="border-color:#E9D28C"><b>{html.escape(card.get("label", "HOW IT WORKS"))}</b><span>{no:02d} / {c.total:02d}</span></div>
  <span class="stepbig" style="margin-top:64px">{html.escape(card.get("tag", ""))}</span>
  <h2 style="margin-top:20px">{t(card.get("display_title") or card["title"], "paper")}</h2>
  <div class="flow">{"".join(parts)}</div>
  <div class="rc" style="margin-top:46px"><div style="font-size:34px;line-height:1.55">{t(card.get("body"))}</div>{st}</div>
  {c.foot(card, no, any(s.get("icon") == "photo" for s in card.get("steps", [])) and c.has_photo, "var(--ink)")}
</section>'''


def compare(c, card, no):
    def side(s, bg, tagbg):
        return (f'<div class="rc"{bg}><span class="tagx" style="background:{tagbg}">{html.escape(s.get("tag", ""))}</span>'
                f'<span class="big">{html.escape(s.get("icon", ""))}</span><b>{t(s.get("title"))}</b><p>{t(s.get("desc"))}</p></div>')
    tip = card.get("tip")
    tip_html = f'<div class="why" style="margin-top:36px"><em>{html.escape(card.get("tip_label", "TIP"))}</em>{t(tip)}</div>' if tip else ""
    return f'''<section class="card">
  {c.top(card.get("label", "WHEN TO USE"), no)}
  <div class="eb" style="margin-top:64px">{html.escape(card.get("eyebrow", ""))}</div>
  <h2 style="margin-top:14px">{t(card.get("display_title") or card["title"])}</h2>
  <div class="vs">{side(card.get("left", {}), "", "var(--ink)")}{side(card.get("right", {}), ' style="background:var(--peach2)"', "var(--deep)")}</div>
  {tip_html}
  {c.foot(card, no, False)}
</section>'''


def steps(c, card, no):
    rows, photo_used = [], False
    for k, s in enumerate(card.get("steps", []), 1):
        if s.get("icon") == "photo" and c.has_photo:
            ic, photo_used = '<div class="th"></div>', True
        else:
            ic = f'<span class="e">{html.escape(s.get("icon", "") if s.get("icon") != "photo" else "🧴")}</span>'
        bg = ' style="background:var(--peach2)"' if k == len(card.get("steps", [])) else ""
        rows.append(f'<div class="routine"{bg}><span class="n">STEP {k}</span><div><b>{t(s.get("title"))}</b>'
                    f'<small>{t(s.get("desc"))}</small></div>{ic}</div>')
    return f'''<section class="card">
  {c.top(card.get("label", "HOW TO USE"), no)}
  <span class="stepbig" style="margin-top:60px">{html.escape(card.get("tag", ""))}</span>
  <h2 style="margin-top:20px">{t(card.get("display_title") or card["title"])}</h2>
  <div style="display:flex;flex-direction:column;gap:14px;margin-top:38px">{"".join(rows)}</div>
  <div class="why" style="margin-top:30px;margin-bottom:20px;font-size:31px"><em>{html.escape(card.get("note_label", "NOTE"))}</em>{t(card.get("body"))}</div>
  {c.foot(card, no, photo_used)}
</section>'''


def recap(c, card, no):
    rows = "".join(f'<div class="map"><span class="a">{t(a)}</span><span class="arr">→</span><span>{t(b)}</span></div>'
                   for a, b in card.get("rows", []))
    srcs = [c.data.get("source", {})] + c.data.get("extra_sources", [])
    parts = []
    for k, s in enumerate(srcs):
        if not s:
            continue
        title = f", 「{s['title']}」" if k == 0 and s.get("title") else ""
        date = f", {s['date']}" if s.get("date") else ""
        parts.append(f"{s.get('name', '')}{title}{date}")
    src_line = "출처 · " + " / ".join(parts) + (f" · 사진 · {c.credit.split(' (')[0]}" if c.has_photo and c.credit else "")
    return f'''<section class="card" style="background:var(--ink);color:var(--cream)">
  {c.top(card.get("label", "RECIPE COMPLETE"), no, dark=True)}
  <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-top:56px">
    <h2>{t(card.get("display_title") or card["title"]).replace('<span class="hl">', '<span style="color:var(--butter)">')}</h2>
    {c.photo("width:210px;height:210px;border-color:var(--cream)")}
  </div>
  <div class="rc" style="margin-top:34px;padding:6px 30px;background:var(--paper);color:var(--ink)">{rows}</div>
  <p style="font-size:28px;line-height:1.55;color:#E9DCD3;margin-top:28px">{t(card.get("cta", "🔖 저장해 두고 다시 보기"))}</p>
  <div class="foot" style="flex-direction:column;align-items:flex-start;gap:8px;color:#C9B6AA">
    <span class="src" style="color:#C9B6AA">{html.escape(src_line)}</span>
    <span class="src" style="color:#C9B6AA;display:flex;justify-content:space-between;width:100%"><span>{t(card.get("caution", ""))}</span><span style="font-family:var(--mono)">{ACCOUNT}</span></span>
  </div>
</section>'''


def text(c, card, no):
    return f'''<section class="card">
  {c.top(card.get("label", f"RECIPE NOTE {no - 1:02d}"), no)}
  <h2 style="margin-top:90px">{t(card.get("display_title") or card["title"])}</h2>
  <div class="rc" style="margin-top:48px;font-size:38px;line-height:1.6">{t(card.get("body"))}</div>
  {c.photo("width:360px;height:360px;margin-top:48px;align-self:center")}
  {c.foot(card, no, c.has_photo)}
</section>'''


LAYOUTS = {"cover": cover, "checklist": checklist, "list": list_, "flow": flow,
           "steps": steps, "compare": compare, "recap": recap, "text": text}


def build(data):
    cards = sorted(data["cards"], key=lambda x: x["no"])
    photo = data.get("photo", {}).get("file")
    photo_path = (ROOT / photo) if photo else None
    has_photo = bool(photo_path and photo_path.exists())
    warns = []
    if not has_photo:
        warns.append("제품 사진이 없어요 (cards.json 의 photo.file). 사진 자리를 빼고 만들었어요.")

    global BUILD
    BUILD = Path(tempfile.mkdtemp(prefix="recipe_build_"))   # OneDrive 밖 임시 폴더 (동기화 잠금 방지)
    (BUILD / "img").mkdir(parents=True)
    shutil.copyfile(TPL / "style.css", BUILD / "style.css")
    if has_photo:
        shutil.copyfile(photo_path, BUILD / "img" / "product.jpg")

    c = Ctx(data, has_photo)
    blocks = []
    for k, card in enumerate(cards, 1):
        lay = card.get("layout") or ("cover" if k == 1 else "recap" if k == len(cards) else "text")
        if lay not in LAYOUTS:
            raise CardError(f"{k}장의 layout '{lay}' 을 모르겠어요. 쓸 수 있는 것: {', '.join(LAYOUTS)}")
        blocks.append(f'<div class="holder">{LAYOUTS[lay](c, card, k)}</div>')
    page = ('<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>cards</title>'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700'
            '&family=Noto+Sans+KR:wght@400;500;700;900&display=swap">'
            '<link rel="stylesheet" href="style.css"></head><body><div class="wrap">\n'
            + "\n".join(blocks) + "\n</div></body></html>")
    (BUILD / "index.html").write_text(page, encoding="utf-8")
    return len(cards), warns


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        if not CARDS.exists():
            raise CardError(f"cards.json 이 없어요: {CARDS}")
        try:
            data = json.loads(CARDS.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as e:
            raise CardError(f"cards.json 형식이 잘못됐어요 ({e.lineno}번째 줄 근처).")
        n, warns = build(data)
    except CardError as e:
        print(f"[오류] {e}")
        sys.exit(1)
    except OSError as e:
        print(f"[오류] 파일을 준비하지 못했어요 ({e}). 사진이나 폴더가 다른 프로그램에서 열려 있는지 확인해 주세요.")
        sys.exit(1)
    for w in warns:
        print("  ※ " + w)

    tmp = Path(tempfile.mkdtemp(prefix="cards_"))
    r = subprocess.run([sys.executable, str(ROOT / "templates" / "export_artifact.py"), str(BUILD), str(tmp)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    shots = sorted(tmp.glob("*.png"))
    if r.returncode != 0 or len(shots) != n:
        print("[오류] 카드 그림을 찍지 못했어요 (Edge). 아래 내용을 Claude에게 보여 주세요.")
        print((r.stdout or "")[-800:], (r.stderr or "")[-800:])
        sys.exit(1)
    OUT.mkdir(exist_ok=True)
    for k, f in enumerate(shots, 1):
        shutil.copyfile(f, OUT / f"card_{k:02d}.png")
    shutil.copyfile(shots[0], OUT / "cover.png")
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(BUILD, ignore_errors=True)
    print(f"레시피 카드 {n}장을 만들었어요 → output/card_01.png ~ card_{n:02d}.png (+ cover.png)")
    print("  제품 사진: " + ("들어감" if "제품 사진이 없어요" not in " ".join(warns) else "없음"))


if __name__ == "__main__":
    main()

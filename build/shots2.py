import os
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTD = os.path.join(ROOT,"screenshots"); os.makedirs(OUTD,exist_ok=True)  # git-ignored
TMP = OUTD
CHROME = os.environ.get("CHROME_PATH")  # optional: use a system Chrome instead of Playwright's Chromium
URL="file://"+os.path.join(ROOT,"index.html").replace(os.sep,"/") if os.sep=="/" else "file:///"+os.path.join(ROOT,"index.html").replace(os.sep,"/")
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=["--no-sandbox"]) if CHROME else p.chromium.launch()
    def page(w,scheme="light",mobile=False):
        ctx=b.new_context(viewport={"width":w,"height":844 if mobile else 900},device_scale_factor=2 if mobile else 1,is_mobile=mobile,has_touch=mobile,color_scheme=scheme)
        pg=ctx.new_page(); pg.goto(URL); pg.wait_for_load_state("networkidle")
        # trigger lazy images for full-page shots
        pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')"); pg.wait_for_timeout(300)
        assert pg.evaluate("document.documentElement.scrollWidth")<=w, f"overflow at {w}"
        return pg
    for w in [1280,1000,900,820]:
        pg=page(w); pg.click("#m-reo-poe button.more"); pg.screenshot(path=os.path.join(OUTD,f"shot2-{w}.png"),full_page=True)
    m=page(390,mobile=True); m.click("#m-reo-poe button.more"); m.screenshot(path=os.path.join(OUTD,f"shot2-390.png"),full_page=True)
    d=page(1280,"dark"); d.click("#m-reo-poe button.more"); d.screenshot(path=os.path.join(OUTD,f"shot2-1280-dark.png"),full_page=True)
    # review extras: jump + flash, toggle persistence
    j=page(1280); j.click("a.jump[data-ids=tapo-d230]"); j.wait_for_timeout(700); j.screenshot(path=os.path.join(TMP,"jump.png"))
    j.click("#theme"); print("stored:",j.evaluate("localStorage.getItem('theme')"),"attr:",j.evaluate("document.documentElement.dataset.theme"))
    j.reload(); print("after reload attr:",j.evaluate("document.documentElement.dataset.theme"),"btn:",j.inner_text("#theme"))
    j.screenshot(path=os.path.join(TMP,"dark-top.png"))
    b.close()

import sys
import os
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTD = os.path.join(ROOT,"screenshots"); os.makedirs(OUTD,exist_ok=True)  # git-ignored
TMP = OUTD
CHROME = os.environ.get("CHROME_PATH")  # optional: use a system Chrome instead of Playwright's Chromium
URL="file://"+os.path.join(ROOT,"index.html").replace(os.sep,"/") if os.sep=="/" else "file:///"+os.path.join(ROOT,"index.html").replace(os.sep,"/")
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME,args=["--no-sandbox"]) if CHROME else p.chromium.launch()
    pg=b.new_page(viewport={"width":1280,"height":900})
    pg.goto(URL); pg.screenshot(path=os.path.join(OUTD,f"shot-desktop.png"),full_page=True)
    # interaction: compare + detail open
    pg.check("input.cmp[value=reo-poe]"); pg.check("input.cmp[value=tapo-d230]"); pg.check("input.cmp[value=ring]")
    pg.click("#tray-go"); pg.click("#m-eufy-e340 button.more")
    pg.screenshot(path=os.path.join(TMP,"desk-compare.png"),full_page=True)
    # filter
    pg.click("#tray-clear"); pg.check("#f-rec"); pg.check(".f-pw[value=battery]"); pg.fill("#f-max","100"); pg.dispatch_event("#f-max","input")
    pg.screenshot(path=os.path.join(TMP,"desk-filter.png"),full_page=False)
    print("count shown:",pg.inner_text("#count"))
    # sticky header check
    pg.click("#reset"); pg.evaluate("window.scrollTo(0,900)"); pg.screenshot(path=os.path.join(TMP,"desk-sticky.png"))
    m=b.new_page(viewport={"width":390,"height":844},device_scale_factor=2,is_mobile=True,has_touch=True)
    m.goto(URL); m.screenshot(path=os.path.join(OUTD,f"shot-phone.png"),full_page=True)
    m.check("input.cmp[value=reo-poe]"); m.check("input.cmp[value=tapo-d230]"); m.click("#tray-go"); m.click("#m-reo-poe button.more")
    m.screenshot(path=os.path.join(TMP,"phone-compare.png"),full_page=True)
    b.close()

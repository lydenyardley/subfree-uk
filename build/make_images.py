"""Crop/flatten/resize official product images into self-hosted WebP (thumb 120x160, large 360x480).
Sources are recorded in images.json (also used by build.py)."""
import json, os, io, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
from PIL import Image, ImageChops
RAW=os.path.join(HERE,"img_raw"); OUT=os.path.join(ROOT,"img")  # img_raw/ is a git-ignored download cache
os.makedirs(RAW,exist_ok=True); os.makedirs(OUT,exist_ok=True)
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"}
# id: (image url, page it appears on, crop box as fractions l,t,r,b or None, trim whitespace?)
IMGS={
 "ring":("https://en-uk.ring.com/cdn/shop/files/1_Slate_Sunray_Front_ad46b95a-0b98-4a7e-8f06-0304b31312eb.jpg?v=1779257638","https://en-uk.ring.com/products/battery-doorbell-2nd-gen",None,True),
 "nest":("https://lh3.googleusercontent.com/7as7cJnLssK4ejvx-4zNQCRmNoupXijD6fkO4orVEB54bB0SRfQn75qzZNnT4Ud4gqOabRfO-8J0YIBRKkMG9yvK5QWKz2FwRQ=rw-rj-sc0xffffffff","https://store.google.com/gb/product/nest_doorbell_battery?hl=en-GB",None,True),
 "eufy-e340":("https://cdn.shopify.com/s/files/1/0504/1094/6753/files/T8214321-UK-DTC-RI00-ExpertReviews.png?v=1749789318","https://www.eufy.com/uk/products/T8214311",(0.55,0,1,1),True),
 "eufy-c31":("https://cdn.shopify.com/s/files/1/0504/1094/6753/files/E8223111_E8223J11_E8223J11-11_E8223T11_T8223111_T8223111-80__ProductImage_nocopy.png","https://www.eufy.com/uk/products/t8223311",None,True),
 "reo-wifi":("https://home-cdn.reolink.us/wp-content/uploads/2022/05/170610101652767810.7304.png","https://reolink.com/gb/product/reolink-video-doorbell-wifi/",(0,0,0.5,1),True),
 "reo-poe":("https://home-cdn.reolink.us/wp-content/uploads/2023/07/070730451688715045.0661.png","https://reolink.com/gb/product/reolink-video-doorbell-poe/",(0.5,0,1,1),True),
 "reo-batt":("https://home-cdn.reolink.us/wp-content/uploads/2024/10/doorbell-battery-1pack.png","https://reolink.com/gb/product/reolink-doorbell-battery/",None,True),
 "tapo-d230":("https://uk.store.tapo.com/cdn/shop/files/Tapo_D230S1_Wireless_Battery_Video_Doorbell_Chime_Hub_Included_54898c57-a43f-4e71-bde1-0a5a33cb0bc7.png?v=1757084237&width=2048","https://uk.store.tapo.com/products/tapo-d230s1-smart-battery-video-doorbell",(0.1,0,0.47,1),True),
 "tapo-td21":("https://uk.store.tapo.com/cdn/shop/files/0002290-RedesigntheDoorbellMainImage21.png?v=1776441614&width=2048","https://uk.store.tapo.com/products/battery-video-doorbell-2k-3mp-colour-night-vision-tapo-td21",(0.1,0,0.47,1),True),
 "arlo":("https://www.arlo.com/content/dam/arlo/2024-content/products/essential-wd-2k/en/si-compressed/arlo-2k-wireless-video-doorbell-white.png","https://www.arlo.com/en_gb/doorbells/arlo-2k-wireless-video-doorbell",None,True),
 "aqara-g4":("https://eu.aqara.com/cdn/shop/files/Aqara-Smart-Video-Doorbell-G4.webp?v=1729063964","https://eu.aqara.com/products/aqara-video-doorbell-g4",(0,0,0.46,1),True),
 "blink":("https://images.squarespace-cdn.com/content/v1/5e21c06a08d2fc435f20e6c5/feb6535d-c34d-48dd-a015-648dd5786bac/Blink_Battery_Doorbell_2K.png?format=1000w","https://blinkforhome.com/products",(0.30,0.02,0.72,0.98),False),
 "ezviz-ep3x":("https://mfs.ezvizlife.com/62d7d264ab031e75591d277638d4c440.png","https://www.ezviz.com/uk/product/ep3x-pro/55935",(0,0,0.255,1),True),
 "ezviz-db2":("https://s3.amazonaws.com/mfs.ezvizlife.com/f6a3b42474eefe13047add4b7b3c89c3.jpg","https://www.ezviz.com/uk/product/db2-pro-kit/42371",(0.28,0.2,0.43,0.79),True),
 "reo-argus4":("https://home-cdn.reolink.us/wp-content/uploads/2024/06/argus-4-pro-whitesolar-panel-2-white.png","https://reolink.com/gb/product/argus-4-pro/",None,True),
 "reo-rlc820a":("https://home-cdn.reolink.us/wp-content/uploads/2023/03/200425471679286347.6671.png","https://reolink.com/gb/product/rlc-820a/",None,True),
 "reo-e1out":("https://home-cdn.reolink.us/wp-content/uploads/2023/05/160805511684224351.237.png","https://reolink.com/gb/product/e1-outdoor-pro/",None,True),
 "tapo-c660":("https://uk.store.tapo.com/cdn/shop/files/Tapo_C660_KIT_Solar-Powered_Pan-Tilt-Zoom_4K_Security_Camera.jpg?v=1760541897&width=2048","https://uk.store.tapo.com/products/tapo-c660-kit-4k-clarity-solar-powered-pan-tilt-battery-security-camera-kit",None,True),
 "eufy-s340":("https://cdn.shopify.com/s/files/1/0746/3999/9151/files/T8170-DTC.png?v=1788149525","https://www.anker.com/uk/products/t81703w1",None,True),
 "eufy-e30":("https://cdn.shopify.com/s/files/1/0746/3999/9151/files/Frame_2147226768.png?v=1788149693","https://www.anker.com/uk/products/t8417221",None,True),
 "aqara-g3":("https://eu.aqara.com/cdn/shop/files/G3_1.webp","https://eu.aqara.com/products/aqara-2k-security-indoor-camera-hub-g3",None,True),
 "aqara-e1":("https://eu.aqara.com/cdn/shop/files/aqara-Camera_E1.webp?v=1774333578","https://eu.aqara.com/products/aqara-2k-indoor-security-camera-e1",None,True),
 "ring-outpro":("https://en-uk.ring.com/cdn/shop/files/Ring_GROUPER_White-Plugin_1500x1500_01.jpg?v=1757078401","https://en-uk.ring.com/products/stick-up-cam-pro-plug-in",None,True),
 # The Oura render sits on a studio gradient with the finish swatches below
 # it, so it is cropped rather than trimmed against white.
 "oura-4":("https://ourahealth.imgix.net/blue-sky/pop/gen4/finishes-carousel-slide-silver.png?ixlib=js-3.8.0&auto=format&fit=crop&fm=png&ar=2%3A1&crop=focalpoint&fp-x=0.5&fp-y=0.51&fp-z=1.15&q=70&w=1920&s=2e1d3272a6ead1f907787a0fde071870","https://ouraring.com/store/rings/oura-ring-4",(0.30,0.10,0.66,0.82),False),
 # Ring 5's studio shot sits on a warm background like the Ring 4 render, so it
 # is cropped to portrait rather than trimmed against white, which would have
 # framed it in a white border.
 "oura-5":("https://ourahealth.imgix.net/cooper-pdp/or5-silver-alt.png?ixlib=js-3.8.0&auto=format&fit=max&fm=png&q=70&w=640&s=c1abb1ce6418079507b352bab9ce96da","https://ouraring.com/store/rings/oura-ring-5/silver",(0.22,0.04,0.78,0.96),False),
 "ultra-air":("https://public-web-assets.uh-static.com/web_v2/illustrations/ring-air-front.png","https://www.ultrahuman.com/ring/",None,True),
 "rc-2":("https://ringconn.com/cdn/shop/files/RingConn_Smart_Ring_Gen_2-Royal_Gold.png?v=1780302336&width=1200","https://ringconn.com/products/ringconn-gen-2",None,True),
 "rc-2-air":("https://ringconn.com/cdn/shop/files/ringconn_gen_2_air_1.png?v=1780302386&width=600","https://ringconn.com/products/ringconn-gen-2-air",None,True),
 "rc-3":("https://ringconn.com/cdn/shop/files/1a_9e4056a6-6b65-41d1-804e-03aaa2818425.webp?v=1780302453&width=600","https://ringconn.com/products/ringconn-gen-3",None,True),
 "samsung-ring":("https://images.samsung.com/is/image/samsung/p6pim/uk/2407/gallery/uk-galaxy-ring-q500-sm-q500nzkaeub-542183975?$720_576_JPG$","https://www.samsung.com/uk/rings/galaxy-ring/galaxy-ring-titanium-black-size-10-sm-q500nzkaeub/",None,True),
 "amazfit-helio":("https://uk.amazfit.com/cdn/shop/files/Helioring_1024x1024.jpg?v=1716446501","https://uk.amazfit.com/products/amazfit-helio-ring",None,True),
}
PLACEHOLDER={
 "hik":"Hikvision's own product page for the DS-KB6003-WIP has been removed (discontinued); only a text datasheet remains, so no reliable official image.",
 "blink-out4":"Blink's own site no longer lists the Outdoor 4 (its current cameras are the Outdoor 2K+), so the only official image left is the Amazon UK listing, which does not license a self-hosted copy.",
}
def flat(im):
    im=im.convert("RGBA"); bg=Image.new("RGBA",im.size,(255,255,255,255)); bg.alpha_composite(im); return bg.convert("RGB")
def trim(im):
    diff=ImageChops.difference(im,Image.new("RGB",im.size,(255,255,255))).convert("L").point(lambda v:255 if v>18 else 0)
    bb=diff.getbbox(); return im.crop(bb) if bb else im
def fit(im,W,H,pad):
    c=Image.new("RGB",(W,H),(255,255,255)); im=im.copy(); im.thumbnail((W-2*pad,H-2*pad),Image.LANCZOS)
    c.paste(im,((W-im.width)//2,(H-im.height)//2)); return c
meta={}
for k,(u,page,box,tr) in IMGS.items():
    p=f"{RAW}/{k}.bin"
    if not os.path.exists(p):
        open(p,"wb").write(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30).read())
    im=flat(Image.open(p))
    if box: w,h=im.size; im=im.crop((int(box[0]*w),int(box[1]*h),int(box[2]*w),int(box[3]*h)))
    if tr: im=trim(im)
    for suf,(W,H,pad) in {"sm":(120,160,8),"lg":(360,480,22)}.items():
        fit(im,W,H,pad if tr else 0 if suf=="sm" else 0).save(f"{OUT}/{k}-{suf}.webp","WEBP",quality=80,method=6)
    meta[k]={"src":u,"page":page,"cropped":bool(box)}
for k,why in PLACEHOLDER.items(): meta[k]={"placeholder":True,"why":why}
json.dump(meta,open(os.path.join(HERE,"images.json"),"w"),indent=1)
L=["# Product image sources","","Every photo is the manufacturer's own product image, downloaded once, cropped to the product where the original showed extra items (phone, chime, award badge), flattened onto white and saved as WebP (`-sm` 120×160 for table rows, `-lg` 360×480 for details). Nothing is hotlinked.","","| File | Original image | Found on |","|---|---|---|"]
for k,v in meta.items():
    if v.get("placeholder"): L.append(f"| — ({k}) | None: neutral placeholder used | {v['why']} |")
    else: L.append(f"| `img/{k}-sm.webp`, `img/{k}-lg.webp` | {v['src']}{' (cropped)' if v['cropped'] else ''} | {v['page']} |")
open(os.path.join(ROOT,"IMAGE_SOURCES.md"),"w").write("\n".join(L)+"\n")
print("done",len(IMGS))

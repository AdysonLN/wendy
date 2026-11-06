"""Generate Wendy hardware-screen XML for VirtualDJ (SC LIVE 4)."""
from __future__ import annotations

import copy
import xml.etree.ElementTree as E

V = {"theme": "@$sc2_theme", "size": "@$sc2_wave_size", "four": "@$sc2_four",
     "beats": "@$sc2_hide_beats", "seeklock": "@$sc2_seek_lock",
     "touch": "@$sc2_wave_touch", "menu":"@$sc2_menu_page"}
THEMES = [
    dict(name="BLACK", bg="#0b0c0e", panel="#161719", line="#303236", text="#f2f3f4", muted="#9fa2a8", accent="#f2f3f4", ink="#101114"),
    dict(name="GRAPHITE", bg="#101217", panel="#181b22", line="#2b303a", text="#ecedf0", muted="#939aa8", accent="#b5e4a7", ink="#1b2f19"),
    dict(name="LIGHT", bg="#f5f6f8", panel="#ffffff", line="#e1e5ea", text="#202730", muted="#677181", accent="#347e36", ink="#ffffff"),
]
COLORS_ACTION = "setting 'SkinWaveformType' 'Colors' & setting 'SkinWaveformScratchType' 'Colors'"
SHAPES_ACTION = "setting 'SkinWaveformType' 'Shapes' & setting 'SkinWaveformScratchType' 'Shapes'"
MASTER_QUERY = "get_deck & param_equal `get_activedeck`"
# Native get_time text is unsigned; the stock screen also adds '-' explicitly.
REMAIN_TEXT = "get_text '-`get_time remain short`'"
TIME_DISPLAY = f"display_time 'remain' ? {REMAIN_TEXT} : get_time 'elapsed' 'short'"
def cycle_script(getter, setter, reverse=False):
    """Guard the previously tested native next-size operation with an upper bound.

    beatjump's text query is used by the stock skin and this device's display.
    Cast only to compare with an INTEGER upper bound: fractional text like 1/2
    still remains below 32. Native select handles the fractional step.
    """
    if reverse: return 'loop_half' if getter=='get_loop' else 'beatjump_select -1'
    read='get_loop' if getter=='get_loop' else "get_text '`beatjump`' & param_cast float"
    advance='loop_double' if getter=='get_loop' else 'beatjump_select +1'
    # These are the actual limits observed by this user on VirtualDJ build 8472.
    limit=64 if getter=='get_loop' else 32
    return f'{read} & param_smaller {limit} ? {advance} : {setter} 0.25'


def sub(parent, tag, **attrs):
    return E.SubElement(parent, tag, {k: str(v) for k, v in attrs.items()})


def box(parent, tag, x, y, w, h, **attrs):
    n = sub(parent, tag, **attrs)
    sub(n, "pos", x=x, y=y)
    sub(n, "size", width=w, height=h)
    return n


def panel(parent, query):
    return sub(parent, "panel", visibility=query)


def var(key, value):
    return f"var '{V[key]}' {value}"


class UI:
    def __init__(self, theme):
        self.t = theme

    def rect(self, p, x, y, w, h, color=None, border=None):
        n = box(p, "visual", x, y, w, h)
        attrs = {"color": color or self.t["panel"]}
        if border:
            attrs.update(border=border, border_size=1)
        sub(n, "off", **attrs)
        return n

    def text(self, p, x, y, w, h, text=None, action=None, size=22, muted=False, align="left", visibility=None, fmt=None, color=None):
        attrs = {"scroll": "no"}
        if visibility:
            attrs["visibility"] = visibility
        n = box(p, "textzone", x, y, w, h, **attrs)
        attrs = dict(fontsize=size, color=color or self.t["muted" if muted else "text"],
                     align=align,width=w,scroll="no",valign="center")
        if text is not None:
            attrs["text"] = text
        elif fmt is not None:
            attrs["format"] = fmt
        else:
            attrs["action"] = action
        sub(n, "text", **attrs)
        return n

    def button(self, p, x, y, w, h, text=None, action="nothing", query="off", size=18, textaction=None, status=False, rightclick=None):
        n = box(p, "button", x, y, w, h, action=action, query=query)
        if rightclick: n.set('rightclick',rightclick)
        sub(n, "off", shape="square", color=self.t["panel"], border=self.t["line"], border_size=1, radius=1)
        sub(n, "selected", shape="square", color=self.t["accent"], border=self.t["accent"], border_size=1, radius=1)
        if not status or action!="nothing":
            sub(n, "down", shape="square", color=self.t["accent"], radius=1)
        attrs = dict(fontsize=size, color=self.t["muted"], colorselected=self.t["ink"],
                     colordown=self.t["ink"], align="center", dx=4, width=w-8)
        attrs.update({"action": textaction} if textaction else {"text": text})
        sub(n, "text", **attrs)
        # Some builds do not inherit selected text styling for every button state.
        sub(n, "textselected", **dict(attrs, color=self.t["ink"]))
        return n

    def shield(self, p, x, y, w, h, query):
        return box(p, "button", x, y, w, h, action="nothing", visibility=query)

    def overview(self, p, x, y, w, h):
        n = box(p, "songpos", x, y, w, h, colorPlayed=self.t["bg"],
                colorVocal="#477dff", colorInstru="#36ce9b", colorBeat="#f5c565")
        wave = sub(n, "wave")
        sub(wave, "pos", y="+4")
        sub(wave, "size", height=h-8)
        for tag, sx, sw in (("cues", 30, 18), ("loops", 74, 22)):
            marker = sub(n, tag, dy="-4", shade=0)
            sub(marker, "size", width=sw, height=h)
            sub(marker, "clipmask", x=sx, y=107)
        # Needle seek is enabled by default. Main-wave scratch has a separate lock.
        self.shield(p, x, y, w, h, var("seeklock", 1))

    def wave(self, p, x, y, w, h):
        # A gridless and a gridded native element: never render both at once.
        for enabled in (0, 1):
            branch = panel(p, "setting 'showGridLines'" if enabled else "not setting 'showGridLines'")
            n = box(branch, "scratchwave", x, y, w, h, orientation="horizontal", color="full",
                    colorVocal="#477dff", colorInstru="#36ce9b", colorBeat="#f5c565",
                    colorNoVocal="#253042", colorNoInstru="#254039", colorNoBeat="#423c2a")
            sub(n, "grid", pos="-8", shapepos="-8", height=5, size=2, mainsize=4,
                maincolor=self.t["text"], color=self.t["muted"], mirrored="no",
                shapemirrored="no", background="no", backgroundshaded="no")
            if enabled:
                sub(n, "gridlines", width=1, color=self.t["muted"], transparency="0.45")
            cue = sub(n, "cue", y="-12", height=18)
            sub(cue, "text", dx=18, dy="-2", size=15)
            sub(cue, "mask", width=24, height=21, x=31, y=187)
            for alignment, offset in (("Centered", w//2-1), ("Left", 0)):
                ov = sub(n, "overlay", visibility=f"setting 'WaveformCenter' '{alignment}'")
                sub(ov, "pos", x=f"+{offset}", y="-12")
                sub(ov, "size", width=2, height=h+12)
                sub(ov, "background", color=self.t["text"], shape="square")
        self.shield(p, x, y-12, w, h+12, var("touch", 0))

    def pads(self, p, x, y, width, h, columns=4, size=20):
        gap = 8
        cell = (width-gap*(columns-1))//columns
        for number in range(1, 9):
            px = x + ((number-1) % columns)*(cell+gap)
            py = y + ((number-1)//columns)*(h+8)
            self.button(p, px, py, cell, h, action=f"pad {number}", query=f"pad {number}",
                        textaction=f"pad {number}", size=size)
            color = box(p, "visual", px+10, py+h-7, cell-20, 2,
                        type="color", source=f"pad_color {number}")

    def track_fx(self, p, x, y, w, h, size=20):
        self.button(p, x, y, 40, h, "FX", action="effect_select +1", query="effect_active", size=14, status=True)
        self.text(p, x+50, y, w-50, h, action="get_effect_name", size=size, muted=True)

    def master_border(self, p, x, y, w, h):
        outline = panel(p, MASTER_QUERY)
        for rx,ry,rw,rh in ((x,y,w,2),(x,y+h-2,w,2),(x,y,2,h),(x+w-2,y,2,h)):
            self.rect(outline,rx,ry,rw,rh,self.t["accent"])

    def secondary_time(self, p, x, y, w, small=False):
        # Deck-local choice: TOTAL/REMAIN does not change the primary time display.
        self.text(p,x,y,w,16,action="var 'sc2_total_remain' 0 ? get_text 'TOTAL' : get_text 'REMAIN'",size=11 if small else 12,muted=True)
        self.text(p,x,y+19,w,30 if small else 36,
                  action=f"var 'sc2_total_remain' 0 ? get_time 'total' 'short' : {REMAIN_TEXT}",
                  size=23 if small else 29,muted=True)
        box(p,"button",x-4,y-2,w+8,54 if small else 60,action="toggle 'sc2_total_remain'")

    def large_value(self, p, x, y, title, action, query="off"):
        setter="beatjump_select" if title=="JUMP" else "loop_select"
        b=self.button(p,x,y,72,52,action=cycle_script(action,setter),rightclick=cycle_script(action,setter,True),
                      query=query,textaction=action,size=30,status=True)
        b.find('text').set('dy','+9')
        b.find('textselected').set('dy','+9')
        self.text(p,x+4,y+3,64,12,text=title,size=10,align="center",muted=True,visibility="not "+query)
        self.text(p,x+4,y+3,64,12,text=title,size=10,align="center",color=self.t['ink'],visibility=query)

    def deck_card(self, p, side):
        d = sub(p, "deck", deck=side)
        x = 16 if side == "left" else 640
        self.rect(d, x, 68, 624, 160, border=self.t["line"])
        self.master_border(d,x,68,624,160)
        self.text(d, x+12, 76, 40, 42, action="get_deck", size=34)
        self.text(d, x+64, 74, 368, 30, action="get_title", size=25)
        self.text(d, x+64, 106, 368, 24, action="get_artist", size=19, muted=True)
        self.large_value(d,x+448,76,"JUMP","beatjump")
        self.large_value(d,x+536,76,"LOOP","get_loop","loop")
        for dx, title, query in ((12,"MASTER",MASTER_QUERY),(112,"SYNC","is_sync"),(212,"VINYL","vinyl_mode"),
                                  (312,"SLIP","slip_mode"),(412,"ROLL MODE","loop_roll_mode"),
                                  (512,"KEY LOCK","key_lock")):
            command={"MASTER":"masterdeck","SYNC":"sync","VINYL":"vinyl_mode","SLIP":"slip_mode","ROLL MODE":"loop_roll_mode","KEY LOCK":"key_lock"}[title]
            self.button(d, x+dx, 135, 92, 23, title,
                        action=command,rightclick="masterdeck_auto" if title=="MASTER" else None,
                        query="slip_mode ? on : get_slip_active" if title=="SLIP" else query,
                        textaction="get_slip_active ? get_text 'SLIP*' : get_text 'SLIP'" if title=="SLIP" else None,
                        size=13, status=True)
        for dx, caption, width in ((12,"BPM",132),(168,None,132),(480,"KEY",132)):
            if caption:
                self.text(d, x+dx, 165, width, 17, text=caption, size=12, muted=True)
            else:
                self.text(d, x+dx, 165, width, 17, action="display_time 'remain' ? get_text 'REMAIN' : get_text 'ELAPSED'", size=12, muted=True)
        self.text(d, x+12, 184, 132, 36, action="get_bpm & param_cast '0.00'", size=31)
        self.text(d, x+168, 184, 132, 36, action=TIME_DISPLAY, size=31)
        # Read-only text, with an invisible hit target to switch only the time view.
        box(d, "button", x+164, 163, 140, 60, action="display_time 'remain,elapsed'")
        self.secondary_time(d,x+324,165,132)
        self.text(d, x+480, 184, 132, 36, action="get_key", size=29)
        for divider in (156,312,468):
            self.rect(d,x+divider,165,1,55,self.t['line'])
        self.overview(d, x, 238, 624, 36)

    def two_decks(self, p, mode):
        for side in ("left", "right"):
            self.deck_card(p, side)
        width, height, second, pad_header, pad_y, pad_h, fx_y = (
            (1168, 24, 366, 428, 466, 76, 654),
            (1168, 32, 382, 456, 494, 68, 658),
            (1168, 96, 430, 550, 584, 48, 692),
        )[mode]
        for side, y in (("left", 304), ("right", second)):
            d = sub(p, "deck", deck=side)
            self.text(d, 24, y, 54, 38, action="get_deck", size=31)
            wave_x=1256-width
            # Full horizontal span with roughly the old ECO/SLIM pixel budget.
            # Keep the beat counter under the deck number, outside moving pixels.
            self.text(d,16,y+40,64,22,action="get_text '`get_bar`:`get_beat_num`'",size=15,
                      muted=True,visibility=var("beats",0))
            self.wave(d,wave_x,y,width,height)
            x = 16 if side == "left" else 640
            self.text(d,x+12,pad_header,388,29,action="pad_page & param_uppercase",size=22)
            self.text(d,x+424,pad_header,188,29,action="pad_param",size=17,muted=True,align="right")
            self.pads(d, x, pad_y, 624, pad_h, size=20 if mode<2 else 18)
            self.track_fx(d, x, fx_y, 624, 26 if mode==2 else 34, size=18 if mode==2 else 21)

    def four_decks(self, p, mode):
        height = (22, 32, 48)[mode]
        for deck, y in ((1, 68), (2, 230), (3, 392), (4, 554)):
            d = sub(p, "deck", deck=deck)
            self.rect(d, 16, y, 1240, 1, self.t["line"])
            self.text(d, 24, y+6, 34, 38, action="get_deck", size=30)
            self.text(d, 68, y+6, 344, 27, action="get_title", size=22)
            self.text(d, 68, y+35, 244, 23, action="get_artist", size=17, muted=True)
            self.text(d,320,y+35,92,23,action="get_text 'JUMP `beatjump`'",size=14,muted=True,align="right")
            self.text(d, 24, y+62, 122, 16, text="BPM", size=11, muted=True)
            self.text(d, 156, y+62, 122, 16, action="display_time 'remain' ? get_text 'REMAIN' : get_text 'ELAPSED'", size=11, muted=True)
            self.text(d, 24, y+80, 122, 31, action="get_bpm & param_cast '0.00'", size=26)
            self.text(d, 156, y+80, 122, 31, action=TIME_DISPLAY, size=26)
            box(d, "button", 150, y+60, 132, 53, action="display_time 'remain,elapsed'")
            self.secondary_time(d,286,y+62,126,small=True)
            self.text(d, 24, y+120, 42, 24, action="get_key", size=19)
            for bx, bw, title, query in ((76,66,"MASTER",MASTER_QUERY),(150,50,"SYNC","is_sync"),
                                         (208,54,"VINYL","vinyl_mode"),(270,50,"SLIP","slip_mode")):
                self.button(d, bx, y+119, bw, 24, title,
                            action={"MASTER":"masterdeck","SYNC":"sync","VINYL":"vinyl_mode","SLIP":"slip_mode"}[title],
                            rightclick="masterdeck_auto" if title=="MASTER" else None,
                            query="slip_mode ? on : get_slip_active" if title=="SLIP" else query,
                            textaction="get_slip_active ? get_text 'SLIP*' : get_text 'SLIP'" if title=="SLIP" else None,
                            size=11, status=True)
            self.button(d,328,y+114,84,36,action=cycle_script('get_loop','loop_select'),
                        rightclick=cycle_script('get_loop','loop_select',True),query="loop",textaction="get_text 'L `get_loop`'",size=23,status=True)
            self.button(d,24,y+44,34,16,"ROLL",action="loop_roll_mode",query="loop_roll_mode",size=8,status=True)
            # The text target changes Beat Jump size; it does not execute a jump.
            box(d,"button",320,y+35,92,23,action=cycle_script('beatjump','beatjump_select'),rightclick=cycle_script('beatjump','beatjump_select',True))
            self.overview(d, 432, y+8, 824, 27)
            self.text(d, 432, y+36, 290, 18, action="pad_page & param_uppercase", size=14, muted=True)
            self.text(d,1120,y+38,136,20,action="get_text '`get_bar`:`get_beat_num`'",size=14,
                      muted=True,align="right",visibility=var("beats",0))
            self.wave(d, 432, y+67, 824, height)
            self.pads(d, 432, y+122, 824, 28, columns=8, size=13)
            # A compact track-FX label sits in the gap next to the pad-page name.
            self.button(d, 738, y+36, 30, 20, "FX", action="effect_select +1", query="effect_active", size=11, status=True)
            self.text(d, 776, y+36, 322, 20, action="get_effect_name", size=14, muted=True)

    def global_header(self, p):
        self.rect(p, 0, 0, 1280, 56)
        for x, title, four in ((16,"2D",0),(104,"4D",1)):
            self.button(p,x,8,80,40,title,f"set '{V['four']}' {four} & set '$sclivebrowserextend' 0",var("four",four),size=17)
        self.button(p,200,8,96,40,"COLORS",COLORS_ACTION,"setting 'SkinWaveformType' 'Colors'",size=15)
        self.button(p,304,8,120,40,"SHAPE RGB",SHAPES_ACTION,"setting 'SkinWaveformType' 'Shapes'",size=15)
        # Old variable values: 0=SLIM, 1=ECO, 2=WIDE, retained across first revision.
        for x,title,value in ((440,"ECO",1),(520,"SLIM",0),(600,"WIDE",2)):
            self.button(p,x,8,72,40,title,f"set '{V['size']}' {value}",var("size",value),size=15)
        self.button(p,688,8,72,40,"GRID",
                    "setting 'showGridLines' ? setting 'showGridLines' off : setting 'showGridLines' on",
                    "setting 'showGridLines'", size=15)
        self.button(p,768,8,80,40,"BEATS",f"toggle '{V['beats']}'",var("beats",0),size=15)
        self.button(p,864,8,104,40,"BROWSE","toggle '$sclivebrowserextend' & set '$sclivesettingsview' 0","var '$sclivebrowserextend' 1",size=15)
        self.button(p,976,8,88,40,"MENU","toggle '$sclivesettingsview'","var '$sclivesettingsview' 1",size=15)
        self.button(p,1080,8,56,40,"REC",query="record",size=15,status=True)
        self.text(p,1148,15,108,28,fmt="`get_record_min`:`get_record_sec & param_cast '00'`",size=22,visibility="record")
        self.text(p,1148,15,108,28,text="OFF",size=20,muted=True,visibility="not record")

    def master_fx(self, p):
        self.rect(p, 0, 724, 1280, 76)
        self.rect(p, 0, 724, 1280, 1, self.t["line"])
        d = sub(p, "deck", deck="master")
        self.button(d, 16, 737, 120, 24, "MASTER FX", query="effect_active", size=13, status=True)
        self.text(d, 148, 733, 232, 30, action="get_effect_name", size=22)
        self.text(p, 16, 768, 364, 20, action="var '$livefxselect' 0 ? get_text 'KNOBS: MASTER' : get_text \"KNOBS: DECK `get_var '$livefxselect'`\"", size=13, muted=True)
        for parameter, x in ((1, 408), (2, 696), (3, 984)):
            q = panel(d, f"effect_has_slider {parameter}")
            self.text(q, x, 737, 264, 24,
                      action=f"get_text '`get_effect_slider_shortname {parameter}`  `get_effect_slider_text {parameter}`'", size=21)
            # Native visual tracks the parameter without making it touch-editable.
            meter = box(q, "visual", x, 774, 264, 4, type="linear", source=f"effect_slider {parameter}", orientation="horizontal", direction="right")
            sub(meter, "off", color=self.t["line"])
            sub(meter, "on", color=self.t["text"])

    def browser_tracks(self,p):
        two=panel(p,var("four",0))
        for side,x in (("left",16),("right",640)):
            d=sub(two,"deck",deck=side)
            self.rect(d,x,68,624,88,border=self.t['line'])
            self.master_border(d,x,68,624,88)
            self.text(d,x+12,76,32,30,action="get_deck",size=25)
            self.text(d,x+56,74,552,28,action="get_title",size=23)
            self.text(d,x+56,104,552,20,action="get_artist",size=17,muted=True)
            self.text(d,x+12,128,140,24,action="get_bpm & param_cast '0.00'",size=22)
            self.text(d,x+168,128,140,24,action=TIME_DISPLAY,size=22)
            self.text(d,x+324,128,140,24,action="get_time 'total' 'short'",size=22,muted=True)
            self.text(d,x+480,128,128,24,action="get_key",size=22)
            self.overview(d,x,164,624,24)
        four=panel(p,var("four",1))
        for number,x,y in ((1,16,68),(2,640,68),(3,16,132),(4,640,132)):
            d=sub(four,"deck",deck=number)
            self.rect(d,x,y,624,56,border=self.t['line'])
            self.master_border(d,x,y,624,56)
            self.text(d,x+12,y+6,32,36,action="get_deck",size=25)
            self.text(d,x+56,y+4,552,25,action="get_title",size=21)
            self.text(d,x+56,y+30,140,22,action="get_bpm & param_cast '0.00'",size=18,muted=True)
            self.text(d,x+216,y+30,140,22,action=REMAIN_TEXT,size=18,muted=True)
            self.text(d,x+380,y+30,60,22,action="get_key",size=18,muted=True)
            self.text(d,x+456,y+30,152,22,action="get_text 'JUMP `beatjump`'",size=16,muted=True,align="right")

    def browser(self, p):
        self.browser_tracks(p)
        for x, caption, action in ((16,"FOLDERS","browser_window 'folders'"),
                                   (164,"SONGS","browser_window 'songs'")):
            self.button(p, x, 204, 136, 36, caption, action, action, size=17)
        b = box(p, "browser", 16, 252, 1248, 458, toolbar="no", sideview="no", folders="yes",
                infos="no", effects="no", searchbar="yes", lineheight="1.3")
        colors = sub(b, "colors", background=self.t["bg"])
        sub(colors, "separators", line=self.t["line"])
        sub(colors, "lists", background=self.t["bg"], stripes=self.t["panel"], over=self.t["panel"],
            overstripes=self.t["panel"], selected=self.t["accent"], focus=self.t["accent"],
            text=self.t["text"], overtext=self.t["text"], selectedtext=self.t["ink"], focustext=self.t["ink"], label=self.t["muted"])
        sub(colors, "columns", background=self.t["panel"], text=self.t["text"])
        sub(colors, "toolbars", background=self.t["panel"], text=self.t["text"], label=self.t["muted"])
        sub(colors, "search", background=self.t["panel"], border=self.t["line"], selected=self.t["panel"], text=self.t["text"], cursor=self.t["text"])
        sub(colors, "scrollbars", background=self.t["line"], button=self.t["muted"])
        sub(b, "font", size=23)
        sub(b, "fontheader", size=20)
        sub(b, "fontsearch", size=20)

    def menu_row(self,p,y,caption,choices):
        self.text(p,248,y,288,48,text=caption,size=20,muted=True)
        width=(696-16*(len(choices)-1))//len(choices)
        for index,(title,action,query) in enumerate(choices):
            self.button(p,552+index*(width+16),y,width,48,title,action,query,size=18)

    def menu(self,p):
        names=("DISPLAY","WAVEFORMS","CONTROLS","PERFORMANCE")
        counts=(4,6,4,2)
        for page,title in enumerate(names):
            self.button(p,16,80+page*68,200,56,title,f"set '{V['menu']}' {page}",var('menu',page),size=18)
            q=panel(p,var('menu',page))
            self.text(q,248,76,1000,36,text=title,size=28)
            self.text(q,248,116,1000,24,text=f"{counts[page]} OPTIONS",size=13,muted=True)
            if page==0:
                rows=[
                    ('Theme',[(t['name'],f"set '{V['theme']}' {i}",var('theme',i)) for i,t in enumerate(THEMES)]),
                    ('Deck view',[(f'{n} DECKS',f"set '{V['four']}' {v}",var('four',v)) for n,v in ((2,0),(4,1))]),
                    ('Wave size',[(name,f"set '{V['size']}' {v}",var('size',v)) for name,v in (('ECO',1),('SLIM',0),('WIDE',2))]),
                    ('Bar / beat counter',[('SHOW',f"set '{V['beats']}' 0",var('beats',0)),('HIDE',f"set '{V['beats']}' 1",var('beats',1))]),
                ]
                note='Tap the main time: REMAIN / ELAPSED. Tap TOTAL: TOTAL / REMAIN.'
            elif page==1:
                rows=[
                    ('Main waveform',[('COLORS',COLORS_ACTION,"setting 'SkinWaveformType' 'Colors'"),('SHAPE RGB',SHAPES_ACTION,"setting 'SkinWaveformType' 'Shapes'")]),
                    ('Color palette',[(title,f"setting 'ColoredWaveforms' '{value}'",f"setting 'ColoredWaveforms' '{value}'") for title,value in (('MULTI-COLOR','neutral'),('PER-DECK','per-deck'),('MONO','monochrome'))]),
                    ('Colors from',[('STEMS',"setting 'waveUseFrequency' off","setting 'waveUseFrequency' ? off : on"),('FREQUENCIES',"setting 'waveUseFrequency' on","setting 'waveUseFrequency'")]),
                    ('Beat grid',[('SHOW',"setting 'showGridLines' on","setting 'showGridLines'"),('HIDE',"setting 'showGridLines' off","not setting 'showGridLines'")]),
                    ('Overview',[(title,f"setting 'SkinOverviewType' '{value}'",f"setting 'SkinOverviewType' '{value}'") for title,value in (('COLORS','Colors'),('AUTO','Auto'))]),
                    ('Playhead alignment',[(title,f"setting 'WaveformCenter' '{value}'",f"setting 'WaveformCenter' '{value}'") for title,value in (('CENTERED','Centered'),('LEFT','Left'))]),
                ]
                note='Waveform options also affect the computer skin.'
            elif page==2:
                rows=[
                    ('Main wave touch',[('LOCKED',f"set '{V['touch']}' 0",var('touch',0)),('ENABLED',f"set '{V['touch']}' 1",var('touch',1))]),
                    ('Needle / overview seek',[('ENABLED',f"set '{V['seeklock']}' 0",var('seeklock',0)),('LOCKED',f"set '{V['seeklock']}' 1",var('seeklock',1))]),
                    ('Playing-deck load guard',[('CONFIRM',"setting 'loadSecurity' 'on'","setting 'loadSecurity' 'on'"),('SILENT BLOCK',"setting 'loadSecurity' 'silent'","setting 'loadSecurity' 'silent'")]),
                    ('Pad pages',[(title,f"setting 'padsSkinIndependent' {value}",f"setting 'padsSkinIndependent' ? {'on' if value=='on' else 'off'} : {'off' if value=='on' else 'on'}") for title,value in (('LINKED','off'),('INDEPENDENT','on'))]),
                ]
                note='Tap for the next size. JUMP wraps at 32; LOOP at 64. Right-click selects the previous size.'
            else:
                rows=[
                    ('Skin refresh target',[(f'{fps} FPS',f"setting 'skinFPS' {fps}",f"setting 'skinFPS' {fps}") for fps in (20,30,60)]),
                    ('Overview playhead shadow',[('ON',"setting 'skinPlayheadShadow' on","setting 'skinPlayheadShadow'"),('OFF',"setting 'skinPlayheadShadow' off","not setting 'skinPlayheadShadow'")]),
                ]
                note='These settings also affect the computer skin. Refresh target is not a measured screen FPS.'
            assert len(rows)==counts[page]
            for row,(caption,choices) in enumerate(rows): self.menu_row(q,164+row*64,caption,choices)
            self.text(q,248,558,1000,48,text=note,size=17,muted=True)
        self.button(p,16,570,200,48,'VDJ SETTINGS','settings',size=16)
        self.text(p,16,622,200,24,text='Opens on the computer',size=12,muted=True)
        self.button(p,248,652,232,52,'STANDALONE...',"set '$denonsclivesource' 1")
        self.button(p,496,652,232,52,'POWER OFF...',"set '$denonsclivepower' 1")
        self.button(p,1016,652,232,52,'BACK',"set '$sclivesettingsview' 0")


def build_xml(stock_root):
    root = E.Element("skin", name="denonsclive4", version="2020", width="1280", height="800", nbdecks="4", hidden="true", dpi="1.3")
    defs = sub(root, "group", name="windowdefines")
    sub(defs, "font", name="Arial")
    for name in ("poweroff", "exitusb", "loadsec"):
        defs.append(copy.deepcopy(next(n for n in stock_root.iter("define") if n.get("class")==name)))
    main = panel(root, "var '$denonsclivesource' 0 ? var '$denonsclivepower' 0")
    for index, theme in enumerate(THEMES):
        themed = panel(main, var("theme", index))
        ui = UI(theme)
        ui.rect(themed, 0, 0, 1280, 800, theme["bg"])
        ui.global_header(themed)
        normal = panel(themed, "var '$sclivesettingsview' 0 ? var '$sclivebrowserextend' 0")
        two = panel(normal, var("four", 0))
        four = panel(normal, var("four", 1))
        # Presentation order differs from persistent values inherited from v1.
        for mode, value in ((0, 1), (1, 0), (2, 2)):
            ui.two_decks(panel(two, var("size", value)), mode)
            ui.four_decks(panel(four, var("size", value)), mode)
        ui.browser(panel(themed, "var '$sclivesettingsview' 0 ? var '$sclivebrowserextend' 1"))
        ui.menu(panel(themed, "var '$sclivesettingsview' 1"))
        ui.master_fx(themed)
    # Explicit numeric contexts match the stock security dialog and cover all 4 decks.
    for number in (1, 2, 3, 4):
        d = sub(root, "deck", deck=number)
        modal = panel(d, "load_security_shown")
        UI(THEMES[0]).shield(modal, 0, 0, 1280, 800, "on")
        sub(modal, "panel", **{"class":"loadsec"})
    for cls, state in (("poweroff", "$denonsclivepower"), ("exitusb", "$denonsclivesource")):
        sub(root, "panel", **{"class":cls,"x":"0","y":"0","visibility":f"var '{state}' 1"})
    E.indent(root, space="  ")
    return E.tostring(root, encoding="utf-8", xml_declaration=True)



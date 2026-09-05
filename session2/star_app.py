# Build-a-Star.  Run with:  streamlit run star_app.py
#
# Two log sliders define a star: mass at birth and age now, covering
# the same ranges as the phase plane on the course page. The left
# panel is the star's portrait; the right panel is the phase plane
# with your star marked on it. The rules are the ones from the page.
#
# Extension (see the Metallicity section of Part D): add a
# metallicity slider and thread `zr` through the two marked lines,
# then add the pair-instability branch.

import io
import math
import re

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

SUN_T = 5772.0


def show(fig, col):
    # render as SVG (vector text stays sharp at any screen density)
    # and hand it to st.image, which sizes it properly in the layout
    buf = io.StringIO()
    fig.savefig(buf, format="svg", facecolor=fig.get_facecolor())
    svg = buf.getvalue()
    col.image(svg[svg.index("<svg"):], use_container_width=True)

st.set_page_config(page_title="AppStar", layout="wide")

# trim Streamlit's default padding so the app fits one window
st.markdown("""<style>
.stApp {background-color: #000000;}
.stApp, .stApp p, .stApp label {color: #e8e8e8;}
.block-container {padding-top: 0.4rem; padding-bottom: 0.3rem;
                  max-width: 1000px;}
header[data-testid="stHeader"] {display: none;}
h1, h2, h3 {padding-top: 0 !important; margin: 0 0 0.2rem !important;
            color: #f0f0f0;}
div[data-testid="stVerticalBlock"] {gap: 0.4rem;}
div[data-testid="stSlider"] {padding-top: 0; padding-bottom: 0;}
div[data-testid="stSlider"] label p {font-weight: 700;
                                     font-size: 0.95rem;}
div[data-testid="stImage"] {padding: 6px 10px;}
</style>""", unsafe_allow_html=True)

st.markdown("### AppStar")

# the two panels render into this container, above the controls
panel_box = st.container()
left, right = panel_box.columns(2)

# controls row: three boxes, the stacked sliders, three boxes
BOX_BG = "#3f4a5a"
boxL, mid, boxR = st.columns([1, 2, 1])
slotL = [boxL.empty(), boxL.empty(), boxL.empty()]
slotR = [boxR.empty(), boxR.empty(), boxR.empty()]
lm = mid.slider("log10 mass (suns)", -1.0, 2.45, 0.0, step=0.05)
la = mid.slider("log10 age (billion years)", -4.0, 3.56, 0.66,
                step=0.02)
mass = 10.0 ** lm
age = 10.0 ** la


def fill_box(slot, label, value):
    slot.markdown(
        f'<div style="background:{BOX_BG};border-radius:8px;'
        f'padding:5px 8px;color:#fff;'
        f'font-size:0.72rem;text-align:center">{label}<br>'
        f'<b style="font-size:1rem">{value}</b></div>',
        unsafe_allow_html=True)


fill_box(slotL[0], "mass", f"{mass:.2g} suns")
fill_box(slotR[0], "age", f"{age:.2g} Gyr")
Z = 0.02          # metallicity; extension: make this a slider
zr = Z / 0.02

# main-sequence properties from mass
L = mass ** 3.5 * zr ** -0.1        # luminosity, suns  [uses zr]
R = mass ** 0.8                     # radius, suns
T = SUN_T * (L / R ** 2) ** 0.25    # surface temperature, K
t_pre = 0.03 * mass ** -1.5         # contraction time, Gyr
t_ms = (10.0 * mass ** -2.5 * (1 + 2.5 * np.exp(-mass / 0.12))
        + 0.0025)   # lifetime: Eddington floor, convective stretch
t_g = 1.15 * t_ms                   # end of the giant phase

# what has age made of it?
if age <= t_pre:
    phase = "protostar"
elif age <= t_ms:
    phase = "main sequence"
elif mass < 0.25:
    phase = "white dwarf"           # fully convective: no giant phase
elif mass < 8:
    phase = "red giant" if age <= t_g else "white dwarf"
elif age <= t_g:
    # the supergiant finale of a massive star: blue first, red later
    frac = (age - t_ms) / (t_g - t_ms)
    phase = "blue supergiant" if frac < 0.4 else "red supergiant"
elif age <= 1.10 * t_g:
    phase = "supernova"
elif mass < 18 + 7 * zr:            # remnant boundary  [uses zr]
    phase = "neutron star"
else:
    phase = "black hole"

# displayed temperature, luminosity and radius follow the phase.
# Only the main-sequence radius (R = M^0.8, good to tens of percent)
# comes from the relation taught on the page; the rest are standard
# reference values, noted branch by branch.
T_show, L_show, R_show = float(T), L, R
if phase == "protostar":
    # 3x the main-sequence radius: a crude stand-in for the
    # contracting cloud; real protostars vary wildly
    T_show, L_show, R_show = 0.75 * T, 2 * L, 3 * R
elif phase == "red giant":
    # an inflated radius of order 100 suns: the most invented rule
    # here. Real giants span ~10 to several hundred solar radii.
    T_show = 3900.0
    R_show = max(R * 60, 10.0)
    L_show = R_show ** 2 * (T_show / SUN_T) ** 4
elif phase == "blue supergiant":
    # Rigel-like: tens of solar radii, very hot
    frac = (age - t_ms) / (t_g - t_ms)
    T_show = 12000.0
    R_show = 30 + 120 * frac
    L_show = R_show ** 2 * (T_show / SUN_T) ** 4
elif phase == "red supergiant":
    # Betelgeuse-like: hundreds of solar radii, cool
    frac = (age - t_ms) / (t_g - t_ms)
    T_show = 3500.0
    R_show = min(200 + 900 * frac, 900)
    L_show = R_show ** 2 * (T_show / SUN_T) ** 4
elif phase == "white dwarf":
    # R fixed at 0.009 suns (Earth-sized): the right ballpark, though
    # real white dwarfs shrink as their mass grows
    cool = max(age - (t_ms if mass < 0.25 else t_g), 0.001)
    T_show = float(np.clip(60000.0 * (0.01 / cool) ** 0.3,
                           3500, 150000))
    R_show = 0.009
    L_show = R_show ** 2 * (T_show / SUN_T) ** 4
elif phase == "supernova":
    T_show, L_show, R_show = 8000.0, 5e9, None
elif phase == "neutron star":
    # R fixed at 1.7e-5 suns = 12 km, the measured value
    T_show, L_show, R_show = 1e6, None, 1.7e-5
elif phase == "black hole":
    # the true Schwarzschild radius, 2GM/c^2 = 4.2e-6 suns per 10
    # solar masses: the one rigorous radius in the model
    T_show, L_show, R_show = None, None, 4.2e-6 * mass / 10


def bb_rgb(T):
    # Approximate black-body colour, valid from about 1000 to 40000 K.
    t = T / 100.0
    r = 255.0 if t <= 66 else 329.7 * (t - 60) ** -0.1332
    g = 99.47 * math.log(t) - 161.1 if t <= 66 else 288.1 * (t - 60) ** -0.0755
    if t >= 66:
        b = 255.0
    elif t <= 19:
        b = 0.0
    else:
        b = 138.5 * math.log(t - 10) - 305.0
    return tuple(min(255.0, max(0.0, v)) / 255 for v in (r, g, b))


# ---- the portrait, with a gold ring at the Sun's size ----
boom = phase == "supernova"
panel = "white" if boom else "black"
fig1, ax = plt.subplots(figsize=(4.6, 4.6), layout="constrained")
fig1.get_layout_engine().set(w_pad=0.25, h_pad=0.25)
fig1.patch.set_facecolor(panel)
ax.set_facecolor(panel)
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)
ax.set_aspect("equal")
ax.set_xticks([])
ax.set_yticks([])


# linear scale, re-zoomed per star: the larger of the star and the
# Sun is drawn at 0.85 axes units and the other to true scale
# against it, with a small floor so neither ever vanishes
_zoom = 0.85 / max(R_show if R_show else 1.0, 1.0)


def lin_r(r_suns):
    return float(np.clip(_zoom * r_suns, 0.01, 0.92))


if phase == "black hole":
    ax.add_patch(plt.Circle((0, 0), 0.30, color="black", zorder=3))
    ax.add_patch(plt.Circle((0, 0), 0.34, fill=False,
                            color="#E07000", lw=3))
elif boom:
    rng = np.random.default_rng(4)
    pts = rng.normal(0, 0.4, (150, 2))
    ax.scatter(pts[:, 0], pts[:, 1], s=8, color="#E07000")
elif phase == "neutron star":
    ax.add_patch(plt.Circle((0, 0), 0.04, color="#CDE7FF"))
else:
    ax.add_patch(plt.Circle((0, 0), lin_r(R_show),
                            color=bb_rgb(min(T_show, 40000))))
# the Sun's current size, on the same linear scale, always on top
ax.add_patch(plt.Circle((0, 0), lin_r(1.0), fill=False,
                        color="#DAA520", lw=1.5, zorder=6))
ax.set_title(phase, color="black" if boom else "white")
show(fig1, left)

# ---- the phase plane, styled like the course page ----
Ml = np.geomspace(0.1, 300, 400)
pre_l = 0.03 * Ml ** -1.5
ms_l = (10.0 * Ml ** -2.5 * (1 + 2.5 * np.exp(-Ml / 0.12))
        + 0.0025)
g_l = 1.15 * ms_l
Y0 = 1e-4
Y1 = 1.15 * (10.0 * 0.1 ** -2.5 * (1 + 2.5 * np.exp(-0.1 / 0.12))
             + 0.0025)

# the main sequence is striped by spectral class: on the main
# sequence T = SUN_T * M^0.475, so each OBAFGKM edge is a fixed mass
cls_edge_T = [3700, 5200, 6000, 7500, 10000, 30000]
cls_edge_M = [(t / SUN_T) ** (1 / 0.475) for t in cls_edge_T]
CLS_T = {"M": 3050, "K": 4400, "G": 5500, "F": 6750, "A": 8700,
         "B": 17000, "O": 40000}
cls_bounds = [0.1] + cls_edge_M + [300.0]

fig2, ax2 = plt.subplots(figsize=(4.6, 4.6), layout="constrained")
fig2.get_layout_engine().set(w_pad=0.25, h_pad=0.25)
fig2.patch.set_facecolor("black")
ax2.set_facecolor("black")

ax2.fill_between(Ml, Y0, pre_l, color="#4a3118")            # protostar
for n, blo, bhi in zip("MKGFABO", cls_bounds[:-1], cls_bounds[1:]):
    seg = (Ml >= blo) & (Ml <= bhi)
    ax2.fill_between(Ml[seg], pre_l[seg], ms_l[seg],
                     color=bb_rgb(min(CLS_T[n], 40000)))
giant = Ml >= 0.25
ax2.fill_between(Ml[giant], ms_l[giant], g_l[giant],
                 color="#c73b25")                           # giant
lowm = Ml <= 0.25
ax2.fill_between(Ml[lowm], ms_l[lowm], Y1, color="#b7aec4")
wd = (Ml >= 0.25) & (Ml <= 8)
ax2.fill_between(Ml[wd], g_l[wd], Y1, color="#b7aec4")      # white dwarf
ns = (Ml >= 8) & (Ml <= 25)
ax2.fill_between(Ml[ns], g_l[ns], Y1, color="#7f7590")      # neutron star
bh = Ml >= 25
ax2.fill_between(Ml[bh], g_l[bh], Y1, color="#4a4256")      # black hole
sn = Ml >= 8
ax2.plot(Ml[sn], g_l[sn], color="#ccff00", lw=1)            # supernova
ax2.axhline(13.8, color="#8a2be2", lw=2, ls="--", alpha=0.8)

# region labels, as on the page
ax2.text(0.7, 1.2e-3, "protostars", color="#f5f2ea",
         fontsize=10, ha="center")
ax2.text(2.5, 50, "white dwarfs", color="#26323c",
         fontsize=10, ha="center")
ax2.text(80, 0.1, "black holes", color="#f5f2ea",
         fontsize=10, ha="center")
ax2.text(14.1, 0.47, "neutron\nstars", color="#f5f2ea",
         fontsize=10, ha="center", va="center")
ax2.text(0.40, 205, "giants", color="#c73b25",
         fontsize=10, rotation=-48, ha="center")
ax2.text(4.2, 0.06, "main sequence", color="#5a616b",
         fontsize=11, rotation=-47, ha="center")
ax2.text(13, 0.038, "supernova", color="#ccff00",
         fontsize=9, rotation=-48, ha="center")
ax2.text(0.105, 16.5, "age of the universe", color="#8a2be2",
         fontsize=8, ha="left")

# one letter per spectral-class stripe
cls_mid = [float(np.sqrt(blo * bhi))
           for blo, bhi in zip(cls_bounds[:-1], cls_bounds[1:])]
cls_lo = list(np.clip([0.548 * m ** -2 for m in cls_mid],
                      1.5e-4, None))
cls_lo[0] = 1.8
cls_mid[-1] = 40.0
cls_lo[-1] = 3.4e-4
for m, y, n in zip(cls_mid, cls_lo, "MKGFABO"):
    ax2.text(m, y, n, color="#26323c", fontsize=9,
             fontweight="bold", ha="center")

# R136a1, the most massive star known
r136_top = 10.0 * 200.0 ** -2.5 + 0.0025
ax2.plot([200, 200], [Y0, r136_top], color="#1a3a8f",
         lw=1.5, ls=(0, (2, 3)))
ax2.text(185, 6e-4, "most massive\nobserved star\n(R136a1)",
         color="#1a3a8f", fontsize=7, ha="right")

# the Sun, and your star
ax2.scatter([1.0], [4.6], s=50, color="#1e7d32", zorder=5)
ax2.text(1.0, 1.7, "Sun", color="#1e7d32", fontsize=10,
         fontweight="bold", ha="center")
ax2.scatter([mass], [age], marker="*", s=340, color="#FFC300",
            edgecolor="#8C6A2F", linewidth=1.2,
            zorder=6)                                       # your star

ax2.set_xscale("log")
ax2.set_yscale("log")
ax2.set_xlim(0.1, 300)
ax2.set_ylim(Y0, Y1)
ax2.set_xticks([0.1, 1, 10, 100])
ax2.set_xticklabels(["0.1", "1", "10", "100"])
ax2.set_yticks([1e-3, 1e-2, 0.1, 1, 10, 100, 1000])
ax2.set_yticklabels(["0.001", "0.01", "0.1", "1",
                     "10", "100", "1000"])
ax2.minorticks_off()
ax2.grid(True, color="#2b303b")
ax2.set_axisbelow(True)
ax2.tick_params(colors="#c8c8c8")
for spine in ax2.spines.values():
    spine.set_color("#444444")
ax2.set_xlabel("mass (suns), log scale", color="#c8c8c8")
ax2.set_ylabel("age (billion years), log scale", color="#c8c8c8")
ax2.set_title("Stellar mass-age phase plane", color="white")
show(fig2, right)

fill_box(slotL[1], "main-sequence lifetime", f"{t_ms:.2g} Gyr")
fill_box(slotL[2], "surface temperature",
         f"{T_show:,.0f} K" if T_show else "&mdash;")
fill_box(slotR[1], "luminosity",
         f"{L_show:.3g} suns" if L_show else "&mdash;")
fill_box(slotR[2], "radius",
         f"{R_show:.3g} suns" if R_show else "&mdash;")

"""
Generira dijagram arhitekture sustava kao PNG sliku.
Pokreni: python generate_diagram.py
Slika se spremi kao: arhitektura-dijagram.png
"""

import subprocess
import sys

# Auto-install matplotlib ako nije instaliran
try:
    import matplotlib.pyplot as plt
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
    import matplotlib.pyplot as plt

from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(1, 1, figsize=(10, 14))
ax.set_xlim(0, 10)
ax.set_ylim(0, 14)
ax.axis('off')
fig.patch.set_facecolor('#f8f9fa')


color_client = '#4a90d9'
color_nginx = '#e67e22'
color_api = '#27ae60'
color_dynamo = '#8e44ad'
color_text = 'white'
color_arrow = '#555555'

def draw_box(ax, x, y, w, h, color, title, subtitle=None, radius=0.3):
    """Crti zaokruženu kutiju s naslovom"""
    box = FancyBboxPatch(
        (x - w/2, y - h/2), w, h,
        boxstyle=f"round,pad=0.1,rounding_size={radius}",
        facecolor=color,
        edgecolor='white',
        linewidth=2,
        zorder=2
    )
    ax.add_patch(box)
    
    if subtitle:
        ax.text(x, y + 0.12, title, ha='center', va='center',
                fontsize=11, fontweight='bold', color=color_text, zorder=3)
        ax.text(x, y - 0.22, subtitle, ha='center', va='center',
                fontsize=8, color='#ffffffcc', zorder=3)
    else:
        ax.text(x, y, title, ha='center', va='center',
                fontsize=11, fontweight='bold', color=color_text, zorder=3)

def draw_arrow(ax, x1, y1, x2, y2, label=None):
    """Crti strelicu između dva elementa"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle='->', 
                    color=color_arrow,
                    lw=2,
                    connectionstyle='arc3,rad=0'
                ), zorder=1)
    if label:
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        ax.text(mid_x + 0.15, mid_y, label, ha='left', va='center',
                fontsize=8, color=color_arrow, style='italic', zorder=3)


ax.text(5, 13.5, 'Arhitektura sustava', ha='center', va='center',
        fontsize=16, fontweight='bold', color='#2c3e50')
ax.text(5, 13.1, 'Sportsko društvo "Sparta"', ha='center', va='center',
        fontsize=11, color='#7f8c8d')


draw_box(ax, 5, 12, 2.8, 0.7, color_client, 'Klijent', 'Swagger UI')


draw_arrow(ax, 5, 11.65, 5, 10.85, 'HTTP')


draw_box(ax, 5, 10.5, 3.2, 0.7, color_nginx, 'Nginx', 'Load Balancer (port 80)')

draw_arrow(ax, 3.2, 10.15, 2, 9.15)
draw_arrow(ax, 5, 10.15, 5, 9.15)
draw_arrow(ax, 6.8, 10.15, 8, 9.15)

# 
draw_box(ax, 2, 8.8, 2.2, 0.7, color_api, 'API 1', 'FastAPI (:8081)')
draw_box(ax, 5, 8.8, 2.2, 0.7, color_api, 'API 2', 'FastAPI (:8082)')
draw_box(ax, 8, 8.8, 2.2, 0.7, color_api, 'API 3', 'FastAPI (:8083)')

# 
draw_arrow(ax, 2, 8.45, 3.8, 7.55)
draw_arrow(ax, 5, 8.45, 5, 7.55)
draw_arrow(ax, 8, 8.45, 6.2, 7.55)

# 
draw_box(ax, 5, 7.2, 3.2, 0.7, color_dynamo, 'DynamoDB', 'NoSQL baza (port 8000)')

# 
ax.text(5, 6.4, 'Tablice', ha='center', va='center',
        fontsize=9, fontweight='bold', color='#2c3e50')

# Okvir za tablice
tables_box = FancyBboxPatch(
    (2.2, 4.6), 5.6, 1.6,
    boxstyle="round,pad=0.1,rounding_size=0.2",
    facecolor='#ecf0f1',
    edgecolor='#bdc3c7',
    linewidth=1.5,
    zorder=1
)
ax.add_patch(tables_box)


tables = [
    ('members', 'id, ime, prezime, email, grupa, status'),
    ('sessions', 'id, grupa, dan, vrijeme, max_clanova'),
    ('memberships', 'member_id, datum_uplate, iznos, status')
]

for i, (name, attrs) in enumerate(tables):
    y_pos = 6.0 - i * 0.45
    ax.text(3.0, y_pos, name, ha='left', va='center',
            fontsize=9, fontweight='bold', color=color_dynamo)
    ax.text(3.8, y_pos, attrs, ha='left', va='center',
            fontsize=7.5, color='#555555')


legend_y = 3.8
ax.text(1.5, legend_y, 'Legenda:', ha='left', va='center',
        fontsize=9, fontweight='bold', color='#2c3e50')

legend_items = [
    (color_client, 'Klijent'),
    (color_nginx, 'Load Balancer'),
    (color_api, 'API Instance'),
    (color_dynamo, 'Baza podataka'),
]

for i, (color, label) in enumerate(legend_items):
    x_pos = 1.5 + i * 2.2
    box = FancyBboxPatch(
        (x_pos, legend_y - 0.7), 0.4, 0.3,
        boxstyle="round,pad=0.05,rounding_size=0.1",
        facecolor=color,
        edgecolor='white',
        linewidth=1,
        zorder=2
    )
    ax.add_patch(box)
    ax.text(x_pos + 0.6, legend_y - 0.55, label, ha='left', va='center',
            fontsize=8, color='#2c3e50')


opis_y = 2.5
opis_box = FancyBboxPatch(
    (0.5, 0.3), 9, 2.1,
    boxstyle="round,pad=0.1,rounding_size=0.2",
    facecolor='#eaf2f8',
    edgecolor='#aed6f1',
    linewidth=1.5,
    zorder=1
)
ax.add_patch(opis_box)

ax.text(1.0, 2.2, 'Tok komunikacije (REST):', ha='left', va='center',
        fontsize=9, fontweight='bold', color='#2c3e50')

komunikacija = [
    '1. Klijent šalje HTTP zahtjev na Nginx (port 80)',
    '2. Nginx raspoređuje zahtjev na jednu od API instance (round-robin)',
    '3. API instanca obrađuje zahtjev i komunicira s DynamoDB',
    '4. DynamoDB vraća podatke, API vraća JSON odgovor klijentu',
]

for i, line in enumerate(komunikacija):
    ax.text(1.0, 1.8 - i * 0.35, line, ha='left', va='center',
            fontsize=8, color='#2c3e50')

plt.tight_layout()
plt.savefig('arhitektura-dijagram.png', dpi=150, bbox_inches='tight',
            facecolor=fig.get_facecolor())
plt.show()
print("Dijagram spremen: arhitektura-dijagram.png")
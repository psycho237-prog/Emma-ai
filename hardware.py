"""
EMMA v2.0 - OLED Simulator : Yeux féminins élégants
Yeux en amande, cils, pupille, sourcils fins
"""
import serial
import serial.tools.list_ports
import logging
import threading
import time
import math
import random
import tkinter as tk

log = logging.getLogger("emma.hardware")

W, H     = 420, 200
EYE_CX_L = 120
EYE_CX_R = 300
EYE_CY   = 105

COLORS = {
    'N': {'iris': '#B06AFF', 'pupil': '#1A0033', 'lash': '#CCAAFF', 'glow': '#6600CC', 'bg': '#08000F'},
    'L': {'iris': '#FF6EB4', 'pupil': '#1A0010', 'lash': '#FFBBDD', 'glow': '#CC0066', 'bg': '#0F0008'},
    'T': {'iris': '#FFD700', 'pupil': '#1A1000', 'lash': '#FFE566', 'glow': '#AA7700', 'bg': '#0A0800'},
    'S': {'iris': '#00E5FF', 'pupil': '#001A1F', 'lash': '#88EEFF', 'glow': '#007799', 'bg': '#000A0F'},
}

class OledSimulator:
    def __init__(self):
        self.state      = 'N'
        self.root       = None
        self.canvas     = None
        self.running    = True

        # Animation params
        self.blink_t        = 1.0    # 1 = ouvert, 0 = ferme
        self.blink_closing  = False
        self.next_blink     = time.time() + random.uniform(2, 5)
        self.pulse_phase    = 0.0
        self.scan_x         = 0
        self.scan_dir       = 1
        self.speak_phase    = 0.0
        self.pupil_x        = 0.0   # micro-mouvement de la pupille
        self.pupil_y        = 0.0
        self.pupil_tx       = 0.0
        self.pupil_ty       = 0.0
        self.brow_t         = 0.0   # sourcil (0=neutre, 1=haut)

        t = threading.Thread(target=self._run_gui, daemon=True)
        t.start()

    def _run_gui(self):
        self.root = tk.Tk()
        self.root.title("EMMA Eyes")
        self.root.geometry(f"{W}x{H}+80+40")
        self.root.configure(bg='black')
        self.root.resizable(False, False)
        self.root.overrideredirect(True)

        # Barre custom
        bar = tk.Frame(self.root, bg='#0D0D0D', height=22)
        bar.pack(fill='x')
        tk.Label(bar, text="  ◈  E . M . M . A", bg='#0D0D0D',
                 fg='#B06AFF', font=("Courier", 9, "bold")).pack(side='left')
        tk.Button(bar, text="  ✕  ", bg='#0D0D0D', fg='#555555',
                  relief='flat', command=self.root.destroy,
                  font=("Courier", 9), activebackground='#1A0033',
                  activeforeground='#FF6EB4').pack(side='right')
        bar.bind("<ButtonPress-1>", lambda e: setattr(self, '_dx', e.x) or setattr(self, '_dy', e.y))
        bar.bind("<B1-Motion>", lambda e: self.root.geometry(
            f"+{self.root.winfo_x()+e.x-self._dx}+{self.root.winfo_y()+e.y-self._dy}"))

        self.canvas = tk.Canvas(self.root, width=W, height=H-22,
                                bg=COLORS['N']['bg'], highlightthickness=0)
        self.canvas.pack()
        self._animate()
        self.root.mainloop()

    def _draw_almond_eye(self, cx, cy, pal, open_t, scan_dx=0, speak_amp=0):
        """
        Dessine un oeil en amande féminin complet.
        open_t  : 0 = ferme, 1 = grand ouvert
        scan_dx : decalage horizontal de la pupille
        speak_amp : amplitude ondulation (parole)
        """
        if not self.canvas: return
        c = self.canvas

        ew = 72   # largeur totale de l'oeil
        eh = int(52 * open_t)  # hauteur selon ouverture
        eh = max(eh, 0)

        bx1, bx2 = cx - ew//2, cx + ew//2
        # Points du contour en amande
        # Coin gauche, apex haut, coin droit, apex bas
        # Forme en amande : la partie ext. remonte un peu (effet "cat-eye")
        pts_top = []
        pts_bot = []
        for i in range(101):
            t = i / 100
            # Haut : parabole inversee + legere asyemtrie droite
            x = bx1 + t * ew
            cat = 10 * math.sin(t * math.pi) * (1 + 0.4 * t)  # rehaussement côté droit
            y_top = cy - eh//2 - cat + speak_amp * math.sin(t * math.pi * 2 + self.speak_phase)
            y_bot = cy + eh//2 - 6 * math.sin(t * math.pi)
            pts_top.append((x, y_top))
            pts_bot.append((x, y_bot))

        # Remplissage du blanc de l'oeil
        if eh > 4:
            poly_pts = [(x, y) for x, y in pts_top] + [(x, y) for x, y in reversed(pts_bot)]
            flat_white = [coord for pt in poly_pts for coord in pt]
            c.create_polygon(flat_white, fill='#F0E8FF', outline='', smooth=True, tags='eye')

        # Iris gradient simulé par cercles concentriques
        if eh > 8:
            iris_cx = cx + scan_dx + self.pupil_x
            iris_cy = cy + self.pupil_y
            iris_r  = min(eh // 2 - 4, 20)
            iris_r  = max(iris_r, 1)
            for r_off, alpha in [(8, 0.25), (5, 0.5), (3, 0.75), (0, 1.0)]:
                col = pal['iris'] if r_off == 0 else _glow(pal['iris'], alpha)
                tr = max(iris_r - r_off, 1)
                c.create_oval(iris_cx - tr - r_off, iris_cy - tr,
                              iris_cx + tr + r_off, iris_cy + tr,
                              fill=col, outline='', tags='eye')
            # Pupille
            pr = max(iris_r - 6, 3)
            c.create_oval(iris_cx - pr, iris_cy - pr,
                          iris_cx + pr, iris_cy + pr,
                          fill=pal['pupil'], outline='', tags='eye')
            # Reflet (catchlight)
            c.create_oval(iris_cx - pr + 4, iris_cy - pr + 2,
                          iris_cx - pr + 9, iris_cy - pr + 7,
                          fill='white', outline='', tags='eye')
            c.create_oval(iris_cx + 2, iris_cy - pr + 5,
                          iris_cx + 5, iris_cy - pr + 8,
                          fill='#EEDDFF', outline='', tags='eye')

        # Contour de l'oeil (eyeliner)
        if eh > 2 and len(pts_top) > 2 and len(pts_bot) > 2:
            flat_top = [coord for pt in pts_top for coord in pt]
            flat_bot = [coord for pt in pts_bot for coord in pt]
            if len(flat_top) >= 4:
                c.create_line(flat_top, fill=pal['lash'], width=2, smooth=True, tags='eye')
            if len(flat_bot) >= 4:
                c.create_line(flat_bot, fill=pal['lash'], width=1, smooth=True, tags='eye')

        # Cils superieur (droits, legerement courbés)
        if eh > 15:
            num_lashes = 9
            for i in range(num_lashes):
                # Position le long du bord superieur
                t = 0.15 + (i / (num_lashes - 1)) * 0.72
                ax = bx1 + t * ew
                cat_y = cy - eh//2 - (10 * math.sin(t * math.pi) * (1 + 0.4 * t))
                # Orientation des cils : vers l'exterieur et vers le haut
                angle = math.radians(-85 + t * 30)
                lash_len = int(8 + 5 * math.sin(t * math.pi) * open_t)
                bx = ax + lash_len * math.cos(angle)
                by = cat_y - lash_len * math.sin(abs(angle))
                c.create_line(ax, cat_y, bx, by,
                              fill=pal['lash'], width=2, tags='eye', capstyle='round')

        # Sourcil fin
        brow_y_base = cy - eh//2 - 22
        brow_arch   = -4 - 4 * self.brow_t  # se leve quand en mode ecoute
        brow_x1     = bx1 + 5
        brow_x2     = bx2 + 10  # legere prolongation côté externe (cat-eye brow)
        # Courbe du sourcil
        bmx         = (brow_x1 + brow_x2) // 2
        c.create_line(brow_x1, brow_y_base + 4,
                      bmx, brow_y_base + brow_arch,
                      brow_x2, brow_y_base - 2,
                      fill=pal['lash'], width=2, smooth=True, tags='eye')

    def _animate(self):
        if not self.running or not self.canvas: return
        st  = self.state
        pal = COLORS.get(st, COLORS['N'])
        self.canvas.delete('eye')
        self.canvas.configure(bg=pal['bg'])

        now = time.time()
        self.pulse_phase += 0.08

        # ── Micro-mouvements de la pupille (toujours actifs) ──
        self.pupil_tx = 4 * math.sin(now * 0.7)
        self.pupil_ty = 2 * math.sin(now * 0.5 + 1)
        self.pupil_x += (self.pupil_tx - self.pupil_x) * 0.1
        self.pupil_y += (self.pupil_ty - self.pupil_y) * 0.1

        # ── Etat NEUTRAL : clignement aleatoire ──
        if st == 'N':
            self.brow_t += (0.0 - self.brow_t) * 0.05
            if now > self.next_blink and not self.blink_closing:
                self.blink_closing = True
            if self.blink_closing:
                self.blink_t -= 0.15
                if self.blink_t <= 0:
                    self.blink_t = 0
                    self.blink_closing = False
                    self.next_blink = now + random.uniform(2.5, 6)
            else:
                self.blink_t = min(1.0, self.blink_t + 0.12)
            open_t = self.blink_t
            scan_dx = 0

        # ── Etat LISTENING: yeux grands, sourcils hauts ──
        elif st == 'L':
            self.blink_t = min(1.0, self.blink_t + 0.1)
            open_t = 1.0 + 0.08 * math.sin(self.pulse_phase)
            self.brow_t += (1.0 - self.brow_t) * 0.08
            scan_dx = 0

        # ── Etat THINKING: scan lateral, sourcils fronçés ──
        elif st == 'T':
            open_t = 0.75
            self.brow_t += (-0.5 - self.brow_t) * 0.05
            self.scan_x += self.scan_dir * 1.5
            if abs(self.scan_x) > 22: self.scan_dir *= -1
            scan_dx = self.scan_x

        # ── Etat SPEAKING: pupilles qui bougent, cils vibrent ──
        elif st == 'S':
            open_t = 0.85 + 0.1 * abs(math.sin(self.speak_phase * 2))
            self.speak_phase += 0.18
            self.brow_t += (0.3 - self.brow_t) * 0.05
            scan_dx = 3 * math.sin(self.speak_phase)
        else:
            open_t = 1.0
            scan_dx = 0

        open_t = max(0.0, min(1.15, open_t))

        eye_cy = EYE_CY
        self._draw_almond_eye(EYE_CX_L, eye_cy, pal, open_t, scan_dx)
        self._draw_almond_eye(EYE_CX_R, eye_cy, pal, open_t, scan_dx)

        self.root.after(28, self._animate)  # ~35fps

    def set_state(self, s):
        self.state = s


def _glow(hex_color, alpha):
    r = int(int(hex_color[1:3], 16) * alpha)
    g = int(int(hex_color[3:5], 16) * alpha)
    b = int(int(hex_color[5:7], 16) * alpha)
    return f"#{r:02X}{g:02X}{b:02X}"


class EmmaHardware:
    def __init__(self, baudrate=115200):
        self.ser = None
        self.sim = OledSimulator()
        self._connect(baudrate)

    def _connect(self, baudrate):
        for p in serial.tools.list_ports.comports():
            if any(k in p.description for k in ["Silicon Labs", "USB Serial", "CH340"]):
                try:
                    self.ser = serial.Serial(p.device, baudrate, timeout=1)
                    log.info(f"[Hardware] ESP32 connecte sur {p.device}")
                    return
                except Exception as e:
                    log.warning(f"[Hardware] {p.device} inaccessible: {e}")
        log.info("[Hardware] Mode Simulateur visuel actif.")

    def set_state(self, state_char):
        if self.ser and self.ser.is_open:
            try: self.ser.write(state_char.encode())
            except: pass
        self.sim.set_state(state_char)


hw = EmmaHardware()

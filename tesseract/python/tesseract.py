import pygame
import math
import random
import sys
import os
import time
import colorsys


GAME_SIZE = 800
BASEDIR = os.path.dirname(os.path.abspath(__file__))

# try ../assets first (tesseract/python/tesseract.py)
assets_candidate = os.path.normpath(os.path.join(BASEDIR, "..", "assets"))
if os.path.isdir(assets_candidate):
    ASSETSDIR = assets_candidate
else:
    # fallback to ./assets (for tesseract/tesseract.py)
    ASSETSDIR = os.path.join(BASEDIR, "assets")


CONTROL_STYLES = ['auto', 'manual']

PALETTE_NAMES = [
    "Matrix Green", "Rainbow Cycle", "Cyberpunk Neon", "Vaporwave Pastel", "Monochrome Gray",
    "Ocean Blue", "Sunset Glow", "Forest Deep", "Fire Blaze", "Pastel Dream",
    "Neon Lights", "Retro Wave", "Galaxy Dust", "Candy Floss", "Ice Chill",
    "Lavender Mist", "Gold Shine", "Silver Lining", "Copper Rust", "Electric Blue",
    "Rainbow Shift", "Sunset Shift", "Ocean Shift", "Forest Shift", "Fire Shift",
    "Candy Shift", "Ice Shift", "Lavender Shift", "Gold Shift", "Silver Shift",
    "Copper Shift", "Electric Shift", "Neon Shift", "Retro Shift", "Galaxy Shift",
    "Pastel Shift", "Matrix Shift", "Cyberpunk Shift", "Vaporwave Shift", "Monochrome Shift",
]

BASE_PALETTES = [
    [(0, 255, 0), (0, 180, 0), (0, 100, 0)],
    [(255, 0, 0), (0, 255, 0), (0, 0, 255)],
    [(0, 255, 255), (255, 0, 255), (255, 105, 180)],
    [(255, 20, 147), (173, 216, 230), (255, 105, 180)],
    [(200, 200, 200), (150, 150, 150), (100, 100, 100)],
    [(0, 105, 148), (0, 168, 232), (72, 202, 228)],
    [(252, 92, 101), (253, 150, 68), (254, 211, 48)],
    [(34, 139, 34), (50, 205, 50), (107, 142, 35)],
    [(255, 69, 0), (255, 140, 0), (255, 215, 0)],
    [(255, 179, 186), (255, 223, 186), (255, 255, 186)],
]

def shift_palette(palette, shift_factor):
    shifted = []
    for r, g, b in palette:
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        h = (h + shift_factor) % 1.0
        r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
        shifted.append((int(r2*255), int(g2*255), int(b2*255)))
    return shifted

for set_idx in range(4, 11):
    base_shift = (set_idx - 1) * 0.1
    for base_palette in BASE_PALETTES:
        PALETTE_NAMES.append(f"Set{set_idx} Shift{len(PALETTE_NAMES)+1}"[:20])

ALL_PALETTES = []
fixed_palettes = BASE_PALETTES[:10]

for i in range(10):
    ALL_PALETTES.append(fixed_palettes[i])
for i in range(10):
    ALL_PALETTES.append(fixed_palettes[i])
for set_idx in range(4, 11):
    base_shift = (set_idx - 1) * 0.1
    for base_palette in BASE_PALETTES:
        shifted = shift_palette(base_palette, base_shift)
        ALL_PALETTES.append(shifted)
        if len(ALL_PALETTES) >= 100:
            break
    if len(ALL_PALETTES) >= 100:
        break

pygame.init()
pygame.mixer.init()

display_surface = pygame.display.set_mode((GAME_SIZE, GAME_SIZE), pygame.RESIZABLE)
pygame.display.set_caption("4D Cube (Tesseract)")
clock = pygame.time.Clock()

FONT_PATH = os.path.join(ASSETSDIR, "VCR_OSD_MONO.ttf")
try:
    font = pygame.font.Font(FONT_PATH, 24)
    big_font = pygame.font.Font(FONT_PATH, 50)
except FileNotFoundError:
    font = pygame.font.SysFont('Arial', 24)
    big_font = pygame.font.SysFont('Arial', 50)

def load_sound(name):
    path = os.path.join(ASSETSDIR, name)
    try:
        return pygame.mixer.Sound(path)
    except pygame.error as e:
        print(f"Warning: Could not load sound {name}: {e}")
        return None

try:
    pygame.mixer.music.load(os.path.join(ASSETSDIR, "cell_to_singularity.wav"))
except pygame.error as e:
    print(f"Warning: Could not load background music: {e}")

startup_sound = load_sound("startup_sound.wav")
escape_sound = load_sound("escape_sound.wav")
beep_sounds = [load_sound(f"beep{i}.wav") for i in range(1, 4)]

def generate_points():
    points = []
    for x in [-1,1]:
        for y in [-1,1]:
            for z in [-1,1]:
                for w in [-1,1]:
                    for v in [-1,1]:
                        points.append([x,y,z,w,v])
    return points

def generate_edges(points):
    edges = []
    for i in range(len(points)):
        for j in range(i+1,len(points)):
            diff = sum(points[i][k] != points[j][k] for k in range(5))
            if diff == 1:
                edges.append((i,j))
    return edges

def rotate_5d(point, angles):
    x,y,z,w,v = point
    def rotate(a,b,angle):
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return a*cos_a - b*sin_a, a*sin_a + b*cos_a
    x,y = rotate(x,y,angles['xy'])
    y,z = rotate(y,z,angles['yz'])
    z,w = rotate(z,w,angles['zw'])
    w,v = rotate(w,v,angles['wv'])
    v,x = rotate(v,x,angles['vx'])
    x,z = rotate(x,z,angles['xz'])
    y,w = rotate(y,w,angles['yw'])
    return [x,y,z,w,v]

def project_5d_to_3d(point, distance=4):
    x,y,z,w,v = point
    factor = distance / (distance - v)
    return [x*factor, y*factor, z*factor]

def project_3d_to_2d(point, distance=5):
    x,y,z = point
    factor = distance / (distance - z)
    return (x*factor, y*factor)

motion_blur_surface = pygame.Surface((GAME_SIZE, GAME_SIZE))
motion_blur_surface.set_alpha(40)
motion_blur_surface.fill((0,0,0))

def rainbow_color(t, speed=0.002):
    hue = (t * speed) % 1.0
    r,g,b = colorsys.hsv_to_rgb(hue,1,1)
    return int(r*255), int(g*255), int(b*255)

def color_shift_palette(base_palette, t, speed=0.01):
    shifted = []
    for i, (r, g, b) in enumerate(base_palette):
        h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
        h = (h + t * speed + i * 0.1) % 1.0
        r2, g2, b2 = colorsys.hls_to_rgb(h, l, s)
        shifted.append((int(r2*255), int(g2*255), int(b2*255)))
    return shifted

class FadeSurface:
    def __init__(self, size):
        self.surface = pygame.Surface(size, pygame.SRCALPHA)
        self.alpha = 0
        self.target_alpha = 0
        self.speed = 15

    def fade_in(self):
        self.target_alpha = 180

    def fade_out(self):
        self.target_alpha = 0

    def update(self):
        if self.alpha < self.target_alpha:
            self.alpha = min(self.alpha + self.speed, self.target_alpha)
        elif self.alpha > self.target_alpha:
            self.alpha = max(self.alpha - self.speed, self.target_alpha)
        self.surface.set_alpha(self.alpha)

    def draw(self, surface):
        if self.alpha > 0:
            surface.blit(self.surface, (0, 0))

class TesseractApp:
    def __init__(self):
        self.display_surface = display_surface
        self.game_surface = pygame.Surface((GAME_SIZE, GAME_SIZE))

        self.points = generate_points()
        self.edges = generate_edges(self.points)
        self.angles = {axis: 0 for axis in ['xy','yz','zw','wv','vx','xz','yw']}
        self.rot_speeds = {axis: random.uniform(0.005,0.02) for axis in self.angles}
        self.scale = 150
        self.center = (GAME_SIZE//2, GAME_SIZE//2)

        self.palette_set_idx = 0
        self.palette_idx_in_set = 0
        self.update_current_palette()

        self.control_style_idx = 0
        self.control_style = CONTROL_STYLES[self.control_style_idx]

        self.motion_blur = True
        self.show_keybinds = False

        self.state = 1  # 0 = Visualization , 1 = MainMenu, 2 = PaletteMenu, 3 = KeybindMenu

        self.palette_fade = FadeSurface((GAME_SIZE, GAME_SIZE))
        self.keybind_fade = FadeSurface((GAME_SIZE, GAME_SIZE))

        self.running = True
        self.frame_count = 0
        self.chaos_mode = False
        self.last_chaos_change = time.time()
        self.chaos_change_interval = 0.02
        self.last_palette_switch = time.time()

        self.menu_selected = 0
        self.fullscreen = False

        # Chaos mode cycling
        self.chaos_palette_set = 0
        self.chaos_palette_idx = 0

        # restores palette after chaos mode
        self.last_normal_palette_set = 0
        self.last_normal_palette_idx = 0

    def update_current_palette(self):
        idx = self.palette_set_idx * 10 + self.palette_idx_in_set
        idx %= len(ALL_PALETTES)
        self.current_palette = ALL_PALETTES[idx]
        self.current_palette_name = PALETTE_NAMES[idx] if idx < len(PALETTE_NAMES) else f"Palette {idx+1}"

    def play_sound(self, sound):
        if sound:
            sound.play()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            info = pygame.display.Info()
            self.display_surface = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
        else:
            self.display_surface = pygame.display.set_mode((GAME_SIZE, GAME_SIZE), pygame.RESIZABLE)
    def draw_text(self, text, pos, font, color=(255,255,255)):
        surf = font.render(text, True, color)
        self.game_surface.blit(surf, pos)

    def draw_main_menu(self):
        self.game_surface.fill((0,0,0))
        title = "Main Menu"
        self.draw_text(title, (self.center[0] - big_font.size(title)[0]//2, 100), big_font)

        menu_items = [
            f"Control Style: {self.control_style.capitalize()}",
            f"Palette Set: {self.palette_set_idx+1} (Use < or >)",
            "Start Visualization",
            "Quit",
        ]
        for idx, item in enumerate(menu_items):
            color = (255,255,0) if idx == self.menu_selected else (255,255,255)
            self.draw_text(item, (self.center[0] - 250, 250 + idx*50), font, color)

        line1 = "Use UP/DOWN to navigate menu,"
        line2 = "Use < or > to switch palette, ENTER to select"

        line1_surf = font.render(line1, True, (180, 180, 180))
        line2_surf = font.render(line2, True, (180, 180, 180))

        self.game_surface.blit(line1_surf, ((GAME_SIZE - line1_surf.get_width()) // 2, 600))
        self.game_surface.blit(line2_surf, ((GAME_SIZE - line2_surf.get_width()) // 2, 630))

    def draw_palette_menu(self):
        self.game_surface.fill((10,10,10))
        title = f"Palette Menu - Set {self.palette_set_idx+1} of 10"
        self.draw_text(title, (self.center[0] - big_font.size(title)[0]//2, 20), big_font)

        start_idx = self.palette_set_idx * 10
        for i in range(10):
            idx = start_idx + i
            name = PALETTE_NAMES[idx] if idx < len(PALETTE_NAMES) else f"Palette {idx+1}"
            y = 100 + i*40
            color = (255,255,0) if i == self.palette_idx_in_set else (200,200,200)
            self.draw_text(f"{i+1}. - {name}", (50, y), font, color)

        instruction = "LEFT/RIGHT: Change set | 1-0: Select palette | SHIFT+P: Exit palette menu"
        self.draw_text(instruction, ((GAME_SIZE - font.size(instruction)[0])//2, GAME_SIZE - 40), font, (180,180,180))

    def draw_keybind_menu(self):
        self.keybind_fade.surface.fill((0,0,0,180))
        lines = [
            "KEYBINDS:",
            "-----------------------------",
            "WASD/QE: Rotate (manual control)",
            "SPACE: Cycle palette in current set (disabled in chaos mode)",
            "B: Toggle motion blur",
            "ESC: Return to menu",
            "SHIFT + M: Toggle keybind menu",
            "SHIFT + P: Toggle palette menu (disabled in chaos mode)",
            "C: Toggle Chaos Mode",
            "F11: Toggle fullscreen",
        ]
        y = 50
        for line in lines:
            text_surf = font.render(line, True, (255,255,255))
            self.keybind_fade.surface.blit(text_surf, (50, y))
            y += 30
        self.keybind_fade.update()
        self.keybind_fade.draw(self.game_surface)

    def handle_main_menu_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                self.toggle_fullscreen()
            mods = pygame.key.get_mods()
            # Only allow shift + num if not in chaos mode
            if not self.chaos_mode and mods & pygame.KMOD_SHIFT:
                key_to_set = {
                    pygame.K_1: 0,
                    pygame.K_2: 1,
                    pygame.K_3: 2,
                    pygame.K_4: 3,
                    pygame.K_5: 4,
                    pygame.K_6: 5,
                    pygame.K_7: 6,
                    pygame.K_8: 7,
                    pygame.K_9: 8,
                    pygame.K_0: 9,
                }
                if event.key in key_to_set:
                    self.palette_set_idx = key_to_set[event.key]
                    self.palette_idx_in_set = 0
                    self.update_current_palette()
                    self.play_sound(random.choice(beep_sounds))
                    return

            if event.key == pygame.K_UP:
                self.menu_selected = (self.menu_selected - 1) % 4
                self.play_sound(random.choice(beep_sounds))
            elif event.key == pygame.K_DOWN:
                self.menu_selected = (self.menu_selected + 1) % 4
                self.play_sound(random.choice(beep_sounds))
            elif event.key == pygame.K_LEFT:
                if self.menu_selected == 1:
                    self.palette_set_idx = (self.palette_set_idx - 1) % 10
                    self.palette_idx_in_set = 0
                    self.update_current_palette()
                    self.play_sound(random.choice(beep_sounds))
            elif event.key == pygame.K_RIGHT:
                if self.menu_selected == 1:
                    self.palette_set_idx = (self.palette_set_idx + 1) % 10
                    self.palette_idx_in_set = 0
                    self.update_current_palette()
                    self.play_sound(random.choice(beep_sounds))
            elif event.key == pygame.K_RETURN:
                self.play_sound(startup_sound)
                if self.menu_selected == 0:
                    self.control_style_idx = (self.control_style_idx + 1) % len(CONTROL_STYLES)
                    self.control_style = CONTROL_STYLES[self.control_style_idx]
                elif self.menu_selected == 2:
                    self.state = 0  # Visualization
                    pygame.mixer.music.play(-1)
                elif self.menu_selected == 3:
                    self.running = False

    def handle_palette_menu_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                self.toggle_fullscreen()
            if self.chaos_mode:
                return  # palette menu disabled in chaos mode
            if event.key == pygame.K_LEFT:
                self.palette_set_idx = (self.palette_set_idx - 1) % 10
                self.palette_idx_in_set = 0
                self.update_current_palette()
                self.play_sound(random.choice(beep_sounds))
            elif event.key == pygame.K_RIGHT:
                self.palette_set_idx = (self.palette_set_idx + 1) % 10
                self.palette_idx_in_set = 0
                self.update_current_palette()
                self.play_sound(random.choice(beep_sounds))
            elif pygame.K_1 <= event.key <= pygame.K_9 or event.key == pygame.K_0:
                key_to_idx = {pygame.K_1:0,pygame.K_2:1,pygame.K_3:2,pygame.K_4:3,pygame.K_5:4,
                              pygame.K_6:5,pygame.K_7:6,pygame.K_8:7,pygame.K_9:8,pygame.K_0:9}
                if event.key in key_to_idx:
                    self.palette_idx_in_set = key_to_idx[event.key]
                    self.update_current_palette()
                    self.play_sound(random.choice(beep_sounds))
            elif event.key == pygame.K_p and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                self.state = 0  # back to visualization
                self.play_sound(random.choice(beep_sounds))
            elif event.key == pygame.K_ESCAPE:
                self.state = 1  # back to main menu
                self.play_sound(random.choice(beep_sounds))

    def handle_keybind_menu_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                self.toggle_fullscreen()
            if event.key == pygame.K_m and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                self.state = 0  # back to visualization
                self.play_sound(random.choice(beep_sounds))
            elif event.key == pygame.K_ESCAPE:
                self.state = 1  # back to main menu
                self.play_sound(random.choice(beep_sounds))

    def update_angles_auto(self):
        for axis in self.angles:
            self.angles[axis] += self.rot_speeds[axis]

    def update_angles_manual(self, keys):
        speed = 0.03
        if keys[pygame.K_w]:
            self.angles['xy'] += speed
        if keys[pygame.K_s]:
            self.angles['xy'] -= speed
        if keys[pygame.K_a]:
            self.angles['yz'] += speed
        if keys[pygame.K_d]:
            self.angles['yz'] -= speed
        if keys[pygame.K_q]:
            self.angles['zw'] += speed
        if keys[pygame.K_e]:
            self.angles['zw'] -= speed

    def update_chaos_mode(self):
        current_time = time.time()
        if current_time - self.last_chaos_change > self.chaos_change_interval:
            for axis in self.rot_speeds:
                self.rot_speeds[axis] = random.uniform(-0.1, 0.1)
            self.last_chaos_change = current_time

        if current_time - self.last_palette_switch > 0.02:
            self.chaos_palette_idx += 1
            if self.chaos_palette_idx > 9:
                self.chaos_palette_idx = 0
                self.chaos_palette_set += 1
                if self.chaos_palette_set > 9:
                    self.chaos_palette_set = 0

            self.palette_set_idx = self.chaos_palette_set
            self.palette_idx_in_set = self.chaos_palette_idx
            self.update_current_palette()
            self.last_palette_switch = current_time

    def draw_tesseract(self):
        rotated_points = [rotate_5d(p, self.angles) for p in self.points]
        projected_3d = [project_5d_to_3d(p) for p in rotated_points]
        projected_2d = [project_3d_to_2d(p) for p in projected_3d]

        points_2d = []
        for x, y in projected_2d:
            sx = x * self.scale + self.center[0]
            sy = y * self.scale + self.center[1]
            points_2d.append((sx, sy))

        if self.chaos_mode:
            palette = [ (random.randint(0,255), random.randint(0,255), random.randint(0,255)) for _ in range(3) ]
        elif self.palette_set_idx == 0 and self.palette_idx_in_set == 1:
            c1 = rainbow_color(self.frame_count, speed=0.01)
            c2 = rainbow_color(self.frame_count + 85, speed=0.01)
            c3 = rainbow_color(self.frame_count + 170, speed=0.01)
            palette = [c1, c2, c3]
        elif "Shift" in self.current_palette_name:
            base_name = self.current_palette_name.replace(" Shift","")
            if base_name in PALETTE_NAMES:
                base_idx = PALETTE_NAMES.index(base_name)
                base_palette = fixed_palettes[base_idx % len(fixed_palettes)]
                palette = color_shift_palette(base_palette, self.frame_count, speed=0.01)
            else:
                palette = self.current_palette
        else:
            palette = self.current_palette

        for i, j in self.edges:
            pygame.draw.line(self.game_surface, palette[1], (int(points_2d[i][0]), int(points_2d[i][1])), (int(points_2d[j][0]), int(points_2d[j][1])), 1)

        for p in points_2d:
            pygame.draw.circle(self.game_surface, palette[0], (int(p[0]), int(p[1])), 5)

    def run(self):
        self.play_sound(startup_sound)

        while self.running:
            self.frame_count += 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.state == 1:
                    self.handle_main_menu_events(event)
                elif self.state == 2:
                    self.handle_palette_menu_events(event)
                elif self.state == 3:
                    self.handle_keybind_menu_events(event)
                else:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.state = 1
                            self.chaos_mode = False
                            # restore last palette when exiting chaos mode
                            self.palette_set_idx = self.last_normal_palette_set
                            self.palette_idx_in_set = self.last_normal_palette_idx
                            self.update_current_palette()
                            self.play_sound(escape_sound)
                            pygame.mixer.music.stop()
                        elif event.key == pygame.K_SPACE and not self.chaos_mode:
                            self.palette_idx_in_set = (self.palette_idx_in_set + 1) % 10
                            self.update_current_palette()
                            self.play_sound(random.choice(beep_sounds))
                        elif event.key == pygame.K_b:
                            self.motion_blur = not self.motion_blur
                            self.play_sound(random.choice(beep_sounds))
                        elif event.key == pygame.K_m and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                            if self.state == 0:
                                self.state = 3
                                self.keybind_fade.fade_in()
                            elif self.state == 3:
                                self.keybind_fade.fade_out()
                                self.state = 0
                            self.play_sound(random.choice(beep_sounds))
                        elif event.key == pygame.K_p and (pygame.key.get_mods() & pygame.KMOD_SHIFT) and not self.chaos_mode:
                            if self.state == 0:
                                self.state = 2
                                self.palette_fade.fade_in()
                            elif self.state == 2:
                                self.palette_fade.fade_out()
                                self.state = 0
                            self.play_sound(random.choice(beep_sounds))
                        elif event.key == pygame.K_c:
                            self.chaos_mode = not self.chaos_mode
                            self.motion_blur = True
                            self.play_sound(random.choice(beep_sounds))
                            if self.chaos_mode:
                                # preserves current palette before chaos mode
                                self.last_normal_palette_set = self.palette_set_idx
                                self.last_normal_palette_idx = self.palette_idx_in_set
                                # start chaos mode cycling at current
                                self.chaos_palette_set = self.palette_set_idx
                                self.chaos_palette_idx = self.palette_idx_in_set
                            else:
                                # restore palette after chaos mode
                                self.palette_set_idx = self.last_normal_palette_set
                                self.palette_idx_in_set = self.last_normal_palette_idx
                                self.update_current_palette()
                        elif event.key == pygame.K_F11:
                            self.toggle_fullscreen()
                        elif (pygame.key.get_mods() & pygame.KMOD_SHIFT) and (pygame.K_1 <= event.key <= pygame.K_0 or event.key == pygame.K_0) and not self.chaos_mode:
                            key_to_set = {
                                pygame.K_1: 0,
                                pygame.K_2: 1,
                                pygame.K_3: 2,
                                pygame.K_4: 3,
                                pygame.K_5: 4,
                                pygame.K_6: 5,
                                pygame.K_7: 6,
                                pygame.K_8: 7,
                                pygame.K_9: 8,
                                pygame.K_0: 9,
                            }
                            if event.key in key_to_set and self.state == 0:
                                self.palette_set_idx = key_to_set[event.key]
                                self.palette_idx_in_set = 0
                                self.update_current_palette()
                                self.play_sound(random.choice(beep_sounds))

            # draws everything to game_surface first
            if self.state == 1:
                self.draw_main_menu()
            elif self.state == 2:
                self.palette_fade.update()
                self.palette_fade.draw(self.game_surface)
                self.draw_palette_menu()
            elif self.state == 3:
                self.keybind_fade.update()
                self.keybind_fade.draw(self.game_surface)
                self.draw_keybind_menu()
            else:
                if self.motion_blur:
                    self.game_surface.blit(motion_blur_surface, (0, 0))
                else:
                    self.game_surface.fill((0, 0, 0))

                keys = pygame.key.get_pressed()
                if self.control_style == 'auto':
                    if self.chaos_mode:
                        self.update_chaos_mode()
                    self.update_angles_auto()
                else:
                    self.update_angles_manual(keys)

                self.draw_tesseract()

                self.draw_text("WASD/QE: Rotate (manual)", (10, 10), font, (180, 180, 180))
                self.draw_text("SPACE: Cycle palette in set", (10, 40), font, (180, 180, 180))
                self.draw_text("B: Toggle motion blur", (10, 70), font, (180, 180, 180))
                self.draw_text("ESC: Return to menu", (10, 100), font, (180, 180, 180))
                self.draw_text("SHIFT+M: Toggle keybind menu", (10, 130), font, (180, 180, 180))
                self.draw_text("SHIFT+P: Toggle palette menu", (10, 160), font, (180, 180, 180))
                self.draw_text("C: Toggle Chaos Mode", (10, 190), font, (180, 180, 180))
                self.draw_text("F11: Toggle fullscreen", (10, 220), font, (180, 180, 180))
                self.draw_text(f"Control: {self.control_style.capitalize()} | Palette Set: {self.palette_set_idx+1} | Palette #: {self.palette_idx_in_set+1}", (10, GAME_SIZE - 30), font, (180, 180, 180))

                if self.chaos_mode:
                    chaos_text = "CHAOS MODE ACTIVE"
                    self.draw_text(chaos_text, (GAME_SIZE - big_font.size(chaos_text)[0] - 20, 20), big_font, (255, 50, 50))

                if self.show_keybinds and self.state == 0:
                    self.keybind_fade.update()
                    self.keybind_fade.draw(self.game_surface)
                    self.draw_keybind_menu()

            # scale and blit game_surface to display_surface
            if self.fullscreen:
                dw, dh = self.display_surface.get_size()
                size = min(dw, dh)
                scaled = pygame.transform.smoothscale(self.game_surface, (size, size))
                x = (dw - size) // 2
                y = (dh - size) // 2
                self.display_surface.fill((0, 0, 0))
                self.display_surface.blit(scaled, (x, y))
            else:
                self.display_surface.blit(self.game_surface, (0, 0))

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    try:
        app = TesseractApp()
        app.run()
    except Exception as e:
        import traceback
        print("An error occurred:", e)
        traceback.print_exc()

        input("Press Enter to close...")

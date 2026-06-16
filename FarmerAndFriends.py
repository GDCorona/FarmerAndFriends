import pygame
import sys
import os

# --- BULLETPROOF PATH FIX ---
# This forces Windows to look for assets in the exact folder where the game lives
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ==========================================
# 1. INITIALIZATION & SETUP
# ==========================================
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 800, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("FARMER AND FRIENDS")
# --- Set the Window Icon ---
try:
    icon_image = pygame.image.load("images/icon.png") 
    pygame.display.set_icon(icon_image)
except (pygame.error, FileNotFoundError):
    pass # If it fails, Pygame just uses its default snake icon
clock = pygame.time.Clock()

# --- Colors ---
BLACK, WHITE = (0, 0, 0), (255, 255, 255)
RED, GREEN, YELLOW = (200, 0, 0), (100, 200, 100), (200, 200, 100)
RED_HOVER, GREEN_HOVER = (250, 50, 50), (150, 250, 150)
BTN_COLOR, HOVER_COLOR = (220, 220, 220), (180, 180, 180)
GRASS_COLOR, RIVER_COLOR, BG_COLOR = (34, 139, 34), (30, 144, 255), (200, 230, 255)

# --- Fonts ---
small_font = pygame.font.SysFont(None, 24)
font = pygame.font.SysFont(None, 30)
large_font = pygame.font.SysFont(None, 48)

# ==========================================
# 2. ASSET LOADING (Images & Sounds)
# ==========================================
def load_img(path, size=None):
    """Helper to safely load and scale images."""
    try:
        img = pygame.image.load(path)
        return pygame.transform.scale(img, size) if size else img
    except (pygame.error, FileNotFoundError):
        return None

def load_snd(path):
    """Helper to safely load sound files."""
    try:
        return pygame.mixer.Sound(path)
    except (pygame.error, FileNotFoundError):
        return None

# Images
loading_img     = load_img("images/loading.png", (WIDTH, HEIGHT))
bg_img         = load_img("images/bg.jpg", (WIDTH, HEIGHT))
heart_img      = load_img("images/heart.png", (30, 30))
farmer_img     = load_img("images/farmer.jpg", (80, 80))
fox_img        = load_img("images/fox.jpg", (80, 80))
goose_img      = load_img("images/goose.jpg", (80, 80))
bean_img       = load_img("images/bean.jpg", (80, 80))
home_img       = load_img("images/home.jpg", (40, 40))
music_on_img   = load_img("images/music_on.jpg", (40, 40))
music_off_img  = load_img("images/music_off.jpg", (40, 40))
speaker_on_img = load_img("images/speaker_on.jpg", (40, 40))
speaker_off_img= load_img("images/speaker_off.jpg", (40, 40))
# --- Load Logo Safely ---
raw_logo = load_img("images/title_logo.png") 
if raw_logo:
    aspect_ratio = raw_logo.get_height() / raw_logo.get_width()
    
    # 1. Loading Screen Logo (Smaller)
    w_small = 400 
    h_small = int(w_small * aspect_ratio)
    logo_small = pygame.transform.smoothscale(raw_logo, (w_small, h_small))
    
    # 2. Main Menu Logo (Bigger)
    w_large = 600 
    h_large = int(w_large * aspect_ratio)
    logo_large = pygame.transform.smoothscale(raw_logo, (w_large, h_large))
else:
    logo_small = None
    logo_large = None

# Sounds
click_snd = load_snd("sound/click.wav")
error_snd = load_snd("sound/error.wav")
win_snd   = load_snd("sound/win.wav")
fail_snd  = load_snd("sound/fail.wav")

try:
    pygame.mixer.music.load("sound/bgmusic.mp3") 
except (pygame.error, FileNotFoundError):
    pass

# ==========================================
# 3. GAME VARIABLES & STATE
# ==========================================
# Application State
current_screen = "LOADING"
loading_progress = 0.0    
music_on, sfx_on = True, True

# Puzzle State
state = (0, 0, 0, 0) # (Farmer, Fox, Goose, Bean). 0 = Left, 1 = Right
move_count = 0
popup_msg, popup_timer = "", 0
confirm_home, show_help = False, False

# Hard Mode State
hard_mode = False
hearts = 3
time_limit = 30.0
time_remaining = time_limit
fail_reason = ""
show_hard_info = False

# Screen Transition Setup
fade_alpha, fade_state = 0, 0 # 0 = Off, 1 = Fading out, -1 = Fading in
target_screen = ""
fade_surface = pygame.Surface((WIDTH, HEIGHT))
fade_surface.fill(BLACK)

# ==========================================
# 4. UI DEFINITIONS (Rects)
# ==========================================
# Global Icons
help_btn_rect  = pygame.Rect(WIDTH - 60, HEIGHT - 60, 40, 40)
sfx_btn_rect   = pygame.Rect(WIDTH - 110, HEIGHT - 60, 40, 40)
music_btn_rect = pygame.Rect(WIDTH - 160, HEIGHT - 60, 40, 40)
home_btn_rect  = pygame.Rect(WIDTH - 210, HEIGHT - 60, 40, 40)

# Menus & Popups
menu_play_btn  = pygame.Rect(300, 250, 200, 60)
menu_hard_btn  = pygame.Rect(300, 330, 200, 60)
win_menu_btn   = pygame.Rect(300, 250, 200, 60)
btn_yes        = pygame.Rect(450, 250, 100, 40)
btn_no         = pygame.Rect(250, 250, 100, 40)
close_help_btn = pygame.Rect(WIDTH // 2 - 50, 330, 100, 40)
close_hard_btn = pygame.Rect(WIDTH // 2 - 50, 280, 100, 40)

# Gameplay Control Buttons
buttons = [
    {"rect": pygame.Rect(330, 100, 160, 40), "label": "Move Farmer", "move": (1, 0, 0, 0)},
    {"rect": pygame.Rect(330, 160, 160, 40), "label": "Take Fox",    "move": (1, 1, 0, 0)},
    {"rect": pygame.Rect(330, 220, 160, 40), "label": "Take Goose",  "move": (1, 0, 1, 0)},
    {"rect": pygame.Rect(330, 280, 160, 40), "label": "Take Bean",   "move": (1, 0, 0, 1)}
]

# ==========================================
# 5. CORE LOGIC FUNCTIONS
# ==========================================
def play_sfx(sound_obj):
    if sfx_on and sound_obj: sound_obj.play()

def change_screen(new_screen):
    global fade_state, target_screen
    if fade_state == 0:
        fade_state, target_screen = 1, new_screen

def show_popup(text, duration=90):
    global popup_msg, popup_timer
    popup_msg, popup_timer = text, duration

def penalize(error_msg):
    """Handles invalid moves, plays sound, and manages hard mode deaths."""
    global hearts, fail_reason
    play_sfx(error_snd)
    show_popup(error_msg)
    if hard_mode:
        hearts -= 1
        if hearts <= 0:
            fail_reason = "You ran out of hearts! :("
            change_screen("FAIL")

def make_move(move):
    global state, move_count

    F, C, G, B = state
    # 1. Location checks
    if move[1] == 1 and C != F: return penalize("Invalid move! Fox is on the other side!")
    if move[2] == 1 and G != F: return penalize("Invalid move! Goose is on the other side!")
    if move[3] == 1 and B != F: return penalize("Invalid move! Bean is on the other side!")

    # 2. Calculate new state
    new_state = tuple((state[i] + move[i]) % 2 for i in range(4))

    # 3. Validation checks
    if new_state[1] == new_state[2] and new_state[0] != new_state[1]:
        return penalize("Invalid move! Goose got eaten by fox :(")
    if new_state[2] == new_state[3] and new_state[0] != new_state[2]:
        return penalize("Invalid move! The goose ate your beans :(")

    # 4. Apply Valid Move
    state = new_state
    move_count += 1
    play_sfx(click_snd)
    if state == (1, 1, 1, 1):
        change_screen("WIN")

# ==========================================
# 6. UI DRAWING HELPERS
# ==========================================
def draw_button(rect, text, default_col, hover_col, mouse_pos, txt_col=BLACK, radius=8):
    """Draws a rounded interactive button with hover effects."""
    color = hover_col if rect.collidepoint(mouse_pos) else default_col
    pygame.draw.rect(screen, color, rect, border_radius=radius)
    pygame.draw.rect(screen, BLACK, rect, max(2, radius//4), border_radius=radius)
    surf = font.render(text, True, txt_col)
    screen.blit(surf, surf.get_rect(center=rect.center))

def draw_panel(rect, rgba_color, border_color=BLACK, radius=15):
    """Draws a semi-transparent rounded background panel."""
    bg_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(bg_surface, rgba_color, bg_surface.get_rect(), border_radius=radius)
    screen.blit(bg_surface, rect.topleft)
    pygame.draw.rect(screen, border_color, rect, 4, border_radius=radius)

def draw_icon_button(rect, img_on, img_off, is_on, fallback_text, fallback_color):
    """Draws small square utility icons (Sound, Music, Home, Help)."""
    target_img = img_on if is_on else img_off
    if target_img:
        screen.blit(target_img, rect)
    else:
        color = fallback_color if is_on else RED
        pygame.draw.rect(screen, color, rect)
        surf = font.render(fallback_text, True, BLACK)
        screen.blit(surf, surf.get_rect(center=rect.center))
    pygame.draw.rect(screen, BLACK, rect, 2)

def draw_wrapped_text(surface, text, font, color, max_width, start_x, start_y, line_spacing=24):
    """Wraps text to fit inside a maximum width and draws it centered."""
    words = text.split(' ')
    lines = []
    current_line = ""
    
    # Measure each word and build lines that fit the max_width
    for word in words:
        test_line = current_line + word + " "
        if font.size(test_line)[0] < max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word + " "
    lines.append(current_line)

    # Draw each line and move down
    y_offset = start_y
    for line in lines:
        text_surf = font.render(line.strip(), True, color)
        surface.blit(text_surf, (start_x, y_offset))
        y_offset += line_spacing
        
    return y_offset # Return the final Y position

# ==========================================
# 7. SCREEN DRAWING FUNCTIONS
# ==========================================
def draw_loading_screen():
    # Draw the splash image (or black if it fails to load)
    if loading_img:
        screen.blit(loading_img, (0, 0))
    else:
        screen.fill(BLACK)
    # --- Draw title logo ---
    if logo_small:
        # Pin the center of the logo near the top of the screen
        logo_rect = logo_small.get_rect(center=(WIDTH // 2, 80))
        screen.blit(logo_small, logo_rect)
    # Draw "Loading..." text with a shadow for visibility
    text = "Loading..."
    shadow_surf = large_font.render(text, True, BLACK)
    screen.blit(shadow_surf, shadow_surf.get_rect(center=(WIDTH // 2 + 2, HEIGHT - 90 + 2)))
    text_surf = large_font.render(text, True, WHITE)
    screen.blit(text_surf, text_surf.get_rect(center=(WIDTH // 2, HEIGHT - 90)))
    
    # --- The Loading Bar ---
    bar_width, bar_height = 400, 30
    bar_x, bar_y = (WIDTH - bar_width) // 2, HEIGHT - 50
    
    # Background of the bar (Empty)
    pygame.draw.rect(screen, BLACK, (bar_x, bar_y, bar_width, bar_height), border_radius=15)
    pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 3, border_radius=15)
    
    # The filling part of the bar
    fill_width = int((loading_progress / 100.0) * (bar_width - 6)) # -6 for border padding
    if fill_width > 0:
        pygame.draw.rect(screen, GREEN, (bar_x + 3, bar_y + 3, fill_width, bar_height - 6), border_radius=12)

def draw_background():
    if bg_img: screen.blit(bg_img, (0, 0))
    else:
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, GRASS_COLOR, (0, 0, 300, HEIGHT))
        pygame.draw.rect(screen, RIVER_COLOR, (300, 0, 200, HEIGHT))
        pygame.draw.rect(screen, GRASS_COLOR, (500, 0, 300, HEIGHT))

def draw_global_ui():
    """Draws the persistent icons in the bottom right."""
    draw_icon_button(help_btn_rect, None, None, True, "?", (100, 200, 255))
    draw_icon_button(sfx_btn_rect, speaker_on_img, speaker_off_img, sfx_on, "🔈", GREEN)
    draw_icon_button(music_btn_rect, music_on_img, music_off_img, music_on, "🎵", GREEN)
    if current_screen == "GAME":
        draw_icon_button(home_btn_rect, home_img, None, True, "H", YELLOW)

def draw_menu(mouse_pos):
    draw_background()
    # Title Panel
    if logo_large:
        # Center the logo near the top
        logo_rect = logo_large.get_rect(center=(WIDTH // 2, 150))
        screen.blit(logo_large, logo_rect)
    else:
        title_rect = pygame.Rect(150, 140, 500, 80)
        draw_panel(title_rect, (255, 255, 255, 180))
        title_surf = large_font.render("FARMER AND FRIENDS", True, BLACK)
        screen.blit(title_surf, title_surf.get_rect(center=title_rect.center))

    # Disable hover if a popup is active
    btn_mouse_pos = (-1, -1) if (show_help or show_hard_info) else mouse_pos
    # Play & Hard Mode Buttons
    draw_button(menu_play_btn, "PLAY GAME", GREEN, GREEN_HOVER, btn_mouse_pos, radius=15)
    hm_text = "HARD MODE: ON" if hard_mode else "HARD MODE: OFF"
    hm_text_col = WHITE if hard_mode else BLACK
    draw_button(menu_hard_btn, hm_text, RED if hard_mode else BTN_COLOR, RED_HOVER, btn_mouse_pos, hm_text_col, 15)

def draw_game(mouse_pos):
    draw_background()
    
    # Draw Characters
    images = [farmer_img, fox_img, goose_img, bean_img]
    y_positions = [40, 130, 220, 310] 
    for i, img in enumerate(images):
        if img: screen.blit(img, (100 if state[i] == 0 else 650, y_positions[i]))

    # Disable background hover if any popup is active
    is_blocked = confirm_home or popup_timer > 0 or show_help or show_hard_info
    btn_mouse_pos = (-1, -1) if is_blocked else mouse_pos
    # Draw Gameplay Buttons & Counters
    for btn in buttons:
        draw_button(btn["rect"], btn["label"], BTN_COLOR, HOVER_COLOR, btn_mouse_pos)
        
    moves_surf = font.render(f"Moves: {move_count}", True, BLACK)
    screen.blit(moves_surf, moves_surf.get_rect(center=(WIDTH // 2, HEIGHT - 40)))

    if hard_mode:
        t_color = RED if time_remaining < 10 else BLACK
        t_surf = font.render(f"Time: {int(time_remaining)}", True, t_color)
        screen.blit(t_surf, t_surf.get_rect(center=(80, HEIGHT - 40)))
        for i in range(hearts):
            x = 140 + (i * 35)
            if heart_img: screen.blit(heart_img, (x, HEIGHT - 55))
            else: pygame.draw.circle(screen, RED, (x + 15, HEIGHT - 40), 12)

    # Popups
    if popup_timer > 0:
        popup_rect = pygame.Rect(180, 150, 450, 100)
        draw_panel(popup_rect, (255, 255, 255, 230), RED)
        msg_surf = font.render(popup_msg, True, BLACK)
        screen.blit(msg_surf, msg_surf.get_rect(center=popup_rect.center))
        
    if confirm_home:
        conf_rect = pygame.Rect(180, 150, 450, 180)
        draw_panel(conf_rect, (255, 255, 255, 230))
        msg_surf = font.render("Quit the game? Progress will not be saved", True, BLACK)
        screen.blit(msg_surf, msg_surf.get_rect(center=(WIDTH//2, 190)))
        draw_button(btn_yes, "Yes", GREEN, GREEN_HOVER, mouse_pos)
        draw_button(btn_no, "No", RED, RED_HOVER, mouse_pos, WHITE)

def draw_help_popup(mouse_pos):
    if not show_help: return
    rect = pygame.Rect(70, 30, 660, 430)
    draw_panel(rect, (255, 255, 255, 240))

    title_surf = large_font.render("How to Play", True, BLACK)
    screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 70)))
    instructions = [
        "A farmer from Morioh-chou is stranded at the riverbank with a bag of beans and his two pets, a goose and a fox. The goose and the fox are both impaired and incapable of swimming for a magical reason. Your task is to help the farmer bring everything safely to the other side of the river. But remember:",
        "1. The farmer is weak so he can only take one item with him each time he crosses the river.",
        "2. The fox and the goose don't get along well and they must not be left alone without the farmer's supervision.",
        "3. The goose is starving and will immediately swallow all of the farmer's beans if he isn't there.",
        "Try to get everyone to the other side to win the game. Good luck!"
    ]
    current_y = 100
    max_text_width = 620
    start_x = 90
    for paragraph in instructions:
        current_y = draw_wrapped_text(screen, paragraph, small_font, BLACK, max_text_width, start_x, current_y) + 10
    close_help_btn.centery = 430
    draw_button(close_help_btn, "Close", RED, RED_HOVER, mouse_pos, WHITE)

def draw_hard_info_popup(mouse_pos):
    if not show_hard_info: return
    
    rect = pygame.Rect(150, 100, 500, 250)
    draw_panel(rect, (255, 255, 255, 250), RED)
    
    title_surf = large_font.render("HARD MODE ACTIVATED!!!", True, RED)
    screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 140)))
    
    instructions = [
        f"1. You only have {int(time_limit)} seconds to win!",
        "2. You only have 3 hearts.",
        "3. Every invalid move costs 1 heart."
    ]
    start_x = 180
    for i, line in enumerate(instructions):
        text_surf = font.render(line, True, BLACK)
        screen.blit(text_surf, (start_x, 190 + (i * 25)))
        
    draw_button(close_hard_btn, "Start", RED, RED_HOVER, mouse_pos, WHITE)

def draw_end_screen(mouse_pos, title, title_col, bg_color, subtext):
    """Handles both the WIN and FAIL screens to reduce redundant code."""
    draw_background()
    panel_rect = pygame.Rect(100, 50, 600, 160)
    draw_panel(panel_rect, bg_color, title_col)
    
    title_surf = large_font.render(title, True, title_col)
    screen.blit(title_surf, title_surf.get_rect(center=(WIDTH // 2, 90)))
    
    sub_surf = font.render(subtext, True, BLACK)
    screen.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, 160)))

    # Disable background hover if a popup is active
    btn_mouse_pos = (-1, -1) if (show_help or show_hard_info) else mouse_pos
    draw_button(win_menu_btn, "MAIN MENU", GREEN, GREEN_HOVER, btn_mouse_pos, radius=15)

# ==========================================
# 8. MAIN GAME LOOP
# ==========================================
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    # --- CURSOR HOVER LOGIC ---
    is_hovering = False
    # Only show pointer if the screen isn't fading
    if fade_state == 0: 
        # 1. Check top-level popups first
        if show_hard_info:
            if close_hard_btn.collidepoint(mouse_pos): is_hovering = True
        elif show_help:
            if close_help_btn.collidepoint(mouse_pos): is_hovering = True
        elif confirm_home:
            if btn_yes.collidepoint(mouse_pos) or btn_no.collidepoint(mouse_pos): is_hovering = True
        
        # 2. Check Standard Screen Elements
        else:
            # Global Buttons
            if help_btn_rect.collidepoint(mouse_pos) or sfx_btn_rect.collidepoint(mouse_pos) or music_btn_rect.collidepoint(mouse_pos):
                is_hovering = True
                
            # Menu Screen
            if current_screen == "MENU":
                if menu_play_btn.collidepoint(mouse_pos) or menu_hard_btn.collidepoint(mouse_pos): 
                    is_hovering = True
                    
            # Game Screen
            elif current_screen == "GAME":
                if home_btn_rect.collidepoint(mouse_pos): is_hovering = True
                if popup_timer == 0: # Only hover game buttons if no error popup is showing
                    for btn in buttons:
                        if btn["rect"].collidepoint(mouse_pos): is_hovering = True
                        
            # End Screens
            elif current_screen in ["WIN", "FAIL"]:
                if win_menu_btn.collidepoint(mouse_pos): is_hovering = True

    # Apply the correct cursor
    if is_hovering:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
    else:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
    # --------------------------
    # 1. Timers & Cooldowns
    if current_screen == "LOADING" and fade_state == 0:
        loading_progress += 1.5
        if loading_progress >= 100:
            loading_progress = 100
            change_screen("MENU")
            if music_on:
                try:
                    pygame.mixer.music.play(-1)
                except pygame.error:
                    pass
    if current_screen == "GAME" and hard_mode and fade_state == 0 and not confirm_home and not show_help and not show_hard_info:
        time_remaining = max(0, time_remaining - 1 / 30.0)
        if time_remaining == 0:
            fail_reason = "You ran out of time! :("
            change_screen("FAIL")
            
    if popup_timer > 0 and not confirm_home:
        popup_timer -= 1

    # 2. Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and fade_state == 0:
            click_pos = event.pos
            # Popups intercept clicks first
            if show_hard_info:
                if close_hard_btn.collidepoint(click_pos): 
                    show_hard_info, _ = False, play_sfx(click_snd)
                continue

            if show_help:
                if close_help_btn.collidepoint(click_pos): show_help, _ = False, play_sfx(click_snd)
                continue
                
            if confirm_home:
                if btn_yes.collidepoint(click_pos): confirm_home, _ = False, play_sfx(click_snd); change_screen("MENU")
                if btn_no.collidepoint(click_pos):  confirm_home, _ = False, play_sfx(click_snd)
                continue

            # Global Icons
            if current_screen != "LOADING":
                if help_btn_rect.collidepoint(click_pos):  show_help, _ = True, play_sfx(click_snd); continue
                if sfx_btn_rect.collidepoint(click_pos):   sfx_on = not sfx_on; play_sfx(click_snd); continue
                if music_btn_rect.collidepoint(click_pos):
                    music_on = not music_on; play_sfx(click_snd)
                    pygame.mixer.music.unpause() if music_on else pygame.mixer.music.pause()
                    continue
                if current_screen == "GAME" and home_btn_rect.collidepoint(click_pos):
                    confirm_home, _ = True, play_sfx(click_snd); continue

            # Screen-Specific Clicks
            if current_screen == "MENU":
                if menu_play_btn.collidepoint(click_pos): play_sfx(click_snd); change_screen("GAME")
                if menu_hard_btn.collidepoint(click_pos): play_sfx(click_snd); hard_mode = not hard_mode
                    
            elif current_screen == "GAME":
                if popup_timer > 0: popup_timer = 0; continue # Dismiss errors
                for btn in buttons:
                    if btn["rect"].collidepoint(click_pos): make_move(btn["move"])
                        
            elif current_screen in ["WIN", "FAIL"]:
                if win_menu_btn.collidepoint(click_pos): play_sfx(click_snd); change_screen("MENU")

    # 3. Draw Current Screen
    if current_screen == "LOADING": draw_loading_screen()
    elif current_screen == "MENU": draw_menu(mouse_pos)
    elif current_screen == "GAME": draw_game(mouse_pos)
    elif current_screen == "WIN":
        draw_end_screen(mouse_pos, "YOU WIN!", (0, 150, 0), (255, 255, 255, 230), f"You brought everyone to the other side in {move_count} moves!")
    elif current_screen == "FAIL":
        draw_end_screen(mouse_pos, "GAME OVER", RED, (255, 200, 200, 230), fail_reason)
    if current_screen != "LOADING":
        draw_global_ui()
        draw_help_popup(mouse_pos)
        draw_hard_info_popup(mouse_pos)

    # 4. Handle Screen Transitions
    if fade_state != 0:
        fade_alpha += fade_state * 15
        if fade_alpha >= 255:
            fade_alpha, fade_state, current_screen = 255, -1, target_screen
            
            # Reset Game Data on Transition
            if target_screen in ["MENU", "GAME"]:
                state, move_count, popup_timer, hearts, time_remaining = (0,0,0,0), 0, 0, 3, time_limit
                if target_screen == "GAME" and hard_mode:
                    show_hard_info = True
                else:
                    show_hard_info = False
            # Play arrival sounds
            if target_screen == "WIN": play_sfx(win_snd)
            elif target_screen == "FAIL": play_sfx(fail_snd)
            
        elif fade_alpha <= 0:
            fade_alpha, fade_state = 0, 0
            
        fade_surface.set_alpha(fade_alpha)
        screen.blit(fade_surface, (0, 0))

    # 5. Update Display
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()

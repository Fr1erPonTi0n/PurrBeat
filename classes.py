import pygame, configparser, sqlite3

# === Чтение конфигурации ===

config = configparser.ConfigParser()
config.read('config.ini')

WIDTH = int(config['General']['WIDTH'])
HEIGHT = int(config['General']['HEIGHT'])
RESOLUTIONS = [tuple(map(int, res.split('x'))) for res in config['Resolutions']['resolutions'].split(',')]
BUTTON_TYPE_MOVABLE = int(config['Buttons']['BUTTON_TYPE_MOVABLE'])
BUTTON_TYPE_HIGHLIGHT = int(config['Buttons']['BUTTON_TYPE_HIGHLIGHT'])
BUTTON_COLOR = tuple(map(int, config['Colors']['BUTTON_COLOR'].split(',')))
BUTTON_HOVER_COLOR = tuple(map(int, config['Colors']['BUTTON_HOVER_COLOR'].split(',')))
HOVER_OFFSET = int(config['Buttons']['HOVER_OFFSET'])
BUTTON_RADIUS = int(config['Buttons']['BUTTON_RADIUS'])

# === Основные классы ===

"""КЛАСС КНОПОК
    - text: текст, который будет отображаться на кнопке.
    - x: горизонтальная позиция кнопки на экране.
    - y: вертикальная позиция кнопки на экране.
    - width: ширина кнопки.
    - height: высота кнопки.
    - action: функция, которая будет вызвана при нажатии на кнопку.
    - button_type: тип кнопки, который определяет ее поведение при наведении курсора."""

class Buttons:
    def __init__(self, text, x, y, width, height, action, button_type, size=36):
        self.text = text
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, width, height)
        self.hovered = False
        self.action = action
        self.button_type = button_type
        self.size = size

    def draw(self, surface):
        if self.hovered:
            if self.button_type == BUTTON_TYPE_MOVABLE:
                color = BUTTON_HOVER_COLOR
                offset_x = -HOVER_OFFSET
            elif self.button_type == BUTTON_TYPE_HIGHLIGHT:
                color = BUTTON_HOVER_COLOR
                offset_x = 0
            else:
                color = BUTTON_COLOR
                offset_x = 0
        else:
            color = BUTTON_COLOR
            offset_x = 0
        pygame.draw.rect(surface, color, self.rect.move(offset_x, 0), border_radius=BUTTON_RADIUS)
        font = pygame.font.Font("../PurrBeats/data/font.ttf", self.size)
        text_surface = font.render(self.text, True, (0, 0, 0))
        text_rect = text_surface.get_rect(center=self.rect.move(offset_x, 0).center)
        surface.blit(text_surface, text_rect)

    def update(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def click(self):
        if self.hovered:
            self.action()

"""КЛАСС НАСТРОЙКИ ЗВУКА С ПОМОЩЬЮ ПОЛЗУНКА
    - x, y: координаты верхнего левого угла ползунка.
    - width, height: ширина и высота ползунка.
    - min_value: минимальное значение громкости (по умолчанию 0).
    - max_value: максимальное значение громкости (по умолчанию 1).
    - initial_value: начальное значение громкости (по умолчанию 0.5)."""

class VolumeSlider:
    def __init__(self, x, y, width, height, min_value=0, max_value=1, initial_value=0.5):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self.value = round(initial_value, 2)
        self.slider_rect = pygame.Rect(x, y, width * self.value, height)
        self.dragging = False

    def draw(self, screen):
        pygame.draw.rect(screen, (200, 200, 200), self.rect)
        pygame.draw.rect(screen, (100, 100, 100), self.slider_rect)

    def update(self, mouse_pos, mouse_pressed):
        if self.dragging:
            if self.rect.collidepoint(mouse_pos):
                new_x = mouse_pos[0] - self.rect.x
                new_x = max(0, min(new_x, self.rect.width))
                self.slider_rect.width = new_x
                self.value = round(
                    self.min_value + (new_x / self.rect.width) * (self.max_value - self.min_value), 2
                )
                pygame.mixer.music.set_volume(self.value)
                self.update_config()
        if mouse_pressed[0]:
            if self.rect.collidepoint(mouse_pos):
                self.dragging = True
        else:
            self.dragging = False

    def get_value(self):
        return self.value

    def update_config(self):
        config['General']['VOLUME'] = str(self.value)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

"""КЛАСС ТЕКСТ 
    - text: текст, который будет отображаться на кнопке.
    - x, y: координаты центра текста на экране.
    - font: путь к файлу шрифта, который будет использоваться для отображения текста.
    - size: размер шрифта.
    - background_color: цвет фона кнопки (по умолчанию светло-серый).
    - text_color: цвет текста (по умолчанию черный).
    - border_radius: радиус округления углов фона кнопки (по умолчанию 10 пикселей)."""

class TextBox:
    def __init__(self, text, x, y, font, size, background_color=(200, 200, 200), text_color=(0, 0, 0),
                 width=None, height=None, border_radius=30):
        self.text = text
        self.x = x
        self.y = y
        self.font = pygame.font.Font(font, size)
        self.background_color = background_color
        self.text_color = text_color
        self.border_radius = border_radius

        if width is not None and height is not None:
            self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        else:
            text_surface = self.font.render(self.text, True, self.text_color)
            self.rect = text_surface.get_rect(center=(x, y))
            self.rect.inflate_ip(20, 20)

    def draw(self, surface):
        pygame.draw.rect(surface, self.background_color, self.rect, border_radius=self.border_radius)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

"""КЛАСС ИЗМЕНЕНИЯ РАЗРЕШЕНИЯ"""

class ResolutionManager:
    def __init__(self):
        self.current_resolution_index = 0

    def change_resolution(self):
        new_resolution = RESOLUTIONS[self.current_resolution_index]
        if new_resolution != (WIDTH, HEIGHT):
            pygame.display.set_mode(new_resolution)
            print(f"Разрешение изменено на: {new_resolution[0]}x{new_resolution[1]}")
            return new_resolution
        return None

    def next_resolution(self):
        self.current_resolution_index = (self.current_resolution_index + 1) % len(RESOLUTIONS)
        return RESOLUTIONS[self.current_resolution_index]

"""КЛАСС АНИМАЦИИ
    - sheet: Спрайтовый лист.
    - columns: Количество колонок в спрайтовом листе.
    - rows: Количество строк в спрайтовом листе.
    - x: Координата X начальной позиции.
    - y: Координата Y начальной позиции.
    - screen_width: Ширина разрешения экрана.
    - screen_height: Высота разрешения экрана.
    - fps: Частота смены кадров (FPS)."""


class AnimatedSprite(pygame.sprite.Sprite):
    def __init__(self, sheet, columns, rows, x, y, screen_width=1280, screen_height=720, fps=10):
        super().__init__()
        self.frames = []
        self.cur_frame = 0
        self.image = None
        self.rect = None
        self.frame_delay = 1000 // fps
        self.last_update = pygame.time.get_ticks()
        default_width, default_height = 1280, 720
        self.scale_factor = min(screen_width / default_width, screen_height / default_height) * 2

        self.cut_sheet(sheet, columns, rows)
        self.image = self.frames[self.cur_frame]
        self.rect = self.image.get_rect(topleft=(x, y))

    def cut_sheet(self, sheet, columns, rows):
        frame_width = sheet.get_width() // columns
        frame_height = sheet.get_height() // rows

        for j in range(rows):
            for i in range(columns):
                frame_location = (frame_width * i, frame_height * j)
                frame = sheet.subsurface(pygame.Rect(frame_location, (frame_width, frame_height)))
                scaled_frame = pygame.transform.scale(frame,
                                                      (int(frame_width * self.scale_factor),
                                                       int(frame_height * self.scale_factor)))
                self.frames.append(scaled_frame)

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update >= self.frame_delay:
            self.last_update = now
            self.cur_frame = (self.cur_frame + 1) % len(self.frames)
            self.image = self.frames[self.cur_frame]

"""КЛАСС РАБОТЫ СО СПИСКОМ ЛИДЕРОВ"""

class LeaderBoard:
    def __init__(self):
        self.con = sqlite3.connect("../PurrBeats/data/leaderboard_game.db")

    def list_leaders(self, level_id):
        cur = self.con.cursor()
        leaders = cur.execute("SELECT username, score FROM leaders WHERE level = ?",
                                (level_id,)).fetchall()
        self.con.close()
        return leaders

    def add_leader(self, username, score, level):
        cur = self.con.cursor()
        existing_leader = cur.execute("SELECT score FROM leaders WHERE username = ? AND level = ?",
                                      (username, level)).fetchone()
        if existing_leader:
            current_high_score = existing_leader[0]
            if score > current_high_score:
                cur.execute("UPDATE leaders SET score = ? WHERE username = ? AND level = ?",
                            (score, username, level))
        elif username is not None:
            cur.execute("INSERT INTO leaders (username, score, level) VALUES (?, ?, ?)",
                        (username, score, level))
        self.con.commit()
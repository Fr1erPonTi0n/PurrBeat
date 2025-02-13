import time, pygame, random, json, configparser, gameover
from classes import AnimatedSprite

# === Чтение конфигурации ===

config = configparser.ConfigParser()
config.read('config.ini')

WIDTH = int(config['General']['WIDTH'])
HEIGHT = int(config['General']['HEIGHT'])
FPS = int(config['General']['FPS'])
VOLUME = float(config['General']['VOLUME'])
BACKGROUND_IMAGE = config['Background']['BACKGROUND_IMAGE']
DEFAULT_FONT = config['Fonts']['DEFAULT_FONT']
BOOT_DELAY = int(config['Game']['BOOT_DELAY'])
ICON_APP = config['Icons']['ICON_APP']
ARROW_SPEED = int(config['Game']['ARROW_SPEED'])
CIRCLE_SPEED = float(config['Game']['CIRCLE_SPEED'])
WAVE_SPEED = float(config['Game']['WAVE_SPEED'])

# === Инициализация Pygame ===

pygame.init()
pygame.mixer.music.set_volume(VOLUME)

# === Настройки экрана ===

screen = pygame.display.set_mode((WIDTH, HEIGHT))
icon = pygame.image.load(ICON_APP)
pygame.display.set_icon(icon)

# === Глобальные переменные  ===

background_image = pygame.image.load(BACKGROUND_IMAGE) # Загрузка изображения
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT)) # Фотография подстраивается под разрешение
font = pygame.font.Font(DEFAULT_FONT, 36) # Шрифт для игры

ARROW_SIZE = (int(150 * (WIDTH / 1280)), int(150 * (HEIGHT / 720))) # Размер стрелков в FNF Mode
CIRCLE_SIZE = int(75 * min(WIDTH / 1280, HEIGHT / 720)) # Размер круга в OSU Mode
WAVE_SIZE = int(50 * min(WIDTH / 1280, HEIGHT / 720)) # Размер волны в Wave Mode
OBSTACLE_IMAGE_SIZE = int(150 * min(WIDTH / 1280, HEIGHT / 720)) # Размер препятствии в Wave Mode
OBSTACLE_SIZE = int(100 * min(WIDTH / 1280, HEIGHT / 720)) # Размер препятствии в Wave Mode

score = 0 # Кол-во набранных очков
current_mode = 1  # Начальный режим
mode_start_time = 0  # Время начала текущего режима

# === Изображения кружочков для OSU Mode ===

CIRCLE_IMAGES = [pygame.transform.scale(pygame.image.load(f"../PurrBeats/data/assets/osu_mode/circle{i}.png" ),
                (CIRCLE_SIZE * 2, CIRCLE_SIZE * 2)) for i in range(1, 6)]

# === Изображения стрелок для FNF Mode ===

ARROW_IMAGES = {direction: pygame.transform.scale(
                pygame.image.load(f"../PurrBeats/data/assets/arrows_mode/{direction}_arrow.png" ), ARROW_SIZE)
                for direction in ["up", "down", "left", "right"]}

# === Изображения, где должны падать стрелки для FNF Mode ===

ZONE_IMAGES = {direction: pygame.transform.scale(
               pygame.image.load(f"../PurrBeats/data/assets/arrows_mode/{direction}_zone.png" ), ARROW_SIZE)
               for direction in ["up", "down", "left", "right"]}

# === Изображение волны для Wave Mode ===

WAVE_IMAGE = pygame.transform.scale(pygame.image.load("../PurrBeats/data/assets/wave_mode/wave.png"), (WAVE_SIZE, WAVE_SIZE))

# === Изображения препятствии для Wave Mode ===

OBSTACLE_IMAGES = [pygame.transform.scale(pygame.image.load(f"../PurrBeats/data/assets/wave_mode/cat{i}.png" ),
             (OBSTACLE_IMAGE_SIZE, OBSTACLE_IMAGE_SIZE)) for i in range(1, 6)]

# === Классы игровых режимов ===

class FNFMode:
    def __init__(self):
        """Инициализация объектов для режима FNF Mode."""
        self.arrow_size = ARROW_SIZE
        self.arrow_speed = ARROW_SPEED
        self.arrows = []
        self.missed_arrows = 0
        self.target_positions = {
            "up": (WIDTH // 1.8 - 1.5 * self.arrow_size[0], HEIGHT // 1.05 - self.arrow_size[1] - 20),
            "down": (WIDTH // 1.8 - 0.5 * self.arrow_size[0], HEIGHT // 1.05 - self.arrow_size[1] - 20),
            "left": (WIDTH // 1.8 - 2.5 * self.arrow_size[0], HEIGHT // 1.05 - self.arrow_size[1] - 20),
            "right": (WIDTH // 1.8 - 0.5 * self.arrow_size[0] + self.arrow_size[0], HEIGHT // 1.05 - self.arrow_size[1] - 20),
        }

    def draw_targets(self):
        """Рисует зоны попадания для стрелок."""
        for direction, position in self.target_positions.items():
            screen.blit(ZONE_IMAGES[direction], position)

    def spawn_arrow(self):
        """Создаёт новую стрелку и добавляет её в список."""
        direction = random.choice(["up", "down", "left", "right"])
        x, y = self.target_positions[direction][0], -self.arrow_size[1]
        self.arrows.append({"type": direction, "pos": [x, y]})

    def draw_arrows(self):
        """Рисует стрелки на экране, изменяя их масштаб при появлении."""
        for arrow in self.arrows:
            if "scale" not in arrow:
                arrow["scale"] = 0.5
            if arrow["scale"] < 1:
                arrow["scale"] += 0.02
                if arrow["scale"] > 1:
                    arrow["scale"] = 1
            scaled_size = (int(self.arrow_size[0] * arrow["scale"]), int(self.arrow_size[1] * arrow["scale"]),)
            scaled_arrow = pygame.transform.scale(ARROW_IMAGES[arrow["type"]], scaled_size)
            offset_x = (scaled_size[0] - self.arrow_size[0]) // 2
            offset_y = (scaled_size[1] - self.arrow_size[1]) // 2
            arrow_rect = pygame.Rect(arrow["pos"][0] - offset_x, arrow["pos"][1] - offset_y, *scaled_size)
            screen.blit(scaled_arrow, arrow_rect.topleft)

    def update_arrows(self, pressed_keys):
        """Обновляет позиции стрелок, проверяет попадания и считает промахи."""
        hits, misses = 0, 0
        for arrow in self.arrows[:]:
            arrow["pos"][1] += self.arrow_speed
            target_y = self.target_positions[arrow["type"]][1]
            if target_y <= arrow["pos"][1] <= target_y + 50:
                if (arrow["type"] == "up" and pressed_keys[pygame.K_UP]) or \
                        (arrow["type"] == "down" and pressed_keys[pygame.K_DOWN]) or \
                        (arrow["type"] == "left" and pressed_keys[pygame.K_LEFT]) or \
                        (arrow["type"] == "right" and pressed_keys[pygame.K_RIGHT]):
                    self.arrows.remove(arrow)
                    hits += 1
                    self.missed_arrows = 0
            if arrow["pos"][1] >= HEIGHT:
                self.arrows.remove(arrow)
                self.missed_arrows += 1
        return hits, self.missed_arrows


class OSUMode:
    def __init__(self):
        """Инициализация объектов для режима OSU Mode."""
        self.circle_size = CIRCLE_SIZE
        self.circle_images = CIRCLE_IMAGES
        self.circle_speed = CIRCLE_SPEED
        self.circles = []
        self.missed_circles = 0
        self.mode_start_time = pygame.time.get_ticks() / 1000
        self.reset()

    def reset(self):
        """Сбрасывает все данные режима OSU Mode."""
        self.circles = []
        self.missed_circles = 0
        self.mode_start_time = pygame.time.get_ticks() / 1000

    def spawn_circle(self):
        """Создаёт новый круг в случайной позиции и добавляет его в список."""
        x = random.randint(self.circle_size, WIDTH - self.circle_size)
        y = random.randint(self.circle_size, HEIGHT - self.circle_size)
        image = random.choice(self.circle_images)
        self.circles.append({
            "pos": [x, y],
            "image": image,
            "spawn_time": pygame.time.get_ticks() / 1000,
            "alpha": 0,
            "clicked": False
        })

    def draw_circles(self):
        """Рисует круги на экране с плавным увеличением прозрачности."""
        for circle in self.circles:
            circle["alpha"] += 255 / (self.circle_speed * FPS)
            if circle["alpha"] > 255:
                circle["alpha"] = 255
            circle_surface = pygame.Surface((self.circle_size * 2, self.circle_size * 2), pygame.SRCALPHA)
            circle_surface.set_alpha(int(circle["alpha"]))
            circle_surface.blit(circle["image"], (0, 0))
            screen.blit(circle_surface, (circle["pos"][0] - self.circle_size, circle["pos"][1] - self.circle_size))

    def handle_click(self, mouse_pos):
        """Обрабатывает нажатие мыши и проверяет попадания по кругам."""
        global score
        for circle in self.circles[:]:
            circle_center = circle["pos"]
            distance = ((mouse_pos[0] - circle_center[0]) ** 2 + (mouse_pos[1] - circle_center[1]) ** 2) ** 0.5
            if distance <= self.circle_size:
                self.circles.remove(circle)
                score += 1

    def update(self):
        """Обновляет состояние кругов и подсчитывает пропущенные."""
        current_time = pygame.time.get_ticks() / 1000
        new_circles = []
        for circle in self.circles:
            if not circle["clicked"] and current_time - circle["spawn_time"] > self.circle_speed:
                self.missed_circles += 1
            else:
                new_circles.append(circle)
        self.circles = new_circles


class WaveMode:
    def __init__(self):
        """Инициализация объектов для режима Wave Mode."""
        self.wave_sprite = AnimatedSprite(
            pygame.image.load("../PurrBeats/data/assets/wave_mode/wave.png"), 6, 2,
            WIDTH // 4, HEIGHT // 2, screen_width=WIDTH, screen_height=HEIGHT
        )
        self.obstacles = []
        self.obstacle_speed = WAVE_SPEED
        self.is_wave_going_up = False
        self.score = 0

    def spawn_obstacle(self):
        """Спавнит препятствие с начальным масштабом 0.5."""
        x = WIDTH
        y = random.randint(0, HEIGHT - OBSTACLE_SIZE)
        image = random.choice(OBSTACLE_IMAGES)
        self.obstacles.append({
            "rect": pygame.Rect(x, y, OBSTACLE_SIZE, OBSTACLE_SIZE),
            "image": image,
            "scale": 0.5
        })

    def update_obstacles(self):
        """Обновляет позицию препятствий и удаляет ушедшие за экран."""
        for obstacle in self.obstacles[:]:
            obstacle["rect"].x -= self.obstacle_speed
            if obstacle["rect"].right < 0:
                self.obstacles.remove(obstacle)

    def check_collision(self):
        """Проверяет столкновение волны с препятствиями."""
        wave_rect = self.wave_sprite.rect
        return any(wave_rect.colliderect(o["rect"]) for o in self.obstacles)

    def update_wave(self):
        """Обновляет позицию волны и анимацию."""
        if self.is_wave_going_up:
            self.wave_sprite.rect.y -= 5
        else:
            self.wave_sprite.rect.y += 5
        self.wave_sprite.rect.y = max(0, min(HEIGHT - self.wave_sprite.rect.height, self.wave_sprite.rect.y))
        self.wave_sprite.update()

    def reset(self):
        """Сбрасывает режим, чтобы избежать багов при переходах."""
        self.obstacles = []
        self.wave_sprite.rect.topleft = (WIDTH // 4, HEIGHT // 2)
        self.score = 0

    def draw_wave(self):
        """Рисует волну с анимацией."""
        screen.blit(self.wave_sprite.image, self.wave_sprite.rect)

    def draw_obstacles(self):
        """Рисует препятствия с плавным увеличением масштаба."""
        for obstacle in self.obstacles:
            obstacle["scale"] = min(1.0, obstacle["scale"] + 0.02)
            scaled_size = tuple(
                int(dim * obstacle["scale"]) for dim in (obstacle["rect"].width, obstacle["rect"].height))
            scaled_image = pygame.transform.scale(obstacle["image"], scaled_size)
            offset_x, offset_y = (scaled_size[0] - obstacle["rect"].width) // 2, (
                        scaled_size[1] - obstacle["rect"].height) // 2
            scaled_rect = obstacle["rect"].move(-offset_x, -offset_y)
            screen.blit(scaled_image, scaled_rect.topleft)

# === Дополнительные функции ===

def switch_mode(current_time, modes):
    """Переключает режим игры в зависимости от времени."""
    global current_mode, mode_start_time
    for mode in modes:
        if mode["start_time"] <= current_time:
            current_mode = mode["mode"]
            mode_start_time = mode["start_time"]
        else:
            break

def show_loading_screen():
    """Загрузочное меню."""
    screen.fill((0, 0, 0))
    text = font.render("Загрузка...", True, (255, 255, 255))
    text_rect = text.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
    screen.blit(text, text_rect)
    pygame.display.flip()
    time.sleep(BOOT_DELAY)

# === Главный цикл игры ===

def open_game(n):
    global score
    background_music = f'data/levels/level{n}/music.mp3'
    with open(f'../PurrBeats/data/levels/level{n}/map.json' , 'r') as file:
        game_data = json.load(file)
    modes = game_data["modes"]
    pygame.mixer.music.load(background_music)
    pygame.display.set_caption(f"Purr Beat: Level {n}")

    while True:
        clock = pygame.time.Clock()
        beat_mode = 0
        start_time = pygame.time.get_ticks()
        show_loading_screen()
        beat_times = game_data["beat_times"]
        pygame.mixer.music.play(0)

        fnf_mode = FNFMode()
        osu_mode = OSUMode()
        osu_mode.reset()
        wave_mode = WaveMode()
        running, levelover = True, False

        while running:
            screen.blit(background_image, (0, 0))
            current_time = (pygame.time.get_ticks() - start_time) / 1000
            events = pygame.event.get()
            pressed_keys = pygame.key.get_pressed()
            mouse_pos = None

            for event in events:
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    score = 0
                    return None, None
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_pos = event.pos
                if current_mode == 3 and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    wave_mode.is_wave_going_up = True
                if current_mode == 3 and event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    wave_mode.is_wave_going_up = False

            switch_mode(current_time, modes)

            # Обработка режимов

            if current_mode == 1:  # FNF Mode
                if beat_mode < len(beat_times) and current_time >= beat_times[beat_mode]:
                    fnf_mode.spawn_arrow()
                    beat_mode += 1
                if fnf_mode.missed_arrows >= 5:
                    pygame.mixer.music.pause()
                    username, score, again = gameover.main_menu('lose', score)
                    levelover = True
                    if again:
                        score = 0
                        running = False
                    else:
                        out_score = score
                        score = 0
                        return username, out_score
                score += fnf_mode.update_arrows(pressed_keys)[0]
                fnf_mode.draw_arrows()
                fnf_mode.draw_targets()
            elif current_mode == 2:  # OSU Mode
                if beat_mode < len(beat_times) and current_time >= beat_times[beat_mode]:
                    osu_mode.spawn_circle()
                    beat_mode += 1
                if mouse_pos:
                    osu_mode.handle_click(mouse_pos)
                osu_mode.update()
                if osu_mode.missed_circles >= 10:
                    pygame.mixer.music.pause()
                    username, score, again = gameover.main_menu('lose', score)
                    levelover = True
                    if again:
                        score = 0
                        running = False
                    else:
                        out_score = score
                        score = 0
                        return username, out_score
                osu_mode.draw_circles()
            elif current_mode == 3:  # Wave Mode
                wave_mode.update_wave()
                if beat_mode < len(beat_times) and current_time >= beat_times[beat_mode]:
                    wave_mode.spawn_obstacle()
                    beat_mode += 1
                wave_mode.update_obstacles()
                if wave_mode.check_collision():
                    pygame.mixer.music.pause()
                    username, score, again = gameover.main_menu('lose', score)
                    levelover = True
                    if again:
                        score = 0
                        running = False
                    else:
                        out_score = score
                        score = 0
                        return username, out_score
                wave_mode.draw_wave()
                wave_mode.draw_obstacles()
                score += 1 / FPS
            score_text = font.render(f"Счет: {int(score)}", True, 'WHITE')
            screen.blit(score_text, (10, 10))
            if not pygame.mixer.music.get_busy() and not levelover:
                username, score, again = gameover.main_menu('win', score)
                if again:
                    score = 0
                    running = False
                else:
                    out_score = score
                    score = 0
                    return username, out_score
            pygame.display.update()
            clock.tick(FPS)
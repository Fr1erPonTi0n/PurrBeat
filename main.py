from classes import Buttons, VolumeSlider, TextBox, ResolutionManager, LeaderBoard
from game import open_game
import pygame, configparser, sys

# === Инициализация Pygame ===

pygame.mixer.pre_init(frequency=44100, size =- 16, channels=2, buffer=512, devicename=None)
pygame.init()
pygame.font.init()
pygame.mixer.init()

# === Загрузка конфигурации ===

config = configparser.ConfigParser()
config.read('config.ini')

# === Получение значений из конфигурации ===

WIDTH = int(config['General']['WIDTH'])
HEIGHT = int(config['General']['HEIGHT'])
FPS = int(config['General']['FPS'])
VOLUME = float(config['General']['VOLUME'])

DEFAULT_FONT = config['Fonts']['DEFAULT_FONT']
DEFAULT_SIZE_TEXT = int(config['Fonts']['DEFAULT_SIZE_TEXT'])

ICON_APP = config['Icons']['ICON_APP']

BACKGROUND_IMAGE = config['Background']['BACKGROUND_IMAGE']
BACKGROUND_MUSIC = config['Background']['BACKGROUND_MUSIC']

# === Настройки кнопок ===

BACKGROUND_COLOR = tuple(map(int, config['Colors']['BACKGROUND_COLOR'].split(',')))
BUTTON_COLOR = tuple(map(int, config['Colors']['BUTTON_COLOR'].split(',')))
BUTTON_HOVER_COLOR = tuple(map(int, config['Colors']['BUTTON_HOVER_COLOR'].split(',')))

MENU_BUTTON_WIDTH = WIDTH / 2.7
MENU_BUTTON_HEIGHT = HEIGHT / 12
MENU_BUTTON_SPACING = MENU_BUTTON_WIDTH / 4
SETTINGS_BUTTON_WIDTH = WIDTH / 2.7
SETTINGS_BUTTON_HEIGHT = HEIGHT / 12
LEADERS_BUTTON_WIDTH = WIDTH / 8
LEADERS_BUTTON_HEIGHT = HEIGHT / 12
SETTINGS_BUTTON_SPACING = SETTINGS_BUTTON_WIDTH / 4

HOVER_OFFSET = int(config['Buttons']['HOVER_OFFSET'])
BUTTON_TYPE_MOVABLE = int(config['Buttons']['BUTTON_TYPE_MOVABLE'])
BUTTON_TYPE_HIGHLIGHT = int(config['Buttons']['BUTTON_TYPE_HIGHLIGHT'])

# === Создание окна ===

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Purr Beat")

# === Загрузка иконки приложения ===

icon = pygame.image.load(ICON_APP)
pygame.display.set_icon(icon)

# === Загрузка фона ===

background_image = pygame.image.load(BACKGROUND_IMAGE)
background_image = pygame.transform.scale(background_image, (WIDTH, HEIGHT))

# === Загрузка и воспроизведение фоновой музыки ===

pygame.mixer.music.load(BACKGROUND_MUSIC)
pygame.mixer.music.set_volume(VOLUME)
pygame.mixer.music.play(-1)

# === Переменные ===

setting_menu = 0
resolution_manager = ResolutionManager()
game_manager = None

# === Классы менюшек ===


class MenuManager:
    def __init__(self):
        """Создает два набора кнопок: основные кнопки меню и кнопки меню настроек."""
        self.menu_buttons = [
            Buttons("Играть", WIDTH / 1.5, HEIGHT / 2 - (HEIGHT / 10), WIDTH / 2.7, HEIGHT / 12, play_game, BUTTON_TYPE_MOVABLE),
            Buttons("Настройки", WIDTH / 1.5, HEIGHT / 2, WIDTH / 2.7, HEIGHT / 12, open_settings, BUTTON_TYPE_MOVABLE),
            Buttons("Выход", WIDTH / 1.5, HEIGHT / 2 + (HEIGHT / 10), WIDTH / 2.7, HEIGHT / 12, exit_game, BUTTON_TYPE_MOVABLE)
        ]
        self.settings_buttons = [
            Buttons("Назад", WIDTH / 3.1, HEIGHT / 1.5, WIDTH / 2.7, HEIGHT / 12, close_settings, BUTTON_TYPE_HIGHLIGHT),
            VolumeSlider(WIDTH / 3.05, HEIGHT / 2, WIDTH / 2.8, 20, 0, 1, VOLUME),
            TextBox("Громкость звука", WIDTH / 1.96, HEIGHT / 2.4, DEFAULT_FONT, 36, BUTTON_COLOR, width=WIDTH / 2.85, height=HEIGHT / 10),
            Buttons("Изменить разрешение", WIDTH / 3.7, HEIGHT / 4.2, WIDTH / 2.7 * 1.3, HEIGHT / 12, change_resolution, BUTTON_TYPE_HIGHLIGHT)
        ]

    def get_buttons(self, menu_type):
        """Возвращает кнопки для заданного типа меню ("main" или "settings")."""
        return self.menu_buttons if menu_type == "main" else self.settings_buttons


class GameManager:
    def __init__(self):
        """Инициализирует начальные данные игры, включая прокрутку и уровни."""
        self.scroll_offset = 0
        self.scroll_speed = 20
        self.game_levels = self.generate_level_buttons()
        self.leaderboard_visible = False
        self.current_level = None

    def generate_level_buttons(self):
        """Создает кнопки для уровней и таблицы лидеров."""
        buttons = []
        for i in range(1, 2):
            buttons.append(Buttons(f"Уровень {i}", WIDTH / 4, HEIGHT / 9 + (i - 1) * int(100 * min(WIDTH / 1280, HEIGHT / 720)),
                                   WIDTH / 2.7, HEIGHT / 12, lambda level=i: self.start_level(level), BUTTON_TYPE_HIGHLIGHT))
            buttons.append(Buttons(f"Лидеры", WIDTH / 1.6, HEIGHT / 9 + (i - 1) * int(100 * min(WIDTH / 1280, HEIGHT / 720)),
                                   WIDTH / 8, HEIGHT / 12, lambda level=i: self.show_leaders(level), BUTTON_TYPE_HIGHLIGHT, 24))
        buttons.append(Buttons("Назад", WIDTH / 3.1, HEIGHT / 1.4 + len(buttons) * int(10 * min(WIDTH / 1280, HEIGHT / 720)),
                               WIDTH / 2.7, HEIGHT / 12, close_settings, BUTTON_TYPE_HIGHLIGHT))
        return buttons

    def start_level(self, level):
        """Запускает выбранный уровень и обновляет таблицу лидеров."""
        username, score = open_game(level)
        if username and score:
            LeaderBoard().add_leader(username, int(score), level)
        pygame.display.set_caption("Purr Beat")
        pygame.mixer.music.load(BACKGROUND_MUSIC)
        pygame.mixer.music.play(-1)

    def show_leaders(self, level):
        """Отображает таблицу лидеров для выбранного уровня."""
        self.leaderboard_visible = True
        self.current_level = level
        global game_levels
        game_levels = self.get_visible_buttons()

    def get_visible_buttons(self):
        """Возвращает кнопки, которые должны быть видимы на текущем экране."""
        if self.leaderboard_visible:
            return self.generate_leaderboard_buttons()
        return [b for b in self.game_levels if -100 < b.rect.y - self.scroll_offset < HEIGHT + 100]

    def generate_leaderboard_buttons(self):
        """Создает кнопки и текстовые блоки для отображения таблицы лидеров."""
        buttons = []
        leaders = LeaderBoard().list_leaders(self.current_level)
        y_offset = HEIGHT / 4
        for index, (username, score) in enumerate(leaders):
            buttons.append(TextBox(f"{index + 1}. {username} - {score}",
                                   WIDTH / 2, y_offset + index * 50,
                                   DEFAULT_FONT, 36, BUTTON_COLOR,
                                   width=WIDTH / 2.5, height=HEIGHT / 15))
        buttons.append(Buttons("Назад", WIDTH / 3.1, y_offset + len(leaders) * 50 + 20,
                               WIDTH / 2.7, HEIGHT / 12, self.close_leaderboard, BUTTON_TYPE_HIGHLIGHT))
        return buttons

    def close_leaderboard(self):
        """Закрывает таблицу лидеров и возвращает видимые кнопки уровней."""
        self.leaderboard_visible = False
        self.current_level = None
        global game_levels
        game_levels = self.get_visible_buttons()


# === Дополнительные функции ===

def play_game():
    """Открывает список уровней."""
    global setting_menu, game_levels
    setting_menu = 2
    game_manager = GameManager()
    game_levels = game_manager.get_visible_buttons()

def open_settings():
    """Открывает меню настроек."""
    global setting_menu
    setting_menu = 1

def close_settings():
    """Закрывает меню настроек и возвращает главное меню."""
    global setting_menu
    setting_menu = 0

def exit_game():
    """Завершает выполнение программы."""
    pygame.quit()
    sys.exit()

def change_resolution():
    """Меняет разрешение экрана и обновляет интерфейс."""
    global WIDTH, HEIGHT, menu_buttons, settings_buttons, game_levels, background_image
    WIDTH, HEIGHT = resolution_manager.next_resolution()
    pygame.display.set_mode((WIDTH, HEIGHT))
    background_image = pygame.transform.scale(pygame.image.load(BACKGROUND_IMAGE), (WIDTH, HEIGHT))
    menu_buttons = MenuManager().get_buttons('main')
    settings_buttons = MenuManager().get_buttons('settings')
    if game_manager:
        game_levels = game_manager.get_visible_buttons()
    config['General']['WIDTH'] = str(WIDTH)
    config['General']['HEIGHT'] = str(HEIGHT)
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

# === Главный цикл игры ===

def main():
    global menu_buttons, settings_buttons, game_levels
    clock = pygame.time.Clock()
    running = True

    menu_manager = MenuManager()
    menu_buttons = menu_manager.get_buttons('main')
    settings_buttons = menu_manager.get_buttons('settings')

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if setting_menu == 0:
                    for button in menu_buttons:
                        if button.rect.collidepoint(mouse_pos):
                            button.click()
                elif setting_menu == 1:
                    for button in settings_buttons:
                        if isinstance(button, Buttons) and button.rect.collidepoint(mouse_pos):
                            button.click()
                elif setting_menu == 2:
                    for button in game_levels:
                        if isinstance(button, Buttons) and button.rect.collidepoint(mouse_pos):
                            button.click()

        if setting_menu == 2 and game_manager:
            game_levels = game_manager.get_visible_buttons()
        screen.blit(background_image, (0, 0))
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        if setting_menu == 0:
            for button in menu_buttons:
                button.update(mouse_pos)
                button.draw(screen)
        elif setting_menu == 1:
            for button in settings_buttons:
                if isinstance(button, VolumeSlider):
                    button.update(mouse_pos, mouse_pressed)
                    button.draw(screen)
                elif isinstance(button, TextBox):
                    button.draw(screen)
                else:
                    button.update(mouse_pos)
                    button.draw(screen)
        elif setting_menu == 2:
            for button in game_levels:
                if isinstance(button, TextBox):
                    button.draw(screen)
                else:
                    button.update(mouse_pos)
                    button.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
import pygame, configparser
from classes import Buttons, TextBox

# === Инициализация Pygame ===

pygame.init()

# === Загрузка конфигурации ===

config = configparser.ConfigParser()
config.read('config.ini')

# === Параметры из конфигурации ===

WIDTH, HEIGHT = int(config['General']['WIDTH']), int(config['General']['HEIGHT'])
FPS = int(config['General']['FPS'])
DEFAULT_FONT = config['Fonts']['DEFAULT_FONT']
DEFAULT_SIZE_TEXT = int(config['Fonts']['DEFAULT_SIZE_TEXT'])
BACKGROUND_IMAGE = pygame.image.load(config['Background']['BACKGROUND_IMAGE_OVER'])
BACKGROUND_IMAGE = pygame.transform.scale(BACKGROUND_IMAGE, (WIDTH, HEIGHT))
BUTTON_COLOR = tuple(map(int, config['Colors']['BUTTON_COLOR'].split(',')))
BUTTON_TYPE_HIGHLIGHT = int(config['Buttons']['BUTTON_TYPE_HIGHLIGHT'])

# === Создание окна ===

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_icon(pygame.image.load(config['Icons']['ICON_APP']))

# === Функции обработки ===

def create_buttons(text, y_offset, callback):
    """Функция создаёт объект кнопки на основе переданных параметров."""
    return Buttons(text, WIDTH / 3.2, HEIGHT / 2 + y_offset, WIDTH / 2.7, HEIGHT / 12, callback, BUTTON_TYPE_HIGHLIGHT)

def draw_buttons(buttons, mouse_pos):
    """функция отрисовывает все кнопки на экране и обновляет их состояние, если они не являются текстовыми."""
    for button in buttons:
        if isinstance(button, TextBox):
            button.draw(screen)
        else:
            button.update(mouse_pos)
            button.draw(screen)

# === Основное меню ===

def main_menu(menu_type, score=0):
    clock = pygame.time.Clock()
    running = True

    if menu_type == "lose":
        buttons = [
            TextBox("Вы проиграли!", WIDTH / 2, HEIGHT / 2.4, DEFAULT_FONT, 36, BUTTON_COLOR),
            create_buttons("Заново", 0, None),
            create_buttons("Выход", 60 * (HEIGHT / 600), None)
        ]
    elif menu_type == "win":
        buttons = [
            TextBox("Вы выиграли!", WIDTH / 2, HEIGHT / 2.4, DEFAULT_FONT, 36, BUTTON_COLOR),
            create_buttons("Заново", 0, None),
            create_buttons("Выход", 60 * (HEIGHT / 600), None)
        ]

    input_active = False
    input_box = pygame.Rect(WIDTH / 3, HEIGHT / 2, WIDTH / 3, 50)
    color_inactive = pygame.Color('gray')
    color_active = pygame.Color('white')
    color = color_inactive
    username = ""

    while running:
        screen.blit(BACKGROUND_IMAGE, (0, 0))
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return None, None, False

            if input_active:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                        running = False
                        return username, score, False
                    elif event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                    elif len(username) < 12:
                        username += event.unicode

            if not input_active and event.type == pygame.MOUSEBUTTONDOWN:
                for button in buttons:
                    if isinstance(button, Buttons) and button.rect.collidepoint(mouse_pos):
                        if button.text == "Выход":
                            input_active = True
                            color = color_active
                        elif button.text == "Заново":
                            running = False
                            return None, None, True

        if input_active:
            pygame.draw.rect(screen, color, input_box, 2)
            font = pygame.font.Font(DEFAULT_FONT, DEFAULT_SIZE_TEXT)
            txt_surface = font.render(username, True, pygame.Color('white'))
            screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
            input_box.w = max(WIDTH // 3, txt_surface.get_width() + 10)
            prompt_surface = font.render("Введите ваше имя:", True, pygame.Color('white'))
            screen.blit(prompt_surface, (WIDTH / 2 - prompt_surface.get_width() / 2, HEIGHT / 2 - 100))
        else:
            draw_buttons(buttons, mouse_pos)

        pygame.display.flip()
        clock.tick(FPS)
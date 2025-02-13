import configparser, librosa, json, random

"""Анализирует аудиофайл и создает JSON с ритмом и игровыми режимами.
   - file_path: путь к аудиофайлу.
   - output_file: имя выходного JSON файла.
   - beat_chance: вероятность включения временной метки (от 0 до 1). None — без фильтрации."""

config = configparser.ConfigParser()
config.read('config.ini')
boot_delay = int(config['Game']['boot_delay'])

def analyze_audio_with_modes(file_path, output_file="game_modes.json", beat_chance=None):
    y, sr = librosa.load(file_path, sr=None)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    if beat_chance is not None:
        filtered_beat_times = [time for time in beat_times if random.random() <= beat_chance]
    else:
        filtered_beat_times = beat_times
    min_mode_duration = 20
    total_duration = librosa.get_duration(y=y, sr=sr)
    modes = []
    current_time = 0
    while current_time < total_duration:
        mode = random.randint(1, 3)
        next_time = current_time + min_mode_duration
        if next_time > total_duration:
            next_time = total_duration
        modes.append({"mode": mode, "start_time": current_time})
        current_time = next_time
    game_data = {
        "tempo": float(tempo),
        "beat_times": [float(time) + boot_delay for time in filtered_beat_times],
        "modes": modes
    }

    with open(output_file, "w") as f:
        json.dump(game_data, f, indent=4)

    print(f"Темп: {tempo} BPM")
    print(f"Данные сохранены в файл: {output_file}")


if __name__ == "__main__":
    file_path = input('Введите путь к вашей музыки:\n')
    output_file = input('Введите путь сохранения:\n')
    analyze_audio_with_modes(file_path, output_file)

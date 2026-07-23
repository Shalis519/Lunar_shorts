import json
import asyncio
import os
from datetime import datetime
from moviepy.editor import *
import edge_tts

# === НАСТРОЙКИ ===
DATA_PATH = "/data/lunar-shorts/data/mansions.json"
ASSETS_PATH = "/data/lunar-shorts/assets"
OUTPUT_PATH = "/data/lunar-shorts/output"

os.makedirs(OUTPUT_PATH, exist_ok=True)

# === ЗАГРУЗКА ДАННЫХ ===
with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

mansions = data["mansions"]

# === ОПРЕДЕЛЕНИЕ ТЕКУЩЕГО ДОМА ===
# Простой цикл: день года % 28 = номер Дома
day_of_year = datetime.now().timetuple().tm_yday
mansion_index = (day_of_year - 1) % 28

# Если в JSON меньше 28, пока используем 7
mansion = mansions[mansion_index % len(mansions)]

print(f"Сегодня: Дом {mansion['number']} — {mansion['name']}")

# === ГЕНЕРАЦИЯ ТЕКСТА ===
script_text = f"""
Доброе утро. Сегодня Луна в Доме номер {mansion['number']} — {mansion['name']}, {mansion['translation']}.
Границы: от {mansion['start']} до {mansion['end']}.
{mansion['nature']}
Что делать: {', '.join(mansion['do'])}.
Чего избегать: {', '.join(mansion['avoid'])}.
Талисман: {mansion['talisman']}. Владыка Дома — {mansion['lord']}.
Подписывайтесь, завтра следующий Дом.
"""

print(f"Текст: {script_text}")

# === ОЗВУЧКА (Edge TTS) ===
async def generate_voice(text, output_path):
    communicate = edge_tts.Communicate(text, voice="ru-RU-SvetlanaNeural")
    await communicate.save(output_path)

audio_path = os.path.join(OUTPUT_PATH, "voice.mp3")
asyncio.run(generate_voice(script_text, audio_path))
print(f"Аудио сохранено: {audio_path}")

# === ВИДЕО ===
image_path = os.path.join(ASSETS_PATH, "images", mansion["image"])

# Если картинки нет — создаём заглушку
if not os.path.exists(image_path):
    print(f"Картинка не найдена: {image_path}")
    # Создаём чёрную заглушку
    from PIL import Image
    img = Image.new('RGB', (1080, 1920), color='black')
    image_path = os.path.join(OUTPUT_PATH, "fallback.png")
    img.save(image_path)

# Загружаем аудио для определения длительности
audio = AudioFileClip(audio_path)
duration = min(audio.duration, 58)  # максимум 58 сек

# Картинка с медленным зумом
clip = ImageClip(image_path, duration=duration)

# Медленный зум: от 100% до 110% за время видео
def zoom(t):
    return 1 + 0.1 * (t / duration)

clip = clip.resize(zoom)

# Титул в начале (первые 3 секунды)
title_text = f"ДОМА ЛУНЫ\nДом {mansion['number']} — {mansion['name']}"
title = TextClip(
    title_text,
    fontsize=60,
    color='white',
    font='Arial-Bold',
    stroke_color='black',
    stroke_width=2,
    method='caption',
    size=(1000, None),
    align='center'
)
title = title.set_position('center').set_duration(3).fadein(0.5).fadeout(0.5)

# Финальный текст (последние 3 секунды)
end_text = "Подпишись\nЗавтра следующий Дом"
end = TextClip(
    end_text,
    fontsize=50,
    color='gold',
    font='Arial-Bold',
    stroke_color='black',
    stroke_width=2,
    method='caption',
    size=(1000, None),
    align='center'
)
end = end.set_position('center').set_start(duration - 3).set_duration(3).fadein(0.5)

# Собираем
final = CompositeVideoClip([clip, title, end])
final = final.set_audio(audio.subclip(0, duration))

# Рендер
output_video = os.path.join(OUTPUT_PATH, f"mansion_{mansion['number']:02d}.mp4")
final.write_videofile(
    output_video,
    fps=12,
    codec='libx264',
    audio_codec='aac',
    preset='ultrafast',
    threads=2
)

print(f"Видео готово: {output_video}")
print(f"Размер: {os.path.getsize(output_video) / 1024 / 1024:.1f} MB")
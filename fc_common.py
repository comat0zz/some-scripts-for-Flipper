from hashlib import sha256
from os import walk, path, stat
from json import dumps as json_dumps
from collections import Counter
from tinydb import TinyDB, Query

FLIPPER_EXTENSIONS = [
  '.sub',
  '.rfid',
  '.txt',
  '.ibtn',
  '.nfc',
  '.ir'
]

SKIP_FW_APPS = [
    "apps",
    "apps_data",
    "dolphin",
    "ibtnfuzzer",
    "Manifest",
    "music_player",
    "rfidfuzzer",
    "subplaylist",
    "swd_scripts",
    "u2f"
]

def get_file_hash(file_path):
  """Вычисляет SHA-256 хеш файла, читая его по частям."""
  sha256_hash = sha256()
  
  try:
    with open(file_path, "rb") as f:
    # Читаем файл блоками по 4 КБ, чтобы не перегружать RAM
      for byte_block in iter(lambda: f.read(4096), b""):
        sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
  except FileNotFoundError:
    return None


def scan_directory(root_path):
  """Рекурсивно обходит каталог через os.scandir."""
  files_to_process = []
      
  for root, dirs, files in walk(root_path):
    for name in files:
      full_path = path.join(root, name)
      try:
        name, ext = path.splitext(full_path)
        if ext in FLIPPER_EXTENSIONS:
          files_to_process.append({
            'fp': full_path,
            'ext': ext
            })
        else:
          print(f'Неизвестный формат файла: {full_path}')
      except OSError:
        continue
  return files_to_process

def dict_to_sha256(data_dict):
    encoded_dict = json_dumps(
        data_dict, 
        sort_keys=True, 
        separators=(',', ':')
    ).encode('utf-8')
    
    return sha256(encoded_dict).hexdigest()


def find_duplicates(db, field_name):
    all_records = db.all()
    
    # Извлекаем все значения нужного поля (пропуская записи, где поля нет)
    values = [doc.get(field_name) for doc in all_records if field_name in doc]
    
    # Подсчитываем количество вхождений каждого значения
    counts = Counter(values)
    
    # Находим значения, которые встречаются больше одного раза
    duplicate_values = {val for val, count in counts.items() if count > 1}
    
    # Собираем все записи, у которых значение поля входит в список дубликатов
    duplicates = [doc for doc in all_records if doc.get(field_name) in duplicate_values]
    
    return duplicates

def random_string():
  from time import time
  return str(int(time()))

def get_sorted_unique_values(db, target_keys = []):
  unique_values = list({
    doc[k] for doc in db.all() for k in target_keys if k in doc
  })
  return sorted(list(unique_values))
from argparse import ArgumentParser
from fc_common import scan_directory, dict_to_sha256, find_duplicates
from os import path as os_path
from tinydb import TinyDB, Query

db = TinyDB('db_rfid.json')
db_row = Query()

HEADER_IBTN = "Flipper RFID key"

def validator_rfid(rfid):
  return True

def parser_rfid(file_path):
  
  rfid = {}

  with open(file_path, "r") as f:
    ibtn_a = f.read().split("\n")
    
    for line in ibtn_a:
      line = line.strip()

      if line == '':
        continue

      if line[0] == '#':
        continue

      tmp = line.split(":")
      header = tmp[0].strip()
      payload = tmp[1].strip()

      if header == 'Filetype':
        if payload != HEADER_IBTN:
          print(f"Некорректный заголовок файла:\n{file_path}\n{payload}")
          return {}
        else:
          continue

      rfid[header] = payload

  rfid['hash'] = dict_to_sha256(rfid)

  return rfid

def enum_files(paths):
  for file in paths:
    name, ext = os_path.splitext(file['fp'])
    if ext not in ['.rfid']:
      continue

    rfid = parser_rfid(file['fp'])

    if db.search(db_row.hash == rfid['hash']):
      print(f"Такой сигнал уже существует!")
      print(file['fp'])
      continue

    if validator_rfid(rfid):
      db.insert(rfid) 
    else:
      print("Какие то проблемы, к разбору:")
      print(rfid)


parser = ArgumentParser()
parser.add_argument('--target', required=True, help='Директория с файлами RFID')
args = parser.parse_args()

if args.target:
  files = scan_directory(args.target)
  enum_files(files)
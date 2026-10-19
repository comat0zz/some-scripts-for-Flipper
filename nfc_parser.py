from argparse import ArgumentParser
from fc_common import scan_directory, dict_to_sha256, find_duplicates
from os import path as os_path
from tinydb import TinyDB, Query

HEADER_IBTN = "Flipper NFC device"

db = TinyDB('db_nfc.json')
db_row = Query()


def validator_nfc(nfc):
  return True

def parser_nfc(file_path):
  
  nfc = {}

  with open(file_path, "r") as f:
    nfc_a = f.read().split("\n")
    
    for line in nfc_a:
      line = line.strip()

      if line == '':
        continue

      if line[0] == '#':
        continue

      tmp = line.split(":")
      header = tmp[0].strip()
      try:
        payload = tmp[1].strip()
      except:
        continue

      if header == 'Filetype':
        if payload != HEADER_IBTN:
          #print(f"Некорректный заголовок файла:\n{file_path}\n{payload}")
          return {}
        else:
          continue

      nfc[header] = payload

  nfc['hash'] = dict_to_sha256(nfc)

  return nfc

def enum_files(paths, root):
  for file in paths:
    name, ext = os_path.splitext(file['fp'])
    if ext not in ['.nfc']:
      continue

    nfc = parser_nfc(file['fp'])
    if nfc == {}:
      continue

    name = name.replace(root, '')
    nfc['filename'] = name

    if 'hash' not in nfc:
      continue
    
    if db.search(db_row.hash == nfc['hash']):
      #print(f"Такой сигнал уже существует!")
      #print(file['fp'])
      continue

    if validator_nfc(nfc):
      print(f"Filename: {name}")
      db.insert(nfc) 
    else:
      print("Какие то проблемы, к разбору:")
      print(nfc)


parser = ArgumentParser()
parser.add_argument('--target', required=True, help='Директория с файлами NFC')
args = parser.parse_args()

if args.target:
  files = scan_directory(args.target)
  enum_files(files, args.target)
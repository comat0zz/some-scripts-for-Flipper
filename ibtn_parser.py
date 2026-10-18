from argparse import ArgumentParser
from fc_common import scan_directory, dict_to_sha256, find_duplicates
from os import path as os_path
from tinydb import TinyDB, Query

db = TinyDB('db_ibtn.json')
db_row = Query()

HEADER_IBTN = "Flipper iButton key"

"""
Format fields
https://developer.flipper.net/flipperzero/doxygen/ibutton_file_format.html

Name          | Type    | Description
protocols     | string  | Currently supported: DS1990, DS1992, DS1996, DS1971, DSGeneric*, Cyfral, Metakom
Rom Data      | hex     | Read-only memory data (Dallas protocols only)
Sram Data     | hex     | Static RAM data (DS1992 and DS1996 only)
Eeprom Data   | hex     | EEPROM data (DS1971 only)
Data          | hex     | Key data (Cyfral & Metakom only)
"""

def parser_ibutton(file_path):
  
  ibtn = {}

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

      ibtn[header] = payload

  '''
    Это писалось в самом конце, потому дальше по тексту может быть проверки на key type
    но толку от них особо никакого, хотя, допускаю встречи еще каких-то протоколов
    я оставляю тут вариант для маневрка - жестко не всем забиваю на второй, т.к. 
    может быть еще какой-либо вариант с Dallas
  '''
  if ibtn['Version'] == '1':
    if ibtn['Key type'] in ['Cyfral', 'Metakom', 'DS1990', 'DS1420', 'Dallas']:
      
      if ibtn['Key type'] in ['Cyfral', 'Metakom']:
        ibtn['Version'] = '2'
        ibtn['Protocol'] = ibtn['Key type']
        del ibtn['Key type']
  
      elif ibtn['Key type'] in ['DS1990', 'DS1420', 'Dallas']:
        data = ibtn['Data'].split(" ")
        key = data[0]
        if key == '01':
          ibtn['Version'] = '2'
          ibtn['Protocol'] = 'DS1990'
          ibtn['Rom Data'] = ibtn['Data']
          del ibtn['Data']
          del ibtn['Key type']
        if key == '81':
          ibtn['Protocol'] = 'DS1420'
          ibtn['Rom Data'] = ibtn['Data']
          ibtn['Version'] = '2'
          del ibtn['Key type']
          del ibtn['Data']

  ibtn['hash'] = dict_to_sha256(ibtn)

  return ibtn

def validator_ibutton(iButton):
  ''' Минимальная проверка от всяких битых и неправильно записанных ключей. Они, в любом случае, не сработают '''
  # TODO: расчет CRC для Dallas ключей, хз насколько актуально, ибо минималки хватает
  
  version = iButton['Version']
  
  data = ''
  if 'Data' in iButton: 
    data = iButton['Data'].strip().split(" ")

  if version == '1' and "Key type" in iButton:
    key_type = iButton["Key type"]
    if key_type not in ['Cyfral', 'Dallas', 'Metakom']:
      return False
    
    if key_type == 'Cyfral':
      if len(data) == 2:
        return True
      else:
        print(f"Некорректный пайлоад Cyfral: len({iButton['Data']}) bytes != 2")
        return False

    if key_type == 'Metakom':
      if len(data) == 4:
        return True
      else:
        print(f"Некорректный пайлоад Metakom: len({iButton['Data']}) bytes != 4")
        return False

    if key_type == 'Dallas':
      if len(data) == 8:
        return True
      else:
        print(f"Некорректный пайлоад Dallas: len({iButton['Data']}) bytes != 8")
        return False

  elif version == '2' and "Protocol" in iButton:
    protocol = iButton['Protocol']
    if protocol not in ['DS1990', 'DS1992', 'DS1996', 'DS1971', 'DS1420', 'DSGeneric', 'Cyfral', 'Metakom']:
      return False

    if protocol == 'Cyfral':
      if len(data) == 2:
        return True
      else:
        print(f"Некорректный пайлоад Cyfral: len({iButton['Data']}) bytes != 2")
        return False

    if protocol == 'Metakom':
      if len(data) == 4:
        return True
      else:
        print(f"Некорректный пайлоад Metakom: len({iButton['Data']}) bytes != 4")
        return False

    if protocol in ['DS1990', 'DS1992', 'DS1996', 'DS1971', 'DS1420', 'DSGeneric']:
      if 'Rom Data' not in iButton:
        return False

      if protocol == 'DS1971':
        if 'Eeprom Data' not in iButton:
          return False
        eeprom = iButton['Eeprom Data'].strip().split(" ")
        if len(eeprom) != 32:
          return False
        if len(data) > 0 and data[0] != '14':
          return False

      if protocol == 'DS1990':
        if len(data) > 0 and data[0] != '01':
          return False

      if protocol == 'DS1420':
        if len(data) > 0 and data[0] != '81':
          return False

      if protocol == 'DS1992':
        if len(data) > 0 and data[0] != '02':
          return False
        if 'Sram Data' not in iButton:
          return False

      if protocol == 'DS1996':
        if len(data) > 0 and data[0] != '04':
          return False
        if 'Sram Data' not in iButton:
          return False

    return True
  else:
    return False

def enum_files(paths):
  for file in paths:
    name, ext = os_path.splitext(file['fp'])
    if ext not in ['.ibtn']:
      continue

    iButton = parser_ibutton(file['fp'])

    if db.search(db_row.hash == iButton['hash']):
      print(f"Такой сигнал уже существует!")
      print(file['fp'])
      continue

    if validator_ibutton(iButton):
      db.insert(iButton) 
    else:
      print("Какие то проблемы, к разбору:")
      print(iButton)


parser = ArgumentParser()
parser.add_argument('--target', required=True, help='Директория с файлами iButton')
args = parser.parse_args()

if args.target:
  files = scan_directory(args.target)
  enum_files(files)

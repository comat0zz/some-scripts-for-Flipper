from tinydb import TinyDB, Query
from argparse import ArgumentParser, BooleanOptionalAction
from pathlib import Path
from fc_common import random_string, get_sorted_unique_values
from shutil import rmtree


db = TinyDB('db_ibtn.json')
db_row = Query()


def create_subdir(root):
  dirs = get_sorted_unique_values(db, ['Key type', 'Protocol'])
  
  for d in dirs:
    dc = Path(f"{root}/{d}")
    dc.mkdir(parents=True, exist_ok=True)

def dump(dump_path):
  all_records = db.all()

  # Умеет только три варианта
  ibtnfuzzer = {
    'DS1990': [],
    'Metakom': [],
    'Cyfral': []
  }

  index = 0

  for record in all_records:
    index += 1
    data_fuzz = False
    body = "Filetype: Flipper iButton key"

    version = record['Version']
    body += f"\nVersion: {version}"
    if version == '1':
      protocol = record['Key type']
      body += f"\nKey type: {protocol}"
    elif version == '2':
      protocol = record['Protocol']
      body += f"\nProtocol: {protocol}"
    else:
      # Третьего тут не дано, но оставлю заглушкой
      continue

    if 'Data' in record:
      data_fuzz = record['Data']
      body += f"\nData: {record['Data']}"
    if 'Rom Data' in record:
      data_fuzz = record['Rom Data']
      body += f"\nRom Data: {record['Rom Data']}"

    if protocol == 'DS1971':
      body += f"\nEeprom Data: {record['Eeprom Data']}"

    if protocol in ['DS1992', 'DS1996']:
      body += f"\nSram Data: {record['Sram Data']}"

    if protocol in ['DS1990', 'Dallas']  and data_fuzz:
      ibtnfuzzer['DS1990'].append(data_fuzz.replace(' ', ''))

    if protocol == 'Metakom' and data_fuzz:
      ibtnfuzzer['Metakom'].append(data_fuzz.replace(' ', ''))

    if protocol == 'Cyfral' and data_fuzz:
      ibtnfuzzer['Cyfral'].append(data_fuzz.replace(' ', ''))

    # хз какие имена, пусть будут цифры
    filename = f"{dump_path}/{protocol}/{index}.ibtn"
    with open(filename, "w") as f:
      f.write(body)
      f.close()

  if len(ibtnfuzzer['DS1990']) > 0:
    filename = f"{dump_path}/ibtnfuzzer_DS1990.txt"
    with open(filename, "w") as f:
      f.write("\n".join(ibtnfuzzer['DS1990']))
      f.write("\n")

  if len(ibtnfuzzer['Metakom']) > 0:
    filename = f"{dump_path}/ibtnfuzzer_Metakom.txt"
    with open(filename, "w") as f:
      f.write("\n".join(ibtnfuzzer['Metakom']))
      f.write("\n") 

  if len(ibtnfuzzer['Cyfral']) > 0:
    filename = f"{dump_path}/ibtnfuzzer_Cyfral.txt"
    with open(filename, "w") as f:
      f.write("\n".join(ibtnfuzzer['Cyfral']))
      f.write("\n") 

parser = ArgumentParser()
parser.add_argument('--dump_to', help='Директория, куда складывать выгрузку')
parser.add_argument('--remove', help='Удалять предыдущую директорию?', default=False, action=BooleanOptionalAction)
args = parser.parse_args()

if args.dump_to:
  dump_to = Path(args.dump_to)

  if dump_to.exists() and dump_to.is_dir():
    if args.remove:
      rmtree(dump_to)
    else:
      dump_to.rename(f"{dump_to}_{random_string()}")

  dump_to.mkdir(parents=True, exist_ok=True)

  # Не в основном же цикле проверять директории xD
  create_subdir(args.dump_to)
  # Дамп по пути
  dump(args.dump_to)
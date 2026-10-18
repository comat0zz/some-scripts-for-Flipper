from tinydb import TinyDB, Query
from argparse import ArgumentParser, BooleanOptionalAction
from pathlib import Path
from fc_common import random_string, get_sorted_unique_values
from shutil import rmtree


db = TinyDB('db_rfid.json')
db_row = Query()


def create_subdir(root):
  dirs = get_sorted_unique_values(db, ['Key type'])
  
  for d in dirs:
    dc = Path(f"{root}/{d}")
    dc.mkdir(parents=True, exist_ok=True)

def dump(dump_path):
  all_records = db.all()

  index = 0

  for record in all_records:
    index += 1
    body = "Filetype: Flipper RFID key"
    body += f"\nVersion: {record['Version']}"
    body += f"\nKey type: {record['Key type']}"
    body += f"\nData: {record['Data']}"

    protocol = record['Key type'].replace('/', '_')

    if 'name' in record:
      name = record['name']
    else:
      name = index

    filename = f"{dump_path}/{protocol}/{name}.rfid"
    with open(filename, "w") as f:
      f.write(body)
      f.close()

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
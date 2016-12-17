import click
import sys
from ..lib import import_book
from ..lib import parse_dictionary
from ..lib import megatron
import progressbar

@click.group()
def main():
    pass

@click.command(help='import books from a folder')
@click.option('--db', help='database URN', required=True)
@click.argument('dir')
def import_books(db, dir):
    m = megatron.Megatron(db)
    importer = import_book.BookImporter(m)

    progress = progressbar.ProgressBar()
    importer.import_from(dir, progress)

@click.command(help='import words from json dictionary file')
@click.option('--db', help='database URN', required=True)
@click.argument('dict')
def parse_dict(db, dict):
	m = megatron.Megatron(db)
	parser = parse_dictionary.DictionaryParser(m)
	parser.parse_dictionary_from(dict)



@click.command(help='create the database')
@click.option('--db', help='database URN', required=True)
def createdb(db):
    m = megatron.Megatron(db)
    m.database.create_database()
    click.echo('Created the database')

@click.command(help='drop the database')
@click.option('--db', help='database URN', required=True)
def dropdb(db):
    m = megatron.Megatron(db)
    m.database.drop_all()
    click.echo('Dropped the database')

main.add_command(import_books)
main.add_command(parse_dict)
main.add_command(createdb)
main.add_command(dropdb)

if __name__ == '__main__':
    main()
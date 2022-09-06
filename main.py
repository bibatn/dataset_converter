import os
import argparse
import textwrap
import re
from lxml import etree

import sys

if sys.version_info[0] < 3:
    sys.stderr.write("You need Python 3 or later to run this script!\n")
    sys.exit(1)

split_row_pattern = re.compile(r"\s*;\s*")

def parse_args():
    usage = "python3 {} tracking_data_dir [-c classes_file] [-o output_dir] [-t threads_count]".format(os.path.basename(__file__))
    epilog = """CPU count: {}
    Не используйте опцию -t n_threads, если основной задачей является вырезание объектов из видеофайлов.
    FFMpeg сам эффективно использует многоядерные процессоры. 
    """.format(os.cpu_count())
    parser = argparse.ArgumentParser(usage=textwrap.dedent(usage), prog=os.path.basename(__file__), epilog=textwrap.dedent(epilog), formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('source_directory', type=os.path.abspath, action='store',
                        help="Директория датасета")
    parser.add_argument('-c', '--classes', type=os.path.abspath, action='store', required=False,
                        help="Файл с классами (если не указан, будут извлечены все найденные объекты разметки в соотв. с форматом)")
    parser.add_argument('-o', '--output', type=os.path.abspath, action='store', required=False,
                        help="Директория для вырезаемых фрагментов" )
    parser.add_argument('-t', '--threads', type=int, action='store', default=1, required=False,
                        help='Количество потоков обработки (по умолчанию: 1)')
    return vars(parser.parse_args())

def parse_classes(classes_file):
    if not classes_file:
        return []
    if not (os.path.exists(classes_file) and os.path.isfile(classes_file)):
        raise FileNotFoundError(classes_file)
    with open(classes_file, 'r') as fh:
        classes = [subrow for row in fh for subrow in re.split(split_row_pattern, row.strip('\n'))]
    return classes

def convert_dataset(xml_file, images):
    try:
        xml = etree.parse(xml_file)
    except etree.ParseError as err:
        print(err)
        sys.exit(1)
    except OSError:
        print('{} not found'.format(xml_file))
    else:
        root = xml.getroot()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    args = parse_args()

    # classes = parse_classes(args['classes'])
    if args['output']:
        output_dir = args['output']
    else:
        output_dir = os.path.join(os.getcwd(), "ObjectCutter_output")

    if not (os.path.exists(output_dir) and os.path.isdir(output_dir)):
        os.makedirs(output_dir)

    source_dir = args['source_directory']
    xml_file = ''
    for dirname, dirs, files in os.walk(source_dir):
        for f in files:
            if f.lower().endswith('.xml'):
                xml_file = os.path.join(dirname, f)

    convert_dataset(xml_file, source_dir+'/images')
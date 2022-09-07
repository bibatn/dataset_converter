import os
import argparse
import textwrap
import re
from lxml import etree
from lxml import builder

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

def _extract_from_image(image_file, boundboxes_in_frame=[], frame_number=None, dirname='', video_filename=''):
    """Extract objects from frame using Pillow"""
    if not (os.path.exists(image_file) and os.path.isfile(image_file)):
        print("FileNotFoundError: {}".format(image_file))
    else:
        with Image.open(image_file) as img:
            for bbox in boundboxes_in_frame:
                output_dir = os.path.join(self.__output, bbox.className)
                if not (os.path.exists(output_dir) and os.path.isdir(output_dir)):
                    try:
                        os.mkdir(output_dir)
                    except FileExistsError:
                        pass
                try:
                    fragment = img.crop((bbox.x, bbox.y, bbox.width + bbox.x, bbox.height + bbox.y))
                    if not dirname:
                        dirname = os.path.basename(os.path.dirname(image_file if not video_filename else video_filename))
                    if video_filename and frame_number is not None:
                        image_name = "{}_{}".format(os.path.splitext(os.path.basename(video_filename))[0], frame_number)
                    else:
                        image_name = os.path.splitext(os.path.basename(image_file))[0]

                    FragmentFileName = os.path.join(output_dir, "{}_{}_{}_{}.png".format(dirname, image_name, bbox.x, bbox.y))
                    fragment.save(FragmentFileName)
                except SystemError:
                    print('-------------\nBoundBox position error in image: {}\nImage size: {}\n{}\n{} - will be deleted'.format(image_file, img.size, bbox, FragmentFileName))
                    os.remove(FragmentFileName)

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
        if root.tag.lower() == "annotations":
            page = etree.Element("annotations")
            doc = etree.ElementTree(page)
            page.append(root.find('meta'))
            # pageElement = etree.SubElement(page, root.find('meta'))
            for image in root.iter("image"):
                print(image.attrib["name"])
                for box in image.iter("box"):
                    if(box.attrib["label"]=="car"):
                        print(box.attrib)
            doc.write('output.xml', xml_declaration=True, encoding='utf-8')



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

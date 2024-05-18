import os
import pandas as pd
from xml.etree.ElementTree import Element, SubElement, tostring


def find_csv_files(root_dir, file_name):
    csv_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        if file_name in filenames:
            csv_files.append(os.path.join(dirpath, file_name))
    return csv_files

def read_csv_file(csv_file):
    with open(csv_file, 'r', encoding='windows-1252') as file:
        data = pd.read_csv(file, delimiter=';', quotechar='"')
    return data

def generate_mermaid_mindmap_for_all_courses(root_dir, file_name):
    mindmap = "mindmap\n  Kurse\n"
    csv_files = find_csv_files(root_dir, file_name)
    
    for csv_file in csv_files:
        print(f"Processing {csv_file}...")

        with open(csv_file, 'r', encoding='windows-1252') as file:
            data = pd.read_csv(file, delimiter=';', quotechar='"')
            
        courses = data['course_name'].unique()

        for course in courses:
            mindmap += f"    {course}\n"
            course_data = data[data['course_name'] == course]
            sections = course_data['section_name'].unique()
            
            for section in sections:
                mindmap += f"      {section}\n"
                section_data = course_data[course_data['section_name'] == section]
                
                for _, lecture in section_data.iterrows():
                    lecture['lecture_name'].replace('(', ' ').replace(')', ' ')
                    lecture_info = f"{lecture['lecture_name']} (ID: {lecture['lecture_id']}, Position: {lecture['lecture_position']})"
                    mindmap += f"        {lecture_info}\n"
    
    return mindmap

def generate_freemind(root_dir, file_name):
    root = Element('map', version='1.0.1')
    master_node = SubElement(root, 'node', TEXT='Kurse')

    csv_files = find_csv_files(root_dir, file_name)
    
    for csv_file in csv_files:
        data = read_csv_file(csv_file)
        courses = data['course_name'].unique()

        for course in courses:
            course_node = SubElement(master_node, 'node', TEXT=course)
            course_data = data[data['course_name'] == course]
            sections = course_data['section_name'].unique()

            for section in sections:
                section_node = SubElement(course_node, 'node', TEXT=section, FOLDED='false')
                section_data = course_data[course_data['section_name'] == section]

                unique_lectures = section_data.drop_duplicates(subset='lecture_id')
                for _, lecture in unique_lectures.iterrows():
                    lecture_text = f"{lecture['lecture_name']} (ID: {lecture['lecture_id']}, Position: {lecture['lecture_position']})"
                    SubElement(section_node, 'node', TEXT=lecture_text)

    return tostring(root, encoding='unicode')

def generate_xmind(root_dir, file_name):
    root = Element('xmap-content', version='2.0', xmlns="urn:xmind:xmap:xmlns:content:2.0")
    sheet = SubElement(root, 'sheet', name="Kurse")
    topic = SubElement(sheet, 'topic', id="root", structure_class="org.xmind.ui.map.unbalanced")

    title = SubElement(topic, 'title')
    title.text = "Kurse"

    csv_files = find_csv_files(root_dir, file_name)
    
    for csv_file in csv_files:
        data = read_csv_file(csv_file)
        courses = data['course_name'].unique()

        for course in courses:
            course_topic = SubElement(topic, 'topic', id=f"course_{course}")
            course_title = SubElement(course_topic, 'title')
            course_title.text = course

            course_data = data[data['course_name'] == course]
            sections = course_data['section_name'].unique()

            for section in sections:
                section_topic = SubElement(course_topic, 'topic', id=f"section_{section}")
                section_title = SubElement(section_topic, 'title')
                section_title.text = section

                section_data = course_data[course_data['section_name'] == section]

                for _, lecture in section_data.iterrows():
                    lecture_topic = SubElement(section_topic, 'topic', id=f"lecture_{lecture['lecture_id']}")
                    lecture_title = SubElement(lecture_topic, 'title')
                    lecture_title.text = f"{lecture['lecture_name']} (ID: {lecture['lecture_id']}, Position: {lecture['lecture_position']})"

    return tostring(root, encoding='unicode')

def generate_mindmaps_for_all_courses(root_dir, file_name):
    freemind_xml = generate_freemind(root_dir, file_name)
    # xmind_xml = generate_xmind(root_dir, file_name)
    
    return freemind_xml #, xmind_xml

if __name__ == "__main__":
    # Generate the mindmap for all courses
    root_dir = r"G:\\Geteilte Ablagen\\JuliaTulipan\\Teachable Backup"

    file_name = 'course_data.csv'

    # mermaid_mindmap_all_courses = generate_mermaid_mindmap_for_all_courses(root_dir, file_name)
    # print("Saving to mindmap_all_courses.mmd...")
    # with open(os.path.join(root_dir, 'mindmap_all_courses.mmd'), 'w') as f:
    #     f.write(mermaid_mindmap_all_courses)

    freemind_output = generate_mindmaps_for_all_courses(root_dir, file_name)

    # Save outputs to files
    with open('freemind_output.mm', 'w', encoding='utf-8') as f:
        f.write(freemind_output)

    # with open('xmind_output.xml', 'w', encoding='utf-8') as f:
    #     f.write(xmind_output)

    print("FreeMind file generated.")
    
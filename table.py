import os
import csv
import time

import pandas as pd
import json

from loguru import logger


def excel_to_list_of_dicts(path, sheet_name=None):
    """
    Reads an Excel file and converts its contents into a list of dictionaries.
    """

    with pd.ExcelFile(path) as excel_data:
        df = excel_data.parse(sheet_name if sheet_name else excel_data.sheet_names[0])
        df.fillna('', inplace=True)  # Change Nan value to ''
        list_of_dicts = df.to_dict(orient='records')

    return list_of_dicts


def dicts_to_queue(product_list):
    """
    Save the list of dictionaries to queue folder as Json files
    """

    # Clear the queue folder
    for file in get_queue():
        os.remove(f'queue/{file}')

    time.sleep(1)

    for index, product in enumerate(product_list, start=1):
        json_path = f'queue/{str(index).rjust(3,"0")}.json'
        with open(json_path, 'w') as file:
            json.dump(product, file, indent=4)

    time.sleep(1)

    # list the files in queue folder
    files = get_queue()
    return files


def save_result_to_excel(tab, launch_datetime, product_data, row_index, reason):
    """
    Save the finished/unfinished product to the vestiairecollective.com
    :param tab:
    :param launch_datetime:
    :param product_data:
    :param row_index:
    :param reason:
    :return:
    """
    current_url = tab.url
    finished_steps = tab.html.count('AsideMenu_aside__menu__li__item__icon--desktop')
    unfinished_steps = 5 - finished_steps  # 计算出未完成的步骤数量

    save_path = f'result/Result_{launch_datetime}.csv'

    if current_url == 'https://us.vestiairecollective.com/sell-clothes-online/':
        reason = 'Failed in the Category step'
    elif reason == '':
        reason = 'Success'

    new_product_data = {
        'Unfinished Steps': unfinished_steps,
        'Draft URL': current_url,
        'Error': reason,
        **product_data
    }

    # 检查文件是否存在
    file_exists = os.path.exists(save_path)

    # 确保目录存在
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # 写入文件
    with open(save_path, mode='a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['Unfinished Steps', 'Draft URL', 'Error'] + list(product_data.keys()))

        # 如果文件不存在，则写入表头
        if not file_exists:
            writer.writeheader()

        # 写入数据
        writer.writerow(new_product_data)

    logger.warning(f"Save product to {save_path}")


def load_json_data(path):
    """
    Load the JSON data from the specified file
    """
    with open(f'queue/{path}', 'r') as file:
        data = json.load(file)

    index = int(path.split('.')[0])

    return index, data


def get_queue():
    files = os.listdir('queue')
    json_files = []
    for f in files:
        if f.endswith('.json'):
            json_files.append(f)
    return json_files


if __name__ == '__main__':
    # Path to the uploaded file
    file_path = 'Vestiaire Collective Product Information.xlsx'

    # Convert the content of the first sheet to a list of dictionaries
    list_of_dicts = excel_to_list_of_dicts(file_path)

    print(list_of_dicts)
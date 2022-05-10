# -*- coding: utf-8
from __future__ import unicode_literals, absolute_import

from xlsxhelper import get_workbook
from xlsxhelper import get_worksheet
from xlsxhelper import get_cells
import datetime
import codecs
import click

header = """# -*- coding: utf-8
from __future__ import unicode_literals, absolute_import
from bizerror.base import BizErrorBase
from bizerror.base import set_error_info

# Created: {now_time}
# WARNING! All changes made in this file will be lost!

"""

item_class_template = """
class {class_name}({base_name}):
    pass
"""

item_update_message_template = """set_error_info("{language}", "{name}", {code}, "{message}")
"""

template_1_description = """BizError System

1.Always use RAISE-AND-EXCEPT exception handle system when you get error.
2.An exception must provides error code and error message.
3.An exception error code is a 10 digits number.
4.An exception error message is a string that describes the error.
5.Every system or component have it's own BizCode. A BizCode is a 3 digits number, from 100 to 999. BizError framework keeps 100 to 299, and 300 to 999 for user use.
6.TypeCode used for category ErrorCode. A TypeCode is a 3 digits number, from 000 to 999. BizError framework keeps 000 to 299, and 300 to 999 for user use.
7.An ErrorCode is 4 digits number, from 0000 to 9999.
"""

template_2_bizcode_data = [
    ["BizCode", "Description", "Native Description"],
    ["100", "General", "通用"]
]

template_3_typecode_data = [
    ["TypeCode", "Description", "Native Description"],
    ["100", "System error.", "系统错误"],
    ["101", "Http request related error.", "HTTP请求相关错误"],
    ["102", "Config reldated error.", "配置相关错误"],
    ["103", "Data related error.", "数据相关错误"],
    ["104", "Authentication related error.", "认证相关错误"],
    ["105", "Data type related error.", "数据类型相关错误"],
    ["106", "Parameter related error.", "参数相关错误"],
    ["107", "Form related error.", "表单相关错误"],
    ["108", "Bussiness logic related error.", "业务逻辑相关错误"],
]

template_4_errorcode_data = [
    ["BizCode","TypeError","ErrorCode","CODE","MESSAGE","NATIVE MESSAGE","Class","MEMO"],
    ["0", "0", "0", "0", "OK.", "OK", "OK", "Special error, means OK and no errors."],
    ["100", "100", "0000", "1001000000", "System Error.", "系统异常。", "SysError", ""],
]

@click.group()
def main():
    pass

@main.command()
@click.option("-o", "--output", default="template.xlsx")
def template(output):
    """Make a new template.xlsx.
    """
    workbook = get_workbook()
    workbook.remove(workbook.active)
    # 1. Description
    worksheet = get_worksheet(workbook, "1. Description")
    for row_index, line in enumerate(template_1_description.splitlines()):
        worksheet.cell(row_index+1, 1, line)
    # 2. BizCode
    worksheet = get_worksheet(workbook, "2. BizCode")
    for row_index in range(len(template_2_bizcode_data)):
        for col_index in range(len(template_2_bizcode_data[row_index])):
            worksheet.cell(row_index+1, col_index+1, template_2_bizcode_data[row_index][col_index])
    # 3. TypeCode
    worksheet = get_worksheet(workbook, "3. TypeCode")
    for row_index in range(len(template_3_typecode_data)):
        for col_index in range(len(template_3_typecode_data[row_index])):
            worksheet.cell(row_index+1, col_index+1, template_3_typecode_data[row_index][col_index])
    # 4. ErrorCode
    worksheet = get_worksheet(workbook, "4. ErrorCode")
    for row_index in range(len(template_4_errorcode_data)):
        for col_index in range(len(template_4_errorcode_data[row_index])):
            worksheet.cell(row_index+1, col_index+1, template_4_errorcode_data[row_index][col_index])
    workbook.save(output)

@main.command()
@click.option("-n", "--natvie-name", default="zh-hans", help="Native message name, default to zh-hans.")
@click.option("-o", "--output", default="-", help="Save the result to a file.")
@click.argument("workbook", nargs=1)
def make(natvie_name, output, workbook):
    """Make python file of exception classes.
    """
    wb = get_workbook(workbook, data_only=True)
    ws = get_worksheet(wb, "4. ErrorCode")
    cells = get_cells(ws, rows="2-", only_data=True)
    base_names = {
        "0": "BizErrorBase",
    }
    code_text = header.format(now_time=datetime.datetime.now())
    for row in cells:
        biz_code = row[0]
        type_code = row[1]
        error_code = row[2]
        code = row[3]
        message_en = row[4]
        message_native = row[5]
        class_name = row[6]
        if not class_name:
            continue
        if error_code == "0000":
            base_name = base_names["0"]
            base_names[biz_code + type_code] = class_name
        else:
            if biz_code + type_code in base_names:
                base_name = base_names[biz_code + type_code]
            else:
                base_name = base_names["0"]
        code_text +=  item_class_template.format(
            class_name=class_name,
            base_name=base_name,
        )
        code_text += item_update_message_template.format(language="en", name=class_name, code=code, message=message_en)
        code_text += item_update_message_template.format(language=natvie_name, name=class_name, code=code, message=message_native)
    if output == "-":
        print(code_text)
    else:
        with open(output, "wb") as fobj:
            codecs.getwriter("utf-8")(fobj).write(code_text)

if __name__ == "__main__":
    main()

from flask import Blueprint, render_template, request, redirect, url_for, make_response, send_file
import pandas as pd
from io import BytesIO
import logging
from urllib.parse import quote
import os
import datetime
import openpyxl
from io import BytesIO

basic_data_bp = Blueprint('basic_data_bp', __name__, template_folder='templates')

@basic_data_bp.route('/')
def index():
    return render_template('basic_data/index.html')

@basic_data_bp.route('/vehicle_info')
def vehicle_information():
    return render_template('basic_data/vehicle_info.html', title='车辆信息管理')

@basic_data_bp.route('/route_info')
def route_information():
    return render_template('basic_data/route_info.html', title='路线基础数据')

@basic_data_bp.route('/maintenance')
def data_maintenance():
    return render_template('basic_data/maintenance.html', title='数据维护更新')

@basic_data_bp.route('/company_list')
def company_list():
    from app import get_db
    conn = get_db()
    companies = conn.execute('SELECT * FROM Company ORDER BY name').fetchall()
    return render_template('basic_data/company_list.html', companies=companies)

@basic_data_bp.route('/company_new', methods=['GET', 'POST'])
def company_new():
    if request.method == 'POST':
        name = request.form['name']
        bank_name = request.form['bank_name']
        account_number = request.form['account_number']
        address = request.form['address']
        contact_person = request.form['contact_person']
        contact_phone = request.form['contact_phone']
        
        from app import get_db
        conn = get_db()
        conn.execute('''
            INSERT INTO Company (name, bank_name, account_number, address, contact_person, contact_phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, bank_name, account_number, address, contact_person, contact_phone))
        conn.commit()
        return redirect(url_for('basic_data_bp.company_list'))
    return render_template('basic_data/company_edit.html', company=None)

@basic_data_bp.route('/company_edit/<int:id>', methods=['GET', 'POST'])
def company_edit(id):
    from app import get_db
    conn = get_db()
    company = conn.execute('SELECT * FROM Company WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        name = request.form['name']
        bank_name = request.form['bank_name']
        account_number = request.form['account_number']
        address = request.form['address']
        contact_person = request.form['contact_person']
        contact_phone = request.form['contact_phone']
        
        conn.execute('''
            UPDATE Company
            SET name = ?, bank_name = ?, account_number = ?, address = ?, contact_person = ?, contact_phone = ?
            WHERE id = ?
        ''', (name, bank_name, account_number, address, contact_person, contact_phone, id))
        conn.commit()
        return redirect(url_for('basic_data_bp.company_list'))
    
    return render_template('basic_data/company_edit.html', company=company)

@basic_data_bp.route('/company_delete/<int:id>', methods=['POST'])
def company_delete(id):
    from app import get_db
    conn = get_db()
    conn.execute('DELETE FROM Company WHERE id = ?', (id,))
    conn.commit()
    return redirect(url_for('basic_data_bp.company_list'))

@basic_data_bp.route('/company_export')
def company_export():
    # 添加请求处理日志
    logging.debug(f"收到Excel导出请求: {datetime.datetime.now()}")
    
    from app import get_db
    conn = get_db()
    try:
        # 查询数据
        cursor = conn.execute('SELECT id, name, contact_person, contact_phone FROM Company ORDER BY name')
        companies = cursor.fetchall()
        columns = ['id', 'name', 'contact_person', 'contact_phone']
        logging.debug(f"查询到{len(companies)}条单位数据")
    
        # 创建DataFrame
        df = pd.DataFrame(companies, columns=columns)
        logging.debug(f"DataFrame创建成功: {len(df)}行")
    
        # 创建Excel文件
        output = BytesIO()
        try:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='单位信息')
            output.seek(0)
            file_content = output.getvalue()
            file_size = len(file_content)
            logging.debug(f"Excel文件生成成功，大小: {file_size} bytes")
        
            # 验证Excel文件内容
            try:
                workbook = openpyxl.load_workbook(BytesIO(file_content))
                sheet = workbook.active
                logging.debug(f"Excel内容验证成功: {sheet.title}工作表，{sheet.max_row}行数据")
            except Exception as e:
                logging.error(f"Excel内容验证失败: {str(e)}", exc_info=True)
                return "导出失败: 生成的Excel文件无效", 500
        except Exception as e:
            logging.error(f"Excel文件生成失败: {str(e)}", exc_info=True)
            return "导出失败: 文件生成错误", 500
        
        # 设置正确的响应头
        filename = "单位信息导出.xlsx"
        
        try:
            # 使用send_file替代make_response，让Flask自动处理响应头
            return send_file(
                BytesIO(file_content),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            logging.error(f"Excel导出失败: {str(e)}", exc_info=True)
            return f"导出失败: {str(e)}", 500
    except Exception as e:
        logging.error(f"数据库操作失败: {str(e)}", exc_info=True)
        return "导出失败: 数据库错误", 500
    finally:
        conn.close()  # 确保数据库连接关闭

# 添加简单文本下载测试端点
@basic_data_bp.route('/test_download')
def test_download():
    """简单文本文件下载测试端点，用于验证基本下载功能"""
    content = "这是一个测试文件，用于验证下载功能是否正常工作。"
    response = make_response(content)
    response.headers['Content-Type'] = 'text/plain'
    response.headers['Content-Disposition'] = 'attachment; filename*=UTF-8''test_download.txt'
    response.headers['Content-Length'] = str(len(content))
    return response

@basic_data_bp.route('/company_import', methods=['GET', 'POST'])
def company_import():
    if request.method == 'GET':
        return render_template('basic_data/company_import.html')
    else:
        # 验证文件上传
        validation_result = _validate_file_upload(request.files)
        if validation_result:
            return render_template('basic_data/company_import.html', import_result=validation_result)

        file = request.files['file']

        try:
            # 读取Excel文件
            df = _read_excel_file(file)
            if not df.empty:
                # 检查必要列
                required_columns = ['单位名称']
                column_check_result = _check_required_columns(df, required_columns)
                if column_check_result:
                    return render_template('basic_data/company_import.html', import_result=column_check_result)

                # 导入数据到数据库
                import_result = _import_data_to_db(df)
                return render_template('basic_data/company_import.html', import_result=import_result)
            else:
                return render_template('basic_data/company_import.html', import_result={
                    'total': 0,
                    'success': 0,
                    'fail': 0,
                    'errors': ['Excel文件为空，没有可导入的数据']
                })
        except Exception as e:
            return render_template('basic_data/company_import.html', import_result={
                'total': 0,
                'success': 0,
                'fail': 0,
                'errors': [f'导入过程中发生错误: {str(e)}']
            })

def _validate_file_upload(files):
    """验证文件上传"""
    if 'file' not in files:
        return {
            'total': 0,
            'success': 0,
            'fail': 0,
            'errors': ['没有选择文件']
        }

    file = files['file']
    if file.filename == '':
        return {
            'total': 0,
            'success': 0,
            'fail': 0,
            'errors': ['没有选择文件']
        }

    if not file.filename.endswith(('.xlsx', '.xls')):
        return {
            'total': 0,
            'success': 0,
            'fail': 0,
            'errors': ['不支持的文件格式，请上传.xlsx或.xls格式的Excel文件']
        }

    return None


def _read_excel_file(file):
    """读取Excel文件并返回DataFrame"""
    return pd.read_excel(file)

def _check_required_columns(df, required_columns):
    """检查必要列是否存在"""
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return {
            'total': 0,
            'success': 0,
            'fail': 0,
            'errors': [f'缺少必要列: {", ".join(missing_columns)}']
        }
    return None
def _import_data_to_db(df):
    """将DataFrame数据导入数据库"""
    conn = None
    data = []
    total = len(df) if not df.empty else 0
    
    try:
        conn = get_db()
        # 检查必要字段是否存在
        required_fields = ['单位名称']
        missing_fields = [field for field in required_fields if field not in df.columns]
        if missing_fields:
            return {
                'total': total,
                'success': 0,
                'fail': total,
                'errors': [f'缺少必要字段: {", ".join(missing_fields)}']
            }
            
        # 从DataFrame中提取数据
        data = df.to_dict(orient='records')
        
        # 执行批量插入
        conn.executemany(
            'INSERT INTO Company (name, contact_person, contact_phone) VALUES (?, ?, ?)',
            [(item['单位名称'], item.get('联系人', ''), item.get('联系电话', '')) for item in data]
        )
        conn.commit()
        
        return {
            'total': total,
            'success': total,
            'fail': 0,
            'errors': []
        }
        
    except KeyError as e:
        if conn:
            conn.rollback()
        return {
            'total': total,
            'success': 0,
            'fail': total,
            'errors': [f'数据字段错误: 缺少 {str(e)}']
        }
    except Exception as e:
        if conn:
            conn.rollback()
        return {
            'total': total,
            'success': 0,
            'fail': total,
            'errors': [f'数据库导入失败: {str(e)}']
        }
    finally:
        if conn:
            try:
                conn.close()  # 确保连接关闭
            except Exception as close_err:
                print(f"关闭数据库连接失败: {str(close_err)}")

@basic_data_bp.route('/company_import_template')
def company_import_template():
    """下载单位数据导入模板"""
    # 创建一个包含必要列的空DataFrame作为模板
    template_columns = ['单位名称', '开户行', '银行账户', '单位地址', '联系人', '联系电话']
    df = pd.DataFrame(columns=template_columns)

    # 创建Excel文件
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='单位信息模板')
    output.seek(0)

    # 设置响应头并返回文件
    filename = "单位数据导入模板.xlsx"
    return send_file(
        BytesIO(output.getvalue()),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

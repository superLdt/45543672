from datetime import datetime
from services.db_manager_compat import DatabaseManagerCompat as DatabaseManager

def validate_dispatch_data(data):
    """验证派车任务数据（匹配前端表单字段）"""
    required_fields = [
        'requirement_type',      # 需求类型：正班/加班
        'start_location',        # 始发局
        'end_location',          # 邮路名称/路向
        'carrier_company',       # 委办承运公司
        'transport_type',        # 运输类型：单程/往返
        'weight',                # 重量吨
        'volume',                # 容积
        'required_time'          # 要求用车时间
    ]
    
    for field in required_fields:
        if not data.get(field):
            return False, f'缺少必填字段: {field}'
    
    # 验证枚举值
    if data.get('requirement_type') not in ['正班', '加班']:
        return False, '需求类型必须是"正班"或"加班"'

    if data.get('transport_type') not in ['单程', '往返']:
        return False, '运输类型必须是"单程"或"往返"'

    if data.get('dispatch_track') and data.get('dispatch_track') not in ['轨道A', '轨道B']:
        return False, '流程轨道必须是"轨道A"或"轨道B"'
    
    # 验证重量吨选项
    valid_weights = ['5', '8', '12', '20', '30', '40A', '40B']
    if str(data.get('weight')) not in valid_weights:
        return False, f'重量吨必须是以下之一: {", ".join(valid_weights)}'

    # 验证容积
    try:
        volume = float(data.get('volume', 0))
        if volume <= 0:
            return False, '容积必须大于0'
    except (ValueError, TypeError):
        return False, '容积必须是有效数字'

    # 验证时间格式（ISO格式）
    try:
        if data.get('required_time'):
            datetime.strptime(data['required_time'], '%Y-%m-%dT%H:%M')
    except ValueError:
        return False, '时间格式错误，应为YYYY-MM-DDTHH:MM'
    
    return True, None

def generate_task_id():
    """生成任务ID"""
    db_manager = DatabaseManager()
    if not db_manager.connect():
        return None
    
    try:
        today = datetime.now().strftime('%Y%m%d')
        db_manager.cursor.execute("SELECT COUNT(*) FROM manual_dispatch_tasks WHERE task_id LIKE ?", 
                       [f'T{today}%'])
        count = db_manager.cursor.fetchone()[0]
        
        return f'T{today}{str(count + 1).zfill(3)}'
    finally:
        db_manager.disconnect()
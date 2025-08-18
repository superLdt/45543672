import sqlite3
import os
from datetime import datetime
from config import DATABASE  # 从config.py导入数据库路径配置

class DatabaseManager:
    def __init__(self, db_path=DATABASE):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        self.insert_default_data()
        self.insert_sample_dispatch_data()
        self.update_manual_dispatch_tables()  # 更新现有表结构

    def connect(self):
        """连接到数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            # 设置row_factory为sqlite3.Row，以便将查询结果转换为字典
            self.conn.row_factory = sqlite3.Row
            # 启用外键约束
            self.conn.execute('PRAGMA foreign_keys = ON')
            self.cursor = self.conn.cursor()
            print(f'成功连接到数据库: {self.db_path}')
            return True
        except Exception as e:
            print(f'连接数据库失败: {str(e)}')
            return False

    def disconnect(self):
        """断开数据库连接"""
        if self.conn:
            self.conn.close()
            print('数据库连接已关闭')

    def check_table_exists(self, table_name):
        """检查表是否存在"""
        if not self.cursor:
            print('未连接到数据库')
            return False

        try:
            self.cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            result = self.cursor.fetchone()
            return result is not None
        except Exception as e:
            print(f'检查表{table_name}失败: {str(e)}')
            return False

    def list_tables(self):
        """列出所有表"""
        if not self.cursor:
            print('未连接到数据库')
            return []

        try:
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            print(f'列出表失败: {str(e)}')
            return []

    def check_user_table(self):
        """检查用户表结构和数据"""
        if not self.check_table_exists('User'):
            print('用户表不存在')
            return False

        try:
            # 检查表结构
            self.cursor.execute("PRAGMA table_info(User);")
            columns = self.cursor.fetchall()
            print('用户表结构:')
            for column in columns:
                print(f'  {column[1]} ({column[2]})')

            # 检查数据
            self.cursor.execute("SELECT id, username, full_name, is_active FROM User;")
            users = self.cursor.fetchall()
            print('用户数据:')
            if not users:
                print('  没有找到用户数据')
            else:
                for user in users:
                    print(f'  ID: {user[0]}, 用户名: {user[1]}, 姓名: {user[2]}, 激活状态: {user[3]}')
            return True
        except Exception as e:
            print(f'检查用户表失败: {str(e)}')
            return False

    def create_manual_dispatch_tables(self):
        """创建人工派车相关表"""
        if not self.cursor:
            print('数据库未连接')
            return False

        try:
            # 创建派车任务表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS manual_dispatch_tasks (
                task_id TEXT PRIMARY KEY,
                required_date TEXT NOT NULL,
                start_bureau TEXT NOT NULL,
                route_direction TEXT NOT NULL,
                carrier_company TEXT NOT NULL,
                route_name TEXT NOT NULL,
                transport_type TEXT CHECK(transport_type IN ('单程', '往返')) NOT NULL,
                requirement_type TEXT CHECK(requirement_type IN ('正班', '加班')) NOT NULL,
                volume INTEGER NOT NULL,
                weight REAL NOT NULL,
                special_requirements TEXT,
                status TEXT DEFAULT '待提交' NOT NULL CHECK(status IN ('待提交','待调度员审核','待供应商响应','供应商已响应','车间已核查','供应商已确认','任务结束','已取消')),
                
                -- 双轨派车流程字段
                dispatch_track TEXT CHECK(dispatch_track IN ('轨道A', '轨道B')) NOT NULL DEFAULT '轨道A',
                initiator_role TEXT CHECK(initiator_role IN ('车间地调', '区域调度员', '超级管理员')) NOT NULL DEFAULT '车间地调',
                initiator_user_id INTEGER NOT NULL DEFAULT 1,
                initiator_department TEXT,
                
                -- 审核流程字段（仅轨道A需要）
                audit_required BOOLEAN DEFAULT 1,
                auditor_role TEXT,
                auditor_user_id INTEGER,
                audit_status TEXT CHECK(audit_status IN ('待审核', '已通过', '已拒绝')) DEFAULT '待审核',
                audit_time TEXT,
                audit_note TEXT,
                
                -- 当前处理人信息
                current_handler_role TEXT,
                current_handler_user_id INTEGER,
                
                -- 供应商分配信息
                assigned_supplier_id INTEGER,
                
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                
                -- 外键约束
                FOREIGN KEY (carrier_company) REFERENCES Company(name),
                FOREIGN KEY (assigned_supplier_id) REFERENCES User(id)
            )
            ''')

            # 检查vehicles表是否需要更新（移除manifest_serial字段）
            self.cursor.execute("PRAGMA table_info(vehicles)")
            columns = [col[1] for col in self.cursor.fetchall()]
            
            if 'manifest_serial' in columns:
                # 需要重建表来移除manifest_serial字段
                print("检测到vehicles表包含manifest_serial字段，正在重建表...")
                
                # 备份现有数据
                self.cursor.execute("SELECT * FROM vehicles")
                existing_data = self.cursor.fetchall()
                
                # 删除现有表
                self.cursor.execute("DROP TABLE vehicles")
                
                # 创建新表结构（不含manifest_serial）
                self.cursor.execute('''
                CREATE TABLE vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    manifest_number TEXT,
                    dispatch_number TEXT,
                    license_plate TEXT NOT NULL,
                    carriage_number TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES manual_dispatch_tasks(task_id)
                )
                ''')
                
                # 重新插入数据（跳过manifest_serial字段）
                if existing_data:
                    for row in existing_data:
                        new_row = [row[0], row[1], row[2], row[4], row[5], row[6]]  # 跳过manifest_serial
                        self.cursor.execute('''
                        INSERT INTO vehicles (id, task_id, manifest_number, dispatch_number, license_plate, carriage_number, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', new_row)
                    print(f"已迁移{len(existing_data)}条车辆记录到新表结构")
            else:
                # 创建新表
                self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    manifest_number TEXT,
                    dispatch_number TEXT,
                    license_plate TEXT NOT NULL,
                    carriage_number TEXT,
                    notes TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES manual_dispatch_tasks(task_id)
                )
                ''')

            # 创建派车状态历史表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS dispatch_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                status_change TEXT NOT NULL,
                operator TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                note TEXT,
                FOREIGN KEY (task_id) REFERENCES manual_dispatch_tasks(task_id)
            )
            ''')

            # 创建索引
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_date ON manual_dispatch_tasks(required_date)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON manual_dispatch_tasks(status)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_task ON dispatch_status_history(task_id)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_vehicles_task ON vehicles(task_id)')

            self.conn.commit()
            print('人工派车相关表创建成功')
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f'创建表失败: {str(e)}')
            return False

    def insert_sample_dispatch_data(self):
        """插入示例派车数据"""
        if not self.cursor:
            return False

        try:
            # 检查是否已有数据
            self.cursor.execute('SELECT COUNT(*) FROM manual_dispatch_tasks')
            if self.cursor.fetchone()[0] > 0:
                print('派车任务表中已有数据，跳过插入示例数据')
                return True

            # 插入示例任务（包含双轨派车字段，使用新的清晰命名）
            sample_tasks = [
                ('T2024001', '2024-01-15', '北京邮区中心局', '北京-上海', '中国邮政集团', '京沪深线', '单程', '正班', 45, 8.5, '需要冷链运输', '待供应商响应', '2024-01-15 08:00:00', '2024-01-15 08:00:00', '轨道A', '车间地调', 1, '北京中心局', 1, '区域调度员', 2, '已通过', '2024-01-15 09:00:00', '审核通过，请尽快安排', '供应商', 4, 4),
                ('T2024002', '2024-01-16', '上海邮区中心局', '上海-广州', '顺丰速运', '沪深广线', '往返', '加班', 60, 12.0, '时效要求高', '待供应商响应', '2024-01-16 08:00:00', '2024-01-16 08:00:00', '轨道B', '区域调度员', 2, '上海中心局', 0, None, None, '已通过', None, '区域调度直接派车', '供应商', 4, 4),
                ('T2024003', '2024-01-17', '广州邮区中心局', '广州-深圳', '中通快递', '广深线', '单程', '正班', 30, 5.5, None, '待调度员审核', '2024-01-17 08:00:00', '2024-01-17 08:00:00', '轨道A', '车间地调', 3, '广州中心局', 1, '区域调度员', 2, '待审核', None, None, '区域调度员', 2, None)
            ]

            # 处理None值，使用Python的None代替SQL的NULL
            processed_tasks = []
            for task in sample_tasks:
                processed_task = tuple(None if x is None else x for x in task)
                processed_tasks.append(processed_task)

            self.cursor.executemany('''
            INSERT INTO manual_dispatch_tasks 
            (task_id, required_date, start_bureau, route_direction, carrier_company, route_name, 
             transport_type, requirement_type, volume, weight, special_requirements, status,
             created_at, updated_at, dispatch_track, initiator_role, initiator_user_id, initiator_department, 
             audit_required, auditor_role, auditor_user_id, audit_status, audit_time, audit_note,
             current_handler_role, current_handler_user_id, assigned_supplier_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', processed_tasks)

            # 插入示例状态历史
            sample_history = [
                ('T2024001', '创建任务', '系统管理员', '新建派车任务'),
                ('T2024002', '创建任务', '调度员张三', '新建加班任务'),
                ('T2024003', '创建任务', '调度员李四', '新建正班任务')
            ]

            self.cursor.executemany('''
            INSERT INTO dispatch_status_history (task_id, status_change, operator, note)
            VALUES (?, ?, ?, ?)
            ''', sample_history)

            # 插入示例车辆信息
            sample_vehicles = [
                ('T2024001', 'MN2024001', 'DP2024001', '京A12345', '1'),
                ('T2024002', 'MN2024002', 'DP2024002', '沪B67890', '2')
            ]

            self.cursor.executemany('''
            INSERT INTO vehicles (task_id, manifest_number, dispatch_number, license_plate, carriage_number)
            VALUES (?, ?, ?, ?, ?)
            ''', sample_vehicles)

            self.conn.commit()
            print('示例数据插入成功')
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f'插入示例数据失败: {str(e)}')
            return False

    # 人工派车业务方法
    def create_dispatch_task(self, task_data):
        """创建派车任务（支持双轨派车流程）"""
        if not self.cursor:
            return {'success': False, 'error': '数据库未连接'}

        try:
            task_id = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # 确定流程轨道和审核需求
            initiator_role = task_data.get('initiator_role', '车间地调')
            dispatch_track = '轨道B' if initiator_role in ['区域调度员', '超级管理员'] else '轨道A'
            audit_required = 0 if dispatch_track == '轨道B' else 1
            
            # 设置初始状态（使用新的清晰命名）
            if dispatch_track == '轨道A':
                initial_status = '待调度员审核'
                current_handler_role = '区域调度员'
            else:
                initial_status = '待供应商响应'
                current_handler_role = '供应商'
            
            # 获取承运公司对应的供应商用户ID
            self.cursor.execute("SELECT id FROM User WHERE company_id = (SELECT id FROM Company WHERE name = ?) AND id IN (SELECT user_id FROM UserRole WHERE role_id = (SELECT id FROM Role WHERE name = '供应商'))", (task_data['carrier_company'],))
            supplier_row = self.cursor.fetchone()
            assigned_supplier_id = supplier_row[0] if supplier_row else None
            
            # 验证承运公司是否存在对应的供应商用户
            if not supplier_row:
                return {'success': False, 'error': f'公司"{task_data["carrier_company"]}"下暂无供应商用户，请先创建用户'}
            
            self.cursor.execute('''
            INSERT INTO manual_dispatch_tasks 
            (task_id, required_date, start_bureau, route_direction, carrier_company, route_name,
             transport_type, requirement_type, volume, weight, special_requirements,
             dispatch_track, initiator_role, initiator_user_id, initiator_department,
             audit_required, current_handler_role, current_handler_user_id, status, assigned_supplier_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task_id,
                task_data['required_date'],
                task_data['start_bureau'],
                task_data['route_direction'],
                task_data['carrier_company'],
                task_data['route_name'],
                task_data['transport_type'],
                task_data['requirement_type'],
                task_data['volume'],
                task_data['weight'],
                task_data.get('special_requirements'),
                dispatch_track,
                initiator_role,
                task_data.get('initiator_user_id', 1),
                task_data.get('initiator_department', '未知部门'),
                audit_required,
                current_handler_role,
                task_data.get('current_handler_user_id', 1),
                initial_status,
                assigned_supplier_id
            ))

            # 获取发起者用户名
            self.cursor.execute("SELECT full_name FROM User WHERE id = ?", (task_data.get('initiator_user_id', 1),))
            user_row = self.cursor.fetchone()
            operator_name = user_row[0] if user_row else '系统'
            
            # 记录状态历史
            self.cursor.execute('''
            INSERT INTO dispatch_status_history (task_id, status_change, operator, note)
            VALUES (?, ?, ?, ?)
            ''', (task_id, initial_status, operator_name, f'创建{dispatch_track}派车任务'))

            self.conn.commit()
            return {'success': True, 'task_id': task_id}
            
        except sqlite3.IntegrityError as e:
            self.conn.rollback()
            return {'success': False, 'error': f'数据完整性错误: {str(e)}'}
        except sqlite3.Error as e:
            self.conn.rollback()
            return {'success': False, 'error': f'数据库操作错误: {str(e)}'}
        except Exception as e:
            self.conn.rollback()
            return {'success': False, 'error': f'创建任务失败: {str(e)}'}

    def get_dispatch_tasks(self, status=None, date_from=None, date_to=None):
        """获取派车任务列表"""
        if not self.cursor:
            return []

        try:
            query = '''
            SELECT t.*, COUNT(v.id) as vehicle_count
            FROM manual_dispatch_tasks t
            LEFT JOIN vehicles v ON t.task_id = v.task_id
            WHERE 1=1
            '''
            params = []

            if status:
                query += ' AND t.status = ?'
                params.append(status)

            if date_from:
                query += ' AND t.required_date >= ?'
                params.append(date_from)

            if date_to:
                query += ' AND t.required_date <= ?'
                params.append(date_to)

            query += ' GROUP BY t.task_id ORDER BY t.required_date ASC'

            self.cursor.execute(query, params)
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
            
        except Exception as e:
            print(f'获取任务列表失败: {str(e)}')
            return []

    def update_task_status(self, task_id, new_status, operator, note=None):
        """更新任务状态"""
        if not self.cursor:
            return {'success': False, 'error': '数据库未连接'}

        try:
            self.cursor.execute('''
            UPDATE manual_dispatch_tasks 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ?
            ''', (new_status, task_id))

            self.cursor.execute('''
            INSERT INTO dispatch_status_history (task_id, status_change, operator, note)
            VALUES (?, ?, ?, ?)
            ''', (task_id, new_status, operator, note or f'状态更新为{new_status}'))

            self.conn.commit()
            return {'success': True}
            
        except Exception as e:
            self.conn.rollback()
            return {'success': False, 'error': str(e)}

    def get_company_id_by_name(self, company_name):
        """根据公司名称获取公司ID"""
        if not self.cursor:
            return None

        try:
            self.cursor.execute("SELECT id FROM Company WHERE name = ?", (company_name,))
            row = self.cursor.fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f'获取公司ID失败: {str(e)}')
            return None

    def assign_vehicle(self, task_id, vehicle_data):
        """分配车辆到任务"""
        if not self.cursor:
            return {'success': False, 'error': '数据库未连接'}

        try:
            self.cursor.execute('''
            INSERT INTO vehicles (task_id, manifest_number, manifest_serial, dispatch_number, license_plate, carriage_number)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                task_id,
                vehicle_data['manifest_number'],
                vehicle_data['manifest_serial'],
                vehicle_data['dispatch_number'],
                vehicle_data['license_plate'],
                vehicle_data.get('carriage_number')
            ))

            self.conn.commit()
            return {'success': True}
            
        except Exception as e:
            self.conn.rollback()
            return {'success': False, 'error': str(e)}

    def get_dispatch_task_detail(self, task_id):
        """获取派车任务详情"""
        if not self.cursor:
            return None

        try:
            self.cursor.execute('''
            SELECT * FROM manual_dispatch_tasks WHERE task_id = ?
            ''', (task_id,))
            
            row = self.cursor.fetchone()
            if row:
                columns = [description[0] for description in self.cursor.description]
                return dict(zip(columns, row))
            return None
            
        except Exception as e:
            print(f'获取任务详情失败: {str(e)}')
            return None

    def get_task_status_history(self, task_id):
        """获取任务状态变更历史"""
        if not self.cursor:            return []

        try:
            self.cursor.execute('''
            SELECT * FROM dispatch_status_history 
            WHERE task_id = ? 
            ORDER BY timestamp ASC
            ''', (task_id,))
            
            columns = [description[0] for description in self.cursor.description]
            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]
            
        except Exception as e:
            print(f'获取状态历史失败: {str(e)}')
            return []

    @staticmethod
    def init_database():
        """静态方法：初始化数据库，创建所有缺失的表"""
        try:
            db_manager = DatabaseManager()
            if db_manager.connect():
                # 创建人工派车相关表
                db_manager.create_manual_dispatch_tables()
                print("✅ 数据库初始化完成")
                db_manager.disconnect()
                return True
            else:
                print("❌ 数据库连接失败")
                return False
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
            return False

    def update_manual_dispatch_tables(self):
        """更新现有表结构，添加双轨派车所需字段"""
        if not self.cursor:
            print('数据库未连接')
            return False

        try:
            # 检查现有表结构并添加缺失字段
            self.cursor.execute("PRAGMA table_info(manual_dispatch_tasks)")
            existing_columns = [row[1] for row in self.cursor.fetchall()]
            
            new_columns = [
                ("dispatch_track", "TEXT CHECK(dispatch_track IN ('轨道A', '轨道B')) NOT NULL DEFAULT '轨道A'"),
                ("initiator_role", "TEXT CHECK(initiator_role IN ('车间地调', '区域调度员', '超级管理员')) NOT NULL DEFAULT '车间地调'"),
                ("initiator_user_id", "INTEGER NOT NULL DEFAULT 1"),
                ("initiator_department", "TEXT"),
                ("audit_required", "BOOLEAN DEFAULT 1"),
                ("auditor_role", "TEXT"),
                ("assigned_supplier_id", "INTEGER"),
                ("auditor_user_id", "INTEGER"),
                ("audit_status", "TEXT CHECK(audit_status IN ('待审核', '已通过', '已拒绝')) DEFAULT '待审核'"),
                ("audit_time", "TEXT"),
                ("audit_note", "TEXT"),
                ("current_handler_role", "TEXT"),
                ("current_handler_user_id", "INTEGER")
            ]
            
            for column_name, column_def in new_columns:
                if column_name not in existing_columns:
                    self.cursor.execute(f"ALTER TABLE manual_dispatch_tasks ADD COLUMN {column_name} {column_def}")
                    print(f"✅ 添加字段: {column_name}")
                else:
                    print(f"⏭️ 字段已存在: {column_name}")
            
            # 添加外键约束
            if "auditor_user_id" in existing_columns:
                # 检查是否已存在外键约束
                self.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='manual_dispatch_tasks'")
                table_sql = self.cursor.fetchone()[0]
                if "auditor_user_id" in table_sql and "REFERENCES User(id)" not in table_sql and "REFERENCES users(id)" not in table_sql:
                    print("注意：无法直接添加外键约束，需要重新创建表")
            
            # 添加索引
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_manual_dispatch_status ON manual_dispatch_tasks(status)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_manual_dispatch_date ON manual_dispatch_tasks(required_date)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_manual_dispatch_initiator ON manual_dispatch_tasks(initiator_user_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_manual_dispatch_auditor ON manual_dispatch_tasks(auditor_user_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_manual_dispatch_handler ON manual_dispatch_tasks(current_handler_user_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_manual_dispatch_track ON manual_dispatch_tasks(dispatch_track)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_manual_dispatch_supplier ON manual_dispatch_tasks(assigned_supplier_id)")
            
            self.conn.commit()
            print("✅ 表结构更新完成")
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ 更新表结构失败: {str(e)}")
            return False

    def create_tables(self):
        """
        初始化所有数据库表
        包括用户管理、公司管理、人工派车等所有表
        """
        if not self.connect():
            return False
        
        try:
            # 创建用户管理相关表
            self.create_user_tables()
            print("✅ 用户管理相关表创建成功")
            
            # 创建人工派车相关表
            self.create_manual_dispatch_tables()
            print("✅ 人工派车相关表创建成功")
            
            # 更新现有表结构（添加双轨派车字段）
            self.update_manual_dispatch_tables()
            print("✅ 表结构更新完成")
            
            # 验证和更新状态字段
            self.validate_and_update_status_fields()
            print("✅ 状态字段验证完成")
            
            # 插入默认数据
            self.insert_default_data()
            
            return True
        except Exception as e:
            print(f"❌ 初始化表失败: {str(e)}")
            self.conn.rollback()
            return False

    def validate_and_update_status_fields(self):
        """验证和更新状态字段，确保使用新的清晰命名"""
        if not self.cursor:
            print('数据库未连接')
            return False

        try:
            # 检查状态字段约束
            self.cursor.execute("PRAGMA table_info(manual_dispatch_tasks)")
            columns = self.cursor.fetchall()
            
            status_column = next((col for col in columns if col[1] == 'status'), None)
            if status_column:
                print(f"✅ 状态字段类型: {status_column[2]}")
                
                # 检查是否有CHECK约束
                if 'CHECK' not in str(status_column[2]).upper():
                    print("⚠️ 状态字段缺少CHECK约束")
                else:
                    print("✅ 状态字段包含CHECK约束")
            
            # 验证当前数据中的状态值
            self.cursor.execute("SELECT DISTINCT status FROM manual_dispatch_tasks")
            current_statuses = [row[0] for row in self.cursor.fetchall()]
            valid_statuses = ['待提交', '待调度员审核', '待供应商响应', '供应商已响应', '车间已核查', '供应商已确认', '任务结束', '已取消']
            
            invalid_statuses = [status for status in current_statuses if status and status not in valid_statuses]
            if invalid_statuses:
                print(f"⚠️ 发现无效状态值: {invalid_statuses}")
                # 更新无效状态为最接近的有效状态
                status_mapping = {
                    '待区域调度员审核': '待调度员审核',
                    '待承运商响应': '待供应商响应',
                    '已响应': '供应商已响应',
                    '已发车': '车间已核查',
                    '已到达': '供应商已确认',
                    '已完成': '任务结束'
                }
                
                for old_status, new_status in status_mapping.items():
                    if old_status in invalid_statuses:
                        self.cursor.execute("UPDATE manual_dispatch_tasks SET status = ? WHERE status = ?", (new_status, old_status))
                        print(f"✅ 更新状态: {old_status} → {new_status}")
            else:
                print("✅ 所有状态值均有效")
            
            self.conn.commit()
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ 验证状态字段失败: {str(e)}")
            return False

    def create_user_tables(self):
        """创建用户管理相关表"""
        if not self.cursor:
            print('数据库未连接')
            return False

        try:
            # 创建单位表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Company (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                bank_name TEXT,
                account_number TEXT,
                address TEXT,
                contact_person TEXT,
                contact_phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 创建用户表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS User (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                full_name TEXT,
                email TEXT,
                phone TEXT,
                company_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES Company (id)
            )
            ''')

            # 创建角色表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Role (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 创建权限表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Permission (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                module TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # 创建用户角色关联表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS UserRole (
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, role_id),
                FOREIGN KEY (user_id) REFERENCES User (id) ON DELETE CASCADE,
                FOREIGN KEY (role_id) REFERENCES Role (id) ON DELETE CASCADE
            )
            ''')

            # 创建角色权限关联表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS RolePermission (
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                PRIMARY KEY (role_id, permission_id),
                FOREIGN KEY (role_id) REFERENCES Role (id) ON DELETE CASCADE,
                FOREIGN KEY (permission_id) REFERENCES Permission (id) ON DELETE CASCADE
            )
            ''')

            # 创建模块表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS modules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                route_name TEXT,
                icon_class TEXT,
                sort_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                parent_id INTEGER,
                FOREIGN KEY (parent_id) REFERENCES modules (id) ON DELETE SET NULL
            )
            ''')

            # 添加索引提升查询性能
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_username ON User(username)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_role_name ON Role(name)')
            self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_permission_module ON Permission(module)')

            self.conn.commit()
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f'创建用户管理相关表失败: {str(e)}')
            return False

    def insert_default_data(self):
        """插入默认角色、权限和管理员用户，并配置角色权限"""
        if not self.cursor:
            return False

        try:
            # 1. 插入默认角色（包含init_permissions.py中的车间地调角色）
            roles = [
                ('超级管理员', '系统最高权限管理员'),
                ('区域调度员', '负责区域内调度管理'),
                ('对账人员', '负责财务对账工作'),
                ('供应商', '外部供应商账户'),
                ('车间地调', '负责车间车辆需求与供应商车辆审批')
            ]
            self.cursor.executemany('INSERT OR IGNORE INTO Role (name, description) VALUES (?, ?)', roles)

            # 2. 插入默认权限
            permissions = [
                ('user_manage', 'user_management', '用户管理权限'),
                ('role_manage', 'user_management', '角色管理权限'),
                ('permission_manage', 'system', '权限管理权限'),
                ('basic_data_view', 'basic_data', '基础数据查看权限'),
                ('basic_data_edit', 'basic_data', '基础数据编辑权限'),
                ('planning_view', 'planning', '规划数据查看权限'),
                ('planning_edit', 'planning', '规划数据编辑权限'),
                ('cost_view', 'cost_analysis', '成本数据查看权限'),
                ('cost_manage', 'cost_analysis', '成本数据管理权限'),
                ('schedule_view', 'scheduling', '调度数据查看权限'),
                ('schedule_manage', 'scheduling', '调度数据管理权限'),
                ('reconciliation_view', 'reconciliation', '对账数据查看权限'),
                ('reconciliation_manage', 'reconciliation', '对账数据管理权限')
            ]
            self.cursor.executemany('INSERT OR IGNORE INTO Permission (name, module, description) VALUES (?, ?, ?)', permissions)

            # 3. 插入默认模块
            modules = [
                ('dashboard', '控制面板', 'dashboard', 'fas fa-tachometer-alt', 1, 1, None),
                ('system_settings', '系统设置', 'system_bp.system_settings', 'fas fa-cog', 90, 1, None),
                ('user_management', '用户管理', 'system_bp.manage_users', 'fas fa-users', 95, 1, None),
                ('role_permissions', '角色权限配置', 'system_bp.role_permissions', 'fas fa-shield-alt', 99, 1, None)
            ]
            self.cursor.executemany('''
                INSERT OR IGNORE INTO modules 
                (name, display_name, route_name, icon_class, sort_order, is_active, parent_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', modules)

            # 4. 插入默认管理员用户
            admin_username = 'admin'
            admin_password = 'admin123'
            admin_fullname = '系统管理员'
            admin_email = 'admin@example.com'

            # 检查用户是否已存在
            self.cursor.execute('SELECT id FROM User WHERE username = ?', (admin_username,))
            if not self.cursor.fetchone():
                # 对密码进行哈希处理
                from werkzeug.security import generate_password_hash
                hashed_password = generate_password_hash(admin_password)
                
                self.cursor.execute('''
                    INSERT INTO User (username, password, full_name, email, is_active)
                    VALUES (?, ?, ?, ?, ?)
                ''', (admin_username, hashed_password, admin_fullname, admin_email, True))
                
                admin_user_id = self.cursor.lastrowid
                
                # 获取超级管理员角色ID
                self.cursor.execute('SELECT id FROM Role WHERE name = ?', ('超级管理员',))
                admin_role = self.cursor.fetchone()
                
                if admin_role:
                    admin_role_id = admin_role[0]
                    # 分配角色给用户
                    self.cursor.execute('INSERT OR IGNORE INTO UserRole (user_id, role_id) VALUES (?, ?)', 
                                 (admin_user_id, admin_role_id))
                    
                    # 为超级管理员分配所有权限
                    self.cursor.execute('SELECT id FROM Permission')
                    permission_ids = [row[0] for row in self.cursor.fetchall()]
                    role_permissions = [(admin_role_id, pid) for pid in permission_ids]
                    self.cursor.executemany('INSERT OR IGNORE INTO RolePermission (role_id, permission_id) VALUES (?, ?)', 
                                     role_permissions)

            # 5. 插入默认承运公司数据
            companies = [
                ('XX物流有限公司', 'XX物流', '13800138000'),
                ('YY运输集团', 'YY运输', '13900139000'),
                ('ZZ货运公司', 'ZZ货运', '13700137000')
            ]
            self.cursor.executemany('''
                INSERT OR IGNORE INTO Company (name, contact_person, contact_phone)
                VALUES (?, ?, ?)
            ''', companies)

            # 6. 配置角色权限（整合init_permissions.py的功能）
            self._configure_role_permissions()

            self.conn.commit()
            print("✅ 默认数据插入成功")
            return True
            
        except Exception as e:
            self.conn.rollback()
            print(f"❌ 默认数据插入失败: {str(e)}")
            return False

    def _configure_role_permissions(self):
        """配置角色权限（整合自init_permissions.py）"""
        # 角色权限配置映射
        ROLE_PERMISSIONS_CONFIG = {
            '超级管理员': [
                'user_manage', 'role_manage', 'permission_manage',
                'basic_data_view', 'basic_data_edit',
                'planning_view', 'planning_edit',
                'cost_view', 'cost_manage',
                'schedule_view', 'schedule_manage',
                'reconciliation_view', 'reconciliation_manage'
            ],
            '区域调度员': [
                'basic_data_view', 'planning_view', 
                'schedule_view', 'reconciliation_view'
            ],
            '对账人员': [
                'basic_data_view', 'cost_view', 'reconciliation_view'
            ],
            '供应商': [
                'schedule_view', 'reconciliation_view'
            ],
            '车间地调': [
                'basic_data_view', 'schedule_view'
            ]
        }

        # 获取所有权限的ID映射
        self.cursor.execute('SELECT id, name FROM Permission')
        permission_map = {row[1]: row[0] for row in self.cursor.fetchall()}
        
        # 获取所有角色的ID映射
        self.cursor.execute('SELECT id, name FROM Role')
        role_map = {row[1]: row[0] for row in self.cursor.fetchall()}
        
        configured_count = 0
        
        for role_name, permission_names in ROLE_PERMISSIONS_CONFIG.items():
            if role_name not in role_map:
                continue
                
            role_id = role_map[role_name]
            
            for permission_name in permission_names:
                if permission_name not in permission_map:
                    continue
                    
                permission_id = permission_map[permission_name]
                
                self.cursor.execute('''
                    INSERT OR IGNORE INTO RolePermission (role_id, permission_id)
                    VALUES (?, ?)
                ''', (role_id, permission_id))
                
                if self.cursor.rowcount > 0:
                    configured_count += 1
        
        if configured_count > 0:
            print(f"✅ 配置了 {configured_count} 个角色权限关系")
        
        return True

    def check_and_fix_permissions(self):
        """检查并修复权限配置（整合自init_permissions.py）"""
        if not self.connect():
            print("❌ 数据库连接失败，无法检查权限")
            return False
        
        try:
            # 检查角色权限是否完整
            self.cursor.execute('''
                SELECT r.name, COUNT(rp.permission_id) as permission_count
                FROM Role r
                LEFT JOIN RolePermission rp ON r.id = rp.role_id
                GROUP BY r.id, r.name
            ''')
            
            roles_with_permissions = self.cursor.fetchall()
            
            needs_fix = False
            ROLE_PERMISSIONS_CONFIG = {
                '超级管理员': 12, '区域调度员': 4, '对账人员': 3, 
                '供应商': 2, '车间地调': 2
            }
            
            for role_name, count in roles_with_permissions:
                expected_count = ROLE_PERMISSIONS_CONFIG.get(role_name, 0)
                if count != expected_count and expected_count > 0:
                    print(f"⚠️ 角色 {role_name} 权限不完整: 现有 {count}, 期望 {expected_count}")
                    needs_fix = True
            
            if needs_fix:
                print("🔄 检测到权限配置问题，开始修复...")
                self._configure_role_permissions()
                self.conn.commit()
                print("✅ 权限修复完成")
            else:
                print("✅ 权限配置检查完成，无需修复")
            
            return True
            
        except Exception as e:
            print(f"❌ 权限检查失败: {str(e)}")
            return False

# 使用示例
if __name__ == '__main__':
    # 创建数据库管理器实例
    db_manager = DatabaseManager()

    # 连接到数据库
    if db_manager.connect():
        # 列出所有表
        tables = db_manager.list_tables()
        print('数据库中的表:')
        for table in tables:
            print(f'  - {table}')

        # 检查用户表
        db_manager.check_user_table()

        # 断开连接
        db_manager.disconnect()
    else:
        print('无法连接到数据库，检查文件是否存在。')

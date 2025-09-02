#!/usr/bin/env python3
"""
测试派车任务创建接口
"""
import requests
import json

def login():
    """登录获取session"""
    url = "http://127.0.0.1:5000/api/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        session = requests.Session()
        response = session.post(url, json=login_data)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ 登录成功")
                return session
        print(f"登录失败: {response.text}")
        return None
    except Exception as e:
        print(f"登录异常: {e}")
        return None

def test_create_dispatch_task(session):
    """测试创建派车任务接口"""
    url = "http://127.0.0.1:5000/api/dispatch/tasks"
    
    # 测试数据 - 根据API设计文档的字段
    task_data = {
        "required_time": "2024-01-15T14:00",
        "start_location": "北京",
        "end_location": "上海",
        "carrier_company": "顺丰速运",
        "transport_type": "单程",
        "requirement_type": "正班",
        "volume": 10.5,
        "weight": 5,
        "special_requirements": "易碎物品，小心轻放"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = session.post(url, json=task_data, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"创建任务结果: {result}")
            return True
        else:
            print(f"请求失败: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print(f"原始响应: {response.text}")
        return False

if __name__ == "__main__":
    print("开始测试派车任务创建接口...")
    
    # 先登录获取session
    print("正在登录...")
    session = login()
    if not session:
        print("❌ 登录失败，无法继续测试")
        exit(1)
    
    # 测试创建任务
    success = test_create_dispatch_task(session)
    if success:
        print("✅ 测试成功！")
    else:
        print("❌ 测试失败！")
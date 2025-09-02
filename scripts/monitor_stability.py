#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统稳定性监控脚本
监控数据库迁移后的系统运行状态
"""

import time
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stability_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class StabilityMonitor:
    """系统稳定性监控类"""
    
    def __init__(self, db_path: str = 'database.db'):
        """
        初始化监控器
        
        参数:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.metrics = {
            'database_connections': 0,
            'query_executions': 0,
            'failed_queries': 0,
            'response_times': [],
            'start_time': datetime.now()
        }
    
    def check_database_health(self) -> Dict[str, Any]:
        """
        检查数据库健康状态
        
        返回:
            Dict: 包含健康状态信息的字典
        """
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'database_file_exists': False,
            'tables_accessible': False,
            'connection_test': False,
            'table_count': 0,
            'error': None
        }
        
        try:
            # 检查数据库文件是否存在
            import os
            health_status['database_file_exists'] = os.path.exists(self.db_path)
            
            if health_status['database_file_exists']:
                # 测试数据库连接
                conn = sqlite3.connect(self.db_path)
                health_status['connection_test'] = True
                
                # 获取表数量
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                health_status['table_count'] = len(tables)
                health_status['tables_accessible'] = health_status['table_count'] > 0
                
                conn.close()
                
                logger.info(f"数据库健康检查通过: {health_status['table_count']} 个表")
            else:
                logger.warning(f"数据库文件不存在: {self.db_path}")
                
        except Exception as e:
            health_status['error'] = str(e)
            logger.error(f"数据库健康检查失败: {e}")
        
        return health_status
    
    def monitor_performance(self, query: str, params: tuple = None) -> Dict[str, Any]:
        """
        监控查询性能
        
        参数:
            query: SQL查询语句
            params: 查询参数
            
        返回:
            Dict: 包含性能指标和结果的字典
        """
        performance_data = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'execution_time': 0.0,
            'success': False,
            'result_count': 0,
            'error': None
        }
        
        try:
            start_time = time.time()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            performance_data['result_count'] = len(results)
            performance_data['execution_time'] = time.time() - start_time
            performance_data['success'] = True
            
            conn.close()
            
            # 记录性能指标
            self.metrics['query_executions'] += 1
            self.metrics['response_times'].append(performance_data['execution_time'])
            
            logger.info(f"查询执行成功: {performance_data['execution_time']:.4f}秒, {performance_data['result_count']} 条结果")
            
        except Exception as e:
            performance_data['error'] = str(e)
            self.metrics['failed_queries'] += 1
            logger.error(f"查询执行失败: {e}")
        
        return performance_data
    
    def generate_report(self, duration_hours: int = 24) -> Dict[str, Any]:
        """
        生成稳定性报告
        
        参数:
            duration_hours: 报告时间范围（小时）
            
        返回:
            Dict: 稳定性报告
        """
        report = {
            'report_time': datetime.now().isoformat(),
            'monitoring_period': f"{duration_hours}小时",
            'total_queries': self.metrics['query_executions'],
            'failed_queries': self.metrics['failed_queries'],
            'success_rate': 0.0,
            'avg_response_time': 0.0,
            'max_response_time': 0.0,
            'min_response_time': float('inf'),
            'recommendations': []
        }
        
        # 计算成功率
        if report['total_queries'] > 0:
            report['success_rate'] = (1 - report['failed_queries'] / report['total_queries']) * 100
        
        # 计算响应时间统计
        if self.metrics['response_times']:
            report['avg_response_time'] = sum(self.metrics['response_times']) / len(self.metrics['response_times'])
            report['max_response_time'] = max(self.metrics['response_times'])
            report['min_response_time'] = min(self.metrics['response_times'])
        
        # 生成建议
        if report['success_rate'] < 95:
            report['recommendations'].append("数据库错误率较高，建议检查数据库连接和查询语句")
        
        if report['avg_response_time'] > 0.1:  # 100ms
            report['recommendations'].append("平均响应时间较长，建议优化数据库查询和索引")
        
        if report['max_response_time'] > 1.0:  # 1秒
            report['recommendations'].append("存在慢查询，建议分析并优化相关SQL语句")
        
        logger.info(f"生成稳定性报告: 成功率 {report['success_rate']:.1f}%, 平均响应时间 {report['avg_response_time']:.4f}秒")
        
        return report

def main():
    """主监控函数"""
    print("=== 系统稳定性监控启动 ===")
    
    # 创建监控器实例
    monitor = StabilityMonitor()
    
    # 检查数据库健康状态
    health_status = monitor.check_database_health()
    print(f"数据库健康状态: {health_status}")
    
    if not health_status['database_file_exists']:
        print("❌ 数据库文件不存在，监控终止")
        return
    
    # 执行一些测试查询来监控性能
    test_queries = [
        "SELECT name FROM sqlite_master WHERE type='table'",
        "SELECT COUNT(*) FROM User",
        "SELECT COUNT(*) FROM manual_dispatch_tasks",
        "SELECT status, COUNT(*) FROM manual_dispatch_tasks GROUP BY status"
    ]
    
    print("\n=== 执行性能测试查询 ===")
    for i, query in enumerate(test_queries, 1):
        print(f"执行查询 {i}/{len(test_queries)}: {query[:50]}...")
        performance = monitor.monitor_performance(query)
        print(f"  结果: {performance['result_count']} 条, 耗时: {performance['execution_time']:.4f}秒")
    
    # 生成并显示报告
    print("\n=== 稳定性报告 ===")
    report = monitor.generate_report()
    for key, value in report.items():
        if key != 'recommendations':
            print(f"{key}: {value}")
    
    print("\n=== 建议 ===")
    for recommendation in report['recommendations']:
        print(f"• {recommiondation}")
    
    print("\n✅ 监控完成，详细日志请查看 stability_monitor.log")

if __name__ == "__main__":
    main()
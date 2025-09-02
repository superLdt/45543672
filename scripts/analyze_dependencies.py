"""
依赖关系分析脚本

用于分析项目中所有引用 db_manager.py 的文件
为数据库重构提供依赖关系图
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set
import json


def find_python_files(directory: str) -> List[str]:
    """
    查找目录中的所有Python文件
    
    参数:
        directory: 要搜索的目录路径
        
    返回:
        List[str]: Python文件路径列表
    """
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files


def analyze_file_dependencies(file_path: str, target_patterns: List[str]) -> Dict:
    """
    分析单个文件的依赖关系
    
    参数:
        file_path: 文件路径
        target_patterns: 要搜索的目标模式列表
        
    返回:
        Dict: 依赖关系分析结果
    """
    result = {
        'file': file_path,
        'dependencies': [],
        'import_lines': [],
        'usage_lines': []
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # 检查导入语句
                if any(pattern in line_stripped for pattern in target_patterns):
                    result['import_lines'].append({
                        'line_number': i,
                        'content': line_stripped
                    })
                
                # 检查使用情况（类名、函数名等）
                if 'DatabaseManager' in line_stripped or 'db_manager' in line_stripped:
                    # 排除注释行
                    if not line_stripped.startswith('#'):
                        result['usage_lines'].append({
                            'line_number': i,
                            'content': line_stripped
                        })
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        result['error'] = str(e)
    
    # 如果有相关行，则认为有依赖
    if result['import_lines'] or result['usage_lines']:
        result['has_dependency'] = True
    else:
        result['has_dependency'] = False
    
    return result


def analyze_project_dependencies(project_root: str) -> Dict:
    """
    分析整个项目的依赖关系
    
    参数:
        project_root: 项目根目录
        
    返回:
        Dict: 项目依赖关系分析结果
    """
    # 要搜索的目标模式
    target_patterns = [
        'from db_manager',
        'import db_manager',
        'from .db_manager',
        'import .db_manager'
    ]
    
    python_files = find_python_files(project_root)
    
    results = {
        'total_files': len(python_files),
        'files_with_dependencies': 0,
        'dependency_details': [],
        'summary': {}
    }
    
    for file_path in python_files:
        # 跳过db_manager.py本身和测试文件
        if 'db_manager.py' in file_path or 'test_' in file_path or 'tests/' in file_path:
            continue
            
        analysis = analyze_file_dependencies(file_path, target_patterns)
        
        if analysis['has_dependency']:
            results['files_with_dependencies'] += 1
            results['dependency_details'].append(analysis)
    
    # 生成摘要统计
    results['summary'] = {
        'dependency_files_count': results['files_with_dependencies'],
        'dependency_ratio': f"{results['files_with_dependencies'] / results['total_files'] * 100:.1f}%" if results['total_files'] > 0 else '0%'
    }
    
    return results


def generate_dependency_report(results: Dict, output_file: str = None) -> str:
    """
    生成依赖关系报告
    
    参数:
        results: 分析结果
        output_file: 输出文件路径（可选）
        
    返回:
        str: 报告内容
    """
    report = []
    
    # 报告头部
    report.append("=" * 80)
    report.append("📊 数据库管理器依赖关系分析报告")
    report.append("=" * 80)
    report.append(f"分析时间: {os.path.basename(__file__)}")
    report.append(f"项目根目录: {os.path.abspath('.')}")
    report.append(f"总Python文件数: {results['total_files']}")
    report.append(f"有依赖的文件数: {results['files_with_dependencies']}")
    report.append(f"依赖比例: {results['summary']['dependency_ratio']}")
    report.append("")
    
    # 详细依赖信息
    if results['dependency_details']:
        report.append("🔍 详细依赖关系:")
        report.append("-" * 40)
        
        for detail in results['dependency_details']:
            relative_path = os.path.relpath(detail['file'])
            report.append(f"\n📁 文件: {relative_path}")
            
            if detail['import_lines']:
                report.append("  📎 导入语句:")
                for imp in detail['import_lines']:
                    report.append(f"     第 {imp['line_number']} 行: {imp['content']}")
            
            if detail['usage_lines']:
                report.append("  🔧 使用情况:")
                for usage in detail['usage_lines']:
                    report.append(f"     第 {usage['line_number']} 行: {usage['content']}")
    else:
        report.append("✅ 未发现对 db_manager.py 的依赖")
    
    # 重构建议
    report.append("")
    report.append("=" * 80)
    report.append("🚀 重构建议")
    report.append("=" * 80)
    
    if results['files_with_dependencies'] > 0:
        report.append("基于分析结果，建议按以下顺序进行重构：")
        report.append("")
        report.append("1. 🟢 低风险文件（工具脚本、测试文件）")
        report.append("2. 🟡 中风险文件（业务模块、工具函数）")
        report.append("3. 🔴 高风险文件（核心应用、API接口）")
        report.append("")
        report.append("具体重构步骤：")
        report.append("1. 创建兼容层（services/db_manager_compat.py）")
        report.append("2. 逐步替换导入语句")
        report.append("3. 测试功能完整性")
        report.append("4. 移除旧版依赖")
    else:
        report.append("✅ 无需重构，项目中没有对 db_manager.py 的依赖")
    
    report_content = '\n'.join(report)
    
    # 输出到文件
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"✅ 报告已保存到: {output_file}")
        except Exception as e:
            print(f"❌ 保存报告失败: {e}")
    
    return report_content


def export_dependency_graph(results: Dict, output_file: str) -> None:
    """
    导出依赖关系图（JSON格式）
    
    参数:
        results: 分析结果
        output_file: 输出文件路径
    """
    graph_data = {
        'nodes': [],
        'links': []
    }
    
    # 添加中心节点（db_manager.py）
    graph_data['nodes'].append({
        'id': 'db_manager.py',
        'name': 'db_manager.py',
        'type': 'core',
        'value': 10
    })
    
    # 添加依赖节点
    for detail in results['dependency_details']:
        file_name = os.path.basename(detail['file'])
        relative_path = os.path.relpath(detail['file'])
        
        graph_data['nodes'].append({
            'id': relative_path,
            'name': file_name,
            'type': 'dependency',
            'value': len(detail['import_lines']) + len(detail['usage_lines'])
        })
        
        graph_data['links'].append({
            'source': 'db_manager.py',
            'target': relative_path,
            'value': len(detail['import_lines']) + len(detail['usage_lines'])
        })
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)
        print(f"✅ 依赖关系图已导出到: {output_file}")
    except Exception as e:
        print(f"❌ 导出依赖关系图失败: {e}")


def main():
    """主函数"""
    project_root = '.'  # 当前目录作为项目根目录
    
    print("🔍 开始分析项目依赖关系...")
    
    # 分析依赖关系
    results = analyze_project_dependencies(project_root)
    
    # 生成文本报告
    report_file = os.path.join(project_root, 'dependency_analysis_report.txt')
    report_content = generate_dependency_report(results, report_file)
    
    # 导出JSON格式的依赖关系图
    graph_file = os.path.join(project_root, 'dependency_graph.json')
    export_dependency_graph(results, graph_file)
    
    # 在控制台显示摘要
    print("\n" + "=" * 60)
    print("📋 分析摘要")
    print("=" * 60)
    print(f"总文件数: {results['total_files']}")
    print(f"有依赖的文件数: {results['files_with_dependencies']}")
    print(f"依赖比例: {results['summary']['dependency_ratio']}")
    
    if results['files_with_dependencies'] > 0:
        print(f"\n📁 依赖文件列表:")
        for detail in results['dependency_details']:
            print(f"  - {os.path.relpath(detail['file'])}")
    
    print(f"\n✅ 分析完成！详细报告请查看: {report_file}")
    
    return results


if __name__ == '__main__':
    main()
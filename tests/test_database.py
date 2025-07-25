"""
数据库模块测试
"""

import sys
import os
import tempfile
import shutil

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.database import DatabaseManager


def test_database_initialization():
    """测试数据库初始化"""
    print("测试数据库初始化...")
    
    # 创建临时目录用于测试
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    
    try:
        # 创建数据库管理器
        db_manager = DatabaseManager(db_path)
        
        assert db_manager is not None, "数据库管理器创建失败"
        assert os.path.exists(db_path), "数据库文件未创建"
        
        # 验证表是否创建
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ["tasks", "task_results", "config"]
            for table in expected_tables:
                assert table in tables, f"表 {table} 未创建"
        
        print("数据库初始化测试通过")
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


def test_task_management():
    """测试任务管理"""
    print("测试任务管理...")
    
    # 创建临时目录用于测试
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    
    try:
        # 创建数据库管理器
        db_manager = DatabaseManager(db_path)
        
        # 创建任务
        success = db_manager.create_task("task-001", "测试任务1")
        assert success, "任务创建失败"
        
        # 重复创建应该失败
        success = db_manager.create_task("task-001", "测试任务1重复")
        assert not success, "重复任务创建应该失败"
        
        # 创建带父任务的子任务
        success = db_manager.create_task("task-002", "测试任务2", "task-001")
        assert success, "子任务创建失败"
        
        # 获取任务
        task = db_manager.get_task("task-001")
        assert task is not None, "获取任务失败"
        assert task["task_id"] == "task-001", "任务ID不正确"
        assert task["description"] == "测试任务1", "任务描述不正确"
        
        # 获取子任务
        subtasks = db_manager.get_tasks_by_parent("task-001")
        assert len(subtasks) == 1, "子任务数量不正确"
        assert subtasks[0]["task_id"] == "task-002", "子任务ID不正确"
        
        # 更新任务状态
        success = db_manager.update_task_status("task-001", "completed")
        assert success, "任务状态更新失败"
        
        # 验证任务状态更新
        task = db_manager.get_task("task-001")
        assert task["status"] == "completed", "任务状态未更新"
        
        print("任务管理测试通过")
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


def test_task_result_management():
    """测试任务结果管理"""
    print("测试任务结果管理...")
    
    # 创建临时目录用于测试
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    
    try:
        # 创建数据库管理器
        db_manager = DatabaseManager(db_path)
        
        # 创建任务
        db_manager.create_task("task-001", "测试任务1")
        
        # 保存任务结果
        success = db_manager.save_task_result("task-001", "这是任务结果", "pending")
        assert success, "任务结果保存失败"
        
        # 获取任务结果
        result = db_manager.get_task_result("task-001")
        assert result is not None, "获取任务结果失败"
        assert result["result_content"] == "这是任务结果", "任务结果内容不正确"
        assert result["validation_status"] == "pending", "任务结果验证状态不正确"
        
        # 更新结果验证状态
        success = db_manager.update_result_validation_status("task-001", "approved")
        assert success, "结果验证状态更新失败"
        
        # 验证结果验证状态更新
        result = db_manager.get_task_result("task-001")
        assert result["validation_status"] == "approved", "结果验证状态未更新"
        
        print("任务结果管理测试通过")
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


def test_config_management():
    """测试配置管理"""
    print("测试配置管理...")
    
    # 创建临时目录用于测试
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    
    try:
        # 创建数据库管理器
        db_manager = DatabaseManager(db_path)
        
        # 设置配置项
        success = db_manager.set_config("api_key", "test-key", "测试API密钥")
        assert success, "配置项设置失败"
        
        # 获取配置项
        value = db_manager.get_config("api_key")
        assert value == "test-key", "配置项获取失败"
        
        # 获取不存在的配置项
        value = db_manager.get_config("nonexistent")
        assert value is None, "获取不存在的配置项应该返回None"
        
        # 获取所有配置项
        all_config = db_manager.get_all_config()
        assert "api_key" in all_config, "所有配置项中缺少api_key"
        assert all_config["api_key"] == "test-key", "所有配置项中的值不正确"
        
        # 更新配置项
        success = db_manager.set_config("api_key", "new-key")
        assert success, "配置项更新失败"
        
        value = db_manager.get_config("api_key")
        assert value == "new-key", "配置项更新后值不正确"
        
        # 删除配置项
        success = db_manager.delete_config("api_key")
        assert success, "配置项删除失败"
        
        value = db_manager.get_config("api_key")
        assert value is None, "删除配置项后应该返回None"
        
        print("配置管理测试通过")
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    print("开始数据库模块测试...")
    
    try:
        test_database_initialization()
        test_task_management()
        test_task_result_management()
        test_config_management()
        
        print("\n所有数据库模块测试通过!")
    except Exception as e:
        print(f"\n测试失败: {e}")
        sys.exit(1)
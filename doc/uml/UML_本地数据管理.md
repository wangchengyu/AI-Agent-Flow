# 本地数据管理模块UML图

## 类图
```mermaid
classDiagram
    class DatabaseManager {
        +initialize()
        +get_connection()
        +execute_query()
        +backup()
        +restore()
    }

    class TaskHistoryTable {
        +create_table()
        +insert_record()
        +query_records()
    }

    class SubTaskStateTable {
        +create_table()
        +update_state()
        +get_state()
    }

    class DataBackup {
        +create_backup()
        +restore_backup()
        +list_backups()
    }

    class QueryBuilder {
        +build_select()
        +build_insert()
        +build_update()
    }

    DatabaseManager --> TaskHistoryTable : 管理
    DatabaseManager --> SubTaskStateTable : 管理
    DatabaseManager --> DataBackup : 调用
    QueryBuilder --> DatabaseManager : 生成查询
```

## 序列图
```mermaid
sequenceDiagram
    participant TaskExecutor
    participant DatabaseManager
    participant TaskHistoryTable
    participant SubTaskStateTable

    TaskExecutor->>DatabaseManager: 开始事务
    DatabaseManager->>TaskHistoryTable: 插入任务记录
    TaskHistoryTable-->>DatabaseManager: 返回结果
    DatabaseManager->>SubTaskStateTable: 更新子任务状态
    SubTaskStateTable-->>DatabaseManager: 返回结果
    TaskExecutor->>DatabaseManager: 提交事务
    alt 数据量达到阈值
        DatabaseManager->>DataBackup: 执行数据归档
    end
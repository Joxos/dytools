# room_id 数据迁移指南

## 背景

你的数据库中有 **1,057,678 条记录**使用了旧的复合格式：

```
旧格式： 6657:6979222  (短ID:真实ID)
新格式： 6979222       (只保留真实ID)
```

这是之前代码 bug 导致的。新版本已修复，但需要迁移历史数据。

## 📊 当前数据统计

```
6657:6979222  →  6979222     1,056,697 条记录
9999:9999     →  9999            981 条记录
──────────────────────────────────────────
总计需要迁移：                  1,057,678 条记录
```

## 🛡️ 安全特性

✅ **事务安全**：所有更新在一个事务中完成，失败自动回滚  
✅ **Dry-run 模式**：先预览再执行  
✅ **自动验证**：执行后自动检查是否还有遗漏  
✅ **幂等性**：可以重复运行，只处理需要迁移的数据

## 📝 使用方法

### 方法 1：交互式脚本（推荐）

```bash
cd /home/Joxos/source/dytools
export DYTOOLS_DSN="postgresql://douyu:douyu6657@localhost:5432/douyu_danmu"

# 运行交互式迁移
./scripts/migrate_room_id.sh
```

脚本会：
1. 先运行 dry-run 显示预览
2. 询问是否继续
3. 提醒创建备份
4. 执行迁移并显示进度
5. 自动验证结果

### 方法 2：直接运行 Python 脚本

#### 步骤 1：预览（dry-run）

```bash
cd /home/Joxos/source/dytools
export DYTOOLS_DSN="postgresql://douyu:douyu6657@localhost:5432/douyu_danmu"

# 只看预览，不修改数据
uv run python scripts/migrate_room_id.py --dry-run
```

#### 步骤 2：创建备份（强烈推荐）

```bash
# 备份整个数据库
pg_dump "$DYTOOLS_DSN" > backup_$(date +%Y%m%d_%H%M%S).sql

# 或者只备份 danmaku 表
pg_dump "$DYTOOLS_DSN" -t danmaku > backup_danmaku_$(date +%Y%m%d_%H%M%S).sql
```

#### 步骤 3：执行迁移

```bash
# 执行迁移，显示详细进度
uv run python scripts/migrate_room_id.py --verbose
```

## 📤 预期输出

### Dry-run 输出

```
🔍 Analyzing room_id formats in database...

📋 Migration Preview:
======================================================================
Old Format           New Format         Records
----------------------------------------------------------------------
6657:6979222         6979222          1,056,697
9999:9999            9999                   981
----------------------------------------------------------------------
TOTAL                                 1,057,678
======================================================================

🔒 DRY RUN - No changes made
Run without --dry-run to perform migration
```

### 实际迁移输出

```
🔍 Analyzing room_id formats in database...

📋 Migration Preview:
======================================================================
Old Format           New Format         Records
----------------------------------------------------------------------
6657:6979222         6979222          1,056,697
9999:9999            9999                   981
----------------------------------------------------------------------
TOTAL                                 1,057,678
======================================================================

⚙️  Performing migration...
Migrating 6657:6979222 → 6979222... ✅ 1,056,697 records
Migrating 9999:9999 → 9999... ✅ 981 records

✅ Migration complete: 1,057,678 records updated

🔍 Verifying migration...
✅ Verification passed: No compound formats remaining
```

## ⏱️ 预计耗时

- **1,057,678 条记录**
- **预计速度**：~100,000 条/秒
- **预计总时间**：约 **10-15 秒**

实际时间取决于数据库性能和网络延迟。

## 🚨 故障恢复

### 如果迁移失败

由于使用了事务，失败会自动回滚，数据不会损坏。查看错误信息，修复问题后重新运行。

### 如果想回滚

如果之前创建了备份：

```bash
# 恢复整个数据库（注意：会删除当前数据！）
psql "$DYTOOLS_DSN" < backup_20260306_180000.sql

# 或者只恢复 danmaku 表
psql "$DYTOOLS_DSN" -c "TRUNCATE danmaku;"
psql "$DYTOOLS_DSN" < backup_danmaku_20260306_180000.sql
```

## ✅ 验证迁移结果

### 方法 1：使用脚本自动验证

脚本执行后会自动验证，看到这个表示成功：

```
✅ Verification passed: No compound formats remaining
```

### 方法 2：手动检查

```bash
# 连接数据库
psql "$DYTOOLS_DSN"

# 查看当前所有 room_id 格式
SELECT room_id, COUNT(*) as count 
FROM danmaku 
GROUP BY room_id 
ORDER BY count DESC 
LIMIT 10;
```

**预期结果**：应该看不到包含冒号（:）的 room_id

## 📋 完整操作清单

```bash
# 1. 进入项目目录
cd /home/Joxos/source/dytools

# 2. 设置数据库连接
export DYTOOLS_DSN="postgresql://douyu:douyu6657@localhost:5432/douyu_danmu"

# 3. 预览迁移（可选但推荐）
uv run python scripts/migrate_room_id.py --dry-run

# 4. 创建备份（强烈推荐）
pg_dump "$DYTOOLS_DSN" > backup_$(date +%Y%m%d_%H%M%S).sql

# 5. 执行迁移
uv run python scripts/migrate_room_id.py --verbose

# 6. 验证结果（脚本会自动验证，这是额外的手动检查）
psql "$DYTOOLS_DSN" -c "SELECT room_id, COUNT(*) FROM danmaku GROUP BY room_id HAVING room_id LIKE '%:%';"
# 如果返回 0 rows，说明迁移成功
```

## 🔗 相关文档

- [scripts/README.md](scripts/README.md) - 详细的英文技术文档
- [commit dba4ed1](.) - 修复 room_id bug 的提交

## ❓ 常见问题

### Q: 迁移过程中可以中断吗？

A: 可以 Ctrl+C 中断。由于使用事务，中断后不会有任何数据被修改。

### Q: 迁移后新采集的数据会是什么格式？

A: 新代码已经修复，会直接使用真实 ID（如 `6979222`），不会再出现复合格式。

### Q: 已经运行过一次迁移，能再运行一次吗？

A: 可以！脚本是幂等的，会自动跳过已迁移的数据。如果第二次运行看到 "No compound formats found"，说明所有数据都已迁移完成。

### Q: 迁移会影响正在运行的采集器吗？

A: 迁移过程会锁定相关行，但时间很短（10-15秒）。建议在采集器停止时迁移，或选择流量较小的时段。

### Q: 如果数据库很大（千万级），性能如何？

A: 脚本使用批量更新，性能很好。即使数据量更大，也只是时间稍长，不会有性能问题。可以加 `--verbose` 参数查看进度。

## 💡 建议的执行时机

1. **最佳**：在没有采集器运行时
2. **次佳**：在流量低峰期（凌晨）
3. **可接受**：任何时候（锁表时间很短，影响不大）

---

**准备好了吗？运行下面的命令开始迁移：**

```bash
cd /home/Joxos/source/dytools
export DYTOOLS_DSN="postgresql://douyu:douyu6657@localhost:5432/douyu_danmu"
./scripts/migrate_room_id.sh
```

祝顺利！🚀

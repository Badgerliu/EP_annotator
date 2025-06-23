# EP_annotator Performance Optimization Plan

## 🎯 优化目标
- Step 3: 从35秒优化到10-15秒 (60%性能提升)
- Step 5: 从20秒优化到5-8秒 (60%性能提升)
- 整体管道: 从79秒优化到45-50秒 (40%性能提升)
- 基因组信息扩增
- GO注释方案

## 🚨 Step 3: Associate Interactions with Peaks (最高优先级)

### 当前性能问题
- **测试数据**: 3.3M交互 + 219K峰 = 35秒
- **预计大数据**: 10M交互 + 500K峰 = 3-5分钟
- **瓶颈**: 多次bedtools调用 + 大量临时文件I/O

### 优化方案A: IntervalTree索引 (推荐)
```python
# 替换当前的bedtools方法
def optimized_associate_peaks(interactions, peaks):
    # 1. 预建立峰的IntervalTree索引 (一次性)
    peak_trees = build_interval_trees(peaks)  # O(m log m)
    
    # 2. 批量查询最近峰 (向量化)
    results = []
    for chunk in batch_interactions(interactions, 50000):  # 批处理
        chunk_results = find_closest_peaks_batch(chunk, peak_trees)  # O(n log m)
        results.extend(chunk_results)
    
    return results

# 预期性能提升: 35秒 → 12-15秒
```

### 优化方案B: 并行化处理
```python
# 按染色体并行处理
from concurrent.futures import ProcessPoolExecutor

def parallel_associate_peaks(interactions, peaks):
    # 1. 按染色体分组
    chrom_groups = group_by_chromosome(interactions)
    
    # 2. 并行处理每个染色体
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = []
        for chrom, chrom_interactions in chrom_groups.items():
            chrom_peaks = peaks[peaks['chr'] == chrom]
            future = executor.submit(associate_single_chrom, 
                                   chrom_interactions, chrom_peaks)
            futures.append(future)
        
        results = [f.result() for f in futures]
    
    return combine_results(results)

# 预期性能提升: 35秒 → 10-12秒 (4核CPU)
```

## ⚠️ Step 5: Annotate Query Peaks (中等优先级)

### 当前性能问题
- **测试数据**: 1000峰 + 563K交互 = 20秒
- **预计大数据**: 10K峰 + 2M交互 = 5-10分钟
- **瓶颈**: 嵌套循环 + pybedtools临时文件

### 优化方案: 预计算交互索引
```python
def optimized_annotate_peaks(peaks, interactions):
    # 1. 预建立交互端点的哈希索引
    endpoint_index = build_endpoint_index(interactions)  # O(n)
    
    # 2. 空间查询优化
    for peak in peaks:
        # 使用R-tree或类似结构快速查询
        nearby_endpoints = spatial_query(endpoint_index, peak, extend_bp)
        peak_annotations = process_endpoints(nearby_endpoints)
    
    return annotations

# 预期性能提升: 20秒 → 6-8秒
```

## ✅ Step 4: Generate E-P Index (已优化良好)

### 当前性能
- **测试数据**: 563K交互 = 8秒
- **处理速度**: 71K交互/秒
- **算法**: 已使用IntervalTree，性能良好

### 微调建议
```python
# 可考虑的小幅优化
def micro_optimize_step4():
    # 1. 预分配DataFrame容量
    # 2. 使用更快的字符串操作
    # 3. 批量写入而非逐行写入
    pass

# 预期提升: 8秒 → 6-7秒 (微幅)
```

## 📊 整体优化效果预测

### 优化前 (当前)
- Step 1: 5秒
- Step 2: 3秒  
- **Step 3: 35秒** ← 主要瓶颈
- Step 4: 8秒
- **Step 5: 20秒** ← 次要瓶颈
- Step 6: 8秒
- **总计: 79秒**

### 优化后 (预期)
- Step 1: 5秒
- Step 2: 3秒
- **Step 3: 12秒** ← 65%改进
- Step 4: 6秒
- **Step 5: 7秒** ← 65%改进  
- Step 6: 8秒
- **总计: 41秒** ← 48%整体改进

## 🛠️ 实施计划

### Phase 1: Step 3优化 (2-3天)
1. 实现IntervalTree方法
2. 添加批处理逻辑
3. 性能测试和调优
4. 保留bedtools作为fallback

### Phase 2: Step 5优化 (1-2天)  
1. 重构数据结构
2. 减少pybedtools依赖
3. 实现空间索引查询

### Phase 3: 整体测试 (1天)
1. 大数据集测试
2. 内存使用分析
3. 并发安全测试

## 📈 监控指标

### 性能指标
- 处理速度: 交互数/秒
- 内存峰值: 最大内存使用
- CPU利用率: 多核使用效率

### 质量指标  
- 结果一致性: 与原实现对比
- 数据完整性: 无丢失记录
- 错误率: 异常处理能力

## 💾 内存优化

### 大数据集处理策略
```python
# 流式处理大文件
def stream_process_large_files():
    # 1. 分块读取而非全量加载
    # 2. 及时释放中间结果
    # 3. 使用生成器减少内存占用
    pass

# 目标: 支持100M+交互记录处理
```

## 🔧 工具和依赖优化

### 可选择的高性能库
- **pybedtools** → **pyranges** (更快的区间操作)
- **pandas** → **polars** (更快的DataFrame操作)  
- **bedtools** → **直接算法** (减少子进程调用)

---
*此优化计划基于实际测试数据制定，预期在保持结果准确性的前提下显著提升性能。* 
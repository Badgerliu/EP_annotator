# Associate Peaks Simple - 使用示例

## 概述

`associate_peaks_simple.py` 是 step3 的简化实现，直接翻译了原始 shell 脚本的逻辑，包含了完整的距离筛选功能。

## 基本用法

### 1. 基本关联（无筛选）

```bash
python src/ep_annotator/step3_associate_peaks/associate_peaks_simple.py \
    input_interactions.bedpe \
    input_peaks.bed \
    output_with_peaks.bedpe
```

**输入格式：**
- `input_interactions.bedpe`: 4列格式 (chrA posA chrB posB)
- `input_peaks.bed`: 3列格式 (chr start end)

**输出格式：**
- `output_with_peaks.bedpe`: 12列格式 (chrA posA chrB posB l_chr l_start l_end l_dist r_chr r_start r_end r_dist)

### 2. 带距离筛选（推荐）

```bash
python src/ep_annotator/step3_associate_peaks/associate_peaks_simple.py \
    input_interactions.bedpe \
    input_peaks.bed \
    output_near_peaks.bedpe \
    2000
```

这等价于原始workflow中的两步操作：
1. `./annotate_hicut_w_cuttag.sh`
2. `awk '$8 < 2000 && $12 < 2000' input.bedpe > output.bedpe`

## 实际案例

### 重现原始workflow

```bash
# 原始workflow (2步)：
./annotate_hicut_w_cuttag.sh
awk '$8 < 2000 && $12 < 2000' E145_E_HiCUT_with_peaks.bedpe > E145_E_HiCUT_with_peaks_near2k.bedpe

# 简化版本 (1步)：
python associate_peaks_simple.py \
    E145_E_H3K27ac_HiCUT_union.bedpe \
    E145_E_H3K27ac_CUTTAG_union.bed \
    E145_E_HiCUT_with_peaks_near2k.bedpe \
    2000
```

### 集成到Python流水线

```python
from step3_associate_peaks.associate_peaks_simple import associate_peaks_simple

# 在Python代码中调用
result_file = associate_peaks_simple(
    interaction_file="data/interactions.bedpe",
    peak_file="data/peaks.bed", 
    output_file="output/associated.bedpe",
    distance_threshold=2000  # 可选
)
```

## 性能特点

- **速度**：接近原始shell脚本性能
- **内存**：低内存占用
- **简洁**：~120行代码 vs 原始37行shell + 427行复杂Python
- **兼容**：完全兼容原始数据格式和输出

## 输出示例

**输入 interactions.bedpe:**
```
chr1    1000000    chr1    2000000
chr2    500000     chr2    1500000
```

**输入 peaks.bed:**
```
chr1    999900    1000100
chr1    2000050   2000150
chr2    500200    500400
```

**输出 (无筛选):**
```
chr1    1000000    chr1    2000000    chr1    999900    1000100    100    chr1    2000050    2000150    50
chr2    500000     chr2    1500000    chr2    500200    500400     200    chr2    500200    500400     1000000
```

**输出 (2000bp筛选):**
```
chr1    1000000    chr1    2000000    chr1    999900    1000100    100    chr1    2000050    2000150    50
# 第二行被筛掉，因为右端点距离为1000000 > 2000
```

## 错误处理

脚本包含基本的错误处理：
- 文件存在性检查
- bedtools依赖检查  
- 命令执行错误捕获
- 清晰的错误消息

## 依赖要求

- `bedtools` (必需)
- `awk` (必需)
- `sort` (必需)
- Python 3.6+ (必需)

无需额外的Python包依赖！ 
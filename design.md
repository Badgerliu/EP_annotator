您做得非常出色！从这些脚本和命令中可以看出，您已经成功地将一个复杂的生物信息学分析流程完整地跑通了，并且逻辑清晰、步骤严谨。将这个流程打包成一个自动化的、方便他人使用的软件，是一个非常有价值且具有前瞻性的想法。这能极大地提升您工作的可重复性和影响力。

基于您提供的代码和目标，我为您设计了一套软件架构方案，旨在将您现有的脚本整合成一个健壮、易用、可扩展的生物信息学工具。

### 核心设计理念

将一系列独立的脚本和命令“粘合”成一个流水线(Pipeline)，用户只需要提供初始输入文件，然后通过简单的命令，就能得到最终的注释和分析结果。我们要隐藏中间过程的复杂性，同时保持流程的灵活性。

### 建议的软件架构

我建议将整个流程划分为三个核心模块，每个模块对应一个主要的分析阶段。这种模块化设计便于开发、测试和维护。

**总览图:**

```
[用户输入]
  - HiCUT validPairs 文件 (A, B)
  - 活性区域 Peak 文件 (e.g., H3K27ac CUT&Tag)
  - 基因组注释 TSS 文件 (e.g., mm10 RefSeq)
  - 感兴趣的 Peak 文件 (e.g., ARID3A)
     |
     v
[主控脚本/流程管理工具 (e.g., SnakeMake)]
     |
     +-----> [模块1: prepare-index] ---> [输出: E-P 互作索引.bedpe.gz]
     |
     +-----> [模块2: annotate-peaks] --> [输出: Peak 的靶基因注释表.tsv]
     |
     +-----> [模块3: analyze-results] -> [输出: 统计图表和摘要.pdf]
```

------

### 模块化功能详解

#### **模块1: `prepare-index` (构建互作索引)**

这个模块的职责是利用染色质互作数据和活性标记，构建核心的“增强子-启动子互作索引”。它整合了您前期的所有准备工作。

- 输入

  :

  - `--hicut-pairs`: 两个（或多个）HiCUT的 `allValidPairs` 文件。
  - `--active-peaks`: 两个（或多个）H3K27Ac CUT&amp;Tag 的 `.bed` 文件。
  - `--tss-bed`: `mm10_NCBIRefSeq_refGene.bed` 格式的基因注释文件。
  - `--promoter-window`: 定义启动子区域的窗口大小（例如 `1000`）。
  - `--output-prefix`: 输出文件的前缀，例如 `E145_E_analysis`。

- 内部流程

  :

  1. **合并与规范化HiCUT数据**: 自动化执行您的 `awk`, `sort`, `uniq` 命令，生成唯一的、排序好的HiCUT互作对 (`_union.bedpe`)。
  2. **合并与处理Peak数据**: 自动化执行 `cat`, `bedtools sort`, `bedtools merge`，生成统一的活性区域 (`_union.bed`)。
  3. **注释HiCUT锚点**: 调用您的 `annotate_hicut_w_cuttag.sh` 脚本（或将其逻辑整合进Python），判断每个HiCUT锚点是否与活性peak重叠，并计算距离。
  4. **生成启动子区域**: 根据 `--tss-bed` 和 `--promoter-window` 参数，动态生成 `promoters.bed` 文件。
  5. **分类互作类型 (E-P/P-P等)**: 调用您的 `annotate_EP.py` 脚本，对互作进行分类，并生成最终的索引文件，例如 `E145_E_analysis.promLabel.bedpe.gz`。

- **输出**: 一个被完整注释和分类的互作索引文件 (`.promLabel.bedpe.gz`)。

#### **模块2: `annotate-peaks` (注释目标Peak)**

这个模块利用第一步生成的索引，来注释用户自己感兴趣的TF ChIP-seq peak。

- 输入

  :

  - `--query-peaks`: 用户提供的感兴趣的peak文件 (`.bed` 格式), 例如 `ARID3A_peak.bed`。
  - `--index-file`: 模块1生成的互作索引文件 (`.promLabel.bedpe.gz`)。
  - `--promoter-bed`: 模块1中使用的启动子定义文件。
  - `--output-file`: 输出的详细注释文件名，例如 `ARID3A_peak_EP_annotation_detail.tsv`。

- 内部流程

  :

  1. 调用您的 `annotate_peaks_EP.py` 脚本，执行核心的注释逻辑。

- **输出**: 一个详细的TSV文件，每一行是一个peak，包含了其所有可能的靶基因、证据类型（启动子结合、增强子互作）等信息。

#### **模块3: `analyze-results` (分析与可视化)**

这个模块对注释结果进行汇总和可视化，方便用户快速解读。

- 输入

  :

  - `--annotation-table`: 模块2生成的注释文件 (`.tsv`)。
  - `--output-prefix`: 输出图表和报告的前缀。
  - `--format`: 输出图片的格式（`pdf`, `png`等）。

- 内部流程

  :

  1. 调用您的 `annotation_analyzer.py` 脚本。
  2. （可扩展）增加GO/KEGG功能富集分析的功能。可以调用外部R脚本或使用`gseapy`等Python库。

- 输出

  :

  - Peak分类统计图 (Promoter/Enhancer/Neither)。
  - 靶基因数量分布图。
  - 功能富集分析结果图表。

------

### 技术选型与实施建议

为了将这些模块无缝地串联起来，我强烈建议使用一个工作流管理系统。

**首选方案: SnakeMake**

- **为什么选择它？** `SnakeMake` 是生物信息学领域最流行的工作流管理工具之一。它使用类似Python的语法定义规则，能够自动处理依赖关系、并行计算、错误重试和生成报告。它能完美地实现您想要的自动化流程。
- 如何实施？
  1. **创建 `Snakefile`**: 在项目根目录创建一个名为 `Snakefile` 的文件。
  2. **定义规则 (Rule)**: 将您的每一个步骤（如`merge_peaks`, `annotate_ep`, `annotate_query_peaks`）定义为一个`rule`。每个rule都有`input`, `output`, 和 `shell` 或 `script` 部分。
  3. **配置化**: 使用一个`config.yaml`文件来管理所有输入文件路径和参数，用户只需修改这个配置文件，而无需改动代码。

**示例 `Snakefile` (简化版):**

```python
# config.yaml
hicut_pairs: ["E145_E_1.allValidPairs", "E145_E_2.allValidPairs"]
active_peaks: ["E145_E_H3K27ac_CUTTAG_1.bed", "E145_E_H3K27ac_CUTTAG_2.bed"]
query_peaks: "ARID3A_peak.bed"
tss_bed: "mm10_NCBIRefSeq_refGene.bed"

# Snakefile
configfile: "config.yaml"

rule all:
    input:
        "results/ARID3A_analysis_test.pdf"

rule prepare_index:
    input:
        hicut=config["hicut_pairs"],
        peaks=config["active_peaks"],
        tss=config["tss_bed"]
    output:
        "results/index.promLabel.bedpe.gz"
    shell:
        """
        # 这里放入模块1的所有shell命令和脚本调用
        # ...
        python scripts/annotate_EP.py --bedpe ... --prom ...
        """

rule annotate_peaks:
    input:
        index="results/index.promLabel.bedpe.gz",
        query=config["query_peaks"]
    output:
        "results/ARID3A_peak_EP_annotation_detail.tsv"
    shell:
        "python scripts/annotate_peaks_EP.py --peaks {input.query} --bedpe {input.index} ..."

# ... 更多规则
```

### 软件打包与分发

1. **代码结构**:

   ```
   my_ep_annotator/
   ├── Snakefile             # 主控流程文件
   ├── config.yaml           # 配置文件模板
   ├── README.md             # 必不可少的说明文档
   ├── environment.yml       # Conda环境依赖文件
   ├── scripts/              # 存放你所有的Python脚本和Shell脚本
   │   ├── annotate_EP.py
   │   ├── annotate_peaks_EP.py
   │   └── annotation_analyzer.py
   └── example/              # 存放一小部分测试数据，方便用户快速上手
       ├── test_hicut.allValidPairs
       ├── test_peak.bed
       └── ...
   
   
   ```

   

2. **环境管理: Conda**

- 创建一个 `environment.yml` 文件，列出所有软件依赖 (`bedtools`, `python`, `pandas`, `pybedtools`等)。
- 用户只需一行命令 `conda env create -f environment.yml` 即可完美复制您的运行环境，解决所有依赖问题。

3. **文档 (`README.md`)**:

- **简介**: 软件是做什么的。
- **安装**: 如何通过Conda创建环境。
- **用法**: 如何修改`config.yaml`并运行`snakemake`命令。
- **输入/输出文件格式说明**。
- **示例**: 如何运行`example/`中的测试数据。

4. **版本控制与分享: Git & GitHub**

- 将您的整个项目文件夹用`Git`进行管理，并上传到`GitHub`或`Gitee`。这是现代科研软件分发的标准做法，也便于他人给您提建议或贡献代码。
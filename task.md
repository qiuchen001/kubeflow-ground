这是一个涵盖产品需求和技术落地的全面任务。我将为你构建这两个页面的**产品文档（PRD 风格）和技术实现方案文档（Technical Design Document, TDD 风格）**。

-----

# 📝 MLOps Pipeline 可视化构建器：产品文档 (PRD)

## 1\. 目标与愿景

**目标：** 提供一个用户友好的图形化界面，将 Kubeflow Pipelines (KFP) 的构建过程从编写 Python/YAML 代码抽象出来，使数据科学家和 ML 工程师能快速、直观地定义、配置和部署 ML 工作流。

**愿景：** 降低 Kubeflow Pipelines 的使用门槛，提高实验和部署的速度及可重复性。

## 2\. 目标用户

  * **数据科学家 (Primary):** 关注模型和实验逻辑，不熟悉或不想深入 K8s/YAML。
  * **ML 工程师 (Secondary):** 负责组件的容器化、资源的配置和 Pipeline 的模板化。

## 3\. 功能模块划分

我们将系统划分为两个核心页面：

### 页面 A: 组件定义与配置 (Component Builder)

| ID | 功能点 | 目标用户 | 描述 |
| :--- | :--- | :--- | :--- |
| **A.1** | **基础元数据** | DS / MLE | 输入组件名称、描述、类别。 |
| **A.2** | **镜像配置** | MLE | 填写**预构建**的 Docker 镜像 URL 和 Tag (`registry/image:tag`)。 |
| **A.3** | **资源规格** | MLE | 通过下拉菜单或滑块设置 CPU、内存、GPU (类型和数量) 的 **请求 (Request)** 和 **限制 (Limit)**。 |
| **A.4** | **输入/输出定义** | DS | 定义组件函数所需的参数（输入）和它产生的产物（输出 Artifacts），包括数据类型。 |
| **A.5** | **Volcano 调度配置** | MLE | 提供一个开关，如果开启，可设置 `scheduling.k8s.io/group-name` 等 Volcano 所需的 Pod Annotation。 |
| **A.6** | **命令/参数** | MLE | 填写容器启动命令 (`command`) 和参数 (`args`)，用于执行镜像内的脚本（如 `python train.py`）。 |
| **A.7** | **保存为模板** | 所有 | 将配置保存为**可重用的组件 YAML 模板**，并存入后端仓库。 |

### 页面 B: 管道构建与可视化 (Pipeline Builder / DAG Editor)


我们将采用 **三层架构**：前端（UI）、后端服务（API Gateway/Compiler）和数据层（KFP Backend/Storage）。



  * **Nodes (节点):** 引用自组件仓库的组件 ID，以及该任务的名称。
  * **Edges (边):** 定义数据流或依赖关系，格式为 `source_node_id.output_name` -\> `target_node_id.input_name`。

### B.2 Pipeline 代码生成（核心挑战）

这是技术上最复杂的一步。后端需要将前端的 DAG JSON **逆向转换为可编译的 KFP Python 代码**。

**关键步骤：**

1.  **导入组件：** 根据 Nodes 列表，生成 Python 导入语句，使用 KFP SDK 的 `load_component_from_file` 加载所有组件 YAML 文件。
2.  **定义管道函数：** 生成 `@pipeline` 装饰的函数定义。
3.  **生成任务链：** 遍历 DAG 的拓扑排序，为每个节点生成一个 `task = component_op(...)` 调用。
4.  **处理数据依赖：**

这个方案既实现了产品对用户体验的需求，又保留了 Kubeflow 平台的代码驱动、可重复的 ML 最佳实践。
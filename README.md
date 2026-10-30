# 电商智能问数系统 · DB-GPT 本地开发环境

详细功能说明见 [项目功能详解](docs/项目功能详解.md)，包含用户功能、可用状态、数据字典、源码地图和参考 SQL。

本目录以 **DB-GPT v0.8.2** 为基础，准备了独立 Python 环境、原版 Web 界面、数据库、电商模拟数据和 Windows 启停脚本，供后续二次开发。

**当前配置：DeepSeek 在线聊天模型 + 百炼 embedding / reranker + 电商模拟数据库。** 本地 `.env` 配置模型名称、地址和密钥，`configs/online-model.toml` 使用 DeepSeek 原生聊天适配器和项目提供的百炼检索适配器。向量模型为 `text-embedding-v4`（1024 维），排序模型为 `qwen3-rerank`。已通过真实 API 和应用内部接口验证，服务启动后建立 Schema 向量索引。企业文档导入和知识问答仍需单独验收。

## 启动和停止

- 双击 `start.cmd`：在后台启动 DB-GPT，并打开浏览器；检测到本地在线配置时自动启用模型。
- 双击 `stop.cmd`：停止本项目服务，保留数据库。
- 双击 `status.cmd`：检查服务状态和示例数据数量。
- 地址：<http://127.0.0.1:5670>，仅监听本机。
- 初次启动约需一分钟；重启电脑后需要重新运行 `start.cmd`。

在 PowerShell 中也可以运行：

```powershell
cd E:\vscode_qy\ecommerce-ai-analytics
.\scripts\start.ps1 -NoBrowser
.\.venv\Scripts\python.exe .\scripts\check_deployment.py
.\scripts\stop.ps1
```

不需要 Docker、MySQL 或本地 GPU。元数据和电商业务数据分别保存在两个 SQLite 文件中。

## 目录

```text
DB-GPT/                 上游 v0.8.2 完整源码，后端和 Web 前端均在此
.venv/                  本项目 Python 3.11 独立环境
configs/                无模型启动配置、在线模型配置示例
scripts/                安装、数据初始化、注册、启停和部署检查
patches/                为无模型启动添加的源代码补丁
data/ecommerce.db       电商模拟业务数据库
data/metadata/dbgpt.db  DB-GPT 自身的元数据数据库
data/benchmark.json     12 道中文问题、参考 SQL、预期查询结果
data/vectors/           向量存储目录（预留）
logs/                   服务日志
work/                   下载、原始文件备份、验证报告等中间资料
```

前端源码：`DB-GPT/web/`。当前服务使用上游附带的静态构建文件，无需先安装 Node 依赖。修改 React 页面后需重新构建并导出前端，参见上游 `scripts/build_web_static.sh`，该脚本为 Bash 版本，不能直接当作 PowerShell 脚本执行。

后端源码：`DB-GPT/packages/dbgpt-app/`、`dbgpt-core/`、`dbgpt-serve/`、`dbgpt-ext/`。这些包通过 editable 模式安装，修改 Python 后重启服务即可生效。

## 语雀文档连接器

已提供本地语雀 MCP 适配，可在现有连接器页面使用账户验证、知识库列表、文档列表和正文读取工具。配置 `.env` 的 `YUQUE_TOKEN` 后随 `start.cmd` 启动。接入步骤、验收命令和错误排查见 [语雀连接器接入](docs/语雀连接器接入.md)。MCP 握手成功与真实文档读取分别记录，以完整验收报告为准。

## 电商数据与指标口径

数据源名称：`ecommerce_demo`。全部数据为确定性生成的虚构数据，不包含真实客户信息。

| 表 | 内容 | 初始数量 |
|---|---|---:|
| customers | 客户、省份、注册日期 | 300 |
| products | 商品、类目、价格 | 20 |
| orders | 订单、日期、渠道、状态、金额 | 1500 |
| order_items | 订单商品明细 | 3751 |
| refunds | 退款金额、日期、原因 | 107 |

- 时间范围：2026-07-01 至 2026-10-25。
- 金额以整数“分”存储，展示人民币元时除以 `100.0`。
- `paid`、`completed` 计入销售额；`pending`、`cancelled` 不计入。
- 净销售额 = 已支付/已完成订单总额 − 退款总额。本样例统计订单全集，日期区间退款归属口径留待后续业务设计。
- `v_daily_sales`：按日销售额和订单量；`v_product_sales`：按商品销量和销售额。
- 不接入 embedding 模型时，仅登记数据源并读取表结构，不生成 Schema 向量索引。
- 初始化脚本检测到已有数据库时保留数据，不会自动覆盖。

可执行的示例 SQL：

```sql
SELECT COUNT(*) AS order_count FROM orders;
SELECT * FROM v_daily_sales ORDER BY sales_date DESC LIMIT 10;
SELECT product_name, gross_sales_yuan
FROM v_product_sales ORDER BY gross_sales_yuan DESC LIMIT 5;
```

## 模型配置与问数入口

已配置 DeepSeek 官方 API，默认模型 `deepseek-flash`。密钥只写入忽略提交的 `.env`，配置文件通过环境变量引用。关闭 thinking 模式以便 SQL / Agent 输出解析；`start.cmd` 自动启用在线配置。需要仅启动界面和数据库时，停止服务后运行 `scripts/start.ps1 -Offline`。

使用方式：浏览器刷新页面，在应用程序中打开 **Chat Data**，选择模型 `deepseek-flash` 和数据源 `ecommerce_demo`，然后输入问题。若模型列表显示为空，请刷新页面，让前端重新获取启动后的模型列表。

已通过真实模型验证：“请查询电商数据库中 orders 表共有多少笔订单。”生成 `SELECT COUNT(*) AS order_count FROM orders;`，执行结果为 `1500`。记录位于 `work/model-smoke-test.json`。这是单条连通性验证，不代表完整 Text-to-SQL 正确率评测。

如需更换模型：

1. 将 `.env.example` 复制为 `.env`，填写模型名称、API 地址和密钥。
2. 将 `configs/online-model.toml.example` 复制为 `configs/online-model.toml`。
3. 停止当前服务，运行 `scripts/start.ps1 -Online`。
4. 百炼检索模型使用独立的 `DASHSCOPE_API_KEY`，并分别配置 `EMBEDDING_API_URL` 和 `RERANKER_API_URL`。从百炼控制台复制与 Key 对应的 API Host，按 `.env.example` 中的路径填写；不要用其他企业或其他地域的地址。聊天模型和检索模型使用独立配置。

百炼接入代码在 `scripts/bailian_models.py`，由 `scripts/run_server.py` 在解析模型配置前注册。Embedding 会按每批最多 10 条拆分；reranker 使用百炼原生接口，并把按相关度返回的分数还原为输入文档顺序，供 DB-GPT 正确排序。Key 仅保存在被忽略的本地 `.env` 中。

验证命令：

```powershell
.\.venv\Scripts\python.exe .\scripts\test_bailian_models.py
.\.venv\Scripts\python.exe .\scripts\check_rag_models.py
```

第一条为离线协议测试；第二条会调用百炼 API，使用合成文本验证同步和异步向量化、排序，报告写入 `work/rag-model-check.json`。接口依据：[向量化](https://help.aliyun.com/zh/model-studio/text-embedding-synchronous-api)、[文本排序](https://help.aliyun.com/zh/model-studio/text-rerank-api)。更换 embedding 模型或维度时，应按数据源或知识空间重新建立索引。

### 添加 xAI Grok 聊天模型

模型管理 → 创建模型 → 模型类型选择 `llm` → 模型提供商选择 `proxy/grok`。默认候选模型为 `grok-4.7`，也可手动输入 xAI 账户支持的其他 Grok 聊天模型名称。API Base 为 `https://api.x.ai/v1`，API Key 填写 xAI 的 Key，或事先在本地 `.env` 配置 `XAI_API_KEY`。上下文长度应与实际模型一致；默认候选 Grok 4.7 为 500000。

提供商通过 `scripts/grok_models.py` 注册，由项目启动器自动加载；复用兼容的 Chat Completions 接口，支持流式输出。当前实现范围是聊天接入，不会自动启用 xAI 的服务器端联网搜索、图片生成等其他功能。创建并启动成功的聊天模型会出现在探索广场的模型切换菜单中。

离线测试：`.\.venv\Scripts\python.exe scripts/test_grok_models.py`，覆盖注册、配置、凭据隔离和模拟 HTTP 的流式／非流式调用，不代表已完成付费 API 验证。官方接口说明：[xAI Chat Completions](https://docs.x.ai/developers/model-capabilities/legacy/chat-completions)。

请把真实密钥留在本地 `.env`；该文件已经加入忽略列表。在线模式下真实问答按供应商规则消耗 API 额度。

## 已处理的部署适配

1. 独立数据目录的 Alembic 模板：源码 editable 安装不会生成 wheel 专属的模板目录，因此 `init_data.py` 从上游 `pilot/meta_data` 复制缺失的迁移模板，不覆盖已有文件。
2. 空模型启动：上游初始化仅在加载第一个模型时创建 WorkerManager，会在空模型列表时崩溃。现提前初始化空管理器；无 embedding 配置时暂不运行 Schema 向量化监听器。源码改动和对应补丁见 `patches/`。
3. 锁定依赖：安装使用上游 `uv.lock`，避免最新依赖与该发布版不兼容。
4. 运行路径、持久化加密密钥、后台进程日志和端口检查集中在外层脚本。

如果重建运行环境，执行 `scripts/install.ps1`。需要系统已安装 uv；该脚本沿用本地源码与锁文件。

## 验证范围与后续开发

`scripts/check_deployment.py` 检查页面、数据源注册、连接测试、表结构，以及 12 条参考 SQL 通过真实 DB-GPT HTTP 接口执行后的结果。报告写入 `work/deployment-check.json`。

这验证的是部署与数据库执行链路，**并非模型 Text-to-SQL 正确率**。当前未实现电商专用前端、角色权限隔离、只读 SQL 策略或模型重试策略；这些可以作为后续自主开发内容。当前环境仅使用独立模拟数据库。

简历项目建议在实际完成二次开发后，按“基于 DB-GPT 二次开发，负责具体业务模块”的方式说明个人贡献。保留上游 MIT 许可和来源。

上游：<https://github.com/eosphoros-ai/DB-GPT/tree/v0.8.2>

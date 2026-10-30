import { ModelType } from '@/types/chat';
import { DBType } from '@/types/db';
import { ModelIconInfo } from '@/types/models';

export const DEFAULT_ICON_URL = '/models/huggingface.svg';

export const MODEL_ICON_MAP: Record<ModelType, { label: string; icon: string }> = new Proxy({} as any, {
  get: (_target, prop) => {
    const modelId = prop as string;
    return {
      label: getModelLabel(modelId),
      icon: getModelIcon(modelId),
    };
  },
});

export const MODEL_ICON_INFO: Record<string, ModelIconInfo> = {
  deepseek: {
    label: 'DeepSeek',
    icon: '/models/deepseek.png',
    patterns: ['deepseek', 'r1'],
  },
  qwen: {
    label: 'Qwen',
    icon: '/models/qwen2.png',
    patterns: ['qwen', 'qwen2', 'qwen2.5', 'qwq', 'qvq'],
  },
  gemini: {
    label: 'Gemini',
    icon: '/models/gemini.png',
    patterns: ['gemini'],
  },
  moonshot: {
    label: 'Moonshot',
    icon: '/models/moonshot.png',
    patterns: ['moonshot', 'kimi'],
  },
  minimax: {
    label: 'MiniMax',
    icon: '/models/minimax.png',
    patterns: ['minimax', 'm3', 'm2.7'],
  },
  doubao: {
    label: 'Doubao',
    icon: '/models/doubao.png',
    patterns: ['doubao'],
  },
  ernie: {
    label: 'ERNIE',
    icon: '/models/ernie.png',
    patterns: ['ernie'],
  },
  proxyllm: {
    label: "代理 LLM",
    icon: '/models/chatgpt.png',
    patterns: ['proxy'],
  },
  chatgpt: {
    label: 'ChatGPT',
    icon: '/models/chatgpt.png',
    patterns: ['chatgpt', 'gpt', 'o1', 'o3'],
  },
  vicuna: {
    label: 'Vicuna',
    icon: '/models/vicuna.jpeg',
    patterns: ['vicuna'],
  },
  'glm-4': {
    label: 'GLM-4.7',
    icon: '/models/glm4.png',
    patterns: ['glm-4'],
  },
  chatglm: {
    label: 'ChatGLM',
    icon: '/models/chatglm.png',
    patterns: ['chatglm', 'glm'],
  },
  llama: {
    label: 'Llama',
    icon: '/models/llama.jpg',
    patterns: ['llama', 'llama2', 'llama3'],
  },
  baichuan: {
    label: 'Baichuan',
    icon: '/models/baichuan.png',
    patterns: ['baichuan'],
  },
  claude: {
    label: 'Claude',
    icon: '/models/claude.png',
    patterns: ['claude'],
  },
  bard: {
    label: 'Bard',
    icon: '/models/bard.gif',
    patterns: ['bard'],
  },
  tongyi: {
    label: 'Tongyi',
    icon: '/models/tongyi.apng',
    patterns: ['tongyi'],
  },
  yi: {
    label: 'Yi',
    icon: '/models/yi.svg',
    patterns: ['yi'],
  },
  bailing: {
    label: 'Bailing',
    icon: '/models/bailing.svg',
    patterns: ['bailing'],
  },
  wizardlm: {
    label: 'WizardLM',
    icon: '/models/wizardlm.png',
    patterns: ['wizard'],
  },
  internlm: {
    label: 'InternLM',
    icon: '/models/internlm.png',
    patterns: ['internlm'],
  },
  solar: {
    label: 'Solar',
    icon: '/models/solar_logo.png',
    patterns: ['solar'],
  },
  gorilla: {
    label: 'Gorilla',
    icon: '/models/gorilla.png',
    patterns: ['gorilla'],
  },
  zhipu: {
    label: 'Zhipu',
    icon: '/models/zhipu.png',
    patterns: ['zhipu'],
  },
  falcon: {
    label: 'Falcon',
    icon: '/models/falcon.jpeg',
    patterns: ['falcon'],
  },
  huggingface: {
    label: 'Hugging Face',
    icon: '/models/huggingface.svg',
    patterns: ['huggingface', 'hf'],
  },
};

export function getModelLabel(modelId: string): string {
  if (!modelId) return '';

  // 1. Try to match directly
  if (MODEL_ICON_INFO[modelId]?.label) {
    return MODEL_ICON_INFO[modelId].label;
  }

  // 2. Try to match by patterns to get the base name, then add version information
  const formattedModelId = modelId.toLowerCase();
  for (const key in MODEL_ICON_INFO) {
    const modelInfo = MODEL_ICON_INFO[key];

    if (modelInfo.patterns && modelInfo.patterns.some(pattern => formattedModelId.includes(pattern.toLowerCase()))) {
      // Try to extract version information from the model ID
      const versionMatch = modelId.match(/[-_](\d+b|\d+\.\d+b?|v\d+(\.\d+)?)/i);
      const sizePart = modelId.match(/[-_](\d+b)/i);

      // Build the display name
      let displayName = modelInfo.label;

      // Add version information
      if (versionMatch && !sizePart) {
        displayName += ` ${versionMatch[1]}`;
      }

      // Add size information
      if (sizePart) {
        displayName += ` ${sizePart[1]}`;
      }

      return displayName;
    }
  }

  // If no match
  return modelId;
}

export function getModelIcon(modelId: string): string {
  if (!modelId) return DEFAULT_ICON_URL;

  // Format the model ID for matching
  const formattedModelId = modelId.toLowerCase();

  // 1. Try to match directly
  if (MODEL_ICON_INFO[modelId]?.icon) {
    return MODEL_ICON_INFO[modelId].icon;
  }

  // 2. Try to match by patterns
  for (const key in MODEL_ICON_INFO) {
    const modelInfo = MODEL_ICON_INFO[key];

    // Check if the model ID contains one of the patterns
    if (modelInfo.patterns && modelInfo.patterns.some(pattern => formattedModelId.includes(pattern.toLowerCase()))) {
      return modelInfo.icon;
    }
  }

  // Try to match by the model prefix
  const modelParts = formattedModelId.split(/[-_]/);
  if (modelParts.length > 0) {
    const modelPrefix = modelParts[0];
    for (const key in MODEL_ICON_INFO) {
      if (modelPrefix === key.toLowerCase()) {
        return MODEL_ICON_INFO[key].icon;
      }
    }
  }

  // If no match, return the default icon
  return DEFAULT_ICON_URL;
}

export const dbMapper: Record<DBType, { label: string; icon: string; desc: string }> = {
  mysql: {
    label: 'MySQL',
    icon: '/icons/mysql.png',
    desc: "快速、可靠、可扩展的开源关系型数据库管理系统。",
  },
  oceanbase: {
    label: 'OceanBase',
    icon: '/icons/oceanbase.png',
    desc: "超快速且高性价比的分布式 SQL 数据库。",
  },
  mssql: {
    label: 'MSSQL',
    icon: '/icons/mssql.png',
    desc: "由 Microsoft 提供的强大、可扩展且安全的关系型数据库系统。",
  },
  duckdb: {
    label: 'DuckDB',
    icon: '/icons/duckdb.png',
    desc: "具备高效查询处理能力的内存分析型数据库。",
  },
  sqlite: {
    label: 'Sqlite',
    icon: '/icons/sqlite.png',
    desc: "简单易用、轻量级且便于移植的嵌入式关系型数据库。",
  },
  clickhouse: {
    label: 'ClickHouse',
    icon: '/icons/clickhouse.png',
    desc: "面向高性能分析与实时查询的列式数据库。",
  },
  oracle: {
    label: 'Oracle',
    icon: '/icons/oracle.png',
    desc: "在企业中广泛使用的稳健、可扩展且安全的关系型数据库。",
  },
  access: {
    label: 'Access',
    icon: '/icons/access.png',
    desc: "由 Microsoft 提供的面向小型应用的易用关系型数据库。",
  },
  mongodb: {
    label: 'MongoDB',
    icon: '/icons/mongodb.png',
    desc: "面向 Web 和移动应用的灵活、可扩展 NoSQL 文档数据库。",
  },
  doris: {
    label: 'ApacheDoris',
    icon: '/icons/doris.png',
    desc: "新一代开源实时数据仓库。",
  },
  starrocks: {
    label: 'StarRocks',
    icon: '/icons/starrocks.png',
    desc: "开源高性能分析型数据库。",
  },
  db2: { label: 'DB2', icon: '/icons/db2.png', desc: "由 IBM 开发的可扩展且安全的关系型数据库系统。" },
  hbase: {
    label: 'HBase',
    icon: '/icons/hbase.png',
    desc: "面向大规模结构化/半结构化数据的分布式、可扩展 NoSQL 数据库。",
  },
  redis: {
    label: 'Redis',
    icon: '/icons/redis.png',
    desc: "快速、多用途的内存数据结构存储，可用作缓存、数据库或消息代理。",
  },
  cassandra: {
    label: 'Cassandra',
    icon: '/icons/cassandra.png',
    desc: "面向大数据的高可扩展、容错分布式 NoSQL 数据库。",
  },
  couchbase: {
    label: 'Couchbase',
    icon: '/icons/couchbase.png',
    desc: "采用分布式架构的高性能 NoSQL 文档数据库。",
  },
  omc: { label: 'Omc', icon: '/icons/odc.png', desc: "Omc 元数据。" },
  postgresql: {
    label: 'PostgreSQL',
    icon: '/icons/postgresql.png',
    desc: "功能强大、具备可扩展性并遵循 SQL 标准的开源关系型数据库。",
  },
  gaussdb: {
    label: 'GaussDB',
    icon: '/icons/gaussdb.png',
    desc: "华为推出的兼容 PostgreSQL 的分布式数据库",
  },
  openGauss: {
    label: 'openGauss',
    icon: '/icons/opengauss.png',
    desc: "兼容 PostgreSQL 的开源关系型数据库。",
  },
  vertica: {
    label: 'Vertica',
    icon: '/icons/vertica.png',
    desc: "Vertica 是一款强一致、符合 ACID 的 SQL 数据仓库，专为当今数据驱动世界的规模与复杂性而构建。",
  },
  spark: { label: 'Spark', icon: '/icons/spark.png', desc: "面向大规模数据分析的统一引擎。" },
  hive: { label: 'Hive', icon: '/icons/hive.png', desc: "分布式容错数据仓库系统。" },
  maxcompute: {
    label: 'MaxCompute',
    icon: '/icons/maxcompute.png',
    desc: "阿里云提供的面向批量分析的全托管大规模数据仓库服务。",
  },
  space: { label: 'Space', icon: '/icons/knowledge.png', desc: "知识分析。" },
  tugraph: {
    label: 'TuGraph',
    icon: '/icons/tugraph.png',
    desc: "TuGraph 是由蚂蚁集团与清华大学联合开发的高性能图数据库。",
  },
  neo4j: {
    label: 'Neo4j',
    icon: '/icons/neo4j.png',
    desc: "Neo4j 是一款高度可扩展的原生图数据库，专为利用数据关系而构建。",
  },
};

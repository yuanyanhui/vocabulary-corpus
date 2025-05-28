import OpenAI from 'openai'
import dotenv from 'dotenv'
import fs from 'fs'
import path from 'path'

// 加载环境变量
dotenv.config()

const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
  baseURL: 'https://api.x.ai/v1',
})

// 速率限制器类
class RateLimiter {
  private requestTimes: number[] = []
  private maxRequestsPerSecond: number
  private windowSizeMs: number

  constructor(maxRequestsPerSecond: number) {
    this.maxRequestsPerSecond = maxRequestsPerSecond
    this.windowSizeMs = 1000 // 1秒的时间窗口
  }

  async waitForSlot(): Promise<void> {
    const now = Date.now()

    // 清理超过时间窗口的请求记录
    this.requestTimes = this.requestTimes.filter(
      (time) => now - time < this.windowSizeMs
    )

    // 如果当前时间窗口内的请求数已达到限制，等待
    if (this.requestTimes.length >= this.maxRequestsPerSecond) {
      const oldestRequest = this.requestTimes[0]
      const waitTime = this.windowSizeMs - (now - oldestRequest) + 10 // 额外等待10ms确保安全

      if (waitTime > 0) {
        await new Promise((resolve) => setTimeout(resolve, waitTime))
        return this.waitForSlot() // 递归检查
      }
    }

    // 记录当前请求时间
    this.requestTimes.push(now)
  }

  getStats() {
    const now = Date.now()
    const recentRequests = this.requestTimes.filter(
      (time) => now - time < this.windowSizeMs
    )
    return {
      requestsInLastSecond: recentRequests.length,
      maxRequestsPerSecond: this.maxRequestsPerSecond,
    }
  }
}

const prompt = `You are a senior linguist and vocabulary expert, specializing in multidimensional vocabulary analysis and corpus data construction, with the following professional background and abilities:

=== Professional Fields ===
• In-depth etymological research and historical linguistics analysis
• Multi-level semantic analysis and conceptual mapping
• Cross-cultural language usage pattern research
• Applications of cognitive linguistics and memory science
• Corpus linguistics and frequency analysis

=== Analytical Methodology ===
• Empirical analysis based on large-scale corpora
• Memory optimization strategies combined with cognitive science
• Construction of multidimensional semantic networks and associative maps
• In-depth exploration of cultural contexts and social metaphors
• Focus on difficulty assessment oriented towards second language learners


=== Core Principles ===
• Accuracy and authority of data
• Comprehensiveness and systematic analysis
• Practicality and operability
• Cultural sensitivity and inclusiveness
• Evidence-based support from learning sciences

=== Analysis Objectives ===
Please conduct a comprehensive corpus analysis of the following vocabulary:
- Target Vocabulary: "Provided Vocabulary"
- Target Language Output: Please use English for all content except necessary English content.
- Learner's Native Language: Chinese
- Learner's Level: Intermediate
- Focus Areas: Pronunciation, Meaning, Usage, Context, Culture, Memory
- Advanced Features: Enabled

=== Output Requirements ===
Please strictly follow the JSON format below to output complete vocabulary corpus data, ensuring the accuracy and richness of the data:

{
  "word": "提供的词汇",
  "phonetics": {
    "british": "英式音标",
    "american": "美式音标"
  },
  "definitions": [
    {
      "partOfSpeech": "词性（如 adjective）",
      "definition": "英文释义",
      "chineseTranslation": "中文翻译",
      "level": "难度级别（basic/intermediate/advanced/academic）",
      "frequency": "使用频率（high/medium/low）",
      "register": "语域（formal/informal/neutral/technical/colloquial）"
    }
  ],
  "phrases": [
    {
      "phrase": "常用短语",
      "meaning": "短语中文含义",
      "example": "使用例句（英文）",
      "exampleTranslation": "例句中文翻译",
      "frequency": "使用频率"
    }
  ],
  "examples": [
    {
      "sentence": "英文例句",
      "translation": "例句中文翻译",
      "source": "例句来源（如新闻、文学作品等，可选）",
      "difficulty": "难度级别"
    }
  ],
  "etymology": {
    "origin": "词源语言（如拉丁语）",
    "rootWords": [
      {
        "root": "词根",
        "meaning": "词根含义",
        "language": "来源语言"
      }
    ],
    "historicalDevelopment": "从词源到现代意义的演变过程",
    "firstKnownUse": "首次使用时间",
    "relatedWords": ["同源词列表"]
  },
  "difficultyAnalysis": {
    "overallLevel": "CEFR 等级（如 B2、C1、C2）",
    "pronunciationDifficulty": "发音难度（1-10）",
    "spellingDifficulty": "拼写难度（1-10）",
    "meaningComplexity": "语义复杂度（1-10）",
    "usageComplexity": "使用复杂度（1-10）",
    "learningTips": ["结合认知科学的学习建议"]
  },
  "semanticRelations": {
    "synonyms": [
      {
        "word": "近义词",
        "similarity": "相似度（0-1）",
        "context": "适用语境（中文）"
      }
    ],
    "antonyms": [
      {
        "word": "反义词",
        "context": "适用语境（中文）"
      }
    ],
    "hypernyms": ["上位词"],
    "hyponyms": ["下位词"],
    "collocations": [
      {
        "pattern": "常见搭配结构",
        "examples": ["搭配例句（英文）"],
        "strength": "搭配强度（strong/medium/weak）"
      }
    ]
  },
  "culturalContext": {
    "culturalSignificance": "该词在特定文化中的象征意义或隐含语义",
    "regionalVariations": [
      {
        "region": "地区（如英国、美国）",
        "variation": "表达差异",
        "usage": "具体使用说明"
      }
    ],
    "historicalContext": "与历史文化、文学、社会背景的关联",
    "modernUsage": "现代传播媒介或社交语境下的使用趋势"
  },
  "memoryAids": {
    "visualScene": {
      "description": "可视化场景描述",
      "keyElements": ["关键词或形象元素"],
      "emotionalConnection": "联结个人经验或情绪的触发点"
    },
    "mnemonicDevices": [
      {
        "type": "联想/缩略/声音联觉等类型",
        "content": "记忆内容",
        "explanation": "解释说明"
      }
    ],
    "wordAssociations": ["词汇联想（英文单词）"]
  },
  "grammaticalInfo": {
    "irregularForms": {
      "plural": "复数（如无，则为 null）",
      "pastTense": "过去式（如无，则为 null）",
      "pastParticiple": "过去分词（如无，则为 null）",
      "presentParticiple": "现在分词（如无，则为 null）",
      "comparative": "比较级",
      "superlative": "最高级"
    },
    "syntacticPatterns": [
      {
        "pattern": "典型句法结构",
        "description": "结构说明（中文）",
        "examples": ["例句（英文）"]
      }
    ],
    "commonMistakes": [
      {
        "mistake": "常见误用",
        "correction": "正确用法",
        "explanation": "简要说明"
      }
    ]
  },
  "metadata": {
    "frequency": "词频排名或数值",
    "domains": ["典型使用领域，如科技、文化、商业等"],
    "tags": ["语义标签、主题词等"],
    "lastUpdated": "最后更新时间（如 2025-05）",
    "sources": ["主要参考语料来源或词典，如 OED、COCA、BNC 等"]
  }
}
=== Special Requirements ===
1. Ensure all phonetic symbols use the International Phonetic Alphabet (IPA) standard.
2. Example sentences should cover different registers and usage scenarios.
3. Etymology information must be accurate and reliable, with historical basis.
4. Difficulty analysis should be based on language learning theory.
5. Memory aids should incorporate principles of cognitive science.
6. Cultural context should reflect cross-cultural understanding.
7. All data must be supported by authoritative sources.
8. Please confirm that the JSON format is correct before outputting, with each field complete, avoiding omissions or semantic repetition.
9. Please output strictly according to the style of professional linguistic publications, ensuring accurate terminology, real data, and coherent semantics.
10. Except for definitions, example sentences, etc., which must be in English, the rest of the content should be in Chinese as much as possible.`

// 保存JSON文件的辅助函数
const saveWordDataToFile = (word: string, data: any) => {
  const dataDir = path.join(process.cwd(), 'data')

  // 确保data目录存在
  if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true })
  }

  const filename = `${word}.json`
  const filepath = path.join(dataDir, filename)

  // 保存文件
  fs.writeFileSync(filepath, JSON.stringify(data, null, 2), 'utf-8')

  return filepath
}

// 处理单个词汇的函数
const processWord = async (
  word: string,
  rateLimiter: RateLimiter
): Promise<void> => {
  try {
    // 等待速率限制器许可
    await rateLimiter.waitForSlot()

    const completion = await client.chat.completions.create({
      model: 'grok-3-mini',
      messages: [
        {
          role: 'system',
          content: prompt,
        },
        {
          role: 'user',
          content: word.trim(),
        },
      ],
    })

    const responseContent = completion.choices[0].message.content

    // 尝试解析JSON响应
    try {
      const wordData = JSON.parse(responseContent || '{}')
      saveWordDataToFile(word.trim(), wordData)
    } catch (parseError) {
      console.log('JSON 解析失败')
    }
  } catch (error) {
    console.error(`处理词汇 "${word}" 时出现错误:`, error)
  }
}

// 使用示例
const main = async () => {
  try {
    const dataDir = path.join(process.cwd(), 'data')

    // 确保data目录存在
    if (!fs.existsSync(dataDir)) {
      fs.mkdirSync(dataDir, { recursive: true })
    }

    const existingFiles = fs.readdirSync(dataDir)
    const processedWords = new Set(
      existingFiles
        .filter((file) => file.endsWith('.json'))
        .map((file) => file.replace('.json', ''))
    )

    const wordList = fs
      .readFileSync(path.join(process.cwd(), 'word.txt'), 'utf-8')
      .split('\n')
      .map((word) => word.trim())
      .filter((word) => word.length > 0)

    // 过滤掉已经处理过的词汇
    const remainingWords = wordList.filter((word) => !processedWords.has(word))

    console.log('总词汇数量:', wordList.length)
    console.log('已处理词汇数量:', processedWords.size)
    console.log('剩余词汇数量:', remainingWords.length)

    if (remainingWords.length === 0) {
      console.log('所有词汇都已处理完成！')
      return
    }

    // 创建速率限制器，设置为每秒 10个请求
    const rateLimiter = new RateLimiter(10)

    console.log('开始处理词汇，速率限制: 10 RPS')
    console.log('预计完成时间:', Math.ceil(remainingWords.length / 10), '秒')

    let completedCount = 0
    const startTime = Date.now()

    // 创建所有任务的Promise数组
    const tasks = remainingWords.map(async (word, index) => {
      try {
        await processWord(word, rateLimiter)
        completedCount++

        const elapsed = (Date.now() - startTime) / 1000
        const rate = completedCount / elapsed
        const stats = rateLimiter.getStats()

        console.log(
          `已完成: ${completedCount}/${remainingWords.length} | ` +
            `当前速率: ${rate.toFixed(2)} RPS | ` +
            `最近1秒请求数: ${stats.requestsInLastSecond}/${stats.maxRequestsPerSecond}`
        )
      } catch (error) {
        console.error(`处理词汇 "${word}" 失败:`, error)
      }
    })

    // 等待所有任务完成
    await Promise.all(tasks)

    const totalTime = (Date.now() - startTime) / 1000
    const averageRate = completedCount / totalTime

    console.log('\n处理完成!')
    console.log(`总耗时: ${totalTime.toFixed(2)} 秒`)
    console.log(`平均速率: ${averageRate.toFixed(2)} RPS`)
    console.log(`成功处理: ${completedCount} 个词汇`)
  } catch (error) {
    console.error('主程序执行过程中出现错误:', error)
  }
}

main()

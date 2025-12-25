<script setup>
import { ref, reactive, onMounted, onBeforeUnmount,getCurrentInstance } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import service from '../api/request'

const {proxy} = getCurrentInstance()
const totalKwh   = ref(0)
const totalMoney = ref(0)
const avgDaily   = ref(0)
const today      = new Date().toLocaleDateString()

// 这个是折线图和柱状图 两个图表共用的公共配置
// echart官网
const xOptions = reactive({
  // 图例文字颜色
  textStyle: {
    color: "#333",
  },
  legend: {
    top:'top'
  },
  grid: {
    left: "20%",
  },
  // 提示框
  tooltip: {
    trigger: "axis",
  },
  xAxis: {
    type: "category", // 类目轴
    data: [],
    axisLine: {
      lineStyle: {
        color: "#17b3a3",
      },
    },
    axisLabel: {
      interval: 0,
      color: "#333",
    },
  },
  yAxis: [
    {
      type: "value",
      axisLine: {
        lineStyle: {
          color: "#17b3a3",
        },
      },
    },
  ],
  color: ["#2ec7c9", "#b6a2de", "#5ab1ef", "#ffb980", "#d87a80", "#8d98b3"],
  series: [{ name: '电量(kWh)', type: 'line', smooth: true, data: []}],
});

const pieOptions = reactive({
  tooltip: {
    trigger: "item",
  },
  legend: {
    top:'top'
  },
  color: [
    "#0f78f4",
    "#dd536b",
    "#9462e5",
    "#a6a6a6",
    "#e1bb22",
    "#39c362",
    "#3ed1cf",
  ],
  series: [{ name: '用电占比', type: 'pie', radius: '55%', data: [] }]
});

/* --------------  新增：实例 + 通用resize  -------------- */
let lineChart = null
let pieChart  = null

function resizeCharts() {
  lineChart?.resize()
  pieChart?.resize()
}

/* --------------  原来 onMounted 里的逻辑包一层  -------------- */
async function loadData() {
  try {
    const list = await proxy.$api.getPowerLatestMonths()
    if (!list || !list.length) return

    const data = list.map(i => ({ ...i, kwh: +i.kwh, money: +i.money }))
    totalKwh.value   = data.reduce((s, i) => s + i.kwh, 0)
    totalMoney.value = data.reduce((s, i) => s + i.money, 0)
    avgDaily.value   = totalKwh.value / data.length

    const xData = data.map(i => `${i.year}-${String(i.month).padStart(2, '0')}`)
    const yData = data.map(i => i.kwh)

    /* ---- 图表：只 setOption，不再 init ---- */
    lineChart.setOption({
      ...xOptions,
      xAxis: { ...xOptions.xAxis, data: xData },
      series: [{ ...xOptions.series[0], data: yData }]
    })

    pieChart.setOption({
      ...pieOptions,
      series: [{ ...pieOptions.series[0], data: data.map((v, idx) => ({ name: xData[idx], value: v.kwh })) }]
    })
  } catch (e) {
    ElMessage.error('加载失败：' + e.message)
  }
}

onMounted(() => {
  /* 只初始化一次 */
  lineChart = echarts.init(document.getElementById('line'))
  pieChart  = echarts.init(document.getElementById('pie'))

  loadData()                 // 拉数据 + 填图
  window.addEventListener('resize', resizeCharts)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  lineChart?.dispose()
  pieChart?.dispose()
})

const exportData = async () => {
  try {
    const blob = await service.get('power/report/export/', {
      responseType: 'blob',
    })

    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '用电分析报告.pdf'
    a.click()
    URL.revokeObjectURL(url)

    ElMessage.success('报告导出成功')
  } catch (error) {
    console.error(error)
    ElMessage.error('报告导出失败')
  }
}
</script>

<template>
  <div class="page-header">
    <h1>用电概览</h1>
    <span class="date">{{ today }}</span>
  </div>

  <!-- 统计卡片 -->
  <el-row :gutter="16" class="stat-row">
    <el-col :span="6">
      <div class="stat-card">
        <div class="number">{{ totalKwh.toFixed(1) }}</div>
        <div class="label">本月用电 (kWh)</div>
      </div>
    </el-col>
    <el-col :span="6">
      <div class="stat-card">
        <div class="number">¥{{ totalMoney.toFixed(2) }}</div>
        <div class="label">本月电费</div>
      </div>
    </el-col>
    <el-col :span="6">
      <div class="stat-card">
        <div class="number">{{ avgDaily.toFixed(1) }}</div>
        <div class="label">日均用电 (kWh)</div>
      </div>
    </el-col>
    <el-col :span="6">
      <el-button type="primary" @click="exportData">导出用电报告</el-button>
    </el-col>
  </el-row>

  <!-- 图表区域 -->
  <el-row :gutter="16" class="chart-row">
    <el-col :span="16">
      <div class="chart-box">
        <div class="title">近 12 个月趋势</div>
        <div id="line" class="chart"></div>
      </div>
    </el-col>
    <el-col :span="8">
      <div class="chart-box">
        <div class="title">月度占比</div>
        <div id="pie" class="chart"></div>
      </div>
    </el-col>
  </el-row>

  <!-- 快捷操作 -->
  <el-row class="action-row">
    <el-button @click="$router.push('/usage-detail')">查看明细</el-button>
    <el-button @click="$router.push('/bill')">电费账单</el-button>
    <el-button @click="$router.push('/alert')">异常告警</el-button>
  </el-row>
</template>


<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-header h1 {
  margin: 0;
  font-size: 20px;
}
.page-header .date {
  color: #999;
}

.stat-row {
  margin-bottom: 10px;
}
.stat-card {
  background: #fff;
  padding: 16px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,.05);
  text-align: center;
}
.stat-card .number {
  font-size: 24px;
  font-weight: bold;
  color: #2ec7c9;
}
.stat-card .label {
  margin-top: 4px;
  color: #666;
}

.chart-row {
  margin-bottom: 10px;
}
.chart-box {
  background: #fff;
  padding: 16px;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,.05);
}
.chart-box .title {
  margin-bottom: 12px;
  font-weight: 500;
}
.chart {
  width: 100%;
  height: 400px;
}

.action-row {
  text-align: center;
}
</style>
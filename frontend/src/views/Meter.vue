<script setup>
import * as echarts from "echarts";
import { ref, computed, onMounted, watch } from "vue";
import { usePowerStore } from "../stores/power";
import { useRouter } from 'vue-router';

const store = usePowerStore();
const router = useRouter()

const meterOptions = ["METER001", "METER002", "METER003"];
const meterId = ref(store.meterId); // 和 store 同步
const maxPoints = 300;

const wsUrl = computed(() => `ws://${location.hostname}:8001/ws/monitor/meter/${meterId.value}/`);

const statusClass = computed(() => store.wsStatus);
const statusText = computed(() =>
  ({
    idle: "未连接",
    connecting: "连接中",
    open: "在线",
    closed: "断开",
    error: "错误",
  }[store.wsStatus] || "未知")
);

function fmt(n, d = 2) {
  const x = Number(n);
  return Number.isFinite(x) ? x.toFixed(d) : "-";
}


/* ---------- KPI 数据 ---------- */
const latest = computed(() => store.latestRealtime);

const totalPowerW = computed(() => latest.value?.powerW || 0);
const voltageV = computed(() => latest.value?.voltageV || 0);
const currentA = computed(() => latest.value?.currentA || 0);
const energyKWh = computed(() => latest.value?.energyKWh || 0);

const deviceList = computed(() => {
  const data = latest.value?.devices || {};
  return Object.entries(data)
    .filter(([k]) => k !== "_TOTAL")
    .map(([name, v]) => ({
      name,
      power_w: Number(v?.power_w || 0),
      on: Number(v?.power_w || 0) > 0,
    }))
    .sort((a, b) => b.power_w - a.power_w);
});

const lastUpdateText = computed(() =>
  latest.value ? new Date(latest.value.raw?.ts || Date.now()).toLocaleTimeString() : ""
);

/* ---------- 图表 ---------- */
const chartEl = ref(null);
let chart = null;


function initChart() {
  if (!chartEl.value) return;

  const old = echarts.getInstanceByDom(chartEl.value);
  if (old) old.dispose();

  chart = echarts.init(chartEl.value);
  chart.setOption({
    grid: { left: 44, right: 16, top: 18, bottom: 32 },
    tooltip: { trigger: "axis" },
    xAxis: { type: "time" },
    yAxis: { type: "value", name: "W" },
    series: [{ type: "line", showSymbol: false, data: [] }],
  });

  updateChart();
}

function updateChart() {
  if (!chart) return;
  const data = store.realtimeSeries.map((p) => [p.t, p.v]);
  chart.setOption({ series: [{ data }] });
}

function clearSeries() {
  store.clearRealtime();
  updateChart();
}

/* ---------- 事件 ---------- */
function reconnectWS() {
  store.reconnectWS();
}

function handleMeterChange() {
  store.changeMeter(meterId.value);
}

/* ---------- 更新监听 ---------- */
watch(
  () => store.realtimeSeries,
  () => updateChart(),
  { deep: true }
);

/* ---------- 生命周期 ---------- */
onMounted(() => {
  initChart();
  updateChart();
});
</script>

<template>
  <div class="meter-page">
    <div class="topbar">
      <div>
        <div class="title">电表实时监控</div>

        <div class="sub">
          Meter：
          <el-select
            v-model="meterId"
            size="small"
            style="width: 160px"
            @change="handleMeterChange"
          >
            <el-option
              v-for="m in meterOptions"
              :key="m"
              :label="m"
              :value="m"
            />
          </el-select>

          <span class="dot" :class="statusClass"></span>
          <span class="status">{{ statusText }}</span>

          <span v-if="lastUpdateText" class="last">
            · 最近更新 {{ lastUpdateText }}
          </span>
        </div>
      </div>

      <div class="actions">
        <el-button size="small" @click="reconnectWS">重连</el-button>
        <el-button size="small" type="primary" plain @click="clearSeries">
          清空曲线
        </el-button>
      </div>
    </div>

    <!-- KPI -->
    <el-row :gutter="12" class="kpi-row">
      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">总功率</div>
          <div class="kpi-value">
            {{ fmt(totalPowerW, 2) }} <span class="unit">W</span>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">电压</div>
          <div class="kpi-value">
            {{ fmt(voltageV, 1) }} <span class="unit">V</span>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">电流</div>
          <div class="kpi-value">
            {{ fmt(currentA, 3) }} <span class="unit">A</span>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="12" :sm="12" :md="6">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-label">累计电量</div>
          <div class="kpi-value">
            {{ fmt(energyKWh, 6) }} <span class="unit">kWh</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表 + 设备 -->
    <el-row :gutter="12" class="main-row">

      <!-- Chart -->
      <el-col :xs="24" :md="16">
        <el-card shadow="hover" class="panel">
          <template #header>
            <div class="panel-header">
              <span>实时功率曲线（最近 {{ maxPoints }} 秒）</span>
              <span class="hint">来自全局 WebSocket 推送</span>
            </div>
          </template>

          <div ref="chartEl" class="chart"></div>
        </el-card>
      </el-col>

      <!-- Device list -->
      <el-col :xs="24" :md="8">
        <el-card shadow="hover" class="panel">
          <template #header>
            <div class="panel-header">
              <span>设备功率（实时）</span>
              <span class="hint">按功率从高到低</span>
            </div>
          </template>

          <el-table :data="deviceList" size="small" height="420" stripe>
            <el-table-column prop="name" label="设备" min-width="120" />
            <el-table-column prop="power_w" label="功率(W)" width="110" align="right">
              <template #default="{ row }">{{ fmt(row.power_w, 2) }}</template>
            </el-table-column>
            <el-table-column prop="on" label="状态" width="80" align="center">
              <template #default="{ row }">
                <el-tag :type="row.on ? 'success' : 'info'" size="small">
                  {{ row.on ? "ON" : "OFF" }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>

          <div v-if="deviceList.length === 0" class="empty">
            暂无数据（请先运行后端 + 模拟脚本）
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-card class="foot" shadow="never">
      <div class="foot-line"><b>WS</b>：<code>{{ wsUrl }}</code></div>
    </el-card>
  </div>
</template>


<style scoped>
.meter-page {
  padding: 14px;
}

.topbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.title {
  font-size: 18px;
  font-weight: 800;
}

.sub {
  margin-top: 6px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  display: inline-block;
}

.dot.idle { background: #bbb; }
.dot.connecting { background: #f0ad4e; }
.dot.open { background: #28a745; }
.dot.closed { background: #888; }
.dot.error { background: #dc3545; }

.status { font-size: 12px; }
.last { font-size: 12px; color: #888; }

.kpi-row { margin-bottom: 12px; }
.kpi-card { border-radius: 12px; }
.kpi-label { color: #666; font-size: 12px; }
.kpi-value { margin-top: 6px; font-size: 20px; font-weight: 800; }
.unit { font-size: 12px; color: #666; margin-left: 4px; }

.main-row { margin-bottom: 12px; }

.panel { border-radius: 12px; overflow: hidden; }
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.hint { color: #888; font-size: 12px; }

.chart { height: 420px; }

.empty {
  padding: 14px;
  color: #999;
  text-align: center;
}

.foot {
  border-radius: 12px;
}
.foot-line {
  color: #666;
  font-size: 12px;
  margin: 6px 0;
}
code {
  background: #f6f6f6;
  padding: 2px 6px;
  border-radius: 6px;
}
</style>

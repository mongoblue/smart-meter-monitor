<script setup>
import * as echarts from "echarts";
import { ref, watch, onMounted, onBeforeUnmount, nextTick,computed } from "vue";
import service from "../api/request";
import { usePowerStore } from "../stores/power";


const powerStore = usePowerStore();

const meterOptions = ["METER001", "METER002", "METER003"];
const meterId = ref("METER001");

const trendTab = ref("day");
const trendLoading = ref(false);

const dayDate = ref("");
const weekEnd = ref("");
const monthPick = ref("");

const chartEl = ref(null);
let chart = null;

const analysis = ref({
  total_kwh: 0,
  avg_daily_kwh: 0,
  max_day: "",
  max_kwh: 0,
  min_day: "",
  min_kwh: 0,
  night_ratio: 0,
  peak_hour: "",
  workday_avg: 0,
  weekend_avg: 0,
  top3_days: [],
  first_half_kwh: 0,
  second_half_kwh: 0,
  half_compare: 0,
})


function initChart() {
  chart = echarts.init(chartEl.value);

  chart.setOption({
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: [] },
    yAxis: { type: "value", name: "kWh" },
    series: [{ name: "Usage", type: "line", showSymbol: false, data: [] }],
  });
}

function setTrendData(x, y) {
  if (!chart) return;

  chart.setOption({
    xAxis: {
      type: "category",
      data: Array.isArray(x) ? x : [],
    },
    yAxis: {
      type: "value",
      name: "kWh",
    },
    series: [
      {
        name: "Usage",
        type: "line",
        showSymbol: false,
        data: Array.isArray(y) ? y : [],
      },
    ],
  });
}

async function loadTrend() {
  trendLoading.value = true;
  analysis.value = {};

  try {
    let url = "";
    let params = { meter_id: meterId.value };

    if (trendTab.value === "day") {
      url = "/power/trend/day";
      if (dayDate.value) params.date = dayDate.value;
    } else if (trendTab.value === "week") {
      url = "/power/trend/week";
      if (weekEnd.value) params.end = weekEnd.value;
    } else {
      url = "/power/trend/month";
      if (monthPick.value) {
        const [yy, mm] = monthPick.value.split("-");
        params.year = Number(yy);
        params.month = Number(mm);
      }

    }

    const resp = await service.get(url, { params });

    const x = resp.x;
    const y = resp.y;

    setTrendData(x, y);
    analysis.value = resp.analysis
    console.log(analysis.value);
    
    // ⭐ 存进 Pinia 用于缓存
    powerStore.saveTrend(trendTab.value, {
      meter_id: meterId.value,
      x,
      y,
      analysis: resp.analysis,
      fetchedAt: Date.now(),
    });

  } catch (err) {
    console.warn("loadTrend failed:", err);
    setTrendData([], []);
  } finally {
    trendLoading.value = false;
  }
}

const conclusion = computed(() => {
    if (!analysis.value.total_kwh) return ""

    if (analysis.value.night_ratio > 0.4) {
      return "夜间用电占比较高，可能存在夜间设备未关闭情况"
    }
    if (analysis.value.peak_kwh > analysis.value.avg_kwh * 2) {
      return "存在明显用电峰值，建议错峰用电"
    }
    return "用电整体较为平稳"
  })

function tryRestore() {
  const map = {
    day: powerStore.trendDay,
    week: powerStore.trendWeek,
    month: powerStore.trendMonth,
  };

  const snap = map[trendTab.value];

  if (!snap) return false;
  if (snap.meter_id !== meterId.value) return false;

  setTrendData(snap.x, snap.y);
  analysis.value = snap.analysis;
  return true;
}

async function syncToBackend() {
  try {
    await service.post("/power/save-client-data", {
      meter_id: meterId.value,
      latest: powerStore.latestRealtime,
      realtime_series: powerStore.realtimeSeries,
      trend: {
        day: powerStore.trendDay,
        week: powerStore.trendWeek,
        month: powerStore.trendMonth,
      },
    });
  } catch (e) {
    console.warn("Sync failed:", e);
  }
}

watch([trendTab, meterId, dayDate, weekEnd, monthPick], async () => {
  await nextTick();

  if (!tryRestore()) {
    loadTrend();
  }
});

onMounted(() => {
  initChart();

  // 优先恢复
  if (!tryRestore()) loadTrend();

  window.addEventListener("resize", () => chart?.resize());
});

onBeforeUnmount(() => {
  syncToBackend();
  chart?.dispose();
  chart = null;
});
</script>

<template>
  <div class="trend-page">

    <!-- 标题栏 -->
    <div class="topbar">
      <div class="title">用电趋势分析</div>

      <div class="controls">
        <span>Meter：</span>
        <el-select v-model="meterId" size="small" style="width:160px">
          <el-option v-for="m in meterOptions" :key="m" :label="m" :value="m" />
        </el-select>

        <el-button size="small" type="primary" @click="loadTrend" :loading="trendLoading">
          刷新
        </el-button>

        <el-button size="small" @click="syncToBackend">同步到后端</el-button>
      </div>
    </div>

    <el-tabs v-model="trendTab" @tab-change="loadTrend" class="tabs">
      <el-tab-pane label="日（按小时）" name="day" />
      <el-tab-pane label="周（7天）" name="week" />
      <el-tab-pane label="月（按天）" name="month" />
    </el-tabs>

    <div class="filters">
      <template v-if="trendTab === 'day'">
        <el-date-picker
          v-model="dayDate"
          type="date"
          size="small"
          value-format="YYYY-MM-DD"
          placeholder="选择日期"
          @change="loadTrend"
        />
      </template>

      <template v-else-if="trendTab === 'week'">
        <el-date-picker
          v-model="weekEnd"
          type="date"
          size="small"
          value-format="YYYY-MM-DD"
          placeholder="选择截止日期"
          @change="loadTrend"
        />
      </template>

      <template v-else>
        <el-date-picker
          v-model="monthPick"
          type="month"
          size="small"
          value-format="YYYY-MM"
          placeholder="选择月份"
          @change="loadTrend"
        />
      </template>
    </div>

    <div ref="chartEl" class="trend-chart"></div>

    <!-- 用电分析模块 -->
    <div class="analysis-panel" v-if="Object.keys(analysis).length > 0">
      <el-card>
        <div class="analysis-title">用电分析</div>

        <el-row :gutter="16">
          <el-col :span="6">
            <div class="metric">
              <div class="label">总用电量</div>
              <div class="value">{{ analysis.total_kwh }} kWh</div>
            </div>
          </el-col>

          <el-col :span="6">
            <div class="metric">
              <div class="label">峰值时段</div>
              <div class="value">{{ analysis.peak_hour || '--' }}</div>
            </div>
          </el-col>

          <el-col :span="6">
            <div class="metric">
              <div class="label">峰值用电</div>
              <div class="value">{{ analysis.peak_kwh }} kWh</div>
            </div>
          </el-col>

          <el-col :span="6">
            <div class="metric">
              <div class="label">夜间占比</div>
              <div class="value">{{ (analysis.night_ratio * 100).toFixed(1) }} %</div>
            </div>
          </el-col>
        </el-row>

        <!-- 周期特定分析 -->
        <template v-if="trendTab === 'week'">
          <el-row :gutter="16">
            <el-col :span="6">
              <div class="metric">
                <div class="label">工作日平均</div>
                <div class="value">{{ analysis.workday_avg }} kWh</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="metric">
                <div class="label">周末平均</div>
                <div class="value">{{ analysis.weekend_avg }} kWh</div>
              </div>
            </el-col>
          </el-row>
        </template>

        <template v-if="trendTab === 'month'">
          <el-row :gutter="16">
            <el-col :span="6">
              <div class="metric">
                <div class="label">最高用电日</div>
                <div class="value">{{ analysis.max_day }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="metric">
                <div class="label">上半月总用电</div>
                <div class="value">{{ analysis.first_half_kwh }} kWh</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="metric">
                <div class="label">下半月总用电</div>
                <div class="value">{{ analysis.second_half_kwh }} kWh</div>
              </div>
            </el-col>
          </el-row>
        </template>
      </el-card>
    </div>

    <!-- 用电结论 -->
    <div class="conclusion-panel" v-if="conclusion">
      <el-card>
        <div class="analysis-title">用电结论</div>
        <div class="value">{{ conclusion }}</div>
      </el-card>
    </div>

  </div>
</template>

<style scoped>
.trend-page {
  padding: 14px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.title {
  font-size: 18px;
  font-weight: bold;
}

.controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filters {
  margin: 12px 0;
  display: flex;
  gap: 10px;
  align-items: center;
}

.trend-chart {
  height: 420px;
  border-radius: 12px;
}
</style>

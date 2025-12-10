<script setup>
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import service from "@/api/request";
import { usePowerStore } from "../stores/power";

// ------------ 状态 ------------
const store = usePowerStore();

// 当前日期：直接用字符串，配合 value-format="YYYY-MM-DD"
const date = ref(getTodayStr());

// 表格数据
const tableData = ref([]);

// 当前电表（从 Pinia 中拿）
const currentMeterId = computed(() => store.meterId || "");

// 工具：获取今天 'YYYY-MM-DD'
function getTodayStr() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

// ------------ 加载数据 ------------
const loadData = async () => {
  if (!currentMeterId.value) {
    ElMessage.warning("当前没有选中的电表");
    return;
  }

  try {
    const resp = await service.get("/power/detail/", {
      params: {
        meter_id: currentMeterId.value,  // 当前电表编号
        date: date.value                 // 已经是 'YYYY-MM-DD'
      }
    });

    // 后端返回的是 { data: [...] }
    tableData.value = resp?.data || [];
  } catch (e) {
    console.warn("loadData failed:", e);
    ElMessage.error("加载用电明细失败");
    tableData.value = [];
  }
};

// 进入页面自动加载一次
onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="page">
    <h2>用电明细</h2>

    <el-card>
      <div class="filters">
        <el-date-picker
          v-model="date"
          type="date"
          placeholder="选择日期"
          value-format="YYYY-MM-DD"  
          @change="loadData"
        />
        <el-button type="primary" @click="loadData">查询</el-button>
      </div>

      <el-table :data="tableData" style="width: 100%" border>
        <el-table-column prop="time" label="时间" width="160" />
        <el-table-column prop="kwh" label="电量 (kWh)" />
      </el-table>
    </el-card>
  </div>
</template>


<style scoped>
.page {
  padding: 20px;
}
.filters {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
  align-items: center;
}
</style>

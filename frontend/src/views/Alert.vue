<script setup>
import { ref, onMounted } from "vue";
import service from "@/api/request";
import { usePowerStore } from "@/stores/power";

const store = usePowerStore();

const meterList = ["METER001", "METER002", "METER003"]; // 可从后台获取

const filterType = ref("");   
const filterMeter = ref("");

const tableData = ref([]);
const page = ref(1);
const pageSize = 20;
const total = ref(0);

function tagColor(t) {      
  return {
    high_power: "danger",
    sudden_usage: "warning",
    voltage_issue: "info",
    fluctuation: "primary",
  }[t];
}

function typeName(t) {
  return {
    high_power: "功率过高",
    sudden_usage: "用电突增",
    voltage_issue: "电压异常",
    fluctuation: "功率波动异常",
  }[t];
}

async function loadData() {
  const resp = await service.get("/power/alerts/", {
    params: {
      page: page.value,
      page_size: pageSize,
      type: filterType.value || undefined,
      meter_id: filterMeter.value || undefined
    }
  });

  tableData.value = resp.results;
  total.value = resp.count;
}

function handlePage(p) {
  page.value = p;
  loadData();
}

onMounted(loadData);
</script>

<template>
  <div class="page">
    <h2>异常中心</h2>

    <el-card>
      <div class="filters">

        <el-select v-model="filterType" placeholder="异常类型" clearable @change="loadData">
          <el-option label="功率过高" value="high_power"/>
          <el-option label="用电突增" value="sudden_usage"/>
          <el-option label="电压异常" value="voltage_issue"/>
          <el-option label="功率波动异常" value="fluctuation"/>
        </el-select>

        <el-select v-model="filterMeter" placeholder="选择电表" clearable @change="loadData">
          <el-option v-for="m in meterList" :key="m" :label="m" :value="m"/>
        </el-select>

        <el-button type="primary" @click="loadData">查询</el-button>
      </div>

      <el-table :data="tableData" border>

        <el-table-column label="时间" prop="ts" width="180">
          <template #default="{ row }">
            {{ new Date(row.ts).toLocaleString() }}
          </template>
        </el-table-column>

        <el-table-column label="电表" prop="meter_id" width="120"/>

        <el-table-column label="类型" width="140">
          <template #default="{ row }">
            <el-tag :type="tagColor(row.type)">
              {{ typeName(row.type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="详情" prop="desc"/>
      </el-table>

      <div class="pagination">
        <el-pagination
            background
            layout="prev, pager, next"
            :page-size="pageSize"
            :current-page="page"
            :total="total"
            @current-change="handlePage"/>
      </div>

    </el-card>
  </div>
</template>


<style scoped>
.page { padding: 20px; }

.filters {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.pagination {
  margin-top: 16px;
  text-align: center;
}
</style>

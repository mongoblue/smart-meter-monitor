<script setup>
import { ref, onMounted } from "vue";
import service from "@/api/request";
import { useRouter } from "vue-router";

const router = useRouter()
const bills = ref([]);
async function loadData() {
  const resp = await service.get("/power/bill/");
  bills.value = resp.bills || [];
}

function viewDetail() {
    router.push('/electricity-trend')
}

onMounted(loadData);
</script>

<template>
  <div class="page">
    <h2>历史账单</h2>

    <el-table :data="bills" border style="width: 100%">
      <el-table-column label="月份" width="140">
        <template #default="{ row }">
          {{ row.year }}-{{ String(row.month).padStart(2, "0") }}
        </template>
      </el-table-column>

      <el-table-column prop="kwh" label="总电量 (kWh)" width="160" />

      <el-table-column prop="cost" label="费用 (元)" width="160" />

      <el-table-column label="操作">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row)">详情</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>


<style scoped>
.page {
  padding: 20px;
}
</style>

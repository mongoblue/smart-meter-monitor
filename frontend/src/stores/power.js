import { defineStore } from "pinia";
import { ref, watch } from "vue";
import { ElMessage } from "element-plus";

export const usePowerStore = defineStore(
  "power",
  () => {
    /* ------------------ 实时数据 ------------------ */
    const latestRealtime = ref(null);
    const realtimeSeries = ref([]);
    const lastSavedDate = ref(null);

    function checkDailyReset() {
      const today = new Date().toISOString().slice(0, 10);
      if (lastSavedDate.value !== today) {
        realtimeSeries.value = [];
        latestRealtime.value = null;
        lastSavedDate.value = today;
      }
    }

    function saveRealtime(payload) {
      checkDailyReset();
      latestRealtime.value = payload;
    }

    function pushRealtimePoint(p) {
      checkDailyReset();

      const v = Number(p.v);
      if (Number.isNaN(v)) return;

      realtimeSeries.value.push({ t: p.t, v });

      if (realtimeSeries.value.length > 300) {
        realtimeSeries.value.splice(0, realtimeSeries.value.length - 300);
      }
    }

    function clearRealtime() {
      latestRealtime.value = null;
      realtimeSeries.value = [];
      lastSavedDate.value = new Date().toISOString().slice(0, 10);
    }

    /* ------------------ 趋势数据 ------------------ */
    const trendDay = ref(null);
    const trendWeek = ref(null);
    const trendMonth = ref(null);

    function saveTrend(type, data) {
      if (type === "day") trendDay.value = data;
      if (type === "week") trendWeek.value = data;
      if (type === "month") trendMonth.value = data;
    }

    function clearTrends() {
      trendDay.value = null;
      trendWeek.value = null;
      trendMonth.value = null;
    }

    /* ------------------ 当前电表 ------------------ */
    const meterId = ref("METER001"); // 默认电表

    /* ------------------ WebSocket ------------------ */
    const ws = ref(null);
    const wsStatus = ref("idle");

    let heartbeat = null;
    let reconnectTimer = null;
    const alertCount = ref(0);

function pushAlert() {
    alertCount.value++;
}


    /* 统一格式解析 */
function normalize(raw) {
      if (!raw) return null;

      const src = raw.data || raw;
      const devices = src.devices || {};
      const total = devices._TOTAL || {};

      return {
        raw,
        meterId: src.meter_id || src.meterId,
        powerW: Number(src.power_w || total.power_w || 0),
        voltageV: Number(src.voltage_v || total.voltage_v || 0),
        currentA: Number(src.current_a || total.current_a || 0),
        energyKWh: Number(total.energy_kwh_total || 0),
        devices,
      };
    }

function startHeartbeat() {
      if (heartbeat) clearInterval(heartbeat);
      heartbeat = setInterval(() => {
        if (ws.value?.readyState === WebSocket.OPEN) {
          ws.value.send(JSON.stringify({ type: "ping" }));
        }
      }, 15000);
    }

function cleanupWS() {
      if (heartbeat) clearInterval(heartbeat);
      if (reconnectTimer) clearTimeout(reconnectTimer);

      heartbeat = null;
      reconnectTimer = null;

      try {
        ws.value?.close();
      } catch {}

      ws.value = null;
      wsStatus.value = "idle";
    }

function connectWS() {
      cleanupWS();

      const url = `ws://${location.hostname}:8001/ws/monitor/meter/${meterId.value}/`;
      console.log("WS →", url);

      wsStatus.value = "connecting";
      ws.value = new WebSocket(url);

      ws.value.onopen = () => {
        wsStatus.value = "open";
        startHeartbeat();
      };

      ws.value.onmessage = (evt) => {
        try {
          const raw = JSON.parse(evt.data);
          if (raw.type === "alert") {
            ElMessage.error(raw.alert.desc);
            pushAlert();
            return;
          }
          const parsed = normalize(raw);
          if (!parsed) return;

          saveRealtime(parsed);
          pushRealtimePoint({ t: Date.now(), v: parsed.powerW });
        } catch (e) {
          console.warn("WS parse error:", e);
        }
      };

      ws.value.onerror = () => {
        wsStatus.value = "error";
      };

      ws.value.onclose = () => {
        wsStatus.value = "closed";
        reconnectTimer = setTimeout(() => connectWS(), 1500);
      };
    }

function changeMeter(id) {
  meterId.value = id;
  clearRealtime();
  connectWS();     // 切电表时自动切换 WebSocket
}


function reconnectWS() {
      connectWS();
    }

    /* 当 meterId 改变时自动重连 */
    watch(meterId, () => {
      clearRealtime();
      connectWS();
    });

    return {
      latestRealtime,
      realtimeSeries,
      lastSavedDate,

      trendDay,
      trendWeek,
      trendMonth,
      saveTrend,
      clearTrends,
      changeMeter,
      ws,
      wsStatus,
      meterId,
      connectWS,
      reconnectWS,
      saveRealtime,
      pushRealtimePoint,
      clearRealtime,
      checkDailyReset,
    };
  },

  {
    persist: {
      paths: [
        "meterId",
        "latestRealtime",
        "realtimeSeries",
        "trendDay",
        "trendWeek",
        "trendMonth",
      ],
    },
  }
);

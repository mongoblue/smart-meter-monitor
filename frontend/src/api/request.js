import axios from "axios";
import router from "@/router";
import { ElMessage } from "element-plus";

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8001";

const service = axios.create({
  baseURL,
  timeout: 10000,
});

service.interceptors.request.use((config) => {
  const access = localStorage.getItem("access");

  if (access) {
    config.headers.Authorization = `Bearer ${access}`;
  }

  return config;
});

service.interceptors.response.use(
  (res) => res.data,
  async (err) => {
    const original = err.config;

    if (err.response?.status === 401 && !original._retry) {
      original._retry = true;

      const refresh = localStorage.getItem("refresh");

      if (!refresh) {
        localStorage.clear();
        router.push("/login");
        return;
      }

      try {
        const resp = await axios.post(baseURL + "/user/token/refresh/", {
          refresh,
        });

        const newAccess = resp.data.access;
        localStorage.setItem("access", newAccess);

        original.headers.Authorization = `Bearer ${newAccess}`;

        return service(original); 
      } catch (e) {
        localStorage.clear();
        router.push("/login");
        return;
      }
    }
    if (err.response?.status === 400) {
      const detail = err.response.data
      const msg = Object.values(detail).flat().join('；')
      ElMessage.error(msg || '参数错误')
}
    const res = err.response
    if(err.response?.status === 403){
      ElMessage.error(res.data.info || '管理员不允许被操作')
    }

    return Promise.reject(err);
  }
);

/* 登录 */
export const login = (username, password) =>
  service.post("/user/login/", { username, password });

export default service;

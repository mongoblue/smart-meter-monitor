import {createRouter,createWebHashHistory} from 'vue-router'

const routes = [
    {
        path:'/',
        name:'main',
        component:()=>import('@/views/Main.vue'),
        children:[
            {
                path:'/',
                name:'home',
                meta:{title:'首页'},
                component:()=>import('@/views/Home.vue'),
            },
            {
                path: '/user',
                name: 'user',
                meta:{title:'用户管理'},
                component: () => import('@/views/User.vue')
            },
            {
                path: '/settings',
                name: 'settings',
                meta:{title:'系统设置'},
                component: () => import('@/views/System.vue')
            },
            {
                path: '/meter',
                name: 'meter',
                meta:{title:'电表监控'},
                component: () => import('@/views/Meter.vue')
            },
            {
                path: "/electricity-trend",
                name: "MeterRealtimeTrend",
                meta:{title:'用电趋势分析'},
                component: () => import("@/views/Trend.vue"),
            },
            {
                path: '/usage-detail',
                name: 'usageDetail',
                meta:{title:'用电明细'},
                component: () => import('@/views/UsageDetail.vue')
            },
            {
                path: '/bill',
                name: 'bill',
                meta:{title:'账单明细'},
                component: () => import('@/views/Bill.vue')
            },
            {
                path: '/alert',
                name: 'alert',
                meta:{title:'异常中心'},
                component: () => import('@/views/Alert.vue')
            }
        ],
    },
    {
        path:'/login',
        name:'login',
        label:'登录',
        component:()=>import('@/views/Login.vue')
    },
    {
        path: '/userCenter',
        name: 'userCenter',
        label:'用户中心',
        component: () => import('@/views/Usercenter.vue')
    },
]

const router=createRouter({
    history:createWebHashHistory(),
    routes,
})

router.beforeEach((to, from, next) => {
  const access = localStorage.getItem("access");
  const userMenus = JSON.parse(localStorage.getItem("menulist") || "[]");

  if (!access) {
    if (to.path === "/login") {
      return next();
    }
    return next("/login");
  }

  if (to.path === "/login") {
    return next("/");
  }

  const alwaysAllowAfterLogin = ["/login","/userCenter","/usage-detail", "/bill","/alert"];
  if (alwaysAllowAfterLogin.includes(to.path)) {
    return next();
  }

  const allowed = userMenus.some((m) => m.path === to.path);
  if (!allowed) {
    return next("/"); 
  }

  next();
});


export default router;
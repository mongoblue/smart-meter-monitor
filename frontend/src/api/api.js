import service from "./request";

export default{
    getprofile(){
        return service({
            url:'user/profile',
            method:'get'
        })
    },
    getPowerLatestMonths(){
        return service({
            url:'power/usage/lastest-month',
            method:'get'
        })
    },
    savebase(data){
        return service({
            url:'user/profile/',
            method:'post',
            data,
        })
    },
    changepwd(data){
        return service({
            url:'user/changePwd/',
            method:'post',
            data,
        })
    },
    gettoogle(row){
        return service({
            url:`/user/${row.id}/toggle/`,
            method:'post',
            row,
        })
    },
    createuser(data){
        return service({
            url:'user/',
            method:'post',
            data
        })
    },
    getuser(){
        return service({
            url:'user/',
            method:'get',
        })
    },
    deleteUser(data) {
    return service({
        url: `/user/${data.id}/delete/`,
        method: 'post',
        data,
    })
    },
    getSystemOpts() {
    return service({ 
        url: '/system/',
         method: 'get' 
    })
    },
    updateSystemOpt(pk, data) {
    return service({ 
        url: `/system/${pk}/`, 
        method: 'post', 
        data 
    })
    },
    getRoles(){
        return service({
            url:'user/role',
            method:'get'
        })
    }
}
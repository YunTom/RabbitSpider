<template>
  <div class="table">
    <div class="table1" style="width: 70%">
      <el-table ref="tableRef" row-key="name" :data="tableData" style="width: 100%" stripe="true" border>
        <el-table-column prop="name" label="任务名称" width="180"/>
        <el-table-column prop="ip_address" label="服务器地址" width="180"/>
        <el-table-column prop="sync" label="并发数" width="150"/>
        <el-table-column prop="total" label="任务数量" width="150"/>
        <el-table-column prop="status" label="任务状态" width="150"
                         :filters="[{ text: '运行中', value: '运行中' },{ text: '停止', value: '停止' },]"
                         :filter-method="filterTag">
          <template #default="scope">
            <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'">{{ scope.row.status ? '运行中' : '停止' }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="stop_time" label="停止时间" width="200"/>

        <el-table-column width="150" label="操作">
          <template #default="scope">
            <el-button type="danger" :icon="Delete" circle @click="del_msg(scope)"/>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="table2" style="width: 30%">
      <el-table :data="nextData" style="width: 100%" stripe="true" height="1000">
        <el-table-column prop="name" label="任务名称" width="150"/>
        <el-table-column prop="sleep" label="睡眠时间/分钟" width="150"/>
        <el-table-column prop="next_time" label="下次运行时间" width="180"/>
      </el-table>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {
  Delete,
} from '@element-plus/icons-vue'

import {ElMessage, ElMessageBox} from 'element-plus'
import axios from "axios";

import {ref} from 'vue'


const filterTag = (value: string, row) => {
  return row.status === value
}


var tableData = ref([])
var nextData = ref([])


const del_task = (scope) => {
  axios.post('/delete/queue', {'name': scope.row.name}).then(response => {
        tableData.value.splice(scope.$index, 1)
      }
  ).catch(response => {
  })

};


const del_msg = (scope) => {
  ElMessageBox.confirm(
      `确定删除队列${scope.row.name}？`,
      {
        confirmButtonText: 'OK',
        cancelButtonText: 'Cancel',
        type: 'warning',
      }
  ).then(() => {
    del_task(scope)
    ElMessage({
      type: 'success',
      message: `Delete ${scope.row.name}`,
    })
  }).catch(() => {
    ElMessage({
      type: 'info',
      message: 'cancel',
    })
  })
}


setInterval(function () {
  axios.get('/get/task').then(response => {
    tableData.value = response.data
  }), axios.get('/get/done').then(response => {
    nextData.value = response.data
  })
}, 3000)


</script>

<style>

.table {
  display: flex;
  flex-direction: row;
}

</style>
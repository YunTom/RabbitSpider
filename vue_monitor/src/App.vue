<template>
  <el-container style="border: 1px solid #eee">
    <el-header>
      <i style="color:#9966cc">RabbitSpider</i>
    </el-header>
  </el-container>
  <el-container style="border: 1px solid #eee">
    <el-aside width="200px" style="background-color: rgb(238, 241, 246)">
      <el-menu text-color="darkcyan">
        <el-menu-item index="1" style="height: 80px" @click="select_block(1)">
          <el-icon :size="30" style="width: 30px;">
            <sunny color="#ffcc33"></sunny>
          </el-icon>
          <el-badge :value="success_totals" type="primary">
            <span slot="title" style="font-size: 15px">运行中任务</span>
          </el-badge>
        </el-menu-item>
        <el-menu-item index="2" style="height: 80px" @click="select_block(2)">
          <el-icon :size="30" style="width: 30px;">
            <moon-night color="#6699ff"></moon-night>
          </el-icon>
          <el-badge :value="info_totals" type="success">
            <span slot="title" style="font-size: 15px">休眠中任务</span>
          </el-badge>
        </el-menu-item>
        <el-menu-item index="3" style="height: 80px" @click="select_block(3)">
          <el-icon :size="30">
            <cloudy color="#6666cc"></cloudy>
          </el-icon>
          <el-badge :value="danger_totals">
            <span slot="title" style="font-size: 15px;">异常任务</span>
          </el-badge>
        </el-menu-item>
        <el-menu-item index="4" style="height: 80px" @click="select_block(4)">
          <el-icon :size="30" style="width: 30px;">
            <sunrise color="#ffcc99"></sunrise>
          </el-icon>
          <span slot="title" style="font-size: 15px;">添加任务</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-main>
      <div v-if="block===1">
        <el-table ref="tableRef" row-key="name" :data="tableData" style="width: 100%" stripe="true" border>
          <el-table-column prop="name" label="任务名称" width="200"/>
          <el-table-column prop="ip_address" label="服务器地址" width="200"/>
          <el-table-column prop="task_count" label="并发数" width="200"/>
          <el-table-column prop="total" label="任务数量" width="200"/>
          <el-table-column prop="status" label="任务状态" width="200">
            <template #default="scope">
              <el-tag :type="'success'">运行中</el-tag>&nbsp;&nbsp;
              <el-tag>{{ scope.row.mode }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="create_time" label="创建时间" width="200"/>
          <el-table-column width="200" label="操作">
            <template #default="scope">
              <el-button type="danger" :icon="Delete" circle @click="del_msg(scope)"/>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else-if="block===2">
        <el-table ref="tableRef" row-key="name" :data="nextData" style="width: 100%" stripe="true" border>
          <el-table-column prop="name" label="任务名称" width="200"/>
          <el-table-column prop="ip_address" label="服务器地址" width="200"/>
          <el-table-column prop="task_count" label="并发数" width="200"/>
          <el-table-column prop="status" label="任务状态" width="200">
            <el-tag :type="'info'">休眠中</el-tag>
          </el-table-column>
          <el-table-column prop="next_time" label="下次运行" width="200"/>
          <el-table-column width="200" label="操作">
            <template #default="scope">
              <el-button type="danger" :icon="Delete" circle @click="del_msg(scope)"/>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else-if="block===3">
        <el-table ref="tableRef" row-key="name" :data="stopData" style="width: 100%" stripe="true" border>
          <el-table-column prop="name" label="任务名称" width="200"/>
          <el-table-column prop="ip_address" label="服务器地址" width="200"/>
          <el-table-column prop="task_count" label="并发数" width="200"/>
          <el-table-column prop="total" label="任务数量" width="200"/>
          <el-table-column prop="status" label="任务状态" width="200">
            <el-tag :type="'danger'">停止</el-tag>
          </el-table-column>
          <el-table-column prop="stop_time" label="停止时间" width="200"/>
          <el-table-column width="200" label="操作">
            <template #default="scope">
              <el-button type="danger" :icon="Delete" circle @click="del_msg(scope)"/>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else-if="block===4">
        <el-form ref="form" :model="sizeForm" label-width="120px" size="mini" :label-position="'left'">
          <el-form-item label="任务名称">
            <el-input v-model="sizeForm.name" size="large" style="width:300px"></el-input>
          </el-form-item>
          <el-form-item label="运行模式">
            <el-radio-group v-model="sizeForm.mode">
              <el-radio label="auto"></el-radio>
              <el-radio label="m"></el-radio>
              <el-radio label="w"></el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="协程数">
            <el-input-number v-model="sizeForm.task_count" @change="handleChange" :min="1" :max="20"
                             label="描述文字"></el-input-number>
          </el-form-item>
          <el-form-item label="定时crontab">
            <el-input v-model="sizeForm.crontab" style="width:300px" size="large" value="* * * * *"></el-input>
          </el-form-item>
          <el-form-item label="服务器ip">
            <el-select v-model="sizeForm.ip_address" style="width:300px" size="large">
              <el-option label="60.204.154.131" value="60.204.154.131"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="工作目录">
            <el-select v-model="sizeForm.dir" style="width:300px" size="large">
              <el-option label="emmo" value="/mnt/emmo/spiders"></el-option>
            </el-select>
          </el-form-item>
          <el-form-item size="large">
            <el-button type="primary" @click="onSubmit">立即创建</el-button>
            <el-button>取消</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-main>
  </el-container>

</template>

<script lang="ts" setup>
import {
  Delete, Sunny, Sunrise, MoonNight, Cloudy, Refresh
} from '@element-plus/icons-vue'

import {ElMessage, ElMessageBox, ElIcon} from 'element-plus'
import axios from "axios";

import {ref} from 'vue'

const tableData = ref([]);
const nextData = ref([]);
const stopData = ref([]);
const block = ref(1);
const success_totals = ref(0);
const info_totals = ref(0);
const danger_totals = ref(0);
const sizeForm = ref({name: '', mode: '', task_count: 1, crontab: '', ip_address: '', dir: ''})


const select_block = (key) => {
  block.value = key
}

const onSubmit = () => {
  axios.post(`http://${sizeForm.value.ip_address}:8000/create/task`, {
    'name': sizeForm.value.name,
    'mode': sizeForm.value.mode,
    'task_count': sizeForm.value.task_count,
    'crontab': sizeForm.value.crontab,
    'dir': sizeForm.value.dir,
    'ip_address': sizeForm.value.ip_address,
    'status': 2
  }).then(response => {
        ElMessage({
          type: 'success',
          message: `Create ${sizeForm.value.name} success`,
        })
      }
  ).catch(response => {
    ElMessage({
      type: 'warning',
      message: `${sizeForm.value.name}失败！`,
    })
  })

}


const del_task = (scope) => {
  axios.post('http://60.204.154.131:8000/delete/queue', {'pid': scope.row.pid,'name': scope.row.name}).then(response => {
        tableData.value.splice(scope.$index, 1)
      }
  ).catch(response => {
  })

};

const del_msg = (scope) => {
  ElMessageBox.confirm(
      `确定删除任务${scope.row.name}？`,
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
  if (block.value === 1) {
    axios.get('http://60.204.154.131:8000/get/task').then(response => {
      tableData.value = response.data
    })
  } else if (block.value === 2) {
    axios.get('http://60.204.154.131:8000/get/done').then(response => {
      nextData.value = response.data
    })
  } else if (block.value === 3) {
    axios.get('http://60.204.154.131:8000/get/danger').then(response => {
      stopData.value = response.data
    })
  }
  axios.get('http://60.204.154.131:8000/get/count').then(response => {
    success_totals.value = response.data['success_totals']
    info_totals.value = response.data['info_totals']
    danger_totals.value = response.data['danger_totals']
  })

}, 3000)


</script>

<style>

.el-header {
  background-color: #66CDAA;
  text-align: right;
  font-size: 40px;
}

.el-menu {
  background-color: #EDEDED;
  height: 900px
}


.el-table {
  display: flex;
  flex-direction: row;
}

</style>
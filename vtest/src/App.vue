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
          <el-badge :value="34" type="primary">
            <span slot="title" style="font-size: 15px">运行中任务</span>
          </el-badge>
        </el-menu-item>
        <el-menu-item index="2" style="height: 80px" @click="select_block(2)">
          <el-icon :size="30" style="width: 30px;">
            <moon-night color="#6699ff"></moon-night>
          </el-icon>
          <el-badge :value="34" type="success">
            <span slot="title" style="font-size: 15px">休眠任务</span>
          </el-badge>
        </el-menu-item>
        <el-menu-item index="3" style="height: 80px" @click="select_block(3)">
          <el-icon :size="30">
            <cloudy color="#6666cc"></cloudy>
          </el-icon>
          <el-badge :value="34">
            <span slot="title" style="font-size: 15px;">异常任务</span>
          </el-badge>
        </el-menu-item>
        <el-menu-item index="4" style="height: 80px">
          <el-icon :size="30" style="width: 30px;">
            <sunrise color="#ffcc99"></sunrise>
          </el-icon>
          <span slot="title" style="font-size: 15px;" @click="select_block(4)">添加任务</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-main>
      <div v-if="block===1">
        <el-table ref="tableRef" row-key="name" :data="tableData" style="width: 100%" stripe="true" border>
          <el-table-column prop="name" label="任务名称" width="200"/>
          <el-table-column prop="ip_address" label="服务器地址" width="200"/>
          <el-table-column prop="sync" label="并发数" width="200"/>
          <el-table-column prop="total" label="任务数量" width="200"/>
          <el-table-column prop="status" label="任务状态" width="200">
            <el-tag :type="'success'">'运行中'</el-tag>
          </el-table-column>
          <el-table-column prop="wait" label="运行时长" width="200"/>
          <el-table-column width="200" label="操作">
            <template #default="scope">
              <el-button type="danger" :icon="Delete" circle @click="del_msg(scope)"/>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <div v-else-if="block===2">
        <el-table ref="tableRef" row-key="name" :data="tableData" style="width: 100%" stripe="true" border>
          <el-table-column prop="name" label="任务名称" width="200"/>
          <el-table-column prop="ip_address" label="服务器地址" width="200"/>
          <el-table-column prop="sync" label="并发数" width="200"/>
          <el-table-column prop="status" label="任务状态" width="200">
            <el-tag :type="'info'">'休眠中'</el-tag>
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
        <el-table ref="tableRef" row-key="name" :data="tableData" style="width: 100%" stripe="true" border>
          <el-table-column prop="name" label="任务名称" width="200"/>
          <el-table-column prop="ip_address" label="服务器地址" width="200"/>
          <el-table-column prop="sync" label="并发数" width="200"/>
          <el-table-column prop="total" label="任务数量" width="200"/>
          <el-table-column prop="status" label="任务状态" width="200">
            <el-tag :type="'danger'">'停止'</el-tag>
          </el-table-column>
          <el-table-column prop="wait" label="运行时长" width="200"/>
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
            <el-input v-model="sizeForm.name" size="large"></el-input>
          </el-form-item>
          <el-form-item label="运行模式">
            <el-radio-group v-model="sizeForm.model">
              <el-radio label="auto"></el-radio>
              <el-radio label="m"></el-radio>
              <el-radio label="w"></el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="协程数">
            <el-input-number v-model="sizeForm.sync" @change="handleChange" :min="1" :max="10"
                             label="描述文字"></el-input-number>
          </el-form-item>
          <el-form-item label="定时任务/分钟">
            <el-input v-model="sizeForm.wait" size="large"></el-input>
          </el-form-item>
          <el-form-item label="服务器ip">
            <el-select v-model="sizeForm.ip" size="large">
              <el-option label="127.0.0.1" value="127.0.0.1"></el-option>
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
  Delete, Sunny, Sunrise, MoonNight, Cloudy
} from '@element-plus/icons-vue'

import {ElMessage, ElMessageBox, ElIcon} from 'element-plus'
import axios from "axios";

import {ref} from 'vue'

const tableData = ref([]);
const nextData = ref([]);
const block = ref(1);
const sizeForm = ref({name: '', model: '', sync: '', wait: '', ip: ''})


const select_block = (key) => {
  block.value = key
}


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


// setInterval(function () {
//   axios.get('http://127.0.0.1:8000/get/task').then(response => {
//     tableData.value = response.data
//   }), axios.get('http://127.0.0.1:8000/get/done').then(response => {
//     nextData.value = response.data
//   })
// }, 5000)


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
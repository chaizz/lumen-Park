# 首页筛选区 UI 优化设计方案

## 1. 现状分析 (Current Analysis)
目前的筛选区设计存在以下提升空间：
*   **视觉层级**：标题 "场景与分类" 与右侧的分类切换按钮（全部/光线/地点/主题）在同一行，显得较为生硬，缺乏呼吸感。
*   **容器感过强**：使用了明显的边框盒子 (`border`) 包裹，割裂了页面内容的流畅性，不太符合“小清新”的通透感。
*   **标签排版**：标签直接平铺，如果标签数量增多，会占用大量垂直空间，推挤下方内容。

## 2. 设计目标 (Design Goals)
*   **去容器化 (De-containerization)**：移除显式的外边框，利用留白划分区域，使界面更现代、通透。
*   **层级清晰**：将“分类维度”（光线/地点等）提升为一级导航，将具体“标签”作为二级筛选。
*   **交互优化**：引入横向滚动交互，容纳更多标签的同时保持页面整洁。
*   **风格统一**：深度融合 Sage Green (鼠尾草绿) 主题，使用柔和的圆角和微阴影。

## 3. 详细设计方案 (Detailed Design)

### 3.1 布局结构
放弃原本的“标题 + 右侧按钮”布局，改为两行式布局：

*   **第一行（一级维度）**：左对齐或居中的 Tab 切换栏。
    *   选项：全部 | ✨ 光线 | 📍 地点 | 📷 主题
    *   样式：文本标签，选中时文字加粗并带有底部指示条（或背景胶囊）。
*   **第二行（二级标签）**：横向滚动的标签容器。
    *   样式：胶囊形 (Pill-shaped) 标签。
    *   交互：支持鼠标拖拽或触摸滑动，两端带有白色渐变遮罩提示滚动。

### 3.2 组件样式

#### A. 维度切换器 (Category Tabs)
*   **未选中**：灰色文字 (`text-gray-500`)，无背景。
*   **选中**：主色文字 (`text-emerald-700`)，带有一个圆润的底部短横线，或者淡绿色背景胶囊。
*   **动画**：点击时有平滑的颜色过渡。

#### B. 标签 (Filter Chips)
*   **基础样式**：高度 `32px`，全圆角 (`rounded-full`)，字体 `text-sm`。
*   **未选中**：
    *   背景：`bg-white` 或极淡的 `bg-gray-50`。
    *   边框：`border border-gray-200`。
    *   文字：`text-gray-600`。
    *   Hover：`border-emerald-200 text-emerald-600`。
*   **选中 (Active)**：
    *   背景：`bg-emerald-600` (主色)。
    *   边框：无（或同色）。
    *   文字：`text-white`。
    *   阴影：`shadow-md shadow-emerald-200` (增加层次感)。

### 3.3 交互逻辑
1.  **默认状态**：一级维度选中“全部”，二级标签显示所有热门标签。
2.  **切换维度**：点击“光线”，二级标签列表带有轻微的淡入淡出动画，更新为仅显示光线相关的标签。
3.  **多选逻辑**：保持现有的多选逻辑不变，选中的标签高亮显示。

## 4. 视觉参考 (Visual Mockup Code)

```html
<!-- 容器：去边框，增加垂直间距 -->
<div class="mb-8 space-y-4">
  
  <!-- Level 1: Category Tabs -->
  <div class="flex items-center space-x-1 overflow-x-auto no-scrollbar">
    <button class="px-4 py-2 text-sm font-medium rounded-full transition-colors bg-emerald-100 text-emerald-800">
      全部
    </button>
    <button class="px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors">
      ✨ 光线
    </button>
    <!-- ... -->
  </div>

  <!-- Level 2: Tags (Horizontal Scroll) -->
  <div class="relative group">
    <!-- Left Fade Mask (visible when scrolled) -->
    <div class="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-[var(--bg-color)] to-transparent z-10 pointer-events-none"></div>
    
    <!-- Scroll Container -->
    <div class="flex space-x-3 overflow-x-auto pb-2 px-1 no-scrollbar scroll-smooth">
      <div class="flex-shrink-0 px-4 py-1.5 rounded-full text-sm border transition-all cursor-pointer bg-emerald-600 text-white shadow-md shadow-emerald-200/50 border-transparent">
        阴天
      </div>
      <div class="flex-shrink-0 px-4 py-1.5 rounded-full text-sm border border-gray-200 bg-white text-gray-600 hover:border-emerald-300 hover:text-emerald-600 transition-all cursor-pointer">
        咖啡厅
      </div>
      <!-- ... -->
    </div>

    <!-- Right Fade Mask -->
    <div class="absolute right-0 top-0 bottom-0 w-12 bg-gradient-to-l from-[var(--bg-color)] to-transparent z-10 pointer-events-none"></div>
  </div>

</div>
```

## 5. 开发计划
1.  修改 `Home.vue`，移除外层 Card 样式。
2.  重构筛选区 HTML 结构，实现上述两行布局。
3.  引入横向滚动容器，并隐藏默认滚动条。
4.  优化配色 CSS，确保符合 Sage Green 主题。

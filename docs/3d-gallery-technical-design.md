# Lumen Park 3D展厅技术设计文档

## 1. 项目概述

### 1.1 目标

为Lumen Park摄影社交平台构建一个基于Three.js的沉浸式3D虚拟展厅，让用户能够以第一人称视角浏览影集作品，提供接近真实艺术展览的体验。

### 1.2 核心特性

- **圆柱形展厅结构**：360度环绕式作品展示
- **第一人称视角**：FPS风格的漫游体验
- **智能布局系统**：根据作品数量动态调整展厅规模
- **专业画框渲染**：PBR材质和玻璃反射效果
- **多端适配**：支持桌面端鼠标、移动端触摸操作

---

## 2. 技术架构

### 2.1 技术栈选择

#### 前端3D引擎

- **TresJS** (Vue 3 + Three.js封装)
  - 原因：与现有Vue 3技术栈完美集成
  - 优势：组件化开发、响应式数据绑定、TypeScript支持

#### 核心依赖

```json
{
  "three": "^0.160.0",
  "@tresjs/core": "^3.0.0",
  "@tresjs/cientos": "^3.0.0",
  "@tresjs/post-processing": "^0.0.1"
}
```

#### 渲染管线

- **WebGL Renderer**：硬件加速渲染
- **PBR材质系统**：物理基础渲染
- **Shadow Mapping**：实时阴影效果
- **Post-processing**：后期处理效果

### 2.2 组件架构

```
Gallery3D.vue (主入口)
├── GalleryScene.vue (3D场景容器)
│   ├── ExhibitionRoom.vue (展厅结构)
│   │   ├── ArtFrame.vue (单个画框)
│   │   ├── LightingSystem.vue (光照系统)
│   │   └── Environment.vue (环境设置)
│   ├── CameraController.vue (相机控制)
│   ├── InteractionManager.vue (交互管理)
│   └── UIOverlay.vue (界面覆盖层)
├── LoadingScreen.vue (加载界面)
└── ErrorBoundary.vue (错误处理)
```

---

## 3. 展厅设计规范

### 3.1 空间布局

#### 圆柱形展厅参数

```typescript
interface GalleryConfig {
  // 基础尺寸
  radius: number;        // 8-12米，根据作品数量动态计算
  height: number;        // 6-8米，固定高度
  wallSegments: number;  // 64段，保证圆形平滑度
  
  // 作品布局
  frameHeight: number;   // 1.6米，视平线高度
  frameSpacing: number;  // 2米弧长间距
  maxFramesPerRing: number; // 16个，单层最大容量
  
  // 多层支持
  layerCount: number;    // 根据作品数量计算
  layerSpacing: number;  // 2米层间距
}
```

#### 动态半径计算算法

```typescript
const calculateRadius = (frameCount: number): number => {
  const minRadius = 8;
  const spacingPerFrame = 2; // 每个画框占用2米弧长
  const requiredCircumference = frameCount * spacingPerFrame;
  const requiredRadius = requiredCircumference / (2 * Math.PI);
  return Math.max(minRadius, requiredRadius);
};
```

### 3.2 画框系统设计

#### 画框组件结构

```typescript
interface ArtFrameConfig {
  // 基础尺寸
  width: number;         // 根据图片宽高比动态计算
  height: number;        // 固定1.2米
  depth: number;         // 0.1米厚度
  
  // 材质配置
  frameMaterial: {
    color: string;       // "#111111" 深灰色
    roughness: number;   // 0.2
    metalness: number;   // 0.1
  };
  
  glassMaterial: {
    transmission: number;  // 0.9 透明度
    roughness: number;     // 0.0 玻璃光滑度
    metalness: number;     // 0.1
    clearcoat: number;     // 1.0 清漆层
  };
}
```

#### 图片纹理处理

```typescript
class TextureManager {
  private cache: Map<string, THREE.Texture> = new Map();
  
  async loadTexture(url: string): Promise<THREE.Texture> {
    if (this.cache.has(url)) {
      return this.cache.get(url)!;
    }
  
    return new Promise((resolve, reject) => {
      const loader = new THREE.TextureLoader();
      loader.load(
        url,
        (texture) => {
          // 优化纹理设置
          texture.encoding = THREE.sRGBEncoding;
          texture.anisotropy = 16;
          texture.minFilter = THREE.LinearMipmapLinearFilter;
          texture.magFilter = THREE.LinearFilter;
    
          this.cache.set(url, texture);
          resolve(texture);
        },
        undefined,
        reject
      );
    });
  }
}
```

---

## 4. 交互控制系统

### 4.1 相机控制

#### OrbitControls配置

```typescript
const cameraConfig = {
  position: [0, 1.6, 0],      // 人眼高度
  fov: 75,                     // 视野角度
  near: 0.1,                   // 近裁剪面
  far: 1000,                   // 远裁剪面
  
  controls: {
    enableDamping: true,       // 阻尼效果
    dampingFactor: 0.05,       // 阻尼系数
    enableZoom: false,         // 禁用缩放
    enablePan: false,          // 禁用平移
    minPolarAngle: Math.PI / 3, // 俯仰角限制±30°
    maxPolarAngle: 2 * Math.PI / 3,
    rotateSpeed: 0.5,          // 旋转速度
    target: [0, 1.6, 0]        // 观察目标点
  }
};
```

#### 输入处理系统

```typescript
class InputManager {
  private mouse = new THREE.Vector2();
  private isDragging = false;
  private previousMouse = new THREE.Vector2();
  
  // 鼠标事件
  onMouseDown(event: MouseEvent) {
    this.isDragging = true;
    this.previousMouse.set(event.clientX, event.clientY);
  }
  
  onMouseMove(event: MouseEvent) {
    if (!this.isDragging) return;
  
    const deltaX = event.clientX - this.previousMouse.x;
    const deltaY = event.clientY - this.previousMouse.y;
  
    // 转换为旋转角度
    const rotationSpeed = 0.005;
    const yaw = deltaX * rotationSpeed;
    const pitch = deltaY * rotationSpeed;
  
    this.updateCameraRotation(yaw, pitch);
    this.previousMouse.set(event.clientX, event.clientY);
  }
  
  // 触摸事件
  onTouchStart(event: TouchEvent) {
    if (event.touches.length === 1) {
      this.isDragging = true;
      this.previousMouse.set(
        event.touches[0].clientX,
        event.touches[0].clientY
      );
    }
  }
  
  // 键盘事件
  onKeyDown(event: KeyboardEvent) {
    switch(event.key) {
      case 'ArrowLeft':
        this.rotateCamera(-0.1);
        break;
      case 'ArrowRight':
        this.rotateCamera(0.1);
        break;
      case ' ':
        this.resetView();
        break;
    }
  }
}
```

### 4.2 作品交互

#### 射线检测系统

```typescript
class InteractionManager {
  private raycaster = new THREE.Raycaster();
  private mouse = new THREE.Vector2();
  private frames: THREE.Mesh[] = [];
  
  updateMousePosition(event: MouseEvent) {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  }
  
  checkIntersection(): THREE.Intersection | null {
    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(this.frames);
  
    return intersects.length > 0 ? intersects[0] : null;
  }
  
  onFrameClick(frame: THREE.Mesh, post: Post) {
    // 显示作品详情
    this.showPostDetail(post);
  
    // 聚焦效果
    this.focusOnFrame(frame);
  }
}
```

---

## 5. 光照系统设计

### 5.1 多层光照方案

#### 基础光照配置

```typescript
const lightingSetup = {
  // 环境光
  ambient: {
    color: 0xffffff,
    intensity: 0.4
  },
  
  // 主方向光
  directional: {
    color: 0xffffff,
    intensity: 0.8,
    position: [10, 10, 5],
    castShadow: true,
    shadowMapSize: [2048, 2048]
  },
  
  // 天花板聚光灯组
  spotlights: Array.from({length: 6}, (_, i) => ({
    color: 0xffffff,
    intensity: 1.5,
    angle: Math.PI / 4,
    penumbra: 0.4,
    distance: 20,
    position: this.calculateSpotlightPosition(i),
    target: [0, 0, 0],
    castShadow: true
  })),
  
  // 氛围点光源
  pointLights: [
    {
      color: 0xffd700,
      intensity: 0.5,
      position: [0, 6, 0]
    },
    {
      color: 0xffffff,
      intensity: 0.3,
      position: [5, 4, 5]
    },
    {
      color: 0xffffff,
      intensity: 0.3,
      position: [-5, 4, -5]
    }
  ]
};
```

#### 动态光照系统

```typescript
class DynamicLighting {
  private spotlights: THREE.SpotLight[] = [];
  private currentFocusIndex = -1;
  
  focusOnFrame(frameIndex: number) {
    // 重置所有聚光灯
    this.resetSpotlights();
  
    // 强化聚焦画框的照明
    const spotlight = this.spotlights[frameIndex % this.spotlights.length];
    spotlight.intensity = 2.5;
    spotlight.angle = Math.PI / 6;
  
    // 添加光照过渡动画
    this.animateLightTransition(spotlight, {
      intensity: 2.5,
      angle: Math.PI / 6
    }, 500);
  }
  
  private animateLightTransition(
    light: THREE.Light, 
    target: any, 
    duration: number
  ) {
    const start = {
      intensity: light.intensity,
      angle: (light as THREE.SpotLight).angle
    };
  
    const startTime = Date.now();
  
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
  
      // 使用缓动函数
      const easeProgress = this.easeInOutCubic(progress);
  
      light.intensity = start.intensity + 
        (target.intensity - start.intensity) * easeProgress;
  
      if (light instanceof THREE.SpotLight) {
        light.angle = start.angle + 
          (target.angle - start.angle) * easeProgress;
      }
  
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
  
    animate();
  }
}
```

---

## 6. 性能优化策略

### 6.1 渲染优化

#### LOD系统实现

```typescript
class LODManager {
  private lodLevels = [
    { distance: 0, quality: 'high' },
    { distance: 10, quality: 'medium' },
    { distance: 20, quality: 'low' }
  ];
  
  updateLOD(cameraPosition: THREE.Vector3) {
    this.frames.forEach((frame, index) => {
      const distance = cameraPosition.distanceTo(frame.position);
      const lodLevel = this.getLODLevel(distance);
  
      this.updateFrameQuality(frame, lodLevel);
    });
  }
  
  private updateFrameQuality(frame: THREE.Mesh, quality: string) {
    const texture = frame.material.map;
  
    switch(quality) {
      case 'high':
        texture.anisotropy = 16;
        frame.material.roughness = 0.1;
        break;
      case 'medium':
        texture.anisotropy = 8;
        frame.material.roughness = 0.2;
        break;
      case 'low':
        texture.anisotropy = 4;
        frame.material.roughness = 0.3;
        break;
    }
  }
}
```

#### 纹理管理优化

```typescript
class TextureOptimizer {
  private compressionFormats = ['webp', 'ktx2'];
  private maxTextureSize = 1024;
  
  async optimizeTexture(originalUrl: string): Promise<string> {
    // 检查浏览器支持的格式
    const supportedFormat = this.getSupportedFormat();
  
    // 生成优化后的纹理URL
    const optimizedUrl = this.generateOptimizedUrl(
      originalUrl, 
      supportedFormat,
      this.maxTextureSize
    );
  
    return optimizedUrl;
  }
  
  private generateOptimizedUrl(
    url: string, 
    format: string, 
    size: number
  ): string {
    // 假设有图片处理服务
    const baseUrl = url.split('?')[0];
    return `${baseUrl}?format=${format}&size=${size}&quality=80`;
  }
}
```

### 6.2 内存管理

#### 资源生命周期管理

```typescript
class ResourceManager {
  private textures: Map<string, THREE.Texture> = new Map();
  private geometries: Map<string, THREE.BufferGeometry> = new Map();
  private materials: Map<string, THREE.Material> = new Map();
  
  async loadGallery(album: Album) {
    // 预加载关键资源
    await this.preloadCriticalTextures(album.posts.slice(0, 4));
  
    // 延迟加载非关键资源
    this.lazyLoadRemainingTextures(album.posts.slice(4));
  }
  
  private async preloadCriticalTextures(posts: Post[]) {
    const promises = posts.map(post => this.loadTexture(post.image_path));
    await Promise.all(promises);
  }
  
  private lazyLoadRemainingTextures(posts: Post[]) {
    posts.forEach((post, index) => {
      setTimeout(() => {
        this.loadTexture(post.image_path);
      }, index * 200); // 错开加载时间
    });
  }
  
  dispose() {
    // 清理所有资源
    this.textures.forEach(texture => texture.dispose());
    this.geometries.forEach(geometry => geometry.dispose());
    this.materials.forEach(material => material.dispose());
  
    this.textures.clear();
    this.geometries.clear();
    this.materials.clear();
  }
}
```

---

## 7. 用户体验设计

### 7.1 加载体验

#### 渐进式加载策略

```typescript
class LoadingManager {
  private loadingStages = [
    { name: '初始化3D场景', weight: 20 },
    { name: '加载展厅结构', weight: 30 },
    { name: '加载作品纹理', weight: 40 },
    { name: '优化渲染', weight: 10 }
  ];
  
  async loadGallery(album: Album) {
    const loadingScreen = new LoadingScreen();
  
    for (const stage of this.loadingStages) {
      loadingScreen.updateProgress(stage.name, stage.weight);
      await this.executeStage(stage, album);
    }
  
    loadingScreen.complete();
  }
  
  private async executeStage(stage: any, album: Album) {
    switch(stage.name) {
      case '初始化3D场景':
        await this.initializeScene();
        break;
      case '加载展厅结构':
        await this.loadGalleryStructure();
        break;
      case '加载作品纹理':
        await this.loadArtworks(album.posts);
        break;
      case '优化渲染':
        await this.optimizeRendering();
        break;
    }
  }
}
```

### 7.2 界面设计

#### HUD界面元素

```typescript
interface HUDConfig {
  // 顶部信息栏
  header: {
    title: string;
    author: string;
    workCount: number;
  };
  
  // 控制按钮
  controls: {
    resetView: boolean;
    autoRotate: boolean;
    fullscreen: boolean;
    share: boolean;
  };
  
  // 作品信息面板
  artworkInfo: {
    visible: boolean;
    position: 'bottom' | 'side';
    content: {
      title: string;
      description: string;
      camera: string;
      settings: string;
    };
  };
  
  // 导航指示器
  navigation: {
    minimap: boolean;
    progressIndicator: boolean;
    workThumbnails: boolean;
  };
}
```

---

## 8. 响应式设计

### 8.1 多设备适配

#### 设备检测与适配

```typescript
class DeviceAdapter {
  private deviceInfo = this.detectDevice();
  
  private detectDevice() {
    return {
      isMobile: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
      isTablet: /iPad|Android(?!.*Mobile)/i.test(navigator.userAgent),
      isDesktop: !/Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
  
      // 性能检测
      memory: (navigator as any).deviceMemory || 4,
      cores: navigator.hardwareConcurrency || 4,
  
      // WebRTC支持检测
      webgl: this.checkWebGLSupport()
    };
  }
  
  adaptGalleryConfig(): GalleryConfig {
    const baseConfig = this.getDefaultConfig();
  
    if (this.deviceInfo.isMobile) {
      return {
        ...baseConfig,
        maxFramesPerRing: 8,        // 减少单层画框数量
        textureQuality: 'medium',   // 降低纹理质量
        shadowQuality: 'low',       // 降低阴影质量
        antialiasing: false         // 关闭抗锯齿
      };
    }
  
    if (this.deviceInfo.isTablet) {
      return {
        ...baseConfig,
        maxFramesPerRing: 12,
        textureQuality: 'high',
        shadowQuality: 'medium',
        antialiasing: true
      };
    }
  
    return baseConfig;
  }
}
```

### 8.2 触摸交互优化

#### 手势识别系统

```typescript
class TouchGestureManager {
  private touches: Touch[] = [];
  private lastTouchTime = 0;
  private doubleTapThreshold = 300;
  
  onTouchStart(event: TouchEvent) {
    this.touches = Array.from(event.touches);
  
    switch(this.touches.length) {
      case 1:
        this.handleSingleTouch(this.touches[0]);
        break;
      case 2:
        this.handleDoubleTouch(this.touches[0], this.touches[1]);
        break;
    }
  }
  
  private handleSingleTouch(touch: Touch) {
    const currentTime = Date.now();
  
    // 检测双击
    if (currentTime - this.lastTouchTime < this.doubleTapThreshold) {
      this.onDoubleTap(touch);
    }
  
    this.lastTouchTime = currentTime;
    this.startDragRotation(touch);
  }
  
  private handleDoubleTouch(touch1: Touch, touch2: Touch) {
    // 计算两指距离用于缩放检测
    const distance = this.calculateDistance(touch1, touch2);
    this.startPinchZoom(distance);
  }
  
  private onDoubleTap(touch: Touch) {
    // 双击聚焦画框
    const intersectedFrame = this.raycastFromTouch(touch);
    if (intersectedFrame) {
      this.focusOnFrame(intersectedFrame);
    }
  }
}
```

---

## 9. 错误处理与监控

### 9.1 错误边界系统

#### 分层错误处理

```typescript
class ErrorBoundary {
  private errorTypes = {
    WEBGL_CONTEXT_LOST: 'webgl_context_lost',
    TEXTURE_LOAD_FAILED: 'texture_load_failed',
    MEMORY_LIMIT_EXCEEDED: 'memory_limit_exceeded',
    COMPATIBILITY_ISSUE: 'compatibility_issue'
  };
  
  handleError(error: Error, context: string) {
    const errorType = this.classifyError(error);
  
    switch(errorType) {
      case this.errorTypes.WEBGL_CONTEXT_LOST:
        this.handleWebGLContextLost();
        break;
      case this.errorTypes.TEXTURE_LOAD_FAILED:
        this.handleTextureLoadFailed(error);
        break;
      case this.errorTypes.MEMORY_LIMIT_EXCEEDED:
        this.handleMemoryLimitExceeded();
        break;
      case this.errorTypes.COMPATIBILITY_ISSUE:
        this.handleCompatibilityIssue(error);
        break;
    }
  
    // 上报错误日志
    this.reportError(error, context, errorType);
  }
  
  private handleWebGLContextLost() {
    // 显示降级版本或错误提示
    this.showFallbackMessage('WebGL上下文丢失，请刷新页面重试');
  
    // 尝试恢复WebGL上下文
    setTimeout(() => {
      window.location.reload();
    }, 3000);
  }
  
  private handleMemoryLimitExceeded() {
    // 清理非必要资源
    this.resourceManager.disposeNonCritical();
  
    // 降低渲染质量
    this.renderingManager.setQuality('low');
  
    // 显示性能警告
    this.showPerformanceWarning('设备性能不足，已降低渲染质量');
  }
}
```

### 9.2 性能监控

#### 实时性能监控

```typescript
class PerformanceMonitor {
  private stats = {
    fps: 0,
    frameTime: 0,
    memoryUsage: 0,
    drawCalls: 0,
    triangles: 0
  };
  
  private frameCount = 0;
  private lastTime = performance.now();
  
  startMonitoring() {
    this.monitorFrameRate();
    this.monitorMemoryUsage();
    this.monitorRenderStats();
  }
  
  private monitorFrameRate() {
    const measure = () => {
      const currentTime = performance.now();
      const deltaTime = currentTime - this.lastTime;
  
      this.frameCount++;
  
      if (deltaTime >= 1000) {
        this.stats.fps = Math.round((this.frameCount * 1000) / deltaTime);
        this.stats.frameTime = Math.round(deltaTime / this.frameCount);
  
        this.frameCount = 0;
        this.lastTime = currentTime;
  
        this.checkPerformanceThresholds();
      }
  
      requestAnimationFrame(measure);
    };
  
    requestAnimationFrame(measure);
  }
  
  private checkPerformanceThresholds() {
    if (this.stats.fps < 30) {
      console.warn('FPS低于30，当前：', this.stats.fps);
      this.suggestOptimizations();
    }
  
    if (this.stats.memoryUsage > 0.8) {
      console.warn('内存使用率过高：', this.stats.memoryUsage);
      this.triggerGarbageCollection();
    }
  }
}
```

---

## 10. 部署与优化

### 10.1 构建优化

#### Webpack配置优化

```javascript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'three': ['three'],
          'tresjs': ['@tresjs/core', '@tresjs/cientos'],
          'vendor': ['vue', 'vue-router', 'pinia']
        }
      }
    },
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  },
  
  optimizeDeps: {
    include: ['three', '@tresjs/core', '@tresjs/cientos']
  }
});
```

### 10.2 CDN配置

#### 静态资源优化

```typescript
class CDNManager {
  private cdnBase = 'https://cdn.lumen-park.com';
  
  getOptimizedTextureUrl(originalUrl: string, options: {
    format?: 'webp' | 'ktx2';
    quality?: number;
    size?: number;
  } = {}): string {
    const { format = 'webp', quality = 80, size = 1024 } = options;
  
    // 生成CDN优化URL
    return `${this.cdnBase}/images/${this.extractImageId(originalUrl)}?format=${format}&quality=${quality}&size=${size}`;
  }
  
  preloadCriticalTextures(posts: Post[]) {
    const criticalUrls = posts.slice(0, 4).map(post => 
      this.getOptimizedTextureUrl(post.image_path)
    );
  
    criticalUrls.forEach(url => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.as = 'image';
      link.href = url;
      document.head.appendChild(link);
    });
  }
}
```

## 12. 总结

本3D展厅系统为Lumen Park提供了一个技术先进、用户体验优秀的虚拟展览解决方案。通过圆柱形展厅设计、专业的光照系统、智能的性能优化和完善的错误处理机制，用户可以获得接近真实艺术展览的沉浸式体验。

系统的模块化架构确保了良好的可维护性和扩展性，为未来的功能升级和技术演进奠定了坚实基础。通过持续的性能监控和优化，系统能够在各种设备上提供流畅的3D渲染体验。

该系统不仅提升了作品展示的视觉效果，更为摄影作品的数字化展示开辟了新的可能性，是传统线上画廊向沉浸式体验升级的重要一步。

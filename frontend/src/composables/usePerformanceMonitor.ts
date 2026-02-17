import { ref, onMounted, onUnmounted } from 'vue';
import * as THREE from 'three';

export interface PerformanceStats {
  fps: number;
  frameTime: number;
  memoryUsage: number;
  drawCalls: number;
  triangles: number;
  textures: number;
  geometries: number;
}

export interface PerformanceThresholds {
  minFPS: number;
  maxFrameTime: number;
  maxMemoryUsage: number;
  maxDrawCalls: number;
}

export class PerformanceMonitor {
  private stats: PerformanceStats = {
    fps: 0,
    frameTime: 0,
    memoryUsage: 0,
    drawCalls: 0,
    triangles: 0,
    textures: 0,
    geometries: 0
  };

  private thresholds: PerformanceThresholds = {
    minFPS: 30,
    maxFrameTime: 33, // ~30fps
    maxMemoryUsage: 0.8,
    maxDrawCalls: 1000
  };

  private frameCount = 0;
  private lastTime = performance.now();
  private frameTimeHistory: number[] = [];
  private monitoringInterval: number | null = null;
  private renderer: THREE.WebGLRenderer | null = null;
  private scene: THREE.Scene | null = null;

  // 回调函数
  private onPerformanceWarning?: (stats: PerformanceStats, threshold: string) => void;
  private onPerformanceUpdate?: (stats: PerformanceStats) => void;

  constructor(
    renderer?: THREE.WebGLRenderer,
    scene?: THREE.Scene,
    options?: {
      thresholds?: Partial<PerformanceThresholds>;
      onPerformanceWarning?: (stats: PerformanceStats, threshold: string) => void;
      onPerformanceUpdate?: (stats: PerformanceStats) => void;
    }
  ) {
    this.renderer = renderer || null;
    this.scene = scene || null;
    
    if (options?.thresholds) {
      this.thresholds = { ...this.thresholds, ...options.thresholds };
    }
    
    this.onPerformanceWarning = options?.onPerformanceWarning;
    this.onPerformanceUpdate = options?.onPerformanceUpdate;
  }

  /**
   * 开始性能监控
   */
  startMonitoring(): void {
    if (this.monitoringInterval) return;

    this.monitoringInterval = window.setInterval(() => {
      this.updateStats();
      this.checkThresholds();
      
      if (this.onPerformanceUpdate) {
        this.onPerformanceUpdate(this.stats);
      }
    }, 1000); // 每秒更新一次

    this.startFrameRateMonitoring();
  }

  /**
   * 停止性能监控
   */
  stopMonitoring(): void {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = null;
    }
  }

  /**
   * 更新渲染器引用
   */
  setRenderer(renderer: THREE.WebGLRenderer): void {
    this.renderer = renderer;
  }

  /**
   * 更新场景引用
   */
  setScene(scene: THREE.Scene): void {
    this.scene = scene;
  }

  /**
   * 获取当前性能统计
   */
  getStats(): PerformanceStats {
    return { ...this.stats };
  }

  /**
   * 监控帧率
   */
  private startFrameRateMonitoring(): void {
    const measure = () => {
      const currentTime = performance.now();
      const deltaTime = currentTime - this.lastTime;

      this.frameCount++;

      if (deltaTime >= 1000) {
        this.stats.fps = Math.round((this.frameCount * 1000) / deltaTime);
        this.stats.frameTime = Math.round(deltaTime / this.frameCount);

        // 记录帧时间历史
        this.frameTimeHistory.push(this.stats.frameTime);
        if (this.frameTimeHistory.length > 10) {
          this.frameTimeHistory.shift();
        }

        this.frameCount = 0;
        this.lastTime = currentTime;
      }

      requestAnimationFrame(measure);
    };

    requestAnimationFrame(measure);
  }

  /**
   * 更新统计信息
   */
  private updateStats(): void {
    // 内存使用情况
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      this.stats.memoryUsage = memory.usedJSHeapSize / memory.jsHeapSizeLimit;
    }

    // 渲染统计
    if (this.renderer && this.renderer.info) {
      this.stats.drawCalls = this.renderer.info.render.calls;
      this.stats.triangles = this.renderer.info.render.triangles;
    }

    // 场景统计
    if (this.scene) {
      this.stats.textures = this.countTextures(this.scene);
      this.stats.geometries = this.countGeometries(this.scene);
    }
  }

  /**
   * 检查性能阈值
   */
  private checkThresholds(): void {
    // 检查FPS
    if (this.stats.fps < this.thresholds.minFPS) {
      this.handlePerformanceWarning('fps', `FPS过低: ${this.stats.fps}`);
    }

    // 检查帧时间
    if (this.stats.frameTime > this.thresholds.maxFrameTime) {
      this.handlePerformanceWarning('frameTime', `帧时间过长: ${this.stats.frameTime}ms`);
    }

    // 检查内存使用
    if (this.stats.memoryUsage > this.thresholds.maxMemoryUsage) {
      this.handlePerformanceWarning('memory', `内存使用率过高: ${(this.stats.memoryUsage * 100).toFixed(1)}%`);
    }

    // 检查绘制调用
    if (this.stats.drawCalls > this.thresholds.maxDrawCalls) {
      this.handlePerformanceWarning('drawCalls', `绘制调用过多: ${this.stats.drawCalls}`);
    }
  }

  /**
   * 处理性能警告
   */
  private handlePerformanceWarning(type: string, message: string): void {
    console.warn(`Performance Warning [${type}]: ${message}`);
    
    if (this.onPerformanceWarning) {
      this.onPerformanceWarning(this.stats, type);
    }

    // 自动优化建议
    this.suggestOptimizations(type);
  }

  /**
   * 优化建议
   */
  private suggestOptimizations(type: string): void {
    switch (type) {
      case 'fps':
      case 'frameTime':
        console.info('建议: 降低渲染质量、减少阴影、启用LOD');
        break;
      case 'memory':
        console.info('建议: 清理纹理缓存、释放未使用的几何体');
        break;
      case 'drawCalls':
        console.info('建议: 合并几何体、减少材质数量、使用实例化');
        break;
    }
  }

  /**
   * 计算场景中的纹理数量
   */
  private countTextures(scene: THREE.Scene): number {
    const textures = new Set<THREE.Texture>();
    
    scene.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        const material = object.material;
        if (Array.isArray(material)) {
          material.forEach(mat => this.collectTextures(mat, textures));
        } else {
          this.collectTextures(material, textures);
        }
      }
    });

    return textures.size;
  }

  /**
   * 收集材质中的纹理
   */
  private collectTextures(material: THREE.Material, textures: Set<THREE.Texture>): void {
    if ('map' in material && material.map) textures.add(material.map);
    if ('normalMap' in material && material.normalMap) textures.add(material.normalMap);
    if ('roughnessMap' in material && material.roughnessMap) textures.add(material.roughnessMap);
    if ('metalnessMap' in material && material.metalnessMap) textures.add(material.metalnessMap);
    if ('emissiveMap' in material && material.emissiveMap) textures.add(material.emissiveMap);
    if ('aoMap' in material && material.aoMap) textures.add(material.aoMap);
  }

  /**
   * 计算场景中的几何体数量
   */
  private countGeometries(scene: THREE.Scene): number {
    const geometries = new Set<THREE.BufferGeometry>();
    
    scene.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        geometries.add(object.geometry);
      }
    });

    return geometries.size;
  }

  /**
   * 获取平均帧时间
   */
  getAverageFrameTime(): number {
    if (this.frameTimeHistory.length === 0) return 0;
    
    const sum = this.frameTimeHistory.reduce((a, b) => a + b, 0);
    return sum / this.frameTimeHistory.length;
  }

  /**
   * 获取性能等级
   */
  getPerformanceGrade(): 'excellent' | 'good' | 'fair' | 'poor' {
    const fps = this.stats.fps;
    
    if (fps >= 60) return 'excellent';
    if (fps >= 45) return 'good';
    if (fps >= 30) return 'fair';
    return 'poor';
  }

  /**
   * 重置统计
   */
  reset(): void {
    this.stats = {
      fps: 0,
      frameTime: 0,
      memoryUsage: 0,
      drawCalls: 0,
      triangles: 0,
      textures: 0,
      geometries: 0
    };
    this.frameCount = 0;
    this.lastTime = performance.now();
    this.frameTimeHistory = [];
  }

  /**
   * 销毁监控器
   */
  dispose(): void {
    this.stopMonitoring();
    this.renderer = null;
    this.scene = null;
    this.onPerformanceWarning = undefined;
    this.onPerformanceUpdate = undefined;
  }
}

/**
 * 性能监控组合式函数
 */
export function usePerformanceMonitor(
  renderer?: THREE.WebGLRenderer,
  scene?: THREE.Scene,
  options?: {
    thresholds?: Partial<PerformanceThresholds>;
    onPerformanceWarning?: (stats: PerformanceStats, threshold: string) => void;
    onPerformanceUpdate?: (stats: PerformanceStats) => void;
  }
) {
  const monitor = new PerformanceMonitor(renderer, scene, options);
  const stats = ref<PerformanceStats>(monitor.getStats());
  const isMonitoring = ref(false);
  const performanceGrade = ref<'excellent' | 'good' | 'fair' | 'poor'>('good');

  const startMonitoring = () => {
    monitor.startMonitoring();
    isMonitoring.value = true;
  };

  const stopMonitoring = () => {
    monitor.stopMonitoring();
    isMonitoring.value = false;
  };

  const updateStats = () => {
    stats.value = monitor.getStats();
    performanceGrade.value = monitor.getPerformanceGrade();
  };

  const handlePerformanceWarning = (stats: PerformanceStats, threshold: string) => {
    console.warn(`Performance issue detected: ${threshold}`, stats);
    
    // 可以在这里添加自动优化逻辑
    if (threshold === 'memory') {
      // 触发垃圾回收提示
      console.info('Consider clearing texture cache or disposing unused objects');
    }
  };

  // 设置回调
  if (!options?.onPerformanceWarning) {
    monitor.onPerformanceWarning = handlePerformanceWarning;
  }
  
  monitor.onPerformanceUpdate = updateStats;

  onMounted(() => {
    startMonitoring();
  });

  onUnmounted(() => {
    stopMonitoring();
    monitor.dispose();
  });

  return {
    stats,
    isMonitoring,
    performanceGrade,
    startMonitoring,
    stopMonitoring,
    updateStats,
    getAverageFrameTime: () => monitor.getAverageFrameTime(),
    reset: () => monitor.reset()
  };
}
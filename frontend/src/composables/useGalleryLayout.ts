import { computed } from 'vue';

export interface GalleryConfig {
  // 基础尺寸
  radius: number;
  height: number;
  wallSegments: number;
  
  // 作品布局
  frameHeight: number;
  frameSpacing: number;
  maxFramesPerRing: number;
  
  // 多层支持
  layerCount: number;
  layerSpacing: number;
}

export interface FramePosition {
  post: any;
  position: [number, number, number];
  rotation: [number, number, number];
  layer: number;
  index: number;
}

export class GalleryLayoutManager {
  /**
   * 计算展厅半径
   * @param frameCount 画框数量
   * @param minRadius 最小半径
   * @param spacingPerFrame 每个画框占用的弧长
   */
  static calculateRadius(frameCount: number, minRadius: number = 8, spacingPerFrame: number = 2): number {
    if (frameCount === 0) return minRadius;
    
    const requiredCircumference = frameCount * spacingPerFrame;
    const requiredRadius = requiredCircumference / (2 * Math.PI);
    return Math.max(minRadius, requiredRadius);
  }

  /**
   * 计算层数
   * @param frameCount 画框数量
   * @param maxFramesPerRing 每层最大画框数
   */
  static calculateLayerCount(frameCount: number, maxFramesPerRing: number = 16): number {
    if (frameCount === 0) return 0;
    return Math.ceil(frameCount / maxFramesPerRing);
  }

  /**
   * 生成展厅配置
   * @param posts 作品列表
   */
  static generateGalleryConfig(posts: any[]): GalleryConfig {
    const frameCount = posts.length;
    const radius = this.calculateRadius(frameCount);
    const layerCount = this.calculateLayerCount(frameCount);
    
    return {
      radius,
      height: 8, // 固定8米高度
      wallSegments: 64, // 保证圆形平滑度
      
      frameHeight: 1.6, // 视平线高度
      frameSpacing: 2, // 2米弧长间距
      maxFramesPerRing: 16, // 单层最大容量
      
      layerCount,
      layerSpacing: 2 // 2米层间距
    };
  }

  /**
   * 计算画框位置
   * @param posts 作品列表
   * @param config 展厅配置
   */
  static calculateFramePositions(posts: any[], config: GalleryConfig): FramePosition[] {
    const positions: FramePosition[] = [];
    
    posts.forEach((post, index) => {
      const layer = Math.floor(index / config.maxFramesPerRing);
      const indexInLayer = index % config.maxFramesPerRing;
      
      // 计算当前层的画框数量
      const framesInCurrentLayer = Math.min(
        posts.length - layer * config.maxFramesPerRing,
        config.maxFramesPerRing
      );
      
      if (framesInCurrentLayer === 0) return;
      
      // 计算角度步长
      const angleStep = (2 * Math.PI) / framesInCurrentLayer;
      const angle = indexInLayer * angleStep;
      
      // 计算位置
      const x = config.radius * Math.sin(angle);
      const z = config.radius * Math.cos(angle);
      const y = config.frameHeight + (layer * config.layerSpacing);
      
      // 计算旋转（面向圆心）
      const rotY = angle + Math.PI;
      
      positions.push({
        post,
        position: [x, y, z],
        rotation: [0, rotY, 0],
        layer,
        index: indexInLayer
      });
    });
    
    return positions;
  }

  /**
   * 计算聚光灯位置
   * @param config 展厅配置
   * @param lightCount 灯光数量
   */
  static calculateSpotlightPositions(config: GalleryConfig, lightCount: number = 6): Array<{
    position: [number, number, number];
    target: [number, number, number];
  }> {
    const lights: Array<{
      position: [number, number, number];
      target: [number, number, number];
    }> = [];
    
    for (let i = 0; i < lightCount; i++) {
      const angle = (i / lightCount) * Math.PI * 2;
      const x = config.radius * 0.7 * Math.cos(angle);
      const z = config.radius * 0.7 * Math.sin(angle);
      const y = config.height - 0.5;
      
      lights.push({
        position: [x, y, z],
        target: [0, config.frameHeight, 0]
      });
    }
    
    return lights;
  }
}

/**
 * 展厅配置组合式函数
 */
export function useGalleryLayout(posts: any[]) {
  const config = computed(() => GalleryLayoutManager.generateGalleryConfig(posts));
  const framePositions = computed(() => 
    GalleryLayoutManager.calculateFramePositions(posts, config.value)
  );
  const spotlightPositions = computed(() => 
    GalleryLayoutManager.calculateSpotlightPositions(config.value)
  );
  
  return {
    config,
    framePositions,
    spotlightPositions
  };
}
import * as THREE from 'three';
import { ref, computed } from 'vue';

export interface LightConfig {
  ambient: {
    color: number;
    intensity: number;
  };
  directional: {
    color: number;
    intensity: number;
    position: [number, number, number];
    castShadow: boolean;
    shadowMapSize: [number, number];
  };
  spotlights: Array<{
    color: number;
    intensity: number;
    angle: number;
    penumbra: number;
    distance: number;
    position: [number, number, number];
    target: [number, number, number];
    castShadow: boolean;
  }>;
  pointLights: Array<{
    color: number;
    intensity: number;
    position: [number, number, number];
  }>;
}

export class DynamicLightingSystem {
  private scene: THREE.Scene | null = null;
  private lights: Map<string, THREE.Light> = new Map();
  private currentFocusIndex = -1;
  private animationFrameId: number | null = null;

  constructor(scene: THREE.Scene) {
    this.scene = scene;
  }

  /**
   * 初始化光照系统
   */
  initializeLighting(config: LightConfig): void {
    if (!this.scene) return;

    // 清理现有灯光
    this.clearLights();

    // 环境光
    const ambientLight = new THREE.AmbientLight(
      config.ambient.color,
      config.ambient.intensity
    );
    this.lights.set('ambient', ambientLight);
    this.scene.add(ambientLight);

    // 主方向光
    const directionalLight = new THREE.DirectionalLight(
      config.directional.color,
      config.directional.intensity
    );
    directionalLight.position.set(...config.directional.position);
    directionalLight.castShadow = config.directional.castShadow;
    directionalLight.shadow.mapSize.set(...config.directional.shadowMapSize);
    directionalLight.shadow.camera.near = 0.1;
    directionalLight.shadow.camera.far = 50;
    directionalLight.shadow.camera.left = -20;
    directionalLight.shadow.camera.right = 20;
    directionalLight.shadow.camera.top = 20;
    directionalLight.shadow.camera.bottom = -20;
    
    this.lights.set('directional', directionalLight);
    this.scene.add(directionalLight);

    // 聚光灯
    config.spotlights.forEach((spotConfig, index) => {
      const spotlight = new THREE.SpotLight(
        spotConfig.color,
        spotConfig.intensity,
        spotConfig.distance,
        spotConfig.angle,
        spotConfig.penumbra
      );
      
      spotlight.position.set(...spotConfig.position);
      spotlight.target.position.set(...spotConfig.target);
      spotlight.castShadow = spotConfig.castShadow;
      spotlight.shadow.mapSize.set(1024, 1024);
      
      this.lights.set(`spotlight_${index}`, spotlight);
      this.scene.add(spotlight);
      this.scene.add(spotlight.target);
    });

    // 点光源
    config.pointLights.forEach((pointConfig, index) => {
      const pointLight = new THREE.PointLight(
        pointConfig.color,
        pointConfig.intensity
      );
      pointLight.position.set(...pointConfig.position);
      
      this.lights.set(`pointlight_${index}`, pointLight);
      this.scene.add(pointLight);
    });
  }

  /**
   * 聚焦特定画框
   */
  focusOnFrame(frameIndex: number, duration: number = 500): Promise<void> {
    return new Promise((resolve) => {
      if (this.currentFocusIndex === frameIndex) {
        resolve();
        return;
      }

      this.currentFocusIndex = frameIndex;
      const spotlightKey = `spotlight_${frameIndex % 6}`;
      const spotlight = this.lights.get(spotlightKey) as THREE.SpotLight;

      if (!spotlight) {
        resolve();
        return;
      }

      // 重置所有聚光灯
      this.resetSpotlights();

      // 强化聚焦画框的照明
      const targetIntensity = 2.5;
      const targetAngle = Math.PI / 6;

      this.animateLightTransition(
        spotlight,
        { intensity: targetIntensity, angle: targetAngle },
        duration,
        () => resolve()
      );
    });
  }

  /**
   * 重置所有聚光灯
   */
  resetSpotlights(): void {
    this.lights.forEach((light) => {
      if (light instanceof THREE.SpotLight) {
        light.intensity = 1.5;
        light.angle = Math.PI / 4;
      }
    });
  }

  /**
   * 动画过渡光照
   */
  private animateLightTransition(
    light: THREE.Light,
    target: { intensity: number; angle?: number },
    duration: number,
    onComplete?: () => void
  ): void {
    const start = {
      intensity: light.intensity,
      angle: (light as THREE.SpotLight).angle || Math.PI / 4
    };

    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // 使用缓动函数
      const easeProgress = this.easeInOutCubic(progress);

      light.intensity = start.intensity + 
        (target.intensity - start.intensity) * easeProgress;

      if (light instanceof THREE.SpotLight && target.angle !== undefined) {
        light.angle = start.angle + 
          (target.angle - start.angle) * easeProgress;
      }

      if (progress < 1) {
        this.animationFrameId = requestAnimationFrame(animate);
      } else {
        if (onComplete) onComplete();
      }
    };

    animate();
  }

  /**
   * 缓动函数
   */
  private easeInOutCubic(t: number): number {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  /**
   * 清理所有灯光
   */
  clearLights(): void {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }

    this.lights.forEach((light) => {
      if (light instanceof THREE.SpotLight && light.target) {
        this.scene?.remove(light.target);
      }
      this.scene?.remove(light);
    });
    this.lights.clear();
  }

  /**
   * 获取光照统计
   */
  getLightStats(): { count: number; totalIntensity: number } {
    let totalIntensity = 0;
    this.lights.forEach((light) => {
      totalIntensity += light.intensity;
    });

    return {
      count: this.lights.size,
      totalIntensity
    };
  }

  /**
   * 销毁光照系统
   */
  dispose(): void {
    this.clearLights();
    this.scene = null;
  }
}

/**
 * 光照配置生成器
 */
export class LightingConfigGenerator {
  /**
   * 生成默认光照配置
   */
  static generateDefaultConfig(): LightConfig {
    return {
      ambient: {
        color: 0xffffff,
        intensity: 0.4
      },
      directional: {
        color: 0xffffff,
        intensity: 0.8,
        position: [10, 10, 5],
        castShadow: true,
        shadowMapSize: [2048, 2048]
      },
      spotlights: Array.from({ length: 6 }, (_, i) => ({
        color: 0xffffff,
        intensity: 1.5,
        angle: Math.PI / 4,
        penumbra: 0.4,
        distance: 20,
        position: this.calculateSpotlightPosition(i),
        target: [0, 1.6, 0] as [number, number, number],
        castShadow: true
      })),
      pointLights: [
        {
          color: 0xffd700,
          intensity: 0.5,
          position: [0, 6, 0] as [number, number, number]
        },
        {
          color: 0xffffff,
          intensity: 0.3,
          position: [5, 4, 5] as [number, number, number]
        },
        {
          color: 0xffffff,
          intensity: 0.3,
          position: [-5, 4, -5] as [number, number, number]
        }
      ]
    };
  }

  /**
   * 生成不同氛围的光照配置
   */
  static generateThemedConfig(theme: 'gallery' | 'dramatic' | 'soft'): LightConfig {
    const baseConfig = this.generateDefaultConfig();

    switch (theme) {
      case 'gallery':
        return {
          ...baseConfig,
          ambient: {
            color: 0xffffff,
            intensity: 0.5
          },
          directional: {
            ...baseConfig.directional,
            intensity: 1.0
          },
          spotlights: baseConfig.spotlights.map(spot => ({
            ...spot,
            intensity: 2.0,
            angle: Math.PI / 6
          }))
        };

      case 'dramatic':
        return {
          ...baseConfig,
          ambient: {
            color: 0xffffff,
            intensity: 0.2
          },
          directional: {
            ...baseConfig.directional,
            intensity: 0.6,
            color: 0xffcc99
          },
          spotlights: baseConfig.spotlights.map(spot => ({
            ...spot,
            intensity: 3.0,
            angle: Math.PI / 8,
            penumbra: 0.2
          })),
          pointLights: [
            {
              color: 0xff6b6b,
              intensity: 0.8,
              position: [0, 6, 0] as [number, number, number]
            }
          ]
        };

      case 'soft':
        return {
          ...baseConfig,
          ambient: {
            color: 0xfff5e6,
            intensity: 0.6
          },
          directional: {
            ...baseConfig.directional,
            intensity: 0.4,
            color: 0xfff5e6
          },
          spotlights: baseConfig.spotlights.map(spot => ({
            ...spot,
            intensity: 1.0,
            angle: Math.PI / 3,
            penumbra: 0.8
          }))
        };

      default:
        return baseConfig;
    }
  }

  /**
   * 计算聚光灯位置
   */
  private static calculateSpotlightPosition(index: number): [number, number, number] {
    const angle = (index / 6) * Math.PI * 2;
    const radius = 6;
    const x = radius * Math.cos(angle);
    const z = radius * Math.sin(angle);
    const y = 7.5; // 天花板高度

    return [x, y, z];
  }
}

/**
 * 光照系统组合式函数
 */
export function useDynamicLighting(scene: THREE.Scene) {
  const lightingSystem = new DynamicLightingSystem(scene);
  const currentTheme = ref<'gallery' | 'dramatic' | 'soft'>('gallery');
  const isInitialized = ref(false);

  const lightConfig = computed(() => 
    LightingConfigGenerator.generateThemedConfig(currentTheme.value)
  );

  const initializeLighting = () => {
    lightingSystem.initializeLighting(lightConfig.value);
    isInitialized.value = true;
  };

  const focusOnFrame = (frameIndex: number) => {
    return lightingSystem.focusOnFrame(frameIndex);
  };

  const resetFocus = () => {
    lightingSystem.resetSpotlights();
  };

  const changeTheme = (theme: 'gallery' | 'dramatic' | 'soft') => {
    currentTheme.value = theme;
    if (isInitialized.value) {
      lightingSystem.initializeLighting(lightConfig.value);
    }
  };

  const getLightStats = () => lightingSystem.getLightStats();

  const dispose = () => {
    lightingSystem.dispose();
    isInitialized.value = false;
  };

  return {
    currentTheme,
    lightConfig,
    isInitialized,
    initializeLighting,
    focusOnFrame,
    resetFocus,
    changeTheme,
    getLightStats,
    dispose
  };
}
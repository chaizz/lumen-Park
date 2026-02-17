import * as THREE from 'three';

export interface ArtFrameConfig {
  // 基础尺寸
  width: number;
  height: number;
  depth: number;
  
  // 材质配置
  frameMaterial: {
    color: string;
    roughness: number;
    metalness: number;
  };
  
  glassMaterial: {
    transmission: number;
    roughness: number;
    metalness: number;
    clearcoat: number;
    opacity: number;
  };
  
  // 衬纸配置
  matMaterial: {
    color: string;
    roughness: number;
  };
}

export class ArtFrameMaterialManager {
  private static textureCache: Map<string, THREE.Texture> = new Map();
  
  /**
   * 创建画框材质
   */
  static createFrameMaterial(config: ArtFrameConfig['frameMaterial']): THREE.MeshStandardMaterial {
    return new THREE.MeshStandardMaterial({
      color: config.color,
      roughness: config.roughness,
      metalness: config.metalness,
    });
  }
  
  /**
   * 创建玻璃材质
   */
  static createGlassMaterial(config: ArtFrameConfig['glassMaterial']): THREE.MeshPhysicalMaterial {
    return new THREE.MeshPhysicalMaterial({
      color: 0xffffff,
      transmission: config.transmission,
      roughness: config.roughness,
      metalness: config.metalness,
      clearcoat: config.clearcoat,
      opacity: config.opacity,
      transparent: true,
      side: THREE.DoubleSide,
    });
  }
  
  /**
   * 创建衬纸材质
   */
  static createMatMaterial(config: ArtFrameConfig['matMaterial']): THREE.MeshStandardMaterial {
    return new THREE.MeshStandardMaterial({
      color: config.color,
      roughness: config.roughness,
    });
  }
  
  /**
   * 创建图片材质
   */
  static async createImageMaterial(
    textureUrl: string,
    fallbackColor: string = '#333333'
  ): Promise<THREE.MeshStandardMaterial> {
    try {
      const texture = await this.loadTexture(textureUrl);
      
      return new THREE.MeshStandardMaterial({
        map: texture,
        color: 0xffffff,
        roughness: 0.1,
        metalness: 0.0,
      });
    } catch (error) {
      console.warn('Failed to load texture, using fallback color:', error);
      
      return new THREE.MeshStandardMaterial({
        color: fallbackColor,
        roughness: 0.8,
        metalness: 0.1,
      });
    }
  }
  
  /**
   * 加载纹理
   */
  private static loadTexture(url: string): Promise<THREE.Texture> {
    return new Promise((resolve, reject) => {
      if (this.textureCache.has(url)) {
        resolve(this.textureCache.get(url)!);
        return;
      }
      
      const loader = new THREE.TextureLoader();
      loader.load(
        url,
        (texture) => {
          // 优化纹理设置
          texture.encoding = THREE.sRGBEncoding;
          texture.anisotropy = 16;
          texture.minFilter = THREE.LinearMipmapLinearFilter;
          texture.magFilter = THREE.LinearFilter;
          texture.generateMipmaps = true;
          
          this.textureCache.set(url, texture);
          resolve(texture);
        },
        undefined,
        (error) => {
          reject(error);
        }
      );
    });
  }
  
  /**
   * 清理纹理缓存
   */
  static clearTextureCache(): void {
    this.textureCache.forEach(texture => texture.dispose());
    this.textureCache.clear();
  }
  
  /**
   * 获取纹理缓存统计
   */
  static getCacheStats(): { size: number; memoryUsage: number } {
    let memoryUsage = 0;
    this.textureCache.forEach(texture => {
      if (texture.image) {
        const width = texture.image.width || 1024;
        const height = texture.image.height || 1024;
        memoryUsage += width * height * 4; // 假设RGBA格式
      }
    });
    
    return {
      size: this.textureCache.size,
      memoryUsage
    };
  }
}

/**
 * 画框配置生成器
 */
export class ArtFrameConfigGenerator {
  /**
   * 生成默认画框配置
   */
  static generateDefaultConfig(): ArtFrameConfig {
    return {
      width: 1.2,
      height: 1.2,
      depth: 0.1,
      
      frameMaterial: {
        color: '#111111',
        roughness: 0.2,
        metalness: 0.1,
      },
      
      glassMaterial: {
        transmission: 0.9,
        roughness: 0.0,
        metalness: 0.1,
        clearcoat: 1.0,
        opacity: 0.3,
      },
      
      matMaterial: {
        color: '#ffffff',
        roughness: 0.3,
      },
    };
  }
  
  /**
   * 根据图片宽高比生成配置
   */
  static generateConfigForImage(
    imageWidth: number,
    imageHeight: number,
    baseHeight: number = 1.2
  ): ArtFrameConfig {
    const aspectRatio = imageWidth / imageHeight;
    const config = this.generateDefaultConfig();
    
    config.width = baseHeight * aspectRatio;
    config.height = baseHeight;
    
    return config;
  }
  
  /**
   * 生成不同风格的画框配置
   */
  static generateStyledConfig(style: 'modern' | 'classic' | 'minimalist'): ArtFrameConfig {
    const baseConfig = this.generateDefaultConfig();
    
    switch (style) {
      case 'modern':
        return {
          ...baseConfig,
          frameMaterial: {
            color: '#000000',
            roughness: 0.1,
            metalness: 0.2,
          },
          glassMaterial: {
            ...baseConfig.glassMaterial,
            transmission: 0.95,
            roughness: 0.0,
          },
        };
        
      case 'classic':
        return {
          ...baseConfig,
          depth: 0.15,
          frameMaterial: {
            color: '#8B4513',
            roughness: 0.4,
            metalness: 0.0,
          },
          matMaterial: {
            color: '#F5F5DC',
            roughness: 0.5,
          },
        };
        
      case 'minimalist':
        return {
          ...baseConfig,
          depth: 0.05,
          frameMaterial: {
            color: '#ffffff',
            roughness: 0.2,
            metalness: 0.0,
          },
          glassMaterial: {
            ...baseConfig.glassMaterial,
            opacity: 0.1,
          },
        };
        
      default:
        return baseConfig;
    }
  }
}

/**
 * 画框组合式函数
 */
export function useArtFrameMaterials() {
  const createFrameMaterials = async (imageUrl: string, style: 'modern' | 'classic' | 'minimalist' = 'modern') => {
    const config = ArtFrameConfigGenerator.generateStyledConfig(style);
    
    return {
      frame: ArtFrameMaterialManager.createFrameMaterial(config.frameMaterial),
      glass: ArtFrameMaterialManager.createGlassMaterial(config.glassMaterial),
      mat: ArtFrameMaterialManager.createMatMaterial(config.matMaterial),
      image: await ArtFrameMaterialManager.createImageMaterial(imageUrl),
      config,
    };
  };
  
  const getCacheStats = () => ArtFrameMaterialManager.getCacheStats();
  const clearCache = () => ArtFrameMaterialManager.clearTextureCache();
  
  return {
    createFrameMaterials,
    getCacheStats,
    clearCache,
  };
}
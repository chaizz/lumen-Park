import { ref, onMounted, onUnmounted } from 'vue';
import * as THREE from 'three';

export interface InteractionState {
  isDragging: boolean;
  isHovering: boolean;
  selectedFrame: number | null;
  hoveredFrame: number | null;
  cameraPosition: THREE.Vector3;
  cameraRotation: THREE.Euler;
}

export interface GestureState {
  touches: Touch[];
  lastTouchTime: number;
  doubleTapThreshold: number;
  initialPinchDistance: number;
  isPinching: boolean;
}

export class InteractionManager {
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private scene: THREE.Scene;
  private raycaster: THREE.Raycaster;
  private mouse: THREE.Vector2;
  private frames: THREE.Mesh[] = [];
  
  // 状态管理
  private state: InteractionState = {
    isDragging: false,
    isHovering: false,
    selectedFrame: null,
    hoveredFrame: null,
    cameraPosition: new THREE.Vector3(),
    cameraRotation: new THREE.Euler()
  };

  // 手势状态
  private gestureState: GestureState = {
    touches: [],
    lastTouchTime: 0,
    doubleTapThreshold: 300,
    initialPinchDistance: 0,
    isPinching: false
  };

  // 配置
  private config = {
    rotationSpeed: 0.005,
    doubleTapZoomFactor: 1.5,
    minZoom: 0.5,
    maxZoom: 3.0,
    autoRotateSpeed: 0.001,
    autoRotateDelay: 10000 // 10秒后开始自动旋转
  };

  // 自动旋转
  private autoRotateTimer: number | null = null;
  private isAutoRotating = false;

  // 事件回调
  private onFrameClick?: (frameIndex: number, frame: THREE.Mesh) => void;
  private onFrameHover?: (frameIndex: number | null, frame: THREE.Mesh | null) => void;
  private onCameraMove?: (position: THREE.Vector3, rotation: THREE.Euler) => void;

  constructor(
    camera: THREE.PerspectiveCamera,
    renderer: THREE.WebGLRenderer,
    scene: THREE.Scene,
    options?: {
      rotationSpeed?: number;
      doubleTapZoomFactor?: number;
      onFrameClick?: (frameIndex: number, frame: THREE.Mesh) => void;
      onFrameHover?: (frameIndex: number | null, frame: THREE.Mesh | null) => void;
      onCameraMove?: (position: THREE.Vector3, rotation: THREE.Euler) => void;
    }
  ) {
    this.camera = camera;
    this.renderer = renderer;
    this.scene = scene;
    this.raycaster = new THREE.Raycaster();
    this.mouse = new THREE.Vector2();

    if (options) {
      Object.assign(this.config, options);
      this.onFrameClick = options.onFrameClick;
      this.onFrameHover = options.onFrameHover;
      this.onCameraMove = options.onCameraMove;
    }

    this.setupEventListeners();
  }

  /**
   * 设置可交互的画框
   */
  setFrames(frames: THREE.Mesh[]): void {
    this.frames = frames;
  }

  /**
   * 获取当前交互状态
   */
  getState(): InteractionState {
    return { ...this.state };
  }

  /**
   * 设置事件监听器
   */
  private setupEventListeners(): void {
    const canvas = this.renderer.domElement;

    // 鼠标事件
    canvas.addEventListener('mousedown', this.onMouseDown.bind(this));
    canvas.addEventListener('mousemove', this.onMouseMove.bind(this));
    canvas.addEventListener('mouseup', this.onMouseUp.bind(this));
    canvas.addEventListener('click', this.onClick.bind(this));
    canvas.addEventListener('wheel', this.onWheel.bind(this));

    // 触摸事件
    canvas.addEventListener('touchstart', this.onTouchStart.bind(this));
    canvas.addEventListener('touchmove', this.onTouchMove.bind(this));
    canvas.addEventListener('touchend', this.onTouchEnd.bind(this));

    // 键盘事件
    window.addEventListener('keydown', this.onKeyDown.bind(this));

    // 防止右键菜单
    canvas.addEventListener('contextmenu', (e) => e.preventDefault());
  }

  /**
   * 鼠标按下
   */
  private onMouseDown(event: MouseEvent): void {
    if (event.button === 0) { // 左键
      this.state.isDragging = true;
      this.stopAutoRotate();
    }
  }

  /**
   * 鼠标移动
   */
  private onMouseMove(event: MouseEvent): void {
    this.updateMousePosition(event);
    
    // 检查悬停
    this.checkHover();

    if (this.state.isDragging) {
      this.handleDragRotation(event);
    }
  }

  /**
   * 鼠标释放
   */
  private onMouseUp(): void {
    this.state.isDragging = false;
    this.startAutoRotateTimer();
  }

  /**
   * 鼠标点击
   */
  private onClick(event: MouseEvent): void {
    if (this.state.isDragging) return; // 拖拽时不触发点击

    const intersection = this.getIntersection();
    if (intersection) {
      const frameIndex = this.frames.indexOf(intersection.object as THREE.Mesh);
      if (frameIndex !== -1) {
        this.selectFrame(frameIndex);
        if (this.onFrameClick) {
          this.onFrameClick(frameIndex, intersection.object as THREE.Mesh);
        }
      }
    }
  }

  /**
   * 鼠标滚轮
   */
  private onWheel(event: WheelEvent): void {
    event.preventDefault();
    
    const zoomSpeed = 0.001;
    const zoomDelta = event.deltaY * zoomSpeed;
    
    // 调整相机FOV来模拟缩放
    const currentFOV = this.camera.fov;
    const newFOV = THREE.MathUtils.clamp(
      currentFOV + zoomDelta,
      30, // 最小FOV (最大缩放)
      90  // 最大FOV (最小缩放)
    );
    
    this.camera.fov = newFOV;
    this.camera.updateProjectionMatrix();
    
    this.updateCameraState();
  }

  /**
   * 触摸开始
   */
  private onTouchStart(event: TouchEvent): void {
    event.preventDefault();
    this.gestureState.touches = Array.from(event.touches);

    switch (event.touches.length) {
      case 1:
        this.handleSingleTouch(event.touches[0]);
        break;
      case 2:
        this.handleDoubleTouch(event.touches[0], event.touches[1]);
        break;
    }
  }

  /**
   * 触摸移动
   */
  private onTouchMove(event: TouchEvent): void {
    event.preventDefault();
    
    switch (event.touches.length) {
      case 1:
        this.handleTouchDrag(event.touches[0]);
        break;
      case 2:
        this.handlePinchZoom(event.touches[0], event.touches[1]);
        break;
    }
  }

  /**
   * 触摸结束
   */
  private onTouchEnd(event: TouchEvent): void {
    event.preventDefault();
    
    if (event.touches.length === 0) {
      this.state.isDragging = false;
      this.gestureState.isPinching = false;
      this.startAutoRotateTimer();
    }
  }

  /**
   * 键盘按下
   */
  private onKeyDown(event: KeyboardEvent): void {
    switch (event.key) {
      case 'ArrowLeft':
        this.rotateCamera(-0.1);
        break;
      case 'ArrowRight':
        this.rotateCamera(0.1);
        break;
      case 'ArrowUp':
        this.tiltCamera(-0.05);
        break;
      case 'ArrowDown':
        this.tiltCamera(0.05);
        break;
      case ' ':
        event.preventDefault();
        this.resetView();
        break;
      case 'Escape':
        this.deselectFrame();
        break;
    }
  }

  /**
   * 处理单指触摸
   */
  private handleSingleTouch(touch: Touch): void {
    const currentTime = Date.now();
    
    // 检测双击
    if (currentTime - this.gestureState.lastTouchTime < this.gestureState.doubleTapThreshold) {
      this.onDoubleTap(touch);
    }
    
    this.gestureState.lastTouchTime = currentTime;
    this.state.isDragging = true;
    this.stopAutoRotate();
  }

  /**
   * 处理双指触摸
   */
  private handleDoubleTouch(touch1: Touch, touch2: Touch): void {
    const distance = this.calculateTouchDistance(touch1, touch2);
    this.gestureState.initialPinchDistance = distance;
    this.gestureState.isPinching = true;
    this.stopAutoRotate();
  }

  /**
   * 处理触摸拖拽
   */
  private handleTouchDrag(touch: Touch): void {
    if (!this.state.isDragging) return;

    const deltaX = touch.clientX - this.gestureState.touches[0]?.clientX || 0;
    const deltaY = touch.clientY - this.gestureState.touches[0]?.clientY || 0;

    this.rotateCamera(deltaX * this.config.rotationSpeed);
    this.tiltCamera(deltaY * this.config.rotationSpeed);

    this.gestureState.touches = [touch];
  }

  /**
   * 处理捏合缩放
   */
  private handlePinchZoom(touch1: Touch, touch2: Touch): void {
    const currentDistance = this.calculateTouchDistance(touch1, touch2);
    const scale = currentDistance / this.gestureState.initialPinchDistance;

    // 调整相机FOV
    const currentFOV = this.camera.fov;
    const newFOV = THREE.MathUtils.clamp(
      currentFOV / scale,
      30,
      90
    );

    this.camera.fov = newFOV;
    this.camera.updateProjectionMatrix();
    this.updateCameraState();

    this.gestureState.initialPinchDistance = currentDistance;
  }

  /**
   * 双击处理
   */
  private onDoubleTap(touch: Touch): void {
    const intersection = this.raycastFromTouch(touch);
    if (intersection) {
      const frameIndex = this.frames.indexOf(intersection.object as THREE.Mesh);
      if (frameIndex !== -1) {
        this.focusOnFrame(frameIndex);
      }
    }
  }

  /**
   * 更新鼠标位置
   */
  private updateMousePosition(event: MouseEvent): void {
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  }

  /**
   * 检查悬停
   */
  private checkHover(): void {
    const intersection = this.getIntersection();
    const hoveredFrame = intersection ? this.frames.indexOf(intersection.object as THREE.Mesh) : -1;

    if (hoveredFrame !== this.state.hoveredFrame) {
      this.state.hoveredFrame = hoveredFrame >= 0 ? hoveredFrame : null;
      
      if (this.onFrameHover) {
        this.onFrameHover(
          this.state.hoveredFrame,
          hoveredFrame >= 0 ? (intersection.object as THREE.Mesh) : null
        );
      }
    }
  }

  /**
   * 获取射线检测结果
   */
  private getIntersection(): THREE.Intersection | null {
    this.raycaster.setFromCamera(this.mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(this.frames);
    return intersects.length > 0 ? intersects[0] : null;
  }

  /**
   * 从触摸位置进行射线检测
   */
  private raycastFromTouch(touch: Touch): THREE.Intersection | null {
    const rect = this.renderer.domElement.getBoundingClientRect();
    const mouse = new THREE.Vector2();
    mouse.x = ((touch.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((touch.clientY - rect.top) / rect.height) * 2 + 1;

    this.raycaster.setFromCamera(mouse, this.camera);
    const intersects = this.raycaster.intersectObjects(this.frames);
    return intersects.length > 0 ? intersects[0] : null;
  }

  /**
   * 处理拖拽旋转
   */
  private handleDragRotation(event: MouseEvent): void {
    const deltaX = event.movementX * this.config.rotationSpeed;
    const deltaY = event.movementY * this.config.rotationSpeed;

    this.rotateCamera(deltaX);
    this.tiltCamera(deltaY);
  }

  /**
   * 旋转相机
   */
  private rotateCamera(angle: number): void {
    // 围绕Y轴旋转
    const quaternion = new THREE.Quaternion();
    quaternion.setFromAxisAngle(new THREE.Vector3(0, 1, 0), angle);
    
    this.camera.position.applyQuaternion(quaternion);
    this.camera.lookAt(0, 1.6, 0);
    
    this.updateCameraState();
  }

  /**
   * 倾斜相机
   */
  private tiltCamera(angle: number): void {
    // 限制俯仰角
    const currentRotation = this.camera.rotation.x;
    const newRotation = THREE.MathUtils.clamp(
      currentRotation + angle,
      -Math.PI / 6, // -30度
      Math.PI / 6   // +30度
    );

    this.camera.rotation.x = newRotation;
    this.updateCameraState();
  }

  /**
   * 选择画框
   */
  private selectFrame(frameIndex: number): void {
    this.state.selectedFrame = frameIndex;
    this.focusOnFrame(frameIndex);
  }

  /**
   * 取消选择画框
   */
  private deselectFrame(): void {
    this.state.selectedFrame = null;
  }

  /**
   * 聚焦画框
   */
  private focusOnFrame(frameIndex: number): void {
    const frame = this.frames[frameIndex];
    if (!frame) return;

    // 计算聚焦位置
    const framePosition = frame.position.clone();
    const offset = new THREE.Vector3(0, 0, 3); // 距离画框3米
    
    // 将偏移转换为世界坐标
    offset.applyQuaternion(frame.quaternion);
    const targetPosition = framePosition.clone().add(offset);

    // 平滑移动到聚焦位置
    this.animateCameraTo(targetPosition, framePosition);
  }

  /**
   * 动画移动相机
   */
  private animateCameraTo(
    targetPosition: THREE.Vector3,
    lookAtTarget: THREE.Vector3,
    duration: number = 1000
  ): void {
    const startPosition = this.camera.position.clone();
    const startRotation = this.camera.rotation.clone();
    
    const startTime = Date.now();

    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // 使用缓动函数
      const easeProgress = this.easeInOutCubic(progress);

      // 插值位置
      this.camera.position.lerpVectors(startPosition, targetPosition, easeProgress);
      
      // 插值旋转
      this.camera.lookAt(lookAtTarget);
      
      this.updateCameraState();

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    animate();
  }

  /**
   * 重置视角
   */
  private resetView(): void {
    const targetPosition = new THREE.Vector3(0, 1.6, 0);
    const lookAtTarget = new THREE.Vector3(0, 1.6, 1);
    
    this.animateCameraTo(targetPosition, lookAtTarget);
    this.camera.fov = 75;
    this.camera.updateProjectionMatrix();
    
    this.deselectFrame();
  }

  /**
   * 开始自动旋转计时器
   */
  private startAutoRotateTimer(): void {
    if (this.autoRotateTimer) {
      clearTimeout(this.autoRotateTimer);
    }

    this.autoRotateTimer = window.setTimeout(() => {
      this.startAutoRotate();
    }, this.config.autoRotateDelay);
  }

  /**
   * 停止自动旋转计时器
   */
  private stopAutoRotateTimer(): void {
    if (this.autoRotateTimer) {
      clearTimeout(this.autoRotateTimer);
      this.autoRotateTimer = null;
    }
  }

  /**
   * 开始自动旋转
   */
  private startAutoRotate(): void {
    this.isAutoRotating = true;
    this.autoRotate();
  }

  /**
   * 停止自动旋转
   */
  private stopAutoRotate(): void {
    this.isAutoRotating = false;
    this.stopAutoRotateTimer();
  }

  /**
   * 自动旋转
   */
  private autoRotate(): void {
    if (!this.isAutoRotating) return;

    this.rotateCamera(this.config.autoRotateSpeed);
    requestAnimationFrame(() => this.autoRotate());
  }

  /**
   * 更新相机状态
   */
  private updateCameraState(): void {
    this.state.cameraPosition.copy(this.camera.position);
    this.state.cameraRotation.copy(this.camera.rotation);

    if (this.onCameraMove) {
      this.onCameraMove(this.state.cameraPosition, this.state.cameraRotation);
    }
  }

  /**
   * 计算触摸距离
   */
  private calculateTouchDistance(touch1: Touch, touch2: Touch): number {
    const dx = touch2.clientX - touch1.clientX;
    const dy = touch2.clientY - touch1.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  }

  /**
   * 缓动函数
   */
  private easeInOutCubic(t: number): number {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  /**
   * 销毁交互管理器
   */
  dispose(): void {
    const canvas = this.renderer.domElement;
    
    // 移除事件监听器
    canvas.removeEventListener('mousedown', this.onMouseDown.bind(this));
    canvas.removeEventListener('mousemove', this.onMouseMove.bind(this));
    canvas.removeEventListener('mouseup', this.onMouseUp.bind(this));
    canvas.removeEventListener('click', this.onClick.bind(this));
    canvas.removeEventListener('wheel', this.onWheel.bind(this));
    canvas.removeEventListener('touchstart', this.onTouchStart.bind(this));
    canvas.removeEventListener('touchmove', this.onTouchMove.bind(this));
    canvas.removeEventListener('touchend', this.onTouchEnd.bind(this));
    canvas.removeEventListener('contextmenu', () => {});
    
    window.removeEventListener('keydown', this.onKeyDown.bind(this));

    this.stopAutoRotate();
    this.frames = [];
    this.onFrameClick = undefined;
    this.onFrameHover = undefined;
    this.onCameraMove = undefined;
  }
}

/**
 * 交互控制组合式函数
 */
export function useInteractionControl(
  camera: THREE.PerspectiveCamera,
  renderer: THREE.WebGLRenderer,
  scene: THREE.Scene,
  options?: {
    rotationSpeed?: number;
    doubleTapZoomFactor?: number;
    onFrameClick?: (frameIndex: number, frame: THREE.Mesh) => void;
    onFrameHover?: (frameIndex: number | null, frame: THREE.Mesh | null) => void;
    onCameraMove?: (position: THREE.Vector3, rotation: THREE.Euler) => void;
  }
) {
  const interactionManager = new InteractionManager(camera, renderer, scene, options);
  const interactionState = ref(interactionManager.getState());

  const setFrames = (frames: THREE.Mesh[]) => {
    interactionManager.setFrames(frames);
  };

  const resetView = () => {
    interactionManager['resetView']();
  };

  const focusOnFrame = (frameIndex: number) => {
    interactionManager['focusOnFrame'](frameIndex);
  };

  const getState = () => {
    interactionState.value = interactionManager.getState();
    return interactionState.value;
  };

  onUnmounted(() => {
    interactionManager.dispose();
  });

  return {
    interactionState,
    setFrames,
    resetView,
    focusOnFrame,
    getState
  };
}
# 02 Unity 引擎方案

## 2.1 Unity 版本

| 推荐 | 说明 |
|------|------|
| **Unity 2022.3 LTS** | 长期支持，插件兼容好，团队首选 |
| Unity 6 | 新特性多；若全新项目可评估，需验证 Input System / TMP 版本 |

**渲染管线**：URP 2D 或 Built-in 均可。  
- 2D 预渲染迷宫 → **Built-in + Sprite/Quad** 最简单  
- 3D 隧道 → **URP** + 烘焙光照  

垂直切片建议：**Built-in + 全屏 Quad 切换走廊图**，降低美术与 shader 成本。

## 2.2 核心 Package

| Package | 用途 |
|---------|------|
| `com.unity.textmeshpro` | UI 文本 |
| `com.unity.inputsystem` | 键鼠/手柄 |
| `com.unity.2d.sprite` | 2D 资源 |
| `com.unity.cinemachine` | 可选：城镇镜头 |
| `com.unity.nuget.newtonsoft-json` | 存档与配置 |

**不强制**：Addressables、Visual Scripting、Timeline（剧情后期可考虑 Timeline）。

## 2.3 迷宫技术方案（重点）

### 2.3.1 逻辑层：GridDungeon（与渲染解耦）

```csharp
// 概念接口
public interface IDungeonGrid {
    int Width { get; }
    int Height { get; }
    TileType GetTile(int x, int y);
    bool TryMove(Direction dir, out EncounterResult encounter);
    Direction Facing { get; }
    (int x, int y) Position { get; }
}
```

- 地图数据来自 `MapTile.csv` 或 Tiled 导出 JSON  
- 玩家 `Position + Facing` 为唯一真相源  
- 移动前检测：墙 / 门 / 楼梯 / 事件  

### 2.3.2 表现层：第一人称走廊

**方案 A — 2D 预渲染（推荐切片）**

```
每个 (tile_x, tile_y, facing) 对应一张走廊 Sprite
或：每个格子 4 方向各 1 张，转角用特殊图
```

| 优点 | 缺点 |
|------|------|
| 实现快、风格统一 | 地图变大时图量大 |
| 性能极好 | 动态光照弱 |

实现要点：
- `DungeonView` 监听 `GridMoved` 事件，换 Sprite  
- 门开/关：替换同格 `wall_variant`  
- 前方格类型为 `Wall` 显示死路图  

**方案 B — 低模 3D**

- 模块隧道 Prefab：直道、转角、T 字、门  
- `DungeonView3D` 按格拼接 Instantiated mesh  
- 相机固定玩家眼高，yaw 90° 旋转  

### 2.3.3 小地图

- `RenderTexture` 或 UI RawImage  
- `Dimension` 技能：扩大 `fogOfWar` 揭示范围（玩法联动）  

### 2.3.4 遇敌

- 每步 `Random` 对比 `encounter_rate`  
- 或固定「踩雷格」`tile_type = Encounter`  
- 触发 `BattleScene` 或同场景 `BattleState`  

## 2.4 战斗技术方案

### 状态机

```
BattleStart → PlayerCommand → ResolveAction → EnemyTurn → CheckEnd → (循环或 BattleEnd)
```

### 指令模式（可扩展技能）

```csharp
public interface IBattleCommand {
    void Execute(BattleContext ctx);
}
// AttackCommand, SkillCommand, ItemCommand, DefendCommand, EscapeCommand
```

- `BattleContext`：双方队伍、日志、RNG  
- 伤害计算读取 `SkillEffect` + `GameConst`  

### 战斗场景

| 模式 | 说明 |
|------|------|
| 叠加 UI | 迷宫场景不卸载，全屏 Battle Canvas | ✅ 切片推荐 |
| 独立 Scene | `Battle.unity` additive load | 后期特效多时用 |

## 2.5 UI 技术方案

| 界面 | 实现 |
|------|------|
| 表示面板 | 独立 Canvas，`GamePanelController` 切换页签 |
| 战斗 UI | `BattleUI` 绑定 `BattleStateMachine` |
| 对话 | `DialogueUI` + `Dialogue.csv` 驱动 |
| 城镇 | `TownUI` 设施按钮 → `ShopPanel` / `InnPanel` |

**本地化**：`Localization.csv` → 启动时载入 `Dictionary<string,string>`；TMP 自动换字体。

## 2.6 音频

- `AudioManager` 单例：BGM 层 + SE 层  
- BGM 随 `DungeonFloor.bgm_id` 切换  
- 脚步 SE 同步格点移动事件  

## 2.7 输入映射

| 动作 | 键鼠 | 手柄 |
|------|------|------|
| 前进 | W / ↑ | 左摇杆上 |
| 左转 | A / ← | LB |
| 右转 | D / → | RB |
| 后退 | S | 下 |
| 菜单 | Esc / Tab | Start |
| 表示 | C | Y |

## 2.8 可选第三方插件（评估用）

| 插件 | 用途 | 建议 |
|------|------|------|
| Odin Inspector | 配置 SO 编辑 | 可选，提升策划体验 |
| DOTween | UI 动效 | 可选 |
| Yarn Spinner | 对话 | 与 CSV 二选一 |
| A* | 寻路 | ❌ 格点移动不需要 |

## 2.9 性能注意

- 迷宫贴图 Atlas 合并  
- 战斗立绘异步加载  
- 配置表启动时一次加载进 `GameDatabase` 单例，避免战斗中读盘  

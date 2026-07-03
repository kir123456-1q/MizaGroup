# 02 Godot 引擎方案

## 2.1 Godot 版本

| 推荐 | 说明 |
|------|------|
| **Godot 4.4+** | 稳定 4.x；Forward+ 渲染；个人开发首选 |
| .NET 版 | **不选用** — 切片以 GDScript 为主，迭代更快 |

**渲染**：

- 迷宫第一人称 → **3D 场景 + 相机 yaw** 或 **全屏 TextureRect 预渲染**  
- 战斗/城镇 → **Control** 树 UI  
- 小地图 → **TileMapLayer** + [TileMapDual](https://github.com/pablogila/TileMapDual) 插件（双网格）

垂直切片建议：**预渲染走廊贴到 Quad/Sprite3D**，逻辑仍用 `GridDungeon`（与渲染解耦）。

## 2.2 核心组件与插件

| 组件 | 用途 |
|------|------|
| `Control` + `Theme` | 表示 UI、战斗、城镇 |
| `Label` / `RichTextLabel` | 文本（思源黑体 TTF） |
| `InputMap` | 键鼠/手柄（项目设置） |
| `AudioStreamPlayer` / `Bus` | BGM / SE 分层 |
| `JSON` / `FileAccess` | 存档与配置 |
| `Resource` (.tres) | 运行时配置缓存 |
| **TileMapDual**（addons） | 小地图双网格 autotile |
| **Dialogic 2**（可选） | 对话 Timeline；切片可用 CSV 自研 |

**不强制**：C# 模块、NavigationAgent（格点不需要）、多人网络。

## 2.3 迷宫技术方案（重点）

### 2.3.1 逻辑层：GridDungeon（与渲染解耦）

```gdscript
# scripts/domain/dungeon_grid.gd
class_name DungeonGrid
extends RefCounted

func try_move(dir: int) -> Dictionary:
    # 返回 { ok, encounter, event_id }
    pass
```

- 地图：`MapTile.csv` 或 Tiled 导出 JSON → 启动时载入 `Dictionary`  
- 真相源：`position: Vector2i` + `facing: int`  
- 检测：墙 / 门 / 楼梯 / 事件 / 陷阱 / 区域（wild vs safe）

### 2.3.2 表现层：第一人称走廊

**方案 A — 预渲染（推荐切片）**

```
dungeon_view.gd 订阅 EventBus.dungeon_moved
  → 查 (x, y, facing, zone, wall_variant) → 换 texture
```

| 优点 | 缺点 |
|------|------|
| 个人开发快、风格统一 | 大地图贴图量 |
| Godot 加载 Texture 轻量 | 动态光弱 |

**方案 B — 低模 3D GridMap**

- `MeshLibrary`：直道、转角、门、灯（正道）  
- `dungeon_view_3d.gd` 按格实例化；相机 `Camera3D` 眼高 1.6m  

### 2.3.3 小地图（双网格）

| 层 | 节点 | 说明 |
|----|------|------|
| 数据 | `TileMapLayer`（逻辑） | 墙/路/门；不显示或单色 |
| 渲染 | `TileMapDual`（半格偏移） | 16 tile 圆角；见策划案 12 |

`Dimension` 技能：扩大 `fog_of_war` 数组，与 `mod_dimension_map` 叠乘。

### 2.3.4 遇敌

- 每步 `randf()` vs `encounter_rate`（受 SubApp 式模块调节）  
- 固定格 `tile_type = Encounter`  
- 触发 `GameState` → `Battle`（同场景 UI 层）

## 2.4 咏唱与战斗（Godot）

```gdscript
# scripts/gameplay/battle/battle_state_machine.gd
enum State { START, PLAYER_CMD, CHANTING, RESOLVE, ENEMY, CHECK_END }
```

- 咏唱回合：`chant_panel.tscn` 显示 `verse_key` 本地化诗句  
- 代价：`GameSession.chant_debts` 在 `autoload/game_session.gd` 维护  
- 详见策划案 [11-咏唱咒术与整备系统](../策划案/11-咏唱咒术与整备系统.md)

## 2.5 UI 技术方案

| 界面 | 场景 |
|------|------|
| 表示面板 | `ui/representation/representation_panel.tscn` |
| 战斗 | `ui/battle/battle_overlay.tscn` |
| 对话 | `ui/dialogue/dialogue_box.tscn` + CSV |
| 城镇 | `ui/town/town_hub.tscn` |
| 整备所 | `ui/town/guild_workshop.tscn`（模块/刻印） |

**本地化**：`Localization.csv` → `Autoload/Localization`；`tr(key)` 包装。

## 2.6 音频

- `AudioManager`（Autoload）：BGM 交叉淡化  
- `DungeonFloor.bgm_id` 切换；正道/野外用不同混响 Bus  

## 2.7 输入映射（InputMap）

| 动作 | 键鼠 | 手柄 |
|------|------|------|
| move_forward | W / ↑ | 左摇杆上 |
| turn_left | A / ← | LB |
| turn_right | D / → | RB |
| move_back | S | 下 |
| menu | Esc | Start |
| representation | C | Y |
| chant_confirm | Space | A |

## 2.8 推荐参考工程

| 项目 | 用途 |
|------|------|
| [GridFpsDungeonCrawler](https://github.com/bengo501/GridFpsDungeonCrawler) | 格点 FPS + 战斗框架 |
| [RNB Dungeon Template](https://rnb-games.itch.io/dungeon-crawler-godot-template) | 回合 + 3D 迷宫 |
| [TileMapDual](https://github.com/pablogila/TileMapDual) | 双网格小地图 |

## 2.9 性能注意

- 走廊贴图 `compress_mode=VRAM Compressed`，合并 Atlas  
- 配置表启动一次载入 `GameDatabase`  
- 战斗立绘 `load_threaded_request` 异步  

## 2.10 项目结构

```
MizaDRPG/
├── project.godot
├── addons/
│   └── tile_map_dual/
├── assets/                 # 见策划案 12
├── data/
│   ├── source_csv/         # 从 策划案/samples 同步
│   └── generated/          # .tres（可选 gitignore）
├── scenes/
│   ├── boot/
│   ├── title/
│   ├── town/
│   ├── dungeon/
│   └── ui/
└── scripts/
    ├── autoload/
    ├── core/
    ├── domain/
    ├── gameplay/
    └── editor/               # @tool 导入器
```

---

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 0.1 | 2026-07-03 | 自 Unity 方案迁移；Godot 4.4 定稿 |

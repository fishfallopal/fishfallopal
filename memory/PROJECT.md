# Wildveil — устройство проекта

Игра про ловлю и прокачку существ (в духе Palworld/Pokémon): зоны-биомы, орбы для поимки, компаньоны,
бои, база-святилище (Sanctuary), рейды, ежедневные награды, геймпассы.
Снимок сделан 2026-11-01 через MCP. Число в скобках — строк кода (ориентир по размеру).

## Запуск

- **Сервер:** `ServerScriptService.Server.Bootstrap` (Script). Порядок:
  `Network.InitializeRemotes` → мир (`WorldBuilder.BuildWorld()` пропускается, если
  `workspace.WildveilMap` имеет атрибут `Authored = true` — сейчас это так) → `BaseService.BuildSanctuaryHub()` →
  прореживание PointLight у `Wildflowers` → `Init()` сервисов:
  Time, PlayerData, GamePass, Companion, Creature, Capture, Quest, Economy, Provisions, DailyReward,
  Inventory, Zone, Spawn, затем `CombatService.Init(Events)`, `BaseService.Init(Events, Functions)`,
  AntiCheat, `RaidService.Init(Events)`.
- **Клиент:** `StarterPlayer.StarterPlayerScripts.Client.Bootstrap` (LocalScript) загружает контроллеры из
  `Client.Controllers` и инициализирует их.
- Ожидаемый лог: `[Wildveil] Server initialization complete!` и `[Wildveil Client] Controllers initialized successfully!`.

## Сервер — `ServerScriptService.Server.Services` (ModuleScript)

| Сервис | Строк | Назначение |
|---|---|---|
| PlayerDataService | 542 | Профили в DataStore `WildveilPlayerData_v1`, ключ `Wildveil_Profile_v1_<UserId>`. 3 ретрая загрузки/сохранения; при провале загрузки — дефолты и **сохранение отключено** на сессию. Автосейв 120 с, сейв при выходе и BindToClose. Сигналы `OnDataLoaded`, `OnLevelUp`, `OnEssenceGained`. Remotes: `GetPlayerData`, `ToggleFavorite`, `SaveSettings` (rate-limit 0.5 с), синк через `DataUpdate`. |
| CaptureService | 493 | Поимка существ орбами |
| CreatureService / CreatureModelFactory | 353 / 484 | Дикие существа, сборка моделей |
| SpawnService | 153 | Спавн существ по зонам |
| ZoneService | 88 | Зоны, открытие зон |
| CombatService / BattleEngine | 506 / 356 | Бои |
| CompanionService | 777 | Компаньоны игрока |
| BaseService / SanctuaryHubVisuals | 410 / 487 | База-святилище, хаб |
| RaidService | 1320 | Рейды (логово `WebweaverLair` в `ServerStorage.RaidAssets`) |
| EconomyService, InventoryService, ProvisionsService | 68 / 204 / 153 | Валюты, инвентарь/рюкзак, провизия (магазин) |
| QuestService, DailyRewardService, GamePassService | 140 / 87 / 369 | Квесты, ежедневки, геймпассы |
| AntiCheatService | 313 | Античит, считает вызовы remotes |
| TimeService | 42 | Время суток |
| WorldBuilder | 780 | Процедурный мир (сейчас не используется — карта авторская) |

## Shared — `ReplicatedStorage.Shared`

- `Types` — общие типы.
- `Network.Network` — объявления RemoteEvent/RemoteFunction; создаёт папки `ReplicatedStorage.Events` и
  `ReplicatedStorage.Functions`. **Новые remotes добавлять здесь.**
- `Config.*`: Economy, Orbs, Rarities, Zones, BaseConfig, CombatMoves, CompanionAbilities, GamePasses,
  Provisions, DailyRewards, Items, RaidConfig, MinimapData, OrbIcons, ChatEmojis, CreatureVFX,
  CreatureBoneRigs (666), FlaremopRigAnimator (1104), UiTheme (972).
- `CreatureDefinitions.Creatures` — 13 существ: Drizzlefin (Uncommon, Mist), Pufflo (Common, Air),
  Bloombyte (Rare, Nature), Eclipseed (Ancient, Void), Noctilume (Epic, Moon), Mosswisp (Common, Nature),
  Voltik (Rare, Storm), Sporeloom (Uncommon, Nature), Craggle (Uncommon, Stone), AuroraDrake (Ancient, Air),
  Prismole (Epic, Crystal), Aeronook (Mythic, Air), Flaremop (Common, Ember).
- `Quests.QuestDefinitions`.
- `Utilities`: Signal, MathUtils, NumberText, UIAnim, Motion, UiComponents (794), OrbThrowMath, PalStyle.

Зоны (`Config.Zones`): Meadowlight Glade (стартовая), Mistwood Canopy, Glimmerbog Marsh, Frostveil Tundra,
Emberfall Caldera, Starfall Crater.

## Клиент — `StarterPlayer.StarterPlayerScripts`

- `Client.Controllers`: UIController (2652, главный UI), UIModalManager, UIScreenBase, UIScreenRegistry, HUDOverlay,
  PalHud, CombatController (1144), BattleScene, BattleVFXController (1268), CaptureController, OrbAimController,
  InteractionController, PromptStyle, BaseController, SanctuaryStationPanel, BackpackPanel, CreatureBoxPanel,
  WorldMapPanel, GamePassPanel, ProvisionsPanel, DailyRewardsPanel, SettingsController, Keybinds,
  MovementController, StaminaRing, CameraController, ChatController, AudioVFXController, CreatureVFXController,
  CreatureMotionSmoother, BoneRigVFX, BiomeAmbience, RaidController.
- Аниматоры ригов: `Client.VoxelRigAnimator`, `Client.SkinnedRigAnimator`, `Client.BoneRigAnimator`.
- Отдельно: `SingularitySpin`, `HubAmbientMotion` (визуал хаба).

## Мир — `Workspace`

- `WildveilMap` (~10.5k объектов, `Authored = true`): Environment, Locations, Biomes, VeilArchiveShrine,
  SanctuarySpawn, Wildflowers, CelestialSingularity. Плюс Terrain.
- Витрины: `BattleStagePreview`, `OrbShowcase`, `Showcase_Mosswisp`, `Showcase_Flaremop`.

## ServerStorage

- Инструменты разработки (ModuleScript, запускаются вручную через `execute_luau`): `VoxelMeshRigBuilder`,
  `VoxelBoneRigBuilder`, `VoxelGlbRigImporter` (+ `VoxelGlbSources`), `SpiderRigBuilder`, `Dev_BiomeTerrain`,
  `Dev_BiomeProps`, `Dev_SmoothMountains`, `Dev_RaidLairBuilder`.
- Ассеты: `WildveilAssets`, `WildveilProps`, `VoxelMeshAssets`, `RaidAssets`, `RBX_ANIMSAVES`.
- `VFX_Studio_Plugin` — исходники VFX-плагина (не игровой код).
- `LegacyCreatureArchive`, `ScriptsBeforeEdit` — старые версии.

## Бэкапы (конвенция)

Перед правкой создаётся папка в `ServerStorage` с именем `Backup_YYYY-MM-DD_<Причина>`
(например `Backup_2026-10-31_BeforeStamina`). Скрипты внутри — клоны с именем полного пути через `_`:
`ServerScriptService_Server_Services_BaseService`. Для мира — клоны моделей; для терейна — `TerrainRegion`.
Бэкапы старше нескольких итераций можно чистить только с согласия пользователя.

## Studio-атрибуты для тестов

- `PlayerDataService.UseStudioDataStores` (не задан → в Studio данные в памяти, DataStore не трогается).
- `GamePassService.StudioGrantAll` (bool), `GamePassService.StudioGrant` (string) — выдать пассы в Studio.
- `RaidService.ForcePortal` (bool) — принудительно открыть портал рейда.
- `WildveilMap.Authored` — использовать авторскую карту вместо WorldBuilder.

## Известный шум в консоли (не баги игры)

- `Failed to load plugin ... VFXStudio.rbxm` — локальный плагин в Play-режиме.
- `ContentId: rbxassetid://203785492 failed due to: Asset type does not match requested type` — где-то
  используется ассет не того типа; источник не найден (кандидат на починку).
- Лог `Constructing 3-Zone World...` устарел — зон уже 6.

# Прогресс и журнал итераций

## Текущее состояние (на 2026-11-01)

- Игра запускается без ошибок скриптов: сервер и клиент доходят до «initialization complete».
- Карта авторская (`WildveilMap.Authored = true`), 6 зон-биомов, хаб-святилище с CelestialSingularity.
- Реализованы: поимка, компаньоны, бои (с VFX), база, рейды (WebweaverLair), провизия-магазин, рюкзак,
  ежедневки, геймпассы, античит, стамина, настройки, карта мира.
- Последняя известная работа (31.10): удаление «точек» в UI/сервисах (`Backup_2026-10-31_BeforeDotRemoval`),
  рейды и логово, стамина, сглаживание гор, фикс C1 у ригов существ, skinned-риг Sporeloom.

## Следующие шаги / открытые вопросы

- Найти источник `rbxassetid://203785492` (ошибка типа ассета) и исправить.
- Обновить устаревший лог `Constructing 3-Zone World...` в `Server.Bootstrap`.
- Решить с пользователем, нужны ли старые бэкапы 26–30.10 в `ServerStorage`.
- Дальнейшие задачи уточнять у пользователя и записывать сюда.

## Журнал итераций

Записи до 2026-11-01 восстановлены по папкам-бэкапам в `ServerStorage` (точное содержание работ — по названию).
Новые записи добавлять **сверху**.

### 2026-11-01 — создание памяти для агентов
- Созданы `AGENTS.md`, `memory/PROJECT.md`, `memory/PROGRESS.md` (снимок проекта через MCP). Place не изменялся.

### 2026-10-31
- Фикс C1 у ригов всех существ и Flaremop (`Backup_2026-10-31_CreatureRigsBeforeC1Fix`, `..._FlaremopBeforeC1Fix`).
- Переделка CelestialSingularity (`Backup_2026-10-31_SingularityBefore`).
- Skinned-риг Sporeloom (`Backup_2026-10-31_SporeloomSkinned`), импорт GLB (`VoxelGlbRigImporter`).
- Стамина: MovementController + StaminaRing (`Backup_2026-10-31_BeforeStamina`).
- Сглаживание террейна/гор (`Backup_2026-10-31_TerrainBeforeSmooth`, `Dev_SmoothMountains`).
- Рейды: `RaidService`, `RaidController`, `RaidConfig`, логово `WebweaverLair` (`Dev_RaidLairBuilder`, `SpiderRigBuilder`).
- Удаление «точек» в ряде сервисов и UI-панелей (`Backup_2026-10-31_BeforeDotRemoval`).

### 2026-10-30
- Сглаживание движения существ (`MotionBackup_..._BeforeSmoothing`), биомы террейна (`TerrainBackup_..._BeforeBiomes`).
- Ежедневные награды, импорт пропсов, управление и рюкзак, мост/аврора, античит.
- Рестайл спавна и святыни, риги существ (`..._CreatureRigsBeforeHtml`).

### 2026-10-29
- Бои: багфиксы, глубина, VFX (`CombatBackup_*`). Провизия-магазин. Кристаллы и разделение Sanctuary.
- Рестайл UI в PalStyle (`UIRestyleBackup_..._BeforePalStyle`).

### 2026-10-26 … 2026-10-27
- Создание и масштабирование мира, локации, редизайн декора, водопад, прореживание деревьев.

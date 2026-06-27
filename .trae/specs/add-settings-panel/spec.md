# 添加设置面板 (Settings Panel) Spec

## Why

当前 `SelectionWindow` 主界面直接暴露「语言」和「主题」两个下拉框，随着可配置项增加会占用越来越多的主界面空间，且不够清晰。用户希望把配置项集中到独立的设置界面中，并新增 UI 字体、GTP 渲染字体以及对 `ApolloTab.utils.constants.RenderConfig` 中渲染参数的可视化调节能力。

## What Changes

- **新增 `SettingsDialog` 类**: 独立的设置对话框，使用标签页/分组形式组织配置项
  - 「常规」分组：语言、主题、UI 字体
  - 「GTP 渲染」分组：GTP 渲染字体 + `RenderConfig` 第 359–390 行的所有参数
- **SelectionWindow 改造**:
  - 移除主界面中的语言和主题下拉框
  - 在工具栏/标题栏区域新增「设置」按钮（齿轮图标）
  - 点击设置按钮打开 `SettingsDialog`
- **配置持久化扩展**:
  - `config/settings.json` 新增字段：`ui_font`、`gtp_font`、`render_config`
  - 启动时读取并应用；设置对话框中修改后保存
- **运行时应用**:
  - 语言切换：保持现有行为（保存配置并提示重启）
  - 主题切换：保持现有行为（实时刷新所有窗口）
  - UI 字体切换：实时刷新 `SelectionWindow` / `DisplayWindow` 样式表
  - GTP 渲染设置：修改 `RenderConfig` 类属性，下次渲染（重新打开文件或刷新）时生效
- **翻译扩展**: 在 `locales/zh_CN.json`、`locales/en_US.json` 和 `locales/ru_RU.json` 中新增设置面板相关翻译键

## Impact

- Affected specs: 无现有冲突 spec
- Affected code:
  - `TAB Score Viewer.py`: `SelectionWindow`、`SettingsDialog`、配置读写、主题/字体应用
  - `config/settings.json`: 新增字段
  - `locales/zh_CN.json` / `locales/en_US.json` / `locales/ru_RU.json`: 新增翻译键
  - `readme/功能更新.md`: 记录本次变更
  - `readme/开发文档.md` / `readme/实施文档.md`: 同步更新架构说明

## ADDED Requirements

### Requirement: 设置按钮与设置对话框

The system SHALL provide a settings button in `SelectionWindow` that opens a dedicated settings dialog.

#### Scenario: 打开设置
- **WHEN** 用户点击主界面「设置」按钮
- **THEN** 弹出设置对话框，对话框内包含「常规」和「GTP 渲染」两个分组/标签页

### Requirement: 常规设置

The system SHALL allow users to configure language, theme, and UI font in the settings dialog.

#### Scenario: 修改语言
- **WHEN** 用户在设置对话框切换语言
- **THEN** 保存配置，弹出提示告知用户重启后完全生效

#### Scenario: 修改主题
- **WHEN** 用户在设置对话框切换主题
- **THEN** 实时应用主题到所有已打开窗口，并保存配置

#### Scenario: 修改 UI 字体
- **WHEN** 用户在设置对话框选择 UI 字体
- **THEN** 实时刷新主窗口和谱面显示窗口的 `font-family`，并保存配置

### Requirement: GTP 渲染设置

The system SHALL allow users to configure the GTP rendering font and all `RenderConfig` parameters from lines 359–390.

#### Scenario: 修改 GTP 渲染字体
- **WHEN** 用户在设置对话框选择 GTP 渲染字体
- **THEN** 更新 `RenderConfig.NOTE_FONT_FAMILY`，并在下次渲染时生效

#### Scenario: 修改渲染参数
- **WHEN** 用户调节弦线间距、品格数字大小、行间距等参数
- **THEN** 更新对应 `RenderConfig` 类属性，并在下次渲染时生效

### Requirement: 配置持久化

The system SHALL save all settings to `config/settings.json` and restore them on startup.

#### Scenario: 启动恢复
- **WHEN** 应用启动
- **THEN** 从 `config/settings.json` 读取语言、主题、UI 字体、GTP 渲染字体和渲染参数并应用

## MODIFIED Requirements

### Requirement: 主界面布局

`SelectionWindow` 不再在主界面直接显示语言和主题下拉框，改由设置按钮进入设置对话框统一配置。

#### Scenario: 主界面简化
- **WHEN** 用户打开主界面
- **THEN** 只看到文件夹选择、搜索/文件列表和设置按钮

## REMOVED Requirements

无功能移除，仅将语言和主题控件从主界面迁移到设置对话框。

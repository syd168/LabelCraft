# LabelCraft 多语言翻译指南

> **现代化 i18n 系统 - 基于 JSON 格式**

## 📋 目录

1. [概述](#概述)
2. [文件结构](#文件结构)
3. [添加新语言](#添加新语言)
4. [翻译步骤](#翻译步骤)
5. [翻译规范](#翻译规范)
6. [在代码中使用](#在代码中使用)
7. [测试与验证](#测试与验证)
8. [常见问题](#常见问题)

---

## 概述

LabelCraft 使用现代化的 i18n 引擎来支持国际化。所有用户界面的文本都存储在 `locales/` 目录下的 JSON 文件中，程序运行时根据用户选择的语言动态加载对应的翻译，**无需重启**。

### 核心特性

- ✅ **动态语言切换** - 无需重启程序即可切换语言
- ✅ **JSON 格式** - 易于编辑和维护
- ✅ **嵌套键结构** - 更好的组织和可读性
- ✅ **参数插值** - 支持 `{name}`, `{count}` 等占位符
- ✅ **HTML 支持** - 支持富文本格式
- ✅ **自动回退** - 缺失的翻译自动回退到英文

### 支持的语言

- **English** (en) - 默认语言
- **简体中文** (zh-CN)
- **繁體中文** (zh-TW)
- **日本語** (ja-JP)
- **Deutsch** (de-DE)
- **Français** (fr-FR)

---

## 文件结构

多语言文件位于 `locales/` 目录下：

```
locales/
├── en.json          # 英文（默认语言）
├── zh-CN.json       # 简体中文
├── zh-TW.json       # 繁体中文
├── ja-JP.json       # 日语
├── de-DE.json       # 德语
└── fr-FR.json       # 法语
```

### JSON 格式示例

每个 JSON 文件使用嵌套结构组织翻译键：

```json
{
  "menu": {
    "file": "File",
    "edit": "Edit",
    "view": "View"
  },
  "actions": {
    "openFile": "Open",
    "save": "Save",
    "quit": "Quit"
  },
  "panels": {
    "output_settings": "Output Settings",
    "output_path": "Output Path:"
  },
  "messages": {
    "success": "Success!",
    "error": "Error occurred",
    "items_count": "{count} items"
  }
}
```

**重要规则：**

- ✅ Key 必须使用纯英文（蛇形命名法，如 `output_settings`）
- ✅ Value 可以是任何语言的文本
- ✅ 所有语言文件的 Key 结构必须保持一致
- ✅ 使用嵌套对象组织相关的键

---

## 添加新语言

### 步骤 1：创建新的语言文件

假设您要添加**韩语**支持：

1. 复制英文文件作为模板：

   ```bash
   cp locales/en.json locales/ko-KR.json
   ```

### 步骤 2：翻译所有 Value

打开 `ko-KR.json`，将所有 Value 翻译成韩语，**保持 Key 不变**。

**翻译前（英文）：**

```json
{
  "menu": {
    "file": "File",
    "edit": "Edit"
  },
  "actions": {
    "openFile": "Open",
    "save": "Save"
  }
}
```

**翻译后（韩语）：**

```json
{
  "menu": {
    "file": "파일",
    "edit": "편집"
  },
  "actions": {
    "openFile": "열기",
    "save": "저장"
  }
}
```

### 步骤 3：注册新语言

编辑 `libs/i18n_engine.py`，在 `get_available_languages()` 方法中添加新语言：

```python
def get_available_languages(self) -> Dict[str, str]:
    lang_names = {
        'en': 'English',
        'zh-CN': '简体中文',
        'zh-TW': '繁體中文',
        'de-DE': 'Deutsch',
        'fr-FR': 'Français',
        'ja-JP': '日本語',
        'ko-KR': '한국어',  # 添加这一行
    }
    
    available = {}
    for lang_code in self.translations.keys():
        available[lang_code] = lang_names.get(lang_code, lang_code)
    
    return available
```

### 步骤 4：测试

启动程序，切换到新语言，检查所有界面元素是否正确显示。

```bash
python main.py
```

---

## 翻译步骤

### 修改现有翻译

1. 找到对应的 JSON 文件（如 `locales/zh-CN.json`）
2. 编辑需要修改的 Value
3. 保存文件
4. **重新启动程序**或**切换语言**即可看到效果

### 添加新的翻译键

当开发新功能时，需要添加新的翻译键：

1. **在所有语言文件中添加相同的 Key**

   ```json
   // en.json
   {
     "newFeature": {
       "title": "New Feature",
       "description": "This is a new feature"
     }
   }
   
   // zh-CN.json
   {
     "newFeature": {
       "title": "新功能",
       "description": "这是一个新功能"
     }
   }
   ```

2. **在代码中使用新键**

   ```python
   title = self.get_str('newFeature.title')
   desc = self.get_str('newFeature.description')
   ```

3. **测试** - 确保所有语言都能正确显示

---

## 翻译规范

### 1. Key 命名规范

✅ **正确示例：**

```json
{
  "export_dialog": {
    "title": "Export Annotations",
    "success_message": "Successfully exported: {count} images"
  }
}
```

❌ **错误示例：**

```json
{
  "导出标题": "Export Title",  // Key 不能包含中文
  "choose处理方式": "请选择"    // Key 不能包含中文
}
```

**Key 命名规则：**

- 使用小写字母和下划线（snake_case）
- 使用有意义的名称
- 按功能模块组织（如 `menu.file`, `dialog.export`）
- 避免缩写，保持清晰

### 2. 占位符的使用

某些字符串包含动态内容，使用 `{name}`, `{count}` 等占位符：

```json
// en.json
{
  "messages": {
    "images_added": "{count} images added to pending queue",
    "switched_to_next": "Switched to next: {filename} ({current}/{total})"
  }
}

// zh-CN.json
{
  "messages": {
    "images_added": "已添加 {count} 个图像到待标注队列",
    "switched_to_next": "切换到下一张: {filename} ({current}/{total})"
  }
}
```

**注意：** 

- 占位符的名称可以不同，但语义必须一致
- 占位符的数量必须与原文一致
- 在代码中使用：`.format(count=5)` 或 `.format(filename="test.jpg", current=1, total=10)`

### 3. 特殊字符处理

- **换行符**：使用 `\n`

  ```json
  {
    "instructions": "Please open the following file manually:\n\n{filepath}"
  }
  ```

- **引号**：直接包含在 value 中

  ```json
  {
    "recommendation": "建议：启用\"自动保存\"功能"
  }
  ```

- **HTML 标签**：支持简单的 HTML 格式化

  ```json
  {
    "about_feature": "<b>Multi-format Support</b>: PASCAL VOC, YOLO"
  }
  ```

### 4. 一致性原则

- 相同概念的术语在不同地方应保持一致
- 参考现有翻译的风格和用词
- 保持语气统一（正式/友好）
- 标点符号使用目标语言的习惯

### 5. 长度考虑

- 某些语言的文本可能更长（如德语）
- 尽量简洁，避免过长的文本
- 必要时使用缩写或换行

---

## 在代码中使用

这是**开发者**需要掌握的核心内容。翻译人员可以跳过此章节。

### 核心概念

LabelCraft 使用 `I18nEngine` 类来管理多语言字符串。在代码中，你需要：

1. **通过 `self.get_str()` 或 `self.tr()` 获取翻译文本**
2. **处理动态内容（占位符）**
3. **监听语言切换信号并更新 UI**

### 基本用法

```python
def some_method(self):
    # 获取翻译文本
    title = self.get_str('exportDialogTitle')
    message = self.get_str('successfullyExported').format(count=10)
    
    QMessageBox.information(self, title, message)
```

### 完整示例对比

#### ❌ 错误：硬编码文本

```python
def save_file(self):
    # 硬编码中文 - 无法切换语言！
    QMessageBox.information(self, '提示', '文件保存成功')
    
    # 硬编码英文 - 同样有问题！
    self.statusBar().showMessage('File saved successfully')
```

#### ✅ 正确：使用多语言

```python
def save_file(self):
    # 使用多语言字符串
    QMessageBox.information(
        self, 
        self.get_str('tip'),                    # "提示" 或 "Tip"
        self.get_str('fileSavedSuccess')        # "文件保存成功" 或 "File saved"
    )
    
    # 状态栏消息
    self.statusBar().showMessage(self.get_str('fileSavedSuccess'))
```

### 处理带参数的字符串

当字符串包含动态内容时，使用 `.format()` 方法：

```python
def show_progress(self, current, total):
    # properties 文件中定义：
    # "annotatedProgress": "已标注: {current} / {total}"
    
    progress_text = self.get_str('annotatedProgress').format(
        current=current, 
        total=total
    )
    self.progress_label.setText(progress_text)
    # 输出："已标注: 5 / 10" (中文)
    # 输出："Annotated: 5 / 10" (英文)
```

### 常见 UI 元素的多语言使用

#### 1. QAction（菜单项和工具栏按钮）

```python
# 创建 Action 时设置文本和 tooltip
open_action = QAction(self.get_str('actions.openFile'), self)
open_action.setToolTip(self.get_str('tooltips.openFile'))
open_action.setShortcut('Ctrl+O')

# 语言切换时会自动更新（通过信号连接）
```

#### 2. QLabel（标签）

```python
# 初始化时
self.output_label = QLabel(self.get_str('panels.output_path'))

# 语言切换时更新（在 retranslate 方法中）
def retranslate(self):
    self.output_label.setText(self.get_str('panels.output_path'))
```

#### 3. QPushButton（按钮）

```python
# 初始化时
self.save_btn = QPushButton(self.get_str('actions.save'))

# 语言切换时更新
def retranslate(self):
    self.save_btn.setText(self.get_str('actions.save'))
```

#### 4. QGroupBox（分组框）

```python
# 初始化时
self.settings_group = QGroupBox(self.get_str('panels.output_settings'))

# 语言切换时更新
def retranslate(self):
    self.settings_group.setTitle(self.get_str('panels.output_settings'))
```

#### 5. QMessageBox（对话框）

```python
# 信息对话框
QMessageBox.information(
    self,
    self.get_str('dialogs.export_complete'),           # 标题
    self.get_str('messages.successfully_exported').format(count=count)  # 内容
)

# 确认对话框
reply = QMessageBox.question(
    self,
    self.get_str('dialogs.warning_title'),
    self.get_str('messages.unsaved_changes'),
    QMessageBox.Yes | QMessageBox.No
)
```

### 语言切换时的更新机制

当用户切换语言时，`I18nEngine` 会发出 `language_changed` 信号。你需要：

1. **连接信号**（通常在 `__init__` 中）

   ```python
   def __init__(self, parent=None):
       super().__init__(parent)
       
       # 连接语言切换信号
       if parent and hasattr(parent, 'i18n'):
           parent.i18n.language_changed.connect(self.retranslate)
   ```

2. **实现 retranslate 方法**

   ```python
   def retranslate(self):
       """Retranslate all UI elements when language changes"""
       # 更新窗口标题
       self.setWindowTitle(self.get_str('windowTitle'))
       
       # 更新所有 UI 元素
       self.output_label.setText(self.get_str('panels.output_path'))
       self.save_btn.setText(self.get_str('actions.save'))
       self.settings_group.setTitle(self.get_str('panels.output_settings'))
       
       # 刷新界面
       self.update()
   ```

### 最佳实践

1. **始终使用 `self.get_str()` 或 `self.tr()`**

   ```python
   # ✅ 推荐
   text = self.get_str('myKey')
   
   # ❌ 不推荐（硬编码）
   text = "My Text"
   ```

2. **为 Dialog 类连接语言切换信号**

   ```python
   class MyDialog(QDialog):
       def __init__(self, parent=None):
           super().__init__(parent)
           self.parent_window = parent
           
           # 连接语言切换信号
           if parent and hasattr(parent, 'i18n'):
               parent.i18n.language_changed.connect(self.retranslate)
   ```

3. **保持 Key 的一致性**

   ```python
   # ✅ 使用相同的 Key
   btn1.setText(self.get_str('actions.save'))
   btn2.setText(self.get_str('actions.save'))
   
   # ❌ 不要为相同概念创建不同的 Key
   btn1.setText(self.get_str('saveButton'))
   btn2.setText(self.get_str('saveAction'))
   ```

### 调试技巧

#### 查看所有可用的 Key

```python
# 在 Python 控制台中
import json
with open('locales/en.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(json.dumps(data, indent=2, ensure_ascii=False))
```

#### 检查翻译是否完整

```python
# 比较英文和中文的 Key
import json

def get_all_keys(obj, prefix=''):
    keys = set()
    for key, value in obj.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            keys.update(get_all_keys(value, full_key))
        else:
            keys.add(full_key)
    return keys

with open('locales/en.json', 'r', encoding='utf-8') as f:
    en_data = json.load(f)
with open('locales/zh-CN.json', 'r', encoding='utf-8') as f:
    zh_data = json.load(f)

en_keys = get_all_keys(en_data)
zh_keys = get_all_keys(zh_data)

missing = en_keys - zh_keys
if missing:
    print(f"缺少的翻译 ({len(missing)} 个):")
    for key in sorted(missing):
        print(f"  - {key}")
else:
    print("✓ 所有 Key 都已翻译")
```

#### 测试单个字符串

```python
# 快速测试翻译
from libs.i18n_engine import I18nEngine
i18n = I18nEngine()
i18n.set_language('zh-CN')
print(i18n.tr('actions.openFile'))  # 应该输出：打开文件
```

---

## 测试与验证

### 1. 检查 JSON 语法

确保 JSON 文件格式正确：

```bash
# 使用 Python 验证 JSON
python3 -m json.tool locales/zh-CN.json > /dev/null && echo "✓ JSON 格式正确"
```

### 2. 运行程序测试

```bash
python main.py
```

- 切换到新语言
- 遍历所有菜单和对话框
- 检查文本是否正确显示
- 检查布局是否正常（文本长度可能不同）

### 3. 检查遗漏

确保所有 Key 都有翻译：

```python
# 使用上面的脚本检查
python check_translations.py
```

### 4. 测试动态语言切换

1. 启动程序
2. 点击菜单：Language → 选择不同语言
3. 观察所有 UI 元素是否立即更新
4. 多次切换同一语言，确保没有缓存问题

---

## 常见问题

### Q1: 为什么有些文本切换语言后没有变化？

**A:** 可能是以下原因：

1. **硬编码的文本** - 检查代码，将硬编码文本替换为 `self.get_str()`
2. **未连接语言切换信号** - 确保 Dialog 类连接了 `language_changed` 信号
3. **未实现 retranslate 方法** - 添加 `retranslate()` 方法并更新所有 UI 元素

### Q2: 如何添加新的多语言字符串？

**A:**

1. 在所有语言的 `.json` 文件中添加相同的 Key
2. 翻译对应的 Value
3. 在代码中使用 `self.get_str('your.key')`
4. 重启程序或切换语言

### Q3: 翻译后布局错乱怎么办？

**A:**

- 某些语言的文本可能更长，考虑使用缩写
- 调整 widget 的最小宽度
- 使用换行符 `\n` 分割长文本
- 使用 Qt 的布局管理器自动适应

### Q4: 如何测试特定语言？

**A:**

1. 启动 LabelCraft
2. 点击菜单：Language → 选择目标语言
3. 或者修改系统语言设置（程序会自动检测）

### Q5: JSON 文件和旧的 .properties 文件有什么区别？

**A:**

- **旧系统**：使用 `.properties` 文件，扁平键结构（如 `outputSettings`）
- **新系统**：使用 `.json` 文件，嵌套键结构（如 `panels.output_settings`）
- **优势**：JSON 更易读、更易维护、支持嵌套组织

### Q6: 为什么删除了 StringBundle？

**A:**

- StringBundle 是旧的 Java 风格的翻译系统
- 不支持动态语言切换（需要重启程序）
- 使用静态缓存，导致切换语言后 UI 不更新
- 新系统更现代、更灵活、性能更好

---

## 工具推荐

### 文本编辑器

- **VS Code** - 支持 JSON 文件语法高亮和格式化
- **Sublime Text** - 轻量级编辑器
- **Notepad++** - Windows 平台推荐

### JSON 工具

- **JSON Formatter** - VS Code 扩展，自动格式化 JSON
- **jq** - 命令行 JSON 处理工具

### 翻译辅助

- **DeepL** - AI 翻译助手（需人工校对）
- **Google Translate** - 快速参考
- **术语表** - 保持专业术语一致性

### 版本控制

- **Git** - 跟踪翻译变更
- **GitHub/GitLab** - 协作翻译

---

## 联系与支持

如有问题或建议，请：

1. 查看现有翻译作为参考
2. 在 GitHub Issues 中提问
3. 提交 Pull Request 贡献翻译

---

**祝您翻译顺利！🎉**

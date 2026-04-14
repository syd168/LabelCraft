# LabelCraft 使用教程 (v2.0.0)

> **基于项目的图像标注工具** - 基于 [labelImg](https://github.com/tzutalin/labelImg) 开发

## 📖 目录

1. [简介](#简介)
2. [快速开始](#快速开始)
3. [理解项目](#理解项目)
4. [创建第一个项目](#创建第一个项目)
5. [标注工作流](#标注工作流)
6. [高级功能](#高级功能)
7. [格式转换](#格式转换)
8. [快捷键](#快捷键)
9. [最佳实践](#最佳实践)
10. [常见问题](#常见问题)

---

## 简介

LabelCraft v2.0.0 是一款专为目标检测和计算机视觉任务设计的专业图像标注工具。与传统工具不同，LabelCraft 采用**基于项目的工作流**，帮助您高效组织标注工作。

### v2.0 新特性

- ✅ **项目管理**: 将标注组织到带有元数据的项目中
- ✅ **多格式支持**: 5种格式 (VOC, YOLO, CreateML, COCO, CSV)
- ✅ **内置转换器**: 无缝转换所有格式
- ✅ **动态语言切换**: 6种语言无需重启
- ✅ **增强UI**: 更好的组织和可用性
- ✅ **智能工作流**: 待标注队列、验证模式、自动保存

---

## 快速开始

### 安装

```bash
pip install labelcraft
```

### 启动

```bash
labelcraft
```

或从源码：
```bash
./start.sh  # Linux/macOS
start.bat   # Windows
```

---

## 理解项目

### 什么是项目？

LabelCraft 中的**项目**是组织标注工作的容器，包括：

- **项目文件** (`.labelcraft`): 存储配置（名称、标签、格式等）
- **标注目录**: 包含所有标注文件
- **图像**: 您的图像文件（可以放在任何位置）
- **元数据**: 创建日期、最后修改、统计信息

### 为什么要使用项目？

✅ **组织性**: 将相关标注放在一起  
✅ **持久化**: 设置自动保存  
✅ **可移植**: 易于共享和备份  
✅ **跟踪**: 监控进度和统计  
✅ **灵活性**: 项目进行中可更改格式  

### 项目结构

```
MyProject/
├── MyProject.labelcraft      # 项目配置文件
├── annotations/               # 所有标注文件
│   ├── image1.xml
│   ├── image2.xml
│   └── ...
└── images/                    # 您的图像（可选位置）
    ├── image1.jpg
    ├── image2.jpg
    └── ...
```

---

## 创建第一个项目

### 步骤 1: 打开新建项目对话框

**方法1:** 菜单 → `文件` → `新建项目`  
**方法2:** 键盘快捷键 `Ctrl+N`  
**方法3:** 点击工具栏上的"新建项目"按钮

### 步骤 2: 填写项目信息

新建项目对话框将出现：

#### 项目名称
- 输入项目的描述性名称
- 示例："猫狗检测"、"车辆标注"

#### 项目位置
- 选择存储项目的位置
- 点击"浏览"选择目录
- 系统将创建：
  - 项目文件：`{名称}.labelcraft`
  - 标注文件夹：`annotations/`

#### 输出格式
选择您的标注格式：

| 格式 | 扩展名 | 用途 |
|------|--------|------|
| **PASCAL VOC** | `.xml` | Faster R-CNN, SSD, 大多数框架 |
| **YOLO** | `.txt` | YOLOv5, YOLOv8, YOLOv10 |
| **CreateML** | `.json` | Apple CreateML 框架 |
| **COCO** | `.json` | Microsoft COCO 标准 |
| **CSV** | `.csv` | 数据分析、电子表格 |

> 💡 **提示**: 您稍后可以更改！标注将自动转换。

#### 标签（类别）
添加您的对象类别：

1. 在输入框中输入标签名称
2. 点击"添加"或按 Enter
3. 对所有类别重复此操作

宠物检测的标签示例：
```
cat
dog
bird
rabbit
```

**可选操作：**
- **从文件加载**: 点击"加载标签"从文本文件导入
- **清空全部**: 删除所有标签重新开始

### 步骤 3: 创建项目

点击**"创建项目"**按钮。

您将看到成功消息和项目详情：
```
项目 "MyProject" 创建成功！

项目名称: MyProject
位置: /path/to/MyProject
标注目录: /path/to/MyProject/annotations
标签: 4 (cat, dog, bird, rabbit)
输出格式: PASCAL_VOC
```

主窗口标题更新为：`LabelCraft - MyProject`

---

## 标注工作流

### 步骤 1: 添加图像到项目

创建项目后，需要添加图像：

**方法1: 打开目录**
1. 菜单 → `文件` → `打开目录` 或 `Ctrl+U`
2. 选择包含图像的文件夹
3. 所有支持的图像（JPG、PNG、BMP等）自动加载

**方法2: 拖放**
- 直接从文件管理器拖动图像文件
- 放到 LabelCraft 窗口上

**方法3: 添加单个文件**
- 菜单 → `文件` → `添加图像`
- 选择特定图像文件

左侧面板显示**待标注队列** - 等待标注的图像。

### 步骤 2: 开始标注

#### 创建边界框

1. 确保处于**创建模式**（工具栏第一个按钮高亮）
2. 按 `W` 或点击"创建矩形框"
3. 在图像上点击并拖动，围绕对象绘制框
4. 释放鼠标按钮

#### 输入标签

出现标签输入对话框：

**选项A: 手动输入**
- 输入对象类别
- 按 Enter 或点击确定

**选项B: 使用默认标签**
1. 勾选"使用默认标签"复选框（右侧面板）
2. 从下拉列表中选择标签
3. 不会出现对话框 - 自动使用选中的标签
4. 非常适合批量标注同类对象

#### 调整框

**移动：**
- 切换到编辑模式 (`Ctrl+J`)
- 拖动框到新位置

**调整大小：**
- 在编辑模式下，拖动边缘或角点

**微调：**
- 使用方向键进行像素级精确定位

### 步骤 3: 保存标注

**手动保存：**
- 按 `Ctrl+S`
- 或菜单 → `文件` → `保存`

**自动保存（推荐）：**
- 菜单 → `视图` → `自动保存模式`
- 切换图像时自动保存

已保存的标注出现在右侧面板列表中。

### 步骤 4: 验证完成

图像完全标注后：

1. 检查所有边界框
2. 按 `Space` 标记为已验证
3. 文件名前出现 ✓
4. 图像移动到"已完成"列表

### 步骤 5: 在图像间导航

**下一张图像：**
- 按 `D` 或 `→` 方向键
- 或点击"下一张图像"按钮

**上一张图像：**
- 按 `A` 或 `←` 方向键
- 或点击"上一张图像"按钮

**跳转到特定图像：**
- 双击文件列表（左侧面板）中的任意图像

### 步骤 6: 监控进度

在多个地方检查进度：

- **窗口标题**: `LabelCraft - MyProject (5/100)`
  - 显示当前图像编号和总数
- **左侧面板**: 待标注与已完成计数
- **右侧面板**: 当前图像上的标注数量

---

## 高级功能

### 编辑项目

需要修改项目设置？

1. 菜单 → `文件` → `编辑项目` 或 `Ctrl+E`
2. 对话框打开，当前设置已预填充
3. 根据需要修改：
   - 添加/删除标签
   - 更改输出格式
   - 更新项目名称

**重要：** 更改输出格式将提示您迁移现有标注。

### 管理标签

#### 标注期间添加标签

当您执行以下操作时，标签会自动添加到项目中：
- 使用新标签创建新的边界框
- 编辑现有框并更改其标签

#### 从文件加载标签

1. 准备一个文本文件，每行一个标签：
   ```txt
   person
   car
   bicycle
   motorcycle
   ```

2. 在新建/编辑项目对话框中，点击"加载标签"
3. 选择您的文本文件
4. 标签自动填充

#### 删除未使用的标签

1. 菜单 → `文件` → `编辑项目`
2. 在列表中选择标签
3. 点击"删除"或按 Delete 键

> ⚠️ **警告**: 删除标签不会删除现有标注，但可能导致不一致。

### 复制前一帧

对于视频帧或类似的连续图像：

1. 完整标注第一帧
2. 移动到下一帧
3. 菜单 → `文件` → `复制前一帧标注框` 或 `Ctrl+V`
4. 前一帧的所有框都被复制
5. 根据需要调整位置

这在顺序标注中节省大量时间！

### 亮度调节

难以在暗/亮图像中看到对象？

**工具栏滑块：**
- 拖动工具栏上的亮度滑块

**键盘快捷键：**
- `Ctrl+Shift++` : 增加亮度
- `Ctrl+Shift+-` : 降低亮度
- `Ctrl+Shift+=` : 重置为正常

> 💡 这只影响显示，不影响原始图像！

### 验证模式

质量控制至关重要：

1. 标注完图像后，仔细检查
2. 按 `Space` 切换验证状态
3. 已验证的图像在文件列表中显示 ✓
4. 使用此功能跟踪哪些图像需要审查

### 导出标注

以不同格式导出标注：

1. 菜单 → `文件` → `导出标注` 或 `Ctrl+E`
2. 选择导出格式
3. 选择目标目录
4. 点击"导出"

所有标注将被转换并保存。

---

## 格式转换

### 内置转换器

LabelCraft v2.0 包含强大的转换器，支持所有5种格式。

### 编程使用

```python
from libs.annotation_converter import AnnotationConverter

# 初始化转换器
converter = AnnotationConverter()

# 转换整个目录
converter.convert(
    input_dir='path/to/voc_annotations',
    input_format='voc',        # 源格式
    output_format='yolo',      # 目标格式
    output_dir='path/to/yolo_output'
)
```

**支持的格式：**
- `'voc'` - PASCAL VOC (XML)
- `'yolo'` - YOLO (TXT)
- `'createml'` - CreateML (JSON)
- `'coco'` - COCO (JSON)
- `'csv'` - CSV

### 命令行使用

```bash
# 基本转换
python -m libs.annotation_converter \
    --input /path/to/input \
    --input_format voc \
    --output_format yolo \
    --output /path/to/output

# 带选项
python -m libs.annotation_converter \
    --input ./voc_annotations \
    --input_format voc \
    --output_format coco \
    --output ./coco_annotations \
    --verbose
```

### 常见转换场景

#### VOC 转 YOLO
使用 VOC 标注的数据训练 YOLO 模型：
```python
converter.convert('voc_data/', 'voc', 'yolo', 'yolo_data/')
```

#### YOLO 转 COCO
将 YOLO 数据集转换为 COCO 格式：
```python
converter.convert('yolo_dataset/', 'yolo', 'coco', 'coco_dataset/')
```

#### 任意格式转 CSV
导出用于 Excel/电子表格分析：
```python
converter.convert('annotations/', 'voc', 'csv', 'analysis.csv')
```

### 格式详情

#### PASCAL VOC (XML)
```xml
<annotation>
    <folder>images</folder>
    <filename>image1.jpg</filename>
    <size>
        <width>1920</width>
        <height>1080</height>
    </size>
    <object>
        <name>cat</name>
        <bndbox>
            <xmin>100</xmin>
            <ymin>150</ymin>
            <xmax>300</xmax>
            <ymax>350</ymax>
        </bndbox>
    </object>
</annotation>
```

#### YOLO (TXT)
```
0 0.5 0.5 0.4 0.4
1 0.7 0.3 0.2 0.3
```
格式: `<类别ID> <x中心> <y中心> <宽度> <高度>`
- 值归一化为 0-1
- 每个对象一行
- 类别ID从0开始

#### COCO (JSON)
```json
{
  "images": [
    {"id": 1, "file_name": "image1.jpg", "width": 1920, "height": 1080}
  ],
  "annotations": [
    {"id": 1, "image_id": 1, "category_id": 1, 
     "bbox": [100, 150, 200, 200]}
  ],
  "categories": [
    {"id": 1, "name": "cat"},
    {"id": 2, "name": "dog"}
  ]
}
```

#### CSV
```csv
filename,width,height,class,xmin,ymin,xmax,ymax
image1.jpg,1920,1080,cat,100,150,300,350
image1.jpg,1920,1080,dog,500,400,700,600
```

---

## 快捷键

### 项目管理
| 快捷键 | 操作 |
|--------|------|
| `Ctrl+N` | 新建项目 |
| `Ctrl+O` | 打开项目 |
| `Ctrl+E` | 编辑项目 |
| `Ctrl+S` | 保存标注 |
| `Ctrl+Shift+C` | 关闭项目 |

### 文件操作
| 快捷键 | 操作 |
|--------|------|
| `Ctrl+U` | 打开目录 |
| `Ctrl+Shift+O` | 打开标注文件 |
| `Ctrl+W` | 关闭当前图像 |
| `Ctrl+Q` | 退出应用 |

### 标注
| 快捷键 | 操作 |
|--------|------|
| `W` | 创建矩形框 |
| `Ctrl+J` | 切换编辑/创建模式 |
| `Delete` | 删除选中框 |
| `Ctrl+D` | 复制选中框 |
| `Ctrl+E` | 编辑标签 |
| `Ctrl+V` | 复制前一帧 |

### 导航
| 快捷键 | 操作 |
|--------|------|
| `D` 或 `→` | 下一张图像 |
| `A` 或 `←` | 上一张图像 |
| `Space` | 验证/取消验证图像 |
| `Home` | 第一张图像 |
| `End` | 最后一张图像 |

### 视图控制
| 快捷键 | 操作 |
|--------|------|
| `Ctrl++` | 放大 |
| `Ctrl+-` | 缩小 |
| `Ctrl+=` | 原始大小 |
| `Ctrl+F` | 适应窗口 |
| `Ctrl+Shift+F` | 适应宽度 |
| `Ctrl+H` | 隐藏所有框 |
| `Ctrl+A` | 显示所有框 |

### 亮度
| 快捷键 | 操作 |
|--------|------|
| `Ctrl+Shift++` | 增加亮度 |
| `Ctrl+Shift+-` | 降低亮度 |
| `Ctrl+Shift+=` | 重置亮度 |

### 其他
| 快捷键 | 操作 |
|--------|------|
| `Ctrl+T` | 切换工具栏 |
| `Ctrl+R` | 更改保存目录 |
| `Ctrl+Shift+L` | 加载预定义标签 |
| `Ctrl+Shift+D` | 删除图像 |

---

## 最佳实践

### 开始前

✅ **规划标签**: 预先定义所有类别  
✅ **创建项目**: 使用项目进行组织  
✅ **设置正确格式**: 选择与训练框架匹配的格式  
✅ **启用自动保存**: 防止数据丢失  
✅ **学习快捷键**: 显著提高生产力  

### 标注期间

✅ **一致的标签**: 对类别使用完全相同的拼写  
✅ **紧密的框**: 围绕对象紧密绘制框  
✅ **定期验证**: 使用 Space 验证已完成的图像  
✅ **频繁保存**: 即使有自动保存也要经常保存  
✅ **默认标签**: 用于批量标注同类对象  
✅ **质量检查**: 定期查看之前的标注  

### 完成后

✅ **验证所有图像**: 确保所有内容都标记为已验证  
✅ **备份项目**: 复制整个项目目录  
✅ **按需导出**: 转换为所需格式  
✅ **记录统计**: 记录图像数量、每类对象数  
✅ **版本控制**: 使用 Git 跟踪项目  

### 项目组织

```
Projects/
├── Project_1_Cats_Dogs/
│   ├── Project_1_Cats_Dogs.labelcraft
│   ├── annotations/
│   └── images/
├── Project_2_Vehicles/
│   ├── Project_2_Vehicles.labelcraft
│   ├── annotations/
│   └── images/
└── exports/
    ├── voc_export/
    ├── yolo_export/
    └── coco_export/
```

### 效率技巧

1. **批量相似图像**: 将相似图像分组
2. **使用默认标签**: 标注许多同类对象时
3. **复制前一帧**: 用于视频或相似的连续图像
4. **键盘优于鼠标**: 学习并使用快捷键
5. **定期休息**: 通过休息保持标注质量
6. **进度跟踪**: 使用验证模式跟踪完成情况

---

## 常见问题

### Q1: 我可以不创建项目就使用 LabelCraft 吗？

**A:** 可以！您可以使用传统模式：
```bash
python main.py /path/to/images
```
但是，项目提供更好的组织，推荐使用。

### Q2: 如何打开现有项目？

**A:** 
- 菜单 → `文件` → `打开项目` 或 `Ctrl+O`
- 选择 `.labelcraft` 文件
- 或使用菜单中的最近项目列表

### Q3: 我的标注保存在哪里？

**A:** 默认在项目的 `annotations/` 目录中。每个标注文件与图像同名，扩展名适当 (.xml, .txt, .json, .csv)。

### Q4: 开始后我可以更改输出格式吗？

**A:** 可以！编辑项目 (`Ctrl+E`) 并更改格式。将为现有标注提供迁移选项。

### Q5: 如何转换旧的 labelImg 标注？

**A:** 使用内置转换器：
```python
from libs.annotation_converter import AnnotationConverter
converter = AnnotationConverter()
converter.convert('old_annotations/', 'voc', 'yolo', 'new_annotations/')
```

### Q6: 支持什么图像格式？

**A:** JPG、JPEG、PNG、BMP、TIFF、WEBP 和大多数常见图像格式。

### Q7: 如何备份我的项目？

**A:** 复制整个项目目录，包括：
- `.labelcraft` 文件
- `annotations/` 文件夹
- 您的图像（如果存储在项目内）

### Q8: 多人可以同时处理同一个项目吗？

**A:** 不能同时。但是，您可以：
1. 将图像分成子项目
2. 让每个人分别标注
3. 使用转换器合并标注

### Q9: 项目进行中如何添加更多标签？

**A:** 
- 创建框时直接输入新标签名称
- 或编辑项目 (`Ctrl+E`) 管理标签

### Q10: 有撤销功能吗？

**A:** 目前，删除是即时的。删除时要小心。未来版本可能会添加撤销支持。

### Q11: 如何报告错误或请求功能？

**A:** 访问我们的 GitHub Issues 页面：https://github.com/syd168/LabelCraft/issues

### Q12: 我可以为 LabelCraft 做贡献吗？

**A:** 当然！我们欢迎贡献：
1. Fork 仓库
2. 进行更改
3. 提交 Pull Request

查看 README.md 了解开发环境设置说明。

---

## 获取帮助

- **文档**: 检查仓库中的 `doc/` 目录
- **问题**: https://github.com/syd168/LabelCraft/issues
- **讨论**: GitHub Discussions 标签页
- **邮箱**: syd168@users.noreply.github.com

---

**祝您标注愉快！🎉**

*版本 2.0.0 - 为计算机视觉社区用心制作 ❤️*

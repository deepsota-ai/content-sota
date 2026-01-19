// 文字编辑子页面JavaScript

// 页面加载完成事件
window.addEventListener('DOMContentLoaded', () => {
    // === 按钮事件绑定 ===
    const backBtn = document.getElementById('back-btn');
    if (backBtn) {
        backBtn.addEventListener('click', () => {
            window.location.href = '../index.html';
        });
    }

    const backToMainBtn = document.getElementById('back-to-main-btn');
    if (backToMainBtn) {
        backToMainBtn.addEventListener('click', () => {
            window.location.href = '../cover-generator.html';
        });
    }

    // 监听批量保存按钮
    const saveAllBtn = document.getElementById('save-all-btn');
    if (saveAllBtn) {
        saveAllBtn.addEventListener('click', saveAllCanvases);
    }

    // === 多图画布逻辑 ===
    const canvasContainer = document.getElementById('canvas-container');
    // 修改 canvases 存储结构为对象数组: { instance: fabric.Canvas, filename: string }
    const canvases = [];

    // 全局变量存储选中的日期
    let currentSelectedDate = '';

    // 等待字体加载完成的函数
    function waitForFontLoad(fontName, timeout = 5000) {
        return new Promise((resolve, reject) => {
            if (document.fonts && document.fonts.load) {
                document.fonts.load(`16px "${fontName}"`)
                    .then(() => {
                        // 再次检查字体是否真的可用
                        if (document.fonts.check(`16px "${fontName}"`)) {
                            resolve();
                        } else {
                            reject(new Error('Font check failed'));
                        }
                    })
                    .catch(() => reject(new Error('Font load failed')));

                // 设置超时
                setTimeout(() => reject(new Error('Font load timeout')), timeout);
            } else {
                // 浏览器不支持 Font Loading API，直接 resolve
                resolve();
            }
        });
    }

    // 获取裁剪后的图片列表和素材列表
    async function fetchData() {
        try {
            // 0. 先等待字体加载完成
            console.log('等待字体加载...');
            await waitForFontLoad('XinQingNian');
            console.log('字体加载完成');

            // 1. 首先获取所有日期文件夹
            const dateRes = await fetch('/api/publish/folders');
            const dateData = await dateRes.json();

            let folders = [];
            if (dateData.success && dateData.folders && dateData.folders.length > 0) {
                // 默认选中第一个（最新）日期
                currentSelectedDate = dateData.folders[0].name;
                console.log('自动选中最新日期:', currentSelectedDate);

                // 2. 获取该日期下的素材列表
                const matRes = await fetch(`/api/publish/folders?date=${encodeURIComponent(currentSelectedDate)}`);
                const matData = await matRes.json();
                if (matData.success) {
                    folders = matData.folders;
                }
            }

            // 3. 获取裁剪图片列表
            const imgRes = await fetch('/api/get_cropped_images');
            const imgData = await imgRes.json();

            if (imgData.images && imgData.images.length > 0) {
                initCanvases(imgData.images, folders);
            } else {
                canvasContainer.innerHTML = '<div class="error-state"><i class="fas fa-image"></i><p>未找到裁剪后的图片</p></div>';
            }
        } catch (error) {
            console.error('获取数据失败:', error);
            canvasContainer.innerHTML = `<div class="error-state"><i class="fas fa-exclamation-triangle"></i><p>加载失败: ${error.message}</p></div>`;
        }
    }

    // 初始化所有画布
    function initCanvases(imageFiles, folders) {
        canvasContainer.innerHTML = ''; // 清空容器
        canvases.length = 0; // 清空数组

        imageFiles.forEach((fileName, index) => {
            // 1. 创建 DOM 结构
            const wrapper = document.createElement('div');
            wrapper.className = 'canvas-wrapper';
            wrapper.dataset.filename = fileName;

            const canvasEl = document.createElement('canvas');
            canvasEl.id = `canvas-${index}`;

            wrapper.appendChild(canvasEl);
            canvasContainer.appendChild(wrapper);

            // 2. 初始化 Fabric 实例
            const canvas = new fabric.Canvas(`canvas-${index}`, {
                backgroundColor: '#ffffff'
            });

            // 3. 加载图片
            const imageUrl = `/data/coverGeneration/cover/crop/${fileName}`;
            fabric.Image.fromURL(imageUrl, (img) => {
                // 计算缩放比例
                const maxDim = 280;
                let scale = 1;
                if (img.width > maxDim || img.height > maxDim) {
                    scale = Math.min(maxDim / img.width, maxDim / img.height);
                }

                const finalWidth = img.width * scale;
                const finalHeight = img.height * scale;

                canvas.setWidth(finalWidth);
                canvas.setHeight(finalHeight);
                canvas.setZoom(scale);

                img.set({
                    left: 0,
                    top: 0,
                    selectable: false,
                    evented: false
                });

                canvas.add(img);
                canvas.sendToBack(img);

                // --- 自动添加对应的素材标题 ---
                // 提取图片序号，例如 "1.png" -> "1"
                const fileNumber = fileName.split('.')[0];
                // 查找对应的素材文件夹，例如 "素材_1"
                const folderName = `素材_${fileNumber}`;
                const folder = folders.find(f => f.name === folderName);

                if (folder && folder.title) {
                    const titleText = folder.title;
                    const textObj = new fabric.IText(titleText, {
                        left: canvas.width / (2 * scale), // 注意zoom影响，这里除以scale回到原始坐标
                        top: canvas.height / (2 * scale),
                        // fontFamily: 'sans-serif',
                        fontFamily: 'XinQingNian, sans-serif',
                        fontSize: 120,
                        fill: '#f0d402',
                        stroke: '#000000',
                        strokeWidth: 10,
                        paintFirst: 'stroke',
                        textAlign: 'center',
                        originX: 'center',
                        originY: 'center',
                        selectable: true,
                        editable: true,
                        shadow: 'rgba(0,0,0,0.6) 2px 2px 5px'
                    });
                    canvas.add(textObj);
                    canvas.setActiveObject(textObj);
                }

                canvas.requestRenderAll();
            }, { crossOrigin: 'anonymous' });

            // 4. 绑定双击添加文字事件
            canvas.on('mouse:dblclick', (e) => {
                if (e.target) return;
                const pointer = canvas.getPointer(e.e);
                addText(canvas, pointer.x, pointer.y);
            });

            // 存储实例
            canvases.push({
                instance: canvas,
                filename: fileName
            });
        });
    }

    // 添加文字通用函数
    function addText(targetCanvas, x, y) {
        const text = new fabric.IText('双击编辑', {
            left: x,
            top: y,
            fontFamily: 'XinQingNian, sans-serif',
            fontSize: 100,
            fontWeight: 'bold',
            fill: '#f0d402ff',
            stroke: '#000000',
            strokeWidth: 4,
            paintFirst: 'stroke',
            textAlign: 'center',
            originX: 'center',
            originY: 'center',
            selectable: true,
            editable: true
        });

        targetCanvas.add(text);
        targetCanvas.setActiveObject(text);
        targetCanvas.requestRenderAll();
    }

    // 批量保存函数
    async function saveAllCanvases() {
        if (canvases.length === 0) {
            alert('没有可保存的图片');
            return;
        }

        const originalText = saveAllBtn.innerHTML;
        saveAllBtn.disabled = true;
        saveAllBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 保存中...';

        let successCount = 0;
        let failCount = 0;

        try {
            // 串行保存
            for (const item of canvases) {
                const { instance, filename } = item;

                // 导出大图：需要临时取消缩放或计算 multiplier
                const currentZoom = instance.getZoom();
                // 如果原始文件名是 jpg，尝试导出为 jpeg
                const isJpeg = filename.toLowerCase().endsWith('.jpg') || filename.toLowerCase().endsWith('.jpeg');
                const dataURL = instance.toDataURL({
                    format: isJpeg ? 'jpeg' : 'png',
                    quality: 0.95,
                    multiplier: 1 / currentZoom // 放大回原图尺寸
                });

                // 按原名保存
                const newFilename = filename;

                const response = await fetch('/api/save-edited-image', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        imageData: dataURL,
                        filename: newFilename,
                        date: currentSelectedDate // 传递选中的日期
                    })
                });

                if (response.ok) {
                    successCount++;
                } else {
                    failCount++;
                    const errText = await response.text();
                    console.error(`保存失败 ${filename}:`, errText);
                }
            }

            alert(`批量保存完成！\n成功: ${successCount}\n失败: ${failCount}`);

        } catch (error) {
            console.error('批量保存异常:', error);
            alert('保存过程中发生错误，请查看控制台');
        } finally {
            saveAllBtn.disabled = false;
            saveAllBtn.innerHTML = originalText;
        }
    }

    // 全局键盘事件（删除选中元素）
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Delete' || e.key === 'Backspace') {
            canvases.forEach(item => {
                const canvas = item.instance; // 注意这里解构
                const activeObj = canvas.getActiveObject();
                if (activeObj && !activeObj.isEditing) {
                    canvas.remove(activeObj);
                    canvas.discardActiveObject();
                    canvas.requestRenderAll();
                }
            });
        }
    });

    // 启动流程
    fetchData();
});
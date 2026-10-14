# 2026-10-14 客户端下载节点

千云无界 SYNNOVER AI3D 相机的官方 Viewer、客户端 SDK 和客户手册下载入口。相机与推理主机由交付人员配置，用户电脑只需安装对应客户端。

本仓库仅在重要交付节点发布下载包。研发迭代独立管理，不自动同步到此仓库。

本次下载节点：[2026-10-14](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/tag/client-2026.10.14)。该节点汇集现有发布包，不改变组件版本；带 rc 的组件仍为候选版本，请按交付说明选择。

## Viewer 与 SDK

| 用途 | 版本 | 下载 |
|---|---|---|
| Windows Viewer 安装版 | 0.4.1 | [SYNNOVER-AI3D-0.4.1-Windows-Setup.exe](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/SYNNOVER-AI3D-0.4.1-Windows-Setup.exe) |
| Linux Viewer（单相机交付） | 0.4.2-rc.2 | [SYNNOVER-AI3D-0.4.2-rc.2-x86_64.AppImage](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/SYNNOVER-AI3D-0.4.2-rc.2-x86_64.AppImage) |
| Linux Viewer（0.4.1既有交付） | 0.4.1 | [SYNNOVER-AI3D-0.4.1-x86_64.AppImage](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/SYNNOVER-AI3D-0.4.1-x86_64.AppImage) |
| Windows Python SDK | 0.4.2-rc.3 | [SYNNOVER-AI3D-0.4.2-rc.3-Python-SDK-Windows.zip](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/SYNNOVER-AI3D-0.4.2-rc.3-Python-SDK-Windows.zip) |
| Linux Python SDK | 0.4.2-rc.3 | [SYNNOVER-AI3D-0.4.2-rc.3-Python-SDK-Linux.zip](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/SYNNOVER-AI3D-0.4.2-rc.3-Python-SDK-Linux.zip) |
| Windows C++ SDK | 0.4.1 | [SYNNOVER-AI3D-0.4.1-SDK-Windows.zip](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/SYNNOVER-AI3D-0.4.1-SDK-Windows.zip) |
| Linux C++ SDK | 0.4.1 | [SYNNOVER-AI3D-0.4.1-SDK-Linux.tar.gz](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/SYNNOVER-AI3D-0.4.1-SDK-Linux.tar.gz) |

Python 完整包包含该平台 CPython 3.7–3.12 的 wheel 及匹配的 NumPy，支持离线安装。解压后，在包含 `wheelhouse` 的目录执行：

```sh
python -m pip install --no-index --find-links=./wheelhouse synnover-ai3d==0.4.2rc3
python Examples/camera.py 192.168.88.2
```

客户端 SDK 本身不需要安装 CUDA、TensorRT 或 OpenCV；推理在配套 RTX 主机上完成。Python 版本范围指 CPython x86_64，不能用于 ARM 或 PyPy。

<a id="python-wheel-downloads"></a>

## Python wheel 下载索引

首次安装建议使用上面的完整 SDK 包。下列单独 wheel 不包含 NumPy，适用于已有依赖的环境；选择与操作系统及 Python 主次版本完全匹配的文件。

| Python | Linux x86_64 | Windows x64 |
|---|---|---|
| 3.7 | [synnover_ai3d-0.4.2rc3-cp37-cp37m-manylinux_2_35_x86_64.whl](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/synnover_ai3d-0.4.2rc3-cp37-cp37m-manylinux_2_35_x86_64.whl) | [synnover_ai3d-0.4.2rc3-cp37-cp37m-win_amd64.whl](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/synnover_ai3d-0.4.2rc3-cp37-cp37m-win_amd64.whl) |
| 3.8 | [synnover_ai3d-0.4.2rc3-cp38-cp38-manylinux_2_35_x86_64.whl](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/synnover_ai3d-0.4.2rc3-cp38-cp38-manylinux_2_35_x86_64.whl) | [synnover_ai3d-0.4.2rc3-cp38-cp38-win_amd64.whl](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/synnover_ai3d-0.4.2rc3-cp38-cp38-win_amd64.whl) |
| 3.9 | [synnover_ai3d-0.4.2rc3-cp39-cp39-manylinux_2_35_x86_64.whl](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/synnover_ai3d-0.4.2rc3-cp39-cp39-manylinux_2_35_x86_64.whl) | [synnover_ai3d-0.4.2rc3-cp39-cp39-win_amd64.whl](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/synnover_ai3d-0.4.2rc3-cp39-cp39-win_amd64.whl) |
| 3.10 | [synnover_ai3d-0.4.2rc3-cp310-cp310-manylinux_2_35_x86_64.whl](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/synnover_ai3d-0.4.2rc3-cp310-cp310-manylinux_2_35_x86_64.whl) | [synnover_ai3d-0.4.2rc3-cp310-cp310-win_amd64.whl](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/synnover_ai3d-0.4.2rc3-cp310-cp310-win_amd64.whl) |
| 3.11 | [synnover_ai3d-0.4.2rc3-cp311-cp311-manylinux_2_35_x86_64.whl](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/synnover_ai3d-0.4.2rc3-cp311-cp311-manylinux_2_35_x86_64.whl) | [synnover_ai3d-0.4.2rc3-cp311-cp311-win_amd64.whl](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/synnover_ai3d-0.4.2rc3-cp311-cp311-win_amd64.whl) |
| 3.12 | [synnover_ai3d-0.4.2rc3-cp312-cp312-manylinux_2_35_x86_64.whl](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/synnover_ai3d-0.4.2rc3-cp312-cp312-manylinux_2_35_x86_64.whl) | [synnover_ai3d-0.4.2rc3-cp312-cp312-win_amd64.whl](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/synnover_ai3d-0.4.2rc3-cp312-cp312-win_amd64.whl) |

## 客户文档

- [客户使用手册](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/SYNNOVER-AI3D-Customer-Manual.html)
- [Python SDK 接口参考](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/SYNNOVER-AI3D-Python-SDK-Reference.html)
- [C++ SDK 接口参考](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/SYNNOVER-AI3D-CPP-SDK-Reference.html)

下载 HTML 后用浏览器打开；客户手册中的截图已内嵌。需要离线跳转接口参考时，请将三份 HTML 放在同一文件夹。

## 校验与适用范围

[SHA256SUMS](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/SHA256SUMS) · [发布校验记录](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/client-2026.10.14/release-verification.json)

本次 Python SDK 已通过 12 组原生平台/版本安装及模拟协议检查；Linux Python3.7 在现有 RTX3070 与自有相机上完成双分辨率真实取流、方向加载和保存验证。Windows 新 Python SDK 的实机验收尚未完成。客户端包不包含推理主机系统安装、模型或逐台设备授权材料。

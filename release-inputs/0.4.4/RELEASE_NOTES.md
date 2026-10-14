# SYNNOVER AI3D 0.4.4

Windows / Linux Viewer、Python SDK 和 C++ SDK 更新至 0.4.4。

- Viewer 同时提供“SYNNOVER 相机”和“ZED Series”选择入口，一次使用一个来源。选择缺失相机时自动恢复已连接且已配置的相机出流；不要求同时连接两台。
- Python / C++ 增加 `Config.camera_source` 和 `OutputOptions`。读取与保存可共用点云范围、采样步长及染色设置；默认点云 Z 深度 0–100 米、视差染色 0–128 像素、步长 1，原始深度和视差保持完整。
- Python 支持 CPython 3.7–3.12，并复用兼容的已有 NumPy。完整离线包附带依赖和单帧、连续取帧示例；C++ 包附带可直接编译的示例。SDK 包不含 Docs，说明入口为飞书手册。
- Viewer 产品手册直接打开当前飞书文档；内置 HTML 保留离线阅读与接口参考。

下载见[仓库首页](https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product)。核对文件请使用本次附件 `SHA256SUMS`。

验证覆盖原生 Windows 构建、安装/升级/迁移/卸载、Windows/Linux Python 3.7–3.12，以及 Linux 真实自有相机取帧、缺失 ZED 选择回退、2D/3D 和同帧保存。Windows 图像测试使用模拟取流；Windows 10/11 现场相机和新 RTX3060 整机工厂部署仍待实机验收。本次是客户端发行，不代表新盘加密或 TPM 启动策略已经验收。

Linux 版本另包含当前来源断开后的自动恢复增强；Windows 此次采用已通过原生验收的双入口及缺失来源选择回退构建。

上一版 0.4.3 保留，可从历史 Release 下载。

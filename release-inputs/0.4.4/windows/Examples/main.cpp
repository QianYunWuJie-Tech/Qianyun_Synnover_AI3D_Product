#include <synnover/ai3d.hpp>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#ifdef _WIN32
#include <windows.h>
#endif

int main(int argc, char** argv) {
#ifdef _WIN32
    SetConsoleOutputCP(CP_UTF8);
#endif
    synnover::Config config;
    config.address = argc > 1 ? argv[1] : "192.168.88.2";
    config.mode = "1280x720";
    config.camera_source = "synnover";
    synnover::OutputOptions options;
    synnover::Pipeline pipeline;
    try {
        const int frame_count = argc > 2 ? std::stoi(argv[2]) : 1;
        const int save_every = 20; // 默认保存第 1、21、41…帧；改为 1 可保存每帧。
        if (frame_count < 1) throw std::invalid_argument("frame_count must be positive");
        auto timestamp = std::chrono::system_clock::now().time_since_epoch().count();
        auto output_root = std::filesystem::current_path() / "output";
        auto output_run = output_root / ("cpp_frames_" + std::to_string(timestamp));
        if (!std::filesystem::create_directories(output_run))
            throw std::runtime_error("Output directory already exists");
        std::cout << "Output directory: " << output_run.u8string() << std::endl;
        std::ofstream output_file(output_run / "query_pixels.csv");
        output_file.exceptions(std::ios::failbit | std::ios::badbit);
        output_file << "frame_id,x,y,depth_at_pixel_m,saved_directory\n" << std::setprecision(9);
        pipeline.open(config, 180000);
        for (int index = 0; index < frame_count; ++index) {
            auto frame = pipeline.wait_for_frames(10000);
            auto color_bgr = frame.get_rgb("bgr", "left");
            auto depth_m = frame.get_depth("m");
            auto points_xyzrgb = frame.get_pcd("xyzrgb", options);
            int x = frame.width() / 2;
            int y = frame.height() / 2;
            float depth_at_pixel_m = frame.get_distance(x, y);
            std::string saved_directory;
            if (index % save_every == 0) {
                std::ostringstream name;
                name << "frame_" << std::setfill('0') << std::setw(4) << index << "_" << frame.frame_id();
                auto output_dir = output_run / name.str();
                frame.save(output_dir.u8string(), options); // 同一帧的图像、米制深度、完整有效点云。
                saved_directory = name.str();
                std::cout << "Saved: " << output_dir.u8string() << "\n";
            }
            output_file << frame.frame_id() << ',' << x << ',' << y << ',' << depth_at_pixel_m << ',' << saved_directory << '\n';
            std::cout << "frame=" << frame.frame_id() << " size=" << frame.width() << "x" << frame.height()
                      << " points=" << points_xyzrgb.size() << " pixel=(" << x << ',' << y << ") depth_m=";
            if (std::isfinite(depth_at_pixel_m) && depth_at_pixel_m > 0) std::cout << depth_at_pixel_m;
            else std::cout << "invalid";
            std::cout << '\n';
        }
        output_file.close();
        std::cout << "Pixel log: " << (output_run / "query_pixels.csv").u8string() << "\n";
        pipeline.close();
    } catch (const std::exception& error) {
        std::cerr << error.what() << "\n";
        try { pipeline.close(); } catch (const std::exception& close_error) {
            std::cerr << "Shutdown unconfirmed: " << close_error.what() << "\n";
        }
        return 1;
    }
}

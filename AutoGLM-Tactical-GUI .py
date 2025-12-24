import subprocess
import os
import threading
import tkinter as tk
from tkinter import font, ttk
from datetime import datetime
import re
import time
import requests

# 适配 Mac 按钮视觉效果
try:
    from tkmacosx import Button as MacButton
except ImportError:
    MacButton = tk.Button

PLATFORMS = {
    "核心矩阵 (ZhipuAI)": {"base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "autoglm-phone"},
    "深渊节点 (ModelScope)": {"base_url": "https://api-inference.modelscope.cn/v1", "model": "ZhipuAI/AutoGLM-Phone-9B"}
}


class CombatPlatformGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NEURAL INTERFACE V4.6.13 - 递归能级逻辑修正版")
        self.root.geometry("1200x950")
        self.root.configure(bg="#050505")

        # 系统状态变量
        self.process = None
        self.wda_iproxy_process = None
        self.current_mode = "SINGLE"
        self.is_manual_stop = False
        self.is_recording_action = False
        self.is_flashing = False
        self.cycle_start_time = None  # 递归监控起始时间

        # 视觉风格
        self.clr_bg = "#050505";
        self.clr_army = "#00FF41";
        self.clr_action = "#FF4500"
        self.clr_gray = "#333333";
        self.clr_red = "#FF0000";
        self.clr_cyan = "#00FFFF"
        self.clr_entry_bg = "#0D1117";
        self.clr_disabled_bg = "#080808"
        self.console_font = ("Monaco", 12);
        self.font_main = ("Heiti SC", 12)

        self._setup_ui()

    def _setup_ui(self):
        banner = tk.Frame(self.root, bg="#1a1a1a", bd=0)
        banner.pack(fill=tk.X, padx=0, pady=0)
        tk.Label(banner, text="SECURE LINE: ENCRYPTED | CYCLE_LOGIC: RECURSIVE_ACTIVE | PROTOCOL: ZERO-DAWN",
                 bg="#1a1a1a", fg="#586069", font=("Courier", 10)).pack(side=tk.LEFT, padx=20, pady=10)

        status_box = tk.Frame(banner, bg="#1a1a1a")
        status_box.pack(side=tk.RIGHT, padx=20)
        self.time_label = tk.Label(status_box, bg="#1a1a1a", fg=self.clr_army, font=("Share Tech Mono", 14))
        self.time_label.pack(side=tk.TOP, anchor="e")

        timer_box = tk.Frame(status_box, bg="#1a1a1a")
        timer_box.pack(side=tk.TOP, anchor="e")
        self.countdown_label = tk.Label(timer_box, text="", bg="#1a1a1a", fg=self.clr_cyan,
                                        font=("Share Tech Mono", 14, "bold"))
        self.countdown_label.pack(side=tk.LEFT, padx=5)
        self.light_canvas = tk.Canvas(timer_box, width=15, height=15, bg="#1a1a1a", highlightthickness=0)
        self.light_bulb = self.light_canvas.create_oval(2, 2, 13, 13, fill=self.clr_gray)
        self.light_canvas.pack(side=tk.LEFT, padx=5)
        self.update_clock()

        ctrl = tk.Frame(self.root, bg=self.clr_bg, pady=10)
        ctrl.pack(fill=tk.X, padx=20, pady=10)
        config_border = tk.LabelFrame(ctrl, text=" ⚡ TACTICAL PARAMETERS ⚡ ", bg=self.clr_bg, fg=self.clr_cyan,
                                      font=("Orbitron", 10, "bold"), labelanchor="nw", padx=15, pady=10,
                                      highlightthickness=1, highlightbackground="#30363D")
        config_border.pack(fill=tk.X)

        r1 = tk.Frame(config_border, bg=self.clr_bg)
        r1.pack(fill=tk.X, pady=5)
        tk.Label(r1, text="物理架构:", bg=self.clr_bg, fg="#8B949E", font=self.font_main).pack(side=tk.LEFT)
        self.os_combo = ttk.Combobox(r1, values=["Android", "iOS"], width=8, state="readonly", font=self.font_main)
        self.os_combo.current(1);
        self.os_combo.pack(side=tk.LEFT, padx=(5, 15))

        tk.Label(r1, text="演算核心:", bg=self.clr_bg, fg="#8B949E", font=self.font_main).pack(side=tk.LEFT)
        self.plat_combo = ttk.Combobox(r1, values=list(PLATFORMS.keys()), width=15, state="readonly",
                                       font=self.font_main)
        self.plat_combo.current(0);
        self.plat_combo.pack(side=tk.LEFT, padx=(5, 15))

        # 移除外部白色选中框：highlightthickness=0
        tk.Label(r1, text="授权协议(KEY):", bg=self.clr_bg, fg="#8B949E", font=self.font_main).pack(side=tk.LEFT)
        self.key_entry = tk.Entry(r1, bg=self.clr_entry_bg, fg=self.clr_cyan, width=25, font=("Monaco", 12),
                                  relief=tk.SOLID, bd=0, highlightthickness=0)
        self.key_entry.insert(0, "")
        self.key_entry.pack(side=tk.LEFT, padx=(5, 15), ipady=4)

        tk.Label(r1, text="情报同步:", bg=self.clr_bg, fg="#8B949E", font=self.font_main).pack(side=tk.LEFT)
        self.wechat_target = tk.Entry(r1, bg=self.clr_entry_bg, fg=self.clr_cyan, width=15, font=self.font_main,
                                      relief=tk.SOLID, bd=0, highlightthickness=0)
        self.wechat_target.pack(side=tk.LEFT, padx=5, ipady=4)

        r2 = tk.Frame(config_border, bg=self.clr_bg)
        r2.pack(fill=tk.X, pady=10)
        tk.Label(r2, text="作战协议:", bg=self.clr_bg, fg="#8B949E", font=self.font_main).pack(side=tk.LEFT)
        b_sty = {"width": 120, "height": 35, "borderless": 1, "font": ("Heiti SC", 12, "bold")}
        self.btn_m1 = MacButton(r2, text="瞬时打击", bg=self.clr_cyan, fg="#000",
                                command=lambda: self.switch_mode("SINGLE"), **b_sty)
        self.btn_m1.pack(side=tk.LEFT, padx=12)
        self.btn_m2 = MacButton(r2, text="相位偏移", bg=self.clr_gray, fg="#FFF",
                                command=lambda: self.switch_mode("DELAY"), **b_sty)
        self.btn_m2.pack(side=tk.LEFT, padx=12)
        self.btn_m3 = MacButton(r2, text="递归监控", bg=self.clr_gray, fg="#FFF",
                                command=lambda: self.switch_mode("CYCLE"), **b_sty)
        self.btn_m3.pack(side=tk.LEFT, padx=12)

        # 延时和脉冲输入框：黑色底纹，无边框
        tk.Label(r2, text="延时能级(m):", bg=self.clr_bg, fg="#8B949E", font=self.font_main).pack(side=tk.LEFT,
                                                                                                  padx=(20, 0))
        self.entry_total = tk.Entry(r2, bg=self.clr_disabled_bg, fg=self.clr_cyan, width=8, state="disabled",
                                    font=("Monaco", 12), relief=tk.SOLID, bd=0, highlightthickness=0)
        self.entry_total.pack(side=tk.LEFT, padx=5, ipady=3)

        tk.Label(r2, text="脉冲频率(m):", bg=self.clr_bg, fg="#8B949E", font=self.font_main).pack(side=tk.LEFT,
                                                                                                  padx=(15, 0))
        self.entry_interval = tk.Entry(r2, bg=self.clr_disabled_bg, fg=self.clr_cyan, width=8, state="disabled",
                                       font=("Monaco", 12), relief=tk.SOLID, bd=0, highlightthickness=0)
        self.entry_interval.pack(side=tk.LEFT, padx=5, ipady=3)

        r3 = tk.Frame(config_border, bg=self.clr_bg)
        r3.pack(fill=tk.X, pady=5)
        self.prompt_input = tk.Text(r3, bg=self.clr_entry_bg, fg="#E6EDF3", height=3, font=("Heiti SC", 14),
                                    padx=12, pady=10, relief=tk.SOLID, bd=0, highlightthickness=0)
        self.prompt_input.insert("1.0", "打开微信检查是否有未读消息。如果有，依次回复。处理完返回。")
        self.prompt_input.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        btns = tk.Frame(r3, bg=self.clr_bg)
        btns.pack(side=tk.RIGHT, padx=(15, 0))
        self.btn_go = MacButton(btns, text=" 启动序列 \n ENGAGE ", bg=self.clr_army, fg="#000", width=140, height=50,
                                borderless=1, font=("Orbitron", 10, "bold"), command=self.handle_start)
        self.btn_go.pack(pady=2)
        self.btn_stop = MacButton(btns, text=" 紧急熔断 \n ABORT ", bg=self.clr_gray, fg="#FFF", width=140, height=50,
                                  borderless=1, font=("Orbitron", 10, "bold"), state="disabled",
                                  command=self.handle_stop)
        self.btn_stop.pack(pady=2)

        mon_frame = tk.Frame(self.root, bg=self.clr_bg)
        mon_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        self.paned = tk.PanedWindow(mon_frame, orient=tk.HORIZONTAL, bg="#333", sashwidth=4, bd=0)
        self.paned.pack(fill=tk.BOTH, expand=True)
        self.thought_area = tk.Text(self.paned, bg=self.clr_entry_bg, fg=self.clr_army, font=self.console_font, bd=0,
                                    highlightthickness=0)
        self.action_area = tk.Text(self.paned, bg=self.clr_entry_bg, fg=self.clr_action, font=self.console_font, bd=0,
                                   highlightthickness=0)
        self.paned.add(self.thought_area, stretch="always")
        self.paned.add(self.action_area, stretch="always")

    # --- 核心逻辑控制 ---

    def handle_start(self):
        self.is_manual_stop = False

        # 验证输入项
        if self.current_mode == "DELAY":
            if not self.entry_total.get().strip():
                self.log("❌ 启动失败：相位偏移协议需设置[延时能级]");
                return
        elif self.current_mode == "CYCLE":
            if not self.entry_total.get().strip() or not self.entry_interval.get().strip():
                self.log("❌ 启动失败：递归监控协议需设置[延时能级]与[脉冲频率]");
                return

        self.lock_ui(True)

        if self.current_mode == "SINGLE":
            self.set_status_ui(color=self.clr_red, text="CORE_HOT")
            self.trigger_execution_flow()
        elif self.current_mode == "DELAY":
            wait_sec = int(self.entry_total.get()) * 60
            self.start_delay_timer(wait_sec)
        elif self.current_mode == "CYCLE":
            self.cycle_start_time = time.time()  # 记录递归开始时刻
            self.set_status_ui(color=self.clr_cyan, text="GRID_RECURSIVE")
            self.trigger_execution_flow()  # 递归第一次运行

    def start_delay_timer(self, seconds):
        if seconds > 0 and not self.is_manual_stop:
            self.set_status_ui(color=self.clr_cyan, text=f"T-MINUS {seconds}s", flash=True)
            self.root.after(1000, lambda: self.start_delay_timer(seconds - 1))
        elif seconds <= 0 and not self.is_manual_stop:
            self.set_status_ui(color=self.clr_cyan, text="PHASE_ACTIVE", flash=False)
            self.trigger_execution_flow()

    def start_cycle_wait(self, seconds):
        """递归循环中的倒计时逻辑"""
        if seconds > 0 and not self.is_manual_stop:
            self.set_status_ui(color=self.clr_cyan, text=f"NEXT_PULSE {seconds}s", flash=True)
            self.root.after(1000, lambda: self.start_cycle_wait(seconds - 1))
        elif seconds <= 0 and not self.is_manual_stop:
            # 检查总时间是否超出
            total_limit_min = float(self.entry_total.get())
            elapsed_min = (time.time() - self.cycle_start_time) / 60
            if elapsed_min < total_limit_min:
                self.set_status_ui(color=self.clr_cyan, text="PULSE_ACTIVE", flash=False)
                self.trigger_execution_flow()
            else:
                self.log("🏁 延时能级已耗尽，递归序列自动终止。")
                self.handle_stop()

    def trigger_execution_flow(self):
        if self.os_combo.get() == "iOS":
            threading.Thread(target=self._full_diagnosis, daemon=True).start()
        else:
            self.execute_engine()

    def _full_diagnosis(self):
        self.log("🚀 [DIAGNOSIS] 链路探测中...")
        try:
            if not self.wda_iproxy_process:
                self.wda_iproxy_process = subprocess.Popen(["iproxy", "8100", "8100"], stdout=subprocess.PIPE,
                                                           stderr=subprocess.STDOUT)
                time.sleep(1)
            if requests.get("http://127.0.0.1:8100/status", timeout=2).status_code == 200:
                self.root.after(0, self.execute_engine)
                return True
        except:
            pass

        # 简化的 iOS 诊断轮询
        for i in range(5):
            if self.is_manual_stop: return
            try:
                if requests.get("http://127.0.0.1:8100/status", timeout=2).status_code == 200:
                    self.root.after(0, self.execute_engine);
                    return True
            except:
                time.sleep(2)
        self.log("❌ 链路超时，请检查 WDA 状态");
        self.handle_stop()

    def execute_engine(self):
        prompt = self.prompt_input.get("1.0", tk.END).strip()
        target = self.wechat_target.get().strip()
        if target: prompt = f"找到并进入与 {target} 的对话。{prompt}"
        api_key = self.key_entry.get().strip()
        threading.Thread(target=self._worker, args=(prompt, api_key), daemon=True).start()

    def _worker(self, prompt, api_key):
        p_dir = os.path.dirname(os.path.abspath(__file__))
        py_exe = os.path.join(p_dir, "venv", "bin", "python")
        main_py = os.path.join(p_dir, "main.py")
        plat = PLATFORMS[self.plat_combo.get()]
        cmd = [py_exe, "-u", main_py, "--base-url", plat["base_url"], "--model", plat["model"], "--apikey", api_key]
        cmd.extend(["--device-type", "ios" if self.os_combo.get() == "iOS" else "adb"])
        if self.os_combo.get() == "iOS": cmd.extend(["--wda-url", "http://127.0.0.1:8100"])
        cmd.append(prompt)

        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            while True:
                line = self.process.stdout.readline()
                if not line and self.process.poll() is not None: break
                if line: self.root.after(0, self._parse_log, line)
        finally:
            self.root.after(0, self.on_task_finish)

    def on_task_finish(self):
        """任务结束后的判断逻辑"""
        if self.wda_iproxy_process: self.wda_iproxy_process.terminate(); self.wda_iproxy_process = None

        if self.current_mode == "CYCLE" and not self.is_manual_stop:
            # 递归监控逻辑：检查是否需要下一次脉冲
            total_limit_min = float(self.entry_total.get())
            elapsed_min = (time.time() - self.cycle_start_time) / 60
            if elapsed_min < total_limit_min:
                interval_sec = int(self.entry_interval.get()) * 60
                self.log(f"🔄 单次任务结束。脉冲频率：{self.entry_interval.get()}m，开始倒计时...")
                self.start_cycle_wait(interval_sec)
            else:
                self.log("🏁 延时能级耗尽。")
                self.handle_stop()
        else:
            self.handle_stop()

    def handle_stop(self):
        self.is_manual_stop = True
        self.is_flashing = False
        if self.process: self.process.terminate(); self.process = None
        if self.wda_iproxy_process: self.wda_iproxy_process.terminate(); self.wda_iproxy_process = None
        self.set_status_ui(color=self.clr_gray, text="", flash=False)
        self.lock_ui(False)

    # --- UI 辅助 ---

    def set_status_ui(self, color=None, text="", flash=False):
        self.is_flashing = flash
        self.countdown_label.config(text=text, fg=color if color else self.clr_cyan)
        if not flash:
            self.light_canvas.itemconfig(self.light_bulb, fill=color if color else self.clr_gray)
        else:
            self._flash_loop(color)

    def _flash_loop(self, color):
        if self.is_flashing:
            curr = self.light_canvas.itemcget(self.light_bulb, "fill")
            self.light_canvas.itemconfig(self.light_bulb, fill=color if curr == self.clr_gray else self.clr_gray)
            self.root.after(500, lambda: self._flash_loop(color))

    def switch_mode(self, mode):
        self.current_mode = mode
        for b in [self.btn_m1, self.btn_m2, self.btn_m3]: b.config(bg=self.clr_gray, fg="#FFF")
        if mode == "SINGLE":
            self.btn_m1.config(bg=self.clr_cyan, fg="#000"); self._toggle_entries(False, False)
        elif mode == "DELAY":
            self.btn_m2.config(bg=self.clr_cyan, fg="#000"); self._toggle_entries(True, False)
        elif mode == "CYCLE":
            self.btn_m3.config(bg="#FFD700", fg="#000"); self._toggle_entries(True, True)

    def _toggle_entries(self, t, i):
        self.entry_total.config(state="normal" if t else "disabled",
                                bg=self.clr_entry_bg if t else self.clr_disabled_bg)
        self.entry_interval.config(state="normal" if i else "disabled",
                                   bg=self.clr_entry_bg if i else self.clr_disabled_bg)

    def log(self, msg):
        tag = f"[{datetime.now().strftime('%H:%M:%S')}] "
        self.thought_area.insert(tk.END, f"{tag}{msg}\n");
        self.thought_area.see(tk.END)

    def _parse_log(self, line):
        clean_line = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', line).strip()
        if not clean_line: return
        if '"action"' in clean_line or "🎯" in clean_line: self.is_recording_action = True
        if self.is_recording_action:
            self.action_area.insert(tk.END, line);
            self.action_area.see(tk.END)
            if "}" in clean_line or "====" in clean_line: self.is_recording_action = False
        else:
            self.thought_area.insert(tk.END, line); self.thought_area.see(tk.END)

    def update_clock(self):
        self.time_label.config(text=datetime.now().strftime('%Y-%m-%d %H:%M:%S %p'))
        self.root.after(1000, self.update_clock)

    def lock_ui(self, locked):
        self.btn_go.config(state="disabled" if locked else "normal")
        self.btn_stop.config(state="normal" if locked else "disabled", bg=self.clr_red if locked else self.clr_gray)


if __name__ == "__main__":
    root = tk.Tk();
    ttk.Style().theme_use('clam');
    app = CombatPlatformGUI(root);
    root.mainloop()
import os
import sys
import threading
from rembg import remove, new_session
from PIL import Image
import customtkinter as ctk
from tkinter import messagebox
import windnd

def get_base_path():
    """获取程序运行根目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

class Coconut_AI_Remover(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # 基础设置：稳定的横向长方形
        self.title("AI智能抠图工具")
        self.geometry("600x350")
        self.resizable(True, True) 
        ctk.set_appearance_mode("dark")
        
        # 图标设置
        self.icon_path = os.path.join(get_base_path(), "app.ico")
        if os.path.exists(self.icon_path):
            try:
                self.iconbitmap(self.icon_path)
            except: pass

        self.session = None 
        self.is_ready = False

        # --- UI 布局 ---
        # 顶部留白
        ctk.CTkLabel(self, text="", height=60).pack()

        # 主标题区
        self.main_title = ctk.CTkLabel(self, text="椰子牌", font=("Microsoft YaHei UI", 36, "bold"), text_color="#FFFFFF")
        self.main_title.pack(pady=(0, 5))
        
        self.sub_title = ctk.CTkLabel(self, text="智能抠图工具", font=("Microsoft YaHei UI", 22), text_color="#FFFFFF")
        self.sub_title.pack(pady=(0, 15))
        
        self.hint_label = ctk.CTkLabel(self, text="将图片拖入此处自动开始批量处理", font=("Microsoft YaHei UI", 13), text_color="#444444")
        self.hint_label.pack()

        # 状态反馈 (居中显示)
        self.status_label = ctk.CTkLabel(self, text="初始化中...", text_color="#F39C12", font=("Microsoft YaHei UI", 12))
        self.status_label.pack(side="bottom", pady=(0, 40))

        # 底部贴合进度条 (全宽感设计)
        self.progress = ctk.CTkProgressBar(self, height=2, corner_radius=0, fg_color="#1A1A1A", progress_color="#FFFFFF")
        self.progress.pack(side="bottom", fill="x")
        self.progress.set(0)

        # 右下角署名 (在进度条上方一点点)
        self.author_label = ctk.CTkLabel(self, text="Produced by princwang", font=("Consolas", 10), text_color="#2A2A2A")
        self.author_label.place(relx=0.98, rely=0.94, anchor="se")

        # 引擎加载
        threading.Thread(target=self.init_ai_engine, daemon=True).start()
        windnd.hook_dropfiles(self, self.handle_drop)

    def init_ai_engine(self):
        try:
            base_dir = get_base_path()
            m_path = os.path.join(base_dir, "u2net.onnx")
            
            if not os.path.exists(m_path):
                raise FileNotFoundError("缺失 u2net.onnx 模型文件")

            # 环境隔离重定向，确保删掉 C 盘文件夹后依然能读本地
            os.environ["U2NET_HOME"] = base_dir
            self.session = new_session(model_name="u2net", model_path=m_path, providers=['CPUExecutionProvider'])
            
            if self.session:
                self.is_ready = True
                self.after(0, lambda: self.status_label.configure(text="● 离线模式已就绪", text_color="#22c55e"))
        except Exception as e:
            self.after(0, lambda err=str(e): self.status_label.configure(text=f"系统异常: {err}", text_color="#e74c3c"))

    def handle_drop(self, files):
        if not self.is_ready:
            messagebox.showwarning("加载中", "请等待 AI 引擎初始化完成...")
            return
        
        paths = []
        for f in files:
            try:
                p = f.decode('gbk')
                if p.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.bmp')):
                    paths.append(p)
            except: continue
            
        if paths:
            self.progress.set(0)
            threading.Thread(target=self.batch_process, args=(paths,), daemon=True).start()

    def batch_process(self, paths):
        total = len(paths)
        for i, path in enumerate(paths):
            try:
                self.after(0, lambda f=os.path.basename(path): self.status_label.configure(text=f"正在抠图: {f}", text_color="#FFFFFF"))
                input_img = Image.open(path).convert("RGBA")
                output = remove(input_img, session=self.session, alpha_matting=True)
                output.save(f"{os.path.splitext(path)[0]}_no_bg.png")
                self.after(0, lambda x=(i+1)/total: self.progress.set(x))
            except Exception as e: print(e)
                
        self.after(0, lambda: self.status_label.configure(text=f"处理完成 (共 {total} 张)", text_color="#22c55e"))
        messagebox.showinfo("完成", f"已成功处理 {total} 张图片。")

if __name__ == "__main__":
    app = Coconut_AI_Remover()
    app.mainloop()
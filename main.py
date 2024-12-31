import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import pyperclip
import pytesseract
from PIL import ImageGrab, Image, ImageTk
import pandas as pd
import os

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR识别工具")
        self.history = []

        # 设置TESSDATA_PREFIX环境变量
        tessdata_dir = '/opt/homebrew/share/tessdata'
        if 'TESSDATA_PREFIX' not in os.environ:
            os.environ['TESSDATA_PREFIX'] = tessdata_dir

        # 检查TESSDATA_PREFIX环境变量是否正确设置
        if not os.path.exists(os.path.join(os.environ['TESSDATA_PREFIX'], 'chi_sim.traineddata')):
            messagebox.showerror("错误", f"未找到中文语言文件: {os.path.join(os.environ['TESSDATA_PREFIX'], 'chi_sim.traineddata')}\n请确保 'chi_sim.traineddata' 文件存在于 {tessdata_dir} 目录中。\n可以从以下链接下载: https://github.com/tesseract-ocr/tessdata/raw/main/chi_sim.traineddata")
            return

        self.label = tk.Label(root, text="点击识别按钮从剪切板获取图片并进行OCR识别")
        self.label.pack(pady=10)

        # 新增图片显示区域
        self.image_label = tk.Label(root)
        self.image_label.pack(pady=10)
        self.image_label.bind("<Button-1>", self.show_image_in_popup)  # 绑定点击事件

        self.result_text = tk.Text(root, height=10, width=50)
        self.result_text.pack(pady=10)

        self.recognize_button = tk.Button(root, text="识别", command=self.recognize)
        self.recognize_button.pack(pady=5)

        self.export_button = tk.Button(root, text="导出历史记录", command=self.export_history)
        self.export_button.pack(pady=5)

        # 新增按钮以查看和编辑历史记录
        self.view_history_button = tk.Button(root, text="查看历史记录", command=self.view_history)
        self.view_history_button.pack(pady=5)

    def recognize(self):
        image = ImageGrab.grabclipboard()
        if image is None:
            messagebox.showwarning("警告", "剪切板中没有图片")
            return

        # 将图像转换为PNG格式
        temp_path = "temp_image.png"
        image = image.convert("RGB")  # 确保图像为RGB模式
        image.save(temp_path, format="PNG")

        try:
            text = pytesseract.image_to_string(Image.open(temp_path), lang='chi_sim')
            text = text.replace(" ", "")  # 去除识别结果中的空格
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, text)
            self.history.append(text)

            # 显示图片
            photo = Image.open(temp_path)
            width, height = photo.size
            ratio = 300 / width
            new_height = int(height * ratio)
            photo = photo.resize((300, new_height), Image.LANCZOS)  # 保持宽度为300，高度按比例调整
            photo_tk = ImageTk.PhotoImage(photo)
            self.image_label.config(image=photo_tk)
            self.image_label.image = photo_tk  # 保持对图片对象的引用
        except Exception as e:
            messagebox.showerror("错误", f"识别失败: {str(e)}")
        finally:
            os.remove(temp_path)

    def export_history(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if file_path:
            df = pd.DataFrame([self.history], columns=["识别结果"])  # 去除每个识别结果中的换行符
            df.to_csv(file_path, index=False)
            messagebox.showinfo("成功", f"历史记录已导出到 {file_path}")

    # 新增方法以打开历史记录窗口
    def view_history(self):
        HistoryWindow(self.history, self.update_history)

    # 新增方法以更新历史记录
    def update_history(self, new_history):
        self.history = new_history

    # 新增方法以在新窗口中显示图片
    def show_image_in_popup(self, event):
        image = ImageGrab.grabclipboard()
        if image is None:
            messagebox.showwarning("警告", "剪切板中没有图片")
            return

        popup = tk.Toplevel(self.root)
        popup.title("图片查看")
        photo = ImageTk.PhotoImage(image)
        image_label = tk.Label(popup, image=photo)
        image_label.image = photo  # 保持对图片对象的引用
        image_label.pack(pady=10)

    # 新增方法以删除特定的历史记录条目
    def delete_entry(self, index):
        del self.history[index]
        self.update_history(self.history)

# 新增类以显示和编辑历史记录
class HistoryWindow:
    def __init__(self, history, update_callback):
        self.window = tk.Toplevel()
        self.window.title("历史记录")
        self.update_callback = update_callback
        self.text_widgets = []  # 用于存储Text小部件的列表

        for i, entry in enumerate(history):
            text_frame = tk.Frame(self.window)
            text_frame.pack(pady=5, fill=tk.X)

            text_widget = tk.Text(text_frame, height=5, width=80)
            text_widget.insert(tk.END, entry)
            text_widget.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            self.text_widgets.append(text_widget)

            delete_button = tk.Button(text_frame, text="删除", command=lambda i=i: self.delete_entry(i))
            delete_button.pack(side=tk.RIGHT, padx=5)

        self.save_button = tk.Button(self.window, text="保存", command=self.save_history)
        self.save_button.pack(pady=5)

    def delete_entry(self, index):
        self.text_widgets[index].destroy()
        del self.text_widgets[index]
        self.save_history()

    def save_history(self):
        new_history = [text_widget.get("1.0", tk.END).strip() for text_widget in self.text_widgets]
        self.update_callback(new_history)
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()